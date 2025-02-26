import os
import hashlib
import streamlit as st
from datetime import datetime
import secrets

def generate_capture_link():
    """Generate a unique capture link"""
    token = secrets.token_urlsafe(16)
    return token

def is_admin(username, password):
    """Basic authentication check"""
    # In production, use proper authentication and environment variables
    ADMIN_USER = "admin"
    ADMIN_PASS = "admin123"  # In production, use hashed passwords

    return username == ADMIN_USER and password == ADMIN_PASS

def require_admin(func):
    """Decorator to require admin authentication"""
    def wrapper(*args, **kwargs):
        if not st.session_state.get('authenticated', False):
            st.error("Unauthorized access")
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def generate_filename(base_name, extension):
    """Generate a unique filename"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.{extension}"