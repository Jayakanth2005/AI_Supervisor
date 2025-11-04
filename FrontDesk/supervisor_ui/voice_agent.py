import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="FrontDesk Voice Agent")
st.title("🎧 Voice Agent (LiveKit Demo)")

caller_name = st.text_input("Your Name", "User")
room = st.text_input("Room Name", "frontdesk-room")

if st.button("Get LiveKit Token"):
    res = requests.get(f"{BACKEND_URL}/token", params={"identity": caller_name, "room": room})
    st.json(res.json())
