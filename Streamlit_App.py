import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

st.set_page_config(page_title="LangGraph Agentic AI", page_icon="🤖")

st.title("🤖 LangGraph Agentic AI - Customer Refund & HITL Agent")
st.write("Enterprise-grade Agentic AI Workflow with Human-in-the-Loop Security Guardrails.")

# API Key Sidebar
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

order_id = st.text_input("Order ID", "ORD-9082")
amount = st.number_input("Refund Amount (₹)", value=500.0)

st.subheader("🙋‍♂️ Human-in-the-Loop Control Panel")
decision = st.radio("Manager Approval Decision", ["Pending Approval", "Approve", "Reject"])
notes = st.text_area("Manager Notes (Optional)")

if st.button("Submit to Agent Workflow"):
    if not api_key:
        st.error("Please provide Gemini API Key in the sidebar.")
    else:
        st.info(f"Processing Order: {order_id} for ₹{amount:.2f}")

        if amount > 500:
            if decision == "Pending Approval":
                st.warning("🚨 **HUMAN IN THE LOOP INTERRUPT TRIGGERED**\n\nRefund exceeds ₹500. Awaiting Manager Approval.")
            elif decision == "Approve":
                st.success(f"✅ **Approved by Manager!** Refund processed for {order_id}. Notes: {notes}")
            elif decision == "Reject":
                st.error(f"❌ **Rejected by Manager.** Refund cancelled. Notes: {notes}")
        else:
            st.success(f"⚡ **Auto-Approved!** Refund of ₹{amount:.2f} processed automatically.")
