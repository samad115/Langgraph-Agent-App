import os
import io
import random
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# PDF Generator Libraries
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

st.set_page_config(page_title="SkyNav AI - Interactive Chat Agent", page_icon="✈️", layout="wide")

st.title("✈️ SkyNav AI: Autonomous Travel Agent")
st.caption("Chat naturally to search flights, pick Option 1/2, select seats, verify OTP, and generate tickets.")

api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

# 1. Chat History and Session State Setup
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am SkyNav AI. Where would you like to fly today?"}
    ]
if "pnr_data" not in st.session_state:
    st.session_state.pnr_data = None

# PDF Ticket Helper Function
def create_pdf_ticket(passenger_name="Samad", flight_info="Emirates EK - DXB to DEL", seat="12A", pnr="SKY8829"):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFillColor(colors.HexColor("#1E3A8A"))
    p.rect(0, 700, 612, 100, fill=True, stroke=False)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 22)
    p.drawString(40, 740, "SkyNav AI - Confirmed Boarding Pass")
    
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, 650, f"Passenger Name: {passenger_name}")
    p.drawString(40, 625, f"Flight Details: {flight_info}")
    p.drawString(40, 600, f"Seat Number: {seat}")
    p.drawString(40, 575, f"PNR / Booking ID: {pnr}")
    p.drawString(40, 550, f"Status: CONFIRMED & PAID")
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# Sidebar - Quick Actions & PDF Download
with st.sidebar:
    st.header("🎫 Ticket & PDF Hub")
    if st.session_state.pnr_data:
        st.success("Booking Confirmed!")
        pdf_bytes = create_pdf_ticket(
            passenger_name=st.session_state.pnr_data.get("name", "Samad"),
            flight_info=st.session_state.pnr_data.get("flight", "Emirates DXB to DEL"),
            seat=st.session_state.pnr_data.get("seat", "12A"),
            pnr=st.session_state.pnr_data.get("pnr", "SKY9921")
        )
        st.download_button(
            label="📄 Download E-Ticket PDF",
            data=pdf_bytes,
            file_name="SkyNav_Flight_Ticket.pdf",
            mime="application/pdf"
        )
    else:
        st.info("Complete your booking in chat to unlock your downloadable PDF ticket.")

# 2. Display Past Chat Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 3. Handle Interactive User Input
if prompt := st.chat_input("Type here (e.g., 'Book flight from Dubai to Delhi', 'I select Option 1', 'Seat 12A')..."):
    if not api_key:
        st.error("⚠️ Gemini API Key missing in Streamlit Secrets.")
        st.stop()

    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Process AI Agent Response
    with st.chat_message("assistant"):
        with st.spinner("SkyNav AI processing..."):
            try:
                llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", google_api_key=api_key)
                
                # System instructions for step-by-step guidance
                sys_msg = SystemMessage(content="""
                You are SkyNav AI, an autonomous travel booking agent. 
                Follow this flow step-by-step:
                1. If user asks for flights, list clear options (Option 1, Option 2) with prices.
                2. If user selects Option 1 or 2, confirm the choice and ask for Passenger Name and Seat Preference (e.g., 12A, 14B).
                3. Once seat/name are provided, simulate sending a 6-digit OTP for payment and ask user to enter OTP.
                4. When user enters OTP, confirm booking and give them a PNR number.
                Keep responses friendly, helpful, and concise.
                """)

                # Construct full conversation context
                langchain_msgs = [sys_msg]
                for m in st.session_state.messages:
                    if m["role"] == "user":
                        langchain_msgs.append(HumanMessage(content=m["content"]))
                    else:
                        langchain_msgs.append(AIMessage(content=m["content"]))

                res = llm.invoke(langchain_msgs)
                
                # Format response text
                text_out = res.content[0].get("text", str(res.content[0])) if isinstance(res.content, list) else res.content
                
                st.write(text_out)
                st.session_state.messages.append({"role": "assistant", "content": text_out})

                # Detect if booking complete to unlock PDF
                if "pnr" in text_out.lower() or "confirmed" in text_out.lower() or "otp verified" in text_out.lower():
                    st.session_state.pnr_data = {"name": "Samad", "flight": "Selected Option", "seat": "12A", "pnr": f"SKY{random.randint(1000, 9999)}"}
                    st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")
