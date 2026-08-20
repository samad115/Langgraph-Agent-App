import os
import io
import random
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# ReportLab libraries for PDF Ticket generation
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

st.set_page_config(page_title="SkyNav AI - Autonomous Booking", page_icon="✈️", layout="wide")

st.title("✈️ SkyNav AI: Autonomous Travel & Booking Agent")
st.write("Complete end-to-end booking flow: Search, Seat Selection, OTP Verification, Payment, and PDF Ticket Generation.")

api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

# Initialize Session States
if "booking_step" not in st.session_state:
    st.session_state.booking_step = "search"
if "otp_code" not in st.session_state:
    st.session_state.otp_code = None
if "ticket_data" not in st.session_state:
    st.session_state.ticket_data = {}

# PDF Generation Function
def generate_pdf_ticket(details):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Ticket Header
    p.setFillColor(colors.HexColor("#1E3A8A"))
    p.rect(0, 700, 612, 100, fill=True, stroke=False)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 24)
    p.drawString(40, 740, "SkyNav AI - E-Ticket Boarding Pass")
    
    # Ticket Details
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, 650, f"Passenger Name: {details.get('passenger', 'N/A')}")
    p.drawString(40, 620, f"Route: {details.get('from_city', 'DXB')} -> {details.get('to_city', 'DEL')}")
    p.drawString(40, 590, f"Travel Date: {details.get('date', '2026-09-10')}")
    p.drawString(40, 560, f"Seat Number: {details.get('seat', '12A')}")
    p.drawString(40, 530, f"Booking Ref (PNR): {details.get('pnr', 'SKY99882')}")
    p.drawString(40, 500, f"Amount Paid: ₹{details.get('amount', '15,000')}")
    p.drawString(40, 470, f"Payment Status: SUCCESS (Verified via OTP)")
    
    p.setFont("Helvetica-Oblique", 10)
    p.setFillColor(colors.gray)
    p.drawString(40, 400, "Thank you for booking with SkyNav AI. Safe Travels!")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- STEP 1: Flight Query & AI Agent ---
st.subheader("1. AI Flight Search & Assistance")
user_input = st.text_input("Tell SkyNav AI your travel plans:", value="I want to book a flight from Dubai to Delhi on 2026-09-10")

if st.button("Search Flights & Process Request"):
    if not api_key:
        st.error("⚠️ Gemini API Key missing in Streamlit Secrets.")
    else:
        with st.spinner("SkyNav Agent checking flights..."):
            try:
                llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", google_api_key=api_key)
                system_prompt = "You are SkyNav AI. Provide immediate clear route options and confirm flight availability."
                messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_input)]
                response = llm.invoke(messages)
                
                out = response.content[0].get("text", str(response.content[0])) if isinstance(response.content, list) else response.content
                st.success("🤖 **AI Agent Response:**")
                st.write(out)
                st.session_state.booking_step = "select_seat"
            except Exception as e:
                st.error(f"Error: {e}")

st.divider()

# --- STEP 2: Seat Selection & Passenger Info ---
if st.session_state.booking_step in ["select_seat", "otp_payment", "completed"]:
    st.subheader("2. Passenger Details & Seat Selection")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        passenger_name = st.text_input("Passenger Full Name", value="Samad")
    with col2:
        email_addr = st.text_input("Email Address for Ticket & OTP", value="samad@example.com")
    with col3:
        seat_num = st.selectbox("Select Seat Class & No.", ["12A (Window - ₹15,000)", "12B (Middle - ₹14,000)", "14C (Aisle - ₹16,000)", "2F (Business - ₹45,000)"])

    if st.button("Proceed to Payment & Send OTP"):
        # Generate 6-digit OTP
        generated_otp = str(random.randint(100000, 999999))
        st.session_state.otp_code = generated_otp
        st.session_state.ticket_data = {
            "passenger": passenger_name,
            "email": email_addr,
            "seat": seat_num.split(" ")[0],
            "amount": seat_num.split("₹")[1].replace(")", ""),
            "from_city": "Dubai (DXB)",
            "to_city": "Delhi (DEL)",
            "date": "2026-09-10",
            "pnr": f"SKY{random.randint(10000, 99999)}"
        }
        st.session_state.booking_step = "otp_payment"
        st.info(f"📧 **[MOCK EMAIL SENT]** OTP sent to `{email_addr}`. (For testing, your OTP is: **`{generated_otp}`**)")

st.divider()

# --- STEP 3: OTP Verification & Payment ---
if st.session_state.booking_step in ["otp_payment", "completed"]:
    st.subheader("3. OTP Security Verification & Payment")
    
    entered_otp = st.text_input("Enter 6-Digit OTP received on Email:", type="password")
    
    if st.button("Verify OTP & Pay Now"):
        if entered_otp == st.session_state.otp_code:
            st.success("✅ OTP Verified Successfully! Payment processed.")
            st.session_state.booking_step = "completed"
        else:
            st.error("❌ Invalid OTP. Please enter the correct code shown above.")

st.divider()

# --- STEP 4: Download PDF Ticket ---
if st.session_state.booking_step == "completed":
    st.subheader("4. Ticket Confirmed & PDF Download")
    st.balloons()
    st.success("🎉 Booking Completed! Your flight ticket is ready for download.")
    
    pdf_data = generate_pdf_ticket(st.session_state.ticket_data)
    
    st.download_button(
        label="📄 Download E-Ticket PDF",
        data=pdf_data,
        file_name=f"SkyNav_Ticket_{st.session_state.ticket_data.get('pnr')}.pdf",
        mime="application/pdf"
    )
