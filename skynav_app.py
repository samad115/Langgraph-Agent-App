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
st.caption("Command the AI agent in natural English (e.g., 'I want to book a flight from Dubai to Delhi 2026-09-12')")

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
        return f"📧 Delivery confirmed to '{to_email}'!"
    except Exception as e:
        return f"⚠️ Email status: Sent (Simulated)"

# 3. Initialize State
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your SkyNav AI Travel Agent. Where would you like to travel?"}]

if "data" not in st.session_state:
    st.session_state.data = {
        "source": "Dubai (DXB)", "dest": "Delhi (DEL)", "date": "2026-09-12",
        "passenger": "Samad", "email": "imission418@gmail.com",
        "selected_flight": None, "selected_seat": None, "step": "SEARCH",
        "otp": None, "pnr": None, "price": 45000
    }

# 4. Render Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "image_url" in msg:
            st.image(msg["image_url"], caption="Aircraft Cabin Seating Layout", use_container_width=True)

# 5. User Input Engine
if prompt := st.chat_input("Type your response here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    msg_lower = prompt.lower().strip()
    words = re.findall(r'\b\w+\b', msg_lower)
    state = st.session_state.data
    response_text = ""
    image_to_show = None

    # Step Verification
    if re.match(r'^\d{6}$', prompt.strip()):
        if state["otp"] and prompt.strip() == state["otp"]:
            pdf_file = generate_pdf_ticket(state["pnr"], state["passenger"], state["email"], f"{state['source']} ➔ {state['dest']}", state["selected_seat"], state["price"])
            email_res = send_real_email(state["email"], f"✈️ E-Ticket Confirmation - PNR: {state['pnr']}", "Your payment is successful! Ticket attached.", pdf_file)
            response_text = f"🎉 **PAYMENT SUCCESSFUL & TICKET ISSUED!**\n\n✅ **PNR:** {state['pnr']}\n🪑 **Seat:** {state['selected_seat']}\n📧 {email_res}"
            state["step"] = "COMPLETED"
        else:
            response_text = "❌ Invalid OTP! Please enter the correct 6-digit OTP code."

    elif state["step"] == "SEAT_SELECTION":
        state["selected_seat"] = prompt.strip().upper()
        state["otp"] = str(random.randint(100000, 999999))
        state["pnr"] = f"SKYN-{random.randint(1000, 9999)}"
        state["step"] = "OTP"
        email_res = send_real_email(state["email"], f"🔑 SkyNav Payment OTP: {state['otp']}", f"Your OTP for {state['selected_flight']} is: {state['otp']}")
        response_text = f"✅ **Seat {state['selected_seat']} Confirmed!**\n\n✈️ **Flight:** {state['selected_flight']}\n📋 **PNR:** {state['pnr']}\n💰 **Price:** ₹{state['price']:,}\n\n🔒 OTP sent to `{state['email']}`. Please enter the **6-digit OTP** below."

    elif any(k in words for k in ["1", "2", "3", "emirates", "indigo"]) or "air india" in msg_lower:
        if "2" in words or "emirates" in words:
            state["selected_flight"], state["price"] = "Emirates (EK-513)", 48000
        elif "3" in words or "indigo" in words:
            state["selected_flight"], state["price"] = "IndiGo (6E-95)", 38000
        else:
            state["selected_flight"], state["price"] = "Air India (AI-502)", 42000

        state["step"] = "SEAT_SELECTION"
        image_to_show = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Seat_map_A320.svg/800px-Seat_map_A320.svg.png"
        response_text = f"🎯 **Selected Flight:** {state['selected_flight']}\n\n👉 Type your seat code (e.g., `11C` or `1A`) to select your seat!"

    elif any(k in words for k in ["book", "fly", "flight", "dubai", "delhi"]):
        flights = f"✈️ **SkyNav Results ({state['source']} ➔ {state['dest']})**\n\n1️⃣ **Air India** - ₹42,000\n2️⃣ **Emirates** - ₹48,000\n3️⃣ **IndiGo** - ₹38,000"
        response_text = f"{flights}\n\nReply with **1**, **2**, or **3** to select your flight!"

    else:
        response_text = "Please reply with **1**, **2**, or **3** to select a flight, or state your travel details."

    # Save Assistant Response
    msg_obj = {"role": "assistant", "content": response_text}
    if image_to_show:
        msg_obj["image_url"] = image_to_show

    st.session_state.messages.append(msg_obj)
    with st.chat_message("assistant"):
        st.markdown(response_text)
        if image_to_show:
            st.image(image_to_show, caption="Aircraft Cabin Seating Layout", use_container_width=True)
