import os
import io
import random
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# ReportLab for PDF Ticket Generation
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

st.set_page_config(page_title="SkyNav AI - Autonomous Travel Agent", page_icon="✈️", layout="wide")

st.title("✈️ SkyNav AI: Autonomous Travel Agent")
st.caption("Chat with SkyNav AI to search flights, pick options, select seats, verify OTP, and generate tickets.")

api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

# 1. Initialize Chat History & Session Variables
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am SkyNav AI. Where would you like to fly today?"}
    ]

if "booking_pnr" not in st.session_state:
    st.session_state.booking_pnr = None

# Helper Function: PDF Boarding Pass Generator
def generate_pdf(passenger_name="Samad", route="Dubai (DXB) to Delhi (DEL)", seat="12A", pnr="SKY7721"):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Header Banner
    p.setFillColor(colors.HexColor("#1E3A8A"))
    p.rect(0, 700, 612, 100, fill=True, stroke=False)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 22)
    p.drawString(40, 740, "SkyNav AI - Official E-Ticket")
    
    # Ticket Info
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, 650, f"Passenger Name : {passenger_name}")
    p.drawString(40, 620, f"Flight Route    : {route}")
    p.drawString(40, 590, f"Seat Number     : {seat}")
    p.drawString(40, 560, f"PNR / Booking ID: {pnr}")
    p.drawString(40, 530, f"Booking Status  : CONFIRMED & PAID")
    
    p.setFont("Helvetica-Oblique", 10)
    p.setFillColor(colors.gray)
    p.drawString(40, 450, "Thank you for flying with SkyNav AI. Safe Travels!")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# Sidebar - Ticket PDF Section
with st.sidebar:
    st.header("🎫 Booking & E-Ticket")
    if st.session_state.booking_pnr:
        st.success(f"Booking Confirmed! (PNR: {st.session_state.booking_pnr})")
        pdf_file = generate_pdf(passenger_name="Samad", pnr=st.session_state.booking_pnr)
        st.download_button(
            label="📄 Download E-Ticket PDF",
            data=pdf_file,
            file_name=f"SkyNav_Ticket_{st.session_state.booking_pnr}.pdf",
            mime="application/pdf"
        )
    else:
        st.info("Complete your booking conversation in the chat to download your E-Ticket PDF here.")

# 2. Render Existing Chat Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 3. User Input & AI Processing
if user_prompt := st.chat_input("Type here (e.g., 'Book flight from Dubai to Delhi', 'Option 1', 'Seat 12A')..."):
    if not api_key:
        st.error("⚠️ Gemini API Key missing in Streamlit Secrets.")
        st.stop()

    # Append & Display User Message
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    # Generate Response from AI Agent
    with st.chat_message("assistant"):
        with st.spinner("SkyNav AI is processing..."):
            try:
                llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", google_api_key=api_key)
                
                # Instruction for structured conversation
                system_instruction = SystemMessage(content="""
                You are SkyNav AI, an autonomous flight booking assistant.
                Guide the user step-by-step through a complete booking flow:
                1. When asked for flights, present Option 1 and Option 2 with prices and times.
                2. When the user picks an option (e.g., Option 1), ask for their Seat Preference (e.g., 12A, 14C) and Passenger Name.
                3. When seat/name are provided, give them a mock 6-digit OTP code and ask them to verify it.
                4. When the user types the OTP, confirm payment and display a unique PNR Number (e.g., PNR: SKY9823).
                Keep responses concise, clear, and structured.
                """)

                # Construct conversation thread
                history = [system_instruction]
                for msg in st.session_state.messages:
                    if msg["role"] == "user":
                        history.append(HumanMessage(content=msg["content"]))
                    else:
                        history.append(AIMessage(content=msg["content"]))

                response = llm.invoke(history)
                
                # Extract clean string output
                if isinstance(response.content, list) and len(response.content) > 0:
                    clean_output = response.content[0].get("text", str(response.content[0]))
                else:
                    clean_output = str(response.content)

                st.write(clean_output)
                st.session_state.messages.append({"role": "assistant", "content": clean_output})

                # Check if booking completed to trigger PDF download
                if "pnr" in clean_output.lower() or "confirmed" in clean_output.lower():
                    if not st.session_state.booking_pnr:
                        st.session_state.booking_pnr = f"SKY{random.randint(1000, 9999)}"
                        st.rerun()

            except Exception as e:
                st.error(f"Execution Error: {e}")
