import streamlit as st
import random
import re
import smtplib
import os
import tempfile
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# =========================================================
# 1. CONFIG — credentials come from Streamlit secrets / env vars,
#    NEVER hardcoded here. See .streamlit/secrets.toml.example.
# =========================================================
st.set_page_config(page_title="SkyNav AI Travel Agent", page_icon="✈️", layout="centered")


def get_secret(key: str):
    try:
        return st.secrets[key]
    except Exception:
        return os.environ.get(key)


SENDER_EMAIL = get_secret("GMAIL_ADDRESS")
SENDER_PASSWORD = get_secret("GMAIL_APP_PASSWORD")

# =========================================================
# 2. PDF GENERATOR & EMAIL DISPATCH ENGINES
# =========================================================
def generate_pdf_ticket(pnr, passenger_name, email, flight_info, seat_info, total_price, refund_policy):
    try:
        filename = os.path.join(tempfile.gettempdir(), f"Ticket_{pnr}.pdf")
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle(
            "TitleStyle", parent=styles["Heading1"], fontSize=18, textColor=colors.HexColor("#0284c7")
        )
        story.append(Paragraph("✈️ SkyNav Global Aviation - Official E-Ticket", title_style))
        story.append(Spacer(1, 10))

        data = [
            ["PNR / Ticket ID:", pnr],
            ["Passenger Name:", passenger_name],
            ["Passenger Email:", email],
            ["Flight Route & Details:", flight_info],
            ["Assigned Seat:", seat_info],
            ["Total Amount Paid:", f"INR {total_price:,}"],
            ["Refund Policy:", refund_policy],
            ["Booking Status:", "CONFIRMED & ISSUED ✅"],
        ]

        t = Table(data, colWidths=[140, 320])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f9ff")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1e293b")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        story.append(t)
        doc.build(story)
        return filename
    except Exception as e:
        st.error(f"PDF generation error: {e}")
        return None


def send_real_email(to_email, subject, body_text, pdf_path=None):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        return f"⚠️ Email not configured — simulated send to '{to_email}'."

    clean_pwd = SENDER_PASSWORD.replace(" ", "")
    try:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = f"SkyNav AI Assistant <{SENDER_EMAIL}>"
        msg["To"] = to_email
        msg.attach(MIMEText(body_text, "plain"))

        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                part = MIMEApplication(f.read(), _subtype="pdf")
                part.add_header("Content-Disposition", "attachment", filename=os.path.basename(pdf_path))
                msg.attach(part)

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.starttls()
            server.login(SENDER_EMAIL, clean_pwd)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        return f"📧 Email sent to '{to_email}'."
    except Exception as e:
        return f"❌ Email error: {e}"


# =========================================================
# 3. STATIC FLIGHT DATA
# =========================================================
CITIES_MAP = {
    "delhi": "Delhi (DEL)",
    "london": "London (LHR)",
    "dubai": "Dubai (DXB)",
    "mumbai": "Mumbai (BOM)",
    "bengaluru": "Bengaluru (BLR)",
    "new york": "New York (JFK)",
}


def get_flight_options(source, dest, date_str):
    return (
        f"✈️ **SkyNav Search Results ({source} ➔ {dest}) | Date: {date_str}**\n\n"
        f"1️⃣ **Air India (AI-502)** | Dep: 08:00 AM | Price: ₹42,000\n"
        f"2️⃣ **Emirates (EK-513)** | Dep: 02:30 PM | Price: ₹48,000\n"
        f"3️⃣ **IndiGo (6E-95)** | Dep: 10:15 PM | Price: ₹38,000\n"
    )


# =========================================================
# 4. SESSION STATE
# =========================================================
def new_booking():
    return {
        "source": None,
        "dest": None,
        "date": None,
        "passenger": "",
        "email": "",
        "selected_flight": None,
        "selected_seat": None,
        "step": "SEARCH",
        "otp": None,
        "pnr": None,
        "price": 0,
        "pdf_path": None,
    }


