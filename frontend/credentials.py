import streamlit as st
import requests
import os


# API Base URL
API_BASE_URL = "http://localhost:8000"


# --- AUTH FUNCTIONS ---
def register_user(username, email, password):
    try:
        resp = requests.post(f"{API_BASE_URL}/register", params={
            "username": username, "email": email, "password": password
        })
        if resp.status_code == 200:
            st.success("✅ Registration successful! Please login.")
        else:
            st.error(resp.json().get("detail", "Registration failed."))
    except Exception as e:
        st.error(f"Error: {e}")

def login_user(username, password):
    try:
        resp = requests.post(f"{API_BASE_URL}/login", data={
            "username": username, "password": password
        })
        if resp.status_code == 200:
            st.session_state.auth_token = resp.json()["access_token"]
            st.session_state.page = "session_select"
            st.rerun()
        else:
            st.error(resp.json().get("detail", "Login failed."))
    except Exception as e:
        st.error(f"Error: {e}")

def fetch_session_data(session_id):
    headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
    resp = requests.get(f"{API_BASE_URL}/load_session", params={"session_id": session_id}, headers=headers)
    if resp.status_code == 200:
        st.session_state.session_data = resp.json()
    else:
        st.error("❌ Failed to load session data.")
        st.session_state.session_data = {
            "resume_analysis": {},
            "skill_recommendation": {},
            "ats_bullets": {}
        }
