import gradio as gr
import random
import re
import smtplib
import os
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# =========================================================
# 1. GMAIL CONFIGURATION
# =========================================================
SENDER_EMAIL = "mohammedsamad475@gmail.com"        # 👈 Your Gmail address
SENDER_PASSWORD = "eqqz srwy qhzl qhas"       # 👈 Your 16-digit Gmail App Password

# =========================================================
# 2. PDF GENERATOR & EMAIL DISPATCH ENGINES
# =========================================================
def generate_pdf_ticket(pnr, passenger_name, email, flight_info, seat_info, total_price, refund_policy):
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
            ["Refund Policy:", refund_policy],
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
        print(f"PDF Error: {e}")
        return None

def send_real_email(to_email, subject, body_text, pdf_path=None):
    clean_pwd = SENDER_PASSWORD.replace(" ", "")
    if "xxxx" in clean_pwd or len(clean_pwd) == 0:
        return f"⚠️ [SMTP NOTICE]: Gmail App Password missing. Email simulated for '{to_email}'."

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
        return f"📧 [REAL EMAIL SENT]: Successfully delivered to '{to_email}'!"
    except Exception as e:
        return f"❌ Email Error: {str(e)}"

# =========================================================
# 3. BACKEND FLIGHT DATA & SESSION STATE
# =========================================================
CITIES_MAP = {
    "delhi": "Delhi (DEL)", "london": "London (LHR)",
    "dubai": "Dubai (DXB)", "mumbai": "Mumbai (BOM)",
    "bengaluru": "Bengaluru (BLR)", "new york": "New York (JFK)"
}

agent_session_data = {
    "source": "Dubai (DXB)",
    "dest": "Delhi (DEL)",
    "date": "2026-09-12",
    "passenger": "Samad",
    "email": "imission418@gmail.com",
    "selected_flight": None,
    "selected_seat": None,
    "step": "SEARCH",
    "otp": None,
    "pnr": None,
    "price": 45000
}

def get_flight_options(source, dest, date_str):
    return (
        f"✈️ **SkyNav Search Results ({source} ➔ {dest}) | Date: {date_str}**\n\n"
        f"1️⃣ **Air India (AI-502)** | Dep: 08:00 AM | Price: ₹42,000\n"
        f"2️⃣ **Emirates (EK-513)** | Dep: 02:30 PM | Price: ₹48,000\n"
        f"3️⃣ **IndiGo (6E-95)** | Dep: 10:15 PM | Price: ₹38,000\n"
    )