def welcome_message():
    return {
        "role": "assistant",
        "content": (
            "Hello! I am your SkyNav AI Travel Agent. Where would you like to travel? "
            '(e.g. *"I want to fly from Dubai to Delhi on 2026-09-12"*)'
        ),
    }


if "booking" not in st.session_state:
    st.session_state.booking = new_booking()
if "messages" not in st.session_state:
    st.session_state.messages = [welcome_message()]


# =========================================================
# 5. CHAT LOGIC (STATE WORKFLOW ENGINE)
# =========================================================
def process_message(message: str) -> str:
    booking = st.session_state.booking
    msg_lower = message.lower().strip()
    words = re.findall(r"\b\w+\b", msg_lower)

    found_cities = [full for key, full in CITIES_MAP.items() if key in msg_lower]
    date_match = re.search(r"\d{2,4}[-/]\d{1,2}[-/]\d{2,4}", message)
    if date_match:
        booking["date"] = date_match.group(0)

    # STEP 1: Verify OTP (final step)
    if re.match(r"^\d{6}$", message.strip()):
        input_otp = message.strip()
        if booking["otp"] and input_otp == booking["otp"]:
            pdf_file = generate_pdf_ticket(
                pnr=booking["pnr"],
                passenger_name=booking["passenger"] or "Guest",
                email=booking["email"],
                flight_info=f"{booking['source']} ➔ {booking['dest']} | Date: {booking['date']}",
                seat_info=booking["selected_seat"],
                total_price=booking["price"],
                refund_policy="Standard Non-Refundable Premium",
            )
            ticket_res = send_real_email(
                to_email=booking["email"],
                subject=f"✈️ E-Ticket Confirmation - PNR: {booking['pnr']}",
                body_text="Your payment is successful! Your official PDF E-Ticket is attached.",
                pdf_path=pdf_file,
            )
            booking["step"] = "COMPLETED"
            booking["pdf_path"] = pdf_file
            return (
                f"🎉 **PAYMENT SUCCESSFUL & TICKET ISSUED!**\n\n"
                f"✅ **PNR:** {booking['pnr']}\n"
                f"🪑 **Seat Assigned:** {booking['selected_seat']}\n"
                f"📧 **Status:** {ticket_res}\n\n"
                f"Your ticket is ready — use the download button below the chat to grab the PDF."
            )
        else:
            return "❌ Invalid OTP! Please enter the correct 6-digit code sent to your email."

    # STEP 2: Handle seat choice after flight selection
    elif booking["step"] == "SEAT_SELECTION":
        booking["selected_seat"] = message.strip().upper()
        booking["otp"] = str(random.randint(100000, 999999))
        booking["pnr"] = f"SKYN-{random.randint(1000, 9999)}"
        booking["step"] = "OTP"

        email_res = send_real_email(
            to_email=booking["email"],
            subject=f"🔑 SkyNav Payment OTP: {booking['otp']}",
            body_text=(
                f"Your SkyNav Payment Authorization OTP for {booking['selected_flight']} "
                f"(Seat {booking['selected_seat']}) is: {booking['otp']}"
            ),
        )

        return (
            f"✅ **Seat {booking['selected_seat']} Confirmed!**\n\n"
            f"✈️ **Flight:** {booking['selected_flight']}\n"
            f"📋 **Booking PNR:** {booking['pnr']}\n"
            f"💰 **Total Amount:** ₹{booking['price']:,}\n\n"
            f"🔒 A 6-digit security OTP has been sent to `{booking['email']}`.\n"
            f"({email_res})\n\n"
            f"Please enter the **6-digit OTP** here to authorize payment."
        )

    # STEP 3: Handle flight choice (presents seat map)
    elif any(k in words for k in ["1", "2", "3", "emirates", "indigo"]) or "air india" in msg_lower:
        if "2" in words or "emirates" in words:
            booking["selected_flight"] = "Emirates (EK-513)"
            booking["price"] = 48000
        elif "3" in words or "indigo" in words:
            booking["selected_flight"] = "IndiGo (6E-95)"
            booking["price"] = 38000
        else:
            booking["selected_flight"] = "Air India (AI-502)"
            booking["price"] = 42000

        booking["step"] = "SEAT_SELECTION"
        seat_map_url = (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Seat_map_A320.svg/800px-Seat_map_A320.svg.png"
        )

        return (
            f"🎯 **Selected Flight:** {booking['selected_flight']}\n\n"
            f"✈️ **AIRCRAFT CABIN SEAT MAP**\n\n"
            f"![Aircraft Seat Map]({seat_map_url})\n\n"
            f"📍 **Seat Location & Availability Guide:**\n"
            f"* 👑 **Business Class (Rows 1-5):** `1A` · `1C` · `2D`\n"
            f"* 🚀 **Extra Legroom (Exit Rows 11-12):** `11A` · `11C` · `12F`\n"
            f"* 💺 **Standard Economy (Rows 14-38):** `14A` · `15B` · `25C`\n\n"
            f"👉 Type your desired seat code (e.g. `11C`) to select it!"
        )

    # STEP 4: Initial search request
    elif len(found_cities) >= 2 or any(k in words for k in ["book", "fly", "flight"]):
        if len(found_cities) >= 2:
            booking["source"] = found_cities[0]
            booking["dest"] = found_cities[1]
        else:
            booking["source"] = booking["source"] or "Dubai (DXB)"
            booking["dest"] = booking["dest"] or "Delhi (DEL)"
        booking["date"] = booking["date"] or "2026-09-12"

        flights = get_flight_options(booking["source"], booking["dest"], booking["date"])
        return (
            f"Got it! Here's what I found:\n\n"
            f"🔍 Source: `{booking['source']}`, Destination: `{booking['dest']}`, Date: `{booking['date']}`\n\n"
            f"{flights}\n"
            f"Reply with **1** (Air India), **2** (Emirates), or **3** (IndiGo) to select your flight!"
        )

    # STEP 5: Standalone greetings
    elif any(greeting in words for greeting in ["hello", "hi", "hey"]):
        return "Hello! I am your SkyNav AI Travel Agent. Where would you like to travel?"

    else:
        return (
            "I can assist you! Reply with **1**, **2**, or **3** to pick a flight, or tell me something like "
            '*"I want to book a flight from Dubai to Delhi 2026-09-12"*.'
        )


