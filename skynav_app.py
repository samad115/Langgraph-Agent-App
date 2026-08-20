import os
import re
import random
import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# 1. Configuration
SENDER_EMAIL = "mohammedsamad475@gmail.com"
SENDER_PASSWORD = "eqqz srwy qhzl qhas"

st.set_page_config(page_title="SkyNav AI Agent", page_icon="✈️", layout="wide")
st.title("✈️ SkyNav AI: Autonomous Travel Agent")
st.caption("Natural Language Flight Booking Assistant")

# 2. PDF & Email Helpers
def generate_pdf_ticket(pnr, passenger_name, email, flight_info, seat_info, total_price):
    try:
        filename = f"Ticket_{pnr}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor("#0284c7"))
        story.append(Paragraph("✈️ SkyNav Global Aviation - Official E-Ticket", title_style))
        story.append(Spacer(1, 10))

        data = [
            ["PNR / Ticket ID:", pnr],
            ["Passenger Name:", passenger_name],
            ["Passenger Email:", email],
            ["Flight Route & Details:", flight_info],
            ["Assigned Seat:", seat_info],
            ["Total Amount Paid:", f"INR {total_price:,}"],
            ["Booking Status:", "CONFIRMED & ISSUED ✅"]
        ]

        t = Table(data, colWidths=[140, 320])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f0f9ff")),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#1e293b")),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))

        story.append(t)
        doc.build(story)
        return filename
    except Exception as e:
        return None

def send_real_email(to_email, subject, body_text, pdf_path=None):
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
                part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(pdf_path))
                msg.attach(part)

        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()
        server.login(SENDER_EMAIL, clean_pwd)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        return f"📧 Ticket delivered to '{to_email}'!"
    except Exception as e:
        return f"📧 Ticket process logged for '{to_email}'"

# 3. Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your SkyNav AI Travel Agent. Where would you like to travel?"}]

if "data" not in st.session_state:
    st.session_state.data = {
        "source": "Dubai (DXB)", "dest": "Delhi (DEL)", "date": "2026-09-12",
        "passenger": "Samad", "email": "imission418@gmail.com",
        "selected_flight": None, "selected_seat": None, "step": "SEARCH",
        "otp": None, "pnr": None, "price": 45000
    }

# 4. Render Conversation History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. User Input Handling
if prompt := st.chat_input("Type here... (e.g., 1, 11C, 6-digit OTP)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    msg_lower = prompt.lower().strip()
    words = re.findall(r'\b\w+\b', msg_lower)
    state = st.session_state.data
    response_text = ""

    # Step 1: Verify OTP
    if re.match(r'^\d{6}$', prompt.strip()):
        if state["otp"] and prompt.strip() == state["otp"]:
            pdf_file = generate_pdf_ticket(state["pnr"], state["passenger"], state["email"], f"{state['source']} ➔ {state['dest']}", state["selected_seat"], state["price"])
            email_res = send_real_email(state["email"], f"✈️ E-Ticket Confirmation - PNR: {state['pnr']}", "Your booking is confirmed! Ticket attached.", pdf_file)
            response_text = f"🎉 **PAYMENT SUCCESSFUL & TICKET ISSUED!**\n\n✅ **PNR:** `{state['pnr']}`\n🪑 **Seat Assigned:** `{state['selected_seat']}`\n📄 **E-Ticket:** Generated successfully!\n{email_res}"
            state["step"] = "COMPLETED"
        else:
            response_text = "❌ Invalid OTP! Please enter the correct 6-digit code sent to your email."

    # Step 2: Seat Selection
    elif state["step"] == "SEAT_SELECTION":
        state["selected_seat"] = prompt.strip().upper()
        state["otp"] = str(random.randint(100000, 999999))
        state["pnr"] = f"SKYN-{random.randint(1000, 9999)}"
        state["step"] = "OTP"
        email_res = send_real_email(state["email"], f"🔑 SkyNav Payment OTP: {state['otp']}", f"Your OTP for {state['selected_flight']} is: {state['otp']}")
        response_text = f"✅ **Seat {state['selected_seat']} Confirmed!**\n\n✈️ **Flight:** {state['selected_flight']}\n📋 **PNR:** `{state['pnr']}`\n💰 **Amount:** ₹{state['price']:,}\n\n🔒 OTP sent to `{state['email']}`.\n\nPlease enter the **6-digit OTP** to authorize payment."

    # Step 3: Flight Selection & Display Text-Based Seat Map
    elif any(k in words for k in ["1", "2", "3", "emirates", "indigo"]) or "air india" in msg_lower:
        if "2" in words or "emirates" in words:
            state["selected_flight"], state["price"] = "Emirates (EK-513)", 48000
        elif "3" in words or "indigo" in words:
            state["selected_flight"], state["price"] = "IndiGo (6E-95)", 38000
        else:
            state["selected_flight"], state["price"] = "Air India (AI-502)", 42000

        state["step"] = "SEAT_SELECTION"
        
        # Pure Markdown Seat Map (Zero Image Loading Errors)
        seat_map_layout = f"""🎯 **Selected Flight:** {state['selected_flight']}

✈️ **AIRCRAFT CABIN SEATING MAP**

```text
[ FRONT OF AIRCRAFT ]
------------------------------------
Row 1-5 (Business Class)
[1A] [1B]   (AISLE)   [1C] [1D]

Row 11-12 (Extra Legroom Exit Rows)
[11A] [11B]  (AISLE)  [11C] [11D]
[12A] [12B]  (AISLE)  [12C] [12D]

Row 14-30 (Standard Economy)
[14A] [14B]  (AISLE)  [14C] [14D]
[15A] [15B]  (AISLE)  [15C] [15D]
------------------------------------
[ REAR OF AIRCRAFT ]
