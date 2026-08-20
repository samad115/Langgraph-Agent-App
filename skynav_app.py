import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

st.set_page_config(page_title="SkyNav AI", page_icon="✈️")

st.title("✈️ SkyNav AI: Autonomous Travel Agent")
st.write("Command the AI agent in natural English (e.g., *'I want to book a flight from Dubai to Delhi'*).")

api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

user_input = st.text_input("How can SkyNav AI assist your travel today?", placeholder="I want to book a flight from Dubai to Delhi...")

if st.button("Send Request"):
    if not api_key:
        st.error("⚠️ Gemini API Key configured inside Streamlit Secrets is missing.")
    elif not user_input.strip():
        st.warning("Please type a travel request first.")
    else:
        with st.spinner("SkyNav Agent is processing flight options..."):
            try:
                llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", google_api_key=api_key)
                system_prompt = "You are SkyNav AI, an autonomous travel agent. Process user queries politely and provide clear travel routes, flights, or booking assistance."
                messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_input)]
                response = llm.invoke(messages)
                
                # Response formatting fix for raw JSON/List outputs
                if isinstance(response.content, list) and len(response.content) > 0:
                    output_text = response.content[0].get("text", str(response.content[0]))
                else:
                    output_text = response.content

                st.success("🤖 **SkyNav AI Response:**")
                st.write(output_text)
            except Exception as e:
                st.error(f"Error executing agent: {e}")