# =========================================================
# 6. UI
# =========================================================
st.title("✈️ SkyNav AI: Autonomous Travel Agent")
st.caption('Talk to the agent in natural English, e.g. *"I want to book a flight from Dubai to Delhi 2026-09-12"*')

with st.sidebar:
    st.header("Passenger details")
    st.session_state.booking["passenger"] = st.text_input(
        "Full name", value=st.session_state.booking["passenger"]
    )
    st.session_state.booking["email"] = st.text_input(
        "Email (for OTP & ticket)", value=st.session_state.booking["email"]
    )

    if not SENDER_EMAIL or not SENDER_PASSWORD:
        st.info(
            "Email sending isn't configured, so OTP/ticket emails will be simulated. "
            "Add GMAIL_ADDRESS and GMAIL_APP_PASSWORD to Streamlit secrets to send real emails."
        )

    st.divider()
    if st.button("🔄 Reset conversation"):
        st.session_state.booking = new_booking()
        st.session_state.messages = [welcome_message()]
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if not st.session_state.booking["email"]:
        reply = "Please enter your email in the sidebar first so I can send your OTP and ticket."
    else:
        reply = process_message(prompt)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)

pdf_path = st.session_state.booking.get("pdf_path")
if st.session_state.booking["step"] == "COMPLETED" and pdf_path and os.path.exists(pdf_path):
    with open(pdf_path, "rb") as f:
        st.download_button(
            "📄 Download your E-Ticket (PDF)",
            f,
            file_name=os.path.basename(pdf_path),
            mime="application/pdf",
        )