# =========================================================
# 4. CHAT RESPONSE FUNCTION (STATE WORKFLOW ENGINE)
# =========================================================
def ai_agent_response(message, history):
    global agent_session_data
    msg_lower = message.lower().strip()
    words = re.findall(r'\b\w+\b', msg_lower)

    # Extract Cities & Dates dynamically
    found_cities = [city_full for city_key, city_full in CITIES_MAP.items() if city_key in msg_lower]
    date_match = re.search(r'\d{2,4}[-/]\d{1,2}[-/]\d{2,4}', message)
    if date_match:
        agent_session_data["date"] = date_match.group(0)

    # STEP 1: Verify OTP (Final Step)
    if re.match(r'^\d{6}$', message.strip()):
        input_otp = message.strip()
        if agent_session_data["otp"] and input_otp == agent_session_data["otp"]:
            pdf_file = generate_pdf_ticket(
                pnr=agent_session_data["pnr"],
                passenger_name=agent_session_data["passenger"],
                email=agent_session_data["email"],
                flight_info=f"{agent_session_data['source']} ➔ {agent_session_data['dest']} | Date: {agent_session_data['date']}",
                seat_info=agent_session_data["selected_seat"],
                total_price=agent_session_data["price"],
                refund_policy="Standard Non-Refundable Premium"
            )

            ticket_res = send_real_email(
                to_email=agent_session_data["email"],
                subject=f"✈️ E-Ticket Confirmation - PNR: {agent_session_data['pnr']}",
                body_text="Your payment is successful! Your official PDF E-Ticket is attached.",
                pdf_path=pdf_file
            )

            agent_session_data["step"] = "COMPLETED"
            return (
                f"🎉 **PAYMENT SUCCESSFUL & TICKET ISSUED!**\n\n"
                f"✅ **PNR:** {agent_session_data['pnr']}\n"
                f"🪑 **Seat Assigned:** {agent_session_data['selected_seat']}\n"
                f"📄 **PDF Generated:** `{pdf_file}`\n"
                f"📧 **Status:** {ticket_res}\n\n"
                f"Your official PDF E-Ticket has been delivered to your email. Safe travels!"
            )
        else:
            return "❌ Invalid OTP! Please enter the correct 6-digit code sent to your email."

    # STEP 2: Handle Seat Choice after Flight Selection
    elif agent_session_data["step"] == "SEAT_SELECTION":
        agent_session_data["selected_seat"] = message.strip().upper()
        agent_session_data["otp"] = str(random.randint(100000, 999999))
        agent_session_data["pnr"] = f"SKYN-{random.randint(1000, 9999)}"
        agent_session_data["step"] = "OTP"

        email_res = send_real_email(
            to_email=agent_session_data["email"],
            subject=f"🔑 SkyNav Payment OTP: {agent_session_data['otp']}",
            body_text=f"Your SkyNav Payment Authorization OTP for {agent_session_data['selected_flight']} (Seat {agent_session_data['selected_seat']}) is: {agent_session_data['otp']}"
        )

        return (
            f"✅ **Seat {agent_session_data['selected_seat']} Confirmed!**\n\n"
            f"✈️ **Flight:** {agent_session_data['selected_flight']}\n"
            f"📋 **Booking PNR:** {agent_session_data['pnr']}\n"
            f"💰 **Total Amount:** ₹{agent_session_data['price']:,}\n\n"
            f"🔒 A 6-digit security OTP has been sent to `{agent_session_data['email']}`.\n"
            f"({email_res})\n\n"
            f"Please enter the **6-digit OTP** here to authorize payment."
        )

   # STEP 3: Handle Flight Choice (Presents Real Airplane Seat Map)
    elif any(k in words for k in ["1", "2", "3", "emirates", "indigo"]) or "air india" in msg_lower:
        if "2" in words or "emirates" in words:
            agent_session_data["selected_flight"] = "Emirates (EK-513)"
            agent_session_data["price"] = 48000
        elif "3" in words or "indigo" in words:
            agent_session_data["selected_flight"] = "IndiGo (6E-95)"
            agent_session_data["price"] = 38000
        else:
            agent_session_data["selected_flight"] = "Air India (AI-502)"
            agent_session_data["price"] = 42000

        agent_session_data["step"] = "SEAT_SELECTION"

        airplane_seat_map_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Seat_map_A320.svg/800px-Seat_map_A320.svg.png"

        return (
            f"🎯 **Selected Flight:** {agent_session_data['selected_flight']}\n\n"
            f"✈️ **AIRCRAFT CABIN SEAT MAP**\n\n"
            f"![Aircraft Seat Map]({airplane_seat_map_url})\n\n"
            f"📍 **Seat Location & Availability Guide:**\n"
            f"* 👑 **Business Class (Front Section - Rows 1-5):**\n"
            f"  * `1A` ➔ Front Left Window\n"
            f"  * `1C` ➔ Front Left Aisle\n"
            f"  * `2D` ➔ Front Right Aisle\n"
            f"* 🚀 **Extra Legroom Seats (Exit Rows 11-12):**\n"
            f"  * `11A` ➔ Exit Row Left Window\n"
            f"  * `11C` ➔ Exit Row Left Aisle\n"
            f"  * `12F` ➔ Exit Row Right Window\n"
            f"* 💺 **Standard Economy (Rows 14-38):**\n"
            f"  * `14A` ➔ Economy Window\n"
            f"  * `15B` ➔ Economy Middle\n"
            f"  * `25C` ➔ Economy Aisle\n\n"
            f"👉 **How to Book:** Simply type your desired seat code (e.g., `11C` or `1A`) into the chat box below to select it!"
        )
    
    # STEP 4: Initial Search Request
    elif len(found_cities) >= 2 or any(k in words for k in ["book", "fly", "flight"]):
        if len(found_cities) >= 2:
            agent_session_data["source"] = found_cities[0]
            agent_session_data["dest"] = found_cities[1]

        flights = get_flight_options(agent_session_data["source"], agent_session_data["dest"], agent_session_data["date"])
        return (
            f"Understood! Here are the extracted booking details:\n\n"
            f"🔍 **AI Agent Log:** Source: `{agent_session_data['source']}`, Destination: `{agent_session_data['dest']}`, Date: `{agent_session_data['date']}`\n\n"
            f"Available Flight Options:\n\n{flights}\n"
            f"Reply with **1** (Air India), **2** (Emirates), or **3** (IndiGo) to select your flight!"
        )

    # STEP 5: Standalone Greetings
    elif any(greeting in words for greeting in ["hello", "hi", "hey"]):
        return "Hello! I am your SkyNav AI Travel Agent. Where would you like to travel?"

    else:
        return "I can assist you! Reply with **1**, **2**, or **3** to pick a flight, or enter a request like: *'I want to book a flight from Dubai to Delhi 2026-09-12'*."

# =========================================================
# 5. GRADIO UI LAUNCHER
# =========================================================
demo = gr.ChatInterface(
    fn=ai_agent_response,
    title="✈️ SkyNav AI: Autonomous Travel Agent",
    description="Command the AI agent in natural English (e.g., `I want to book a flight from Dubai to Delhi 2026-09-12`)"
)

demo.launch(share=True)
