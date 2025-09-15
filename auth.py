"""
Simple authentication module for Streamlit app
"""
import streamlit as st
import hashlib

# Hardcoded credentials (username: password)
USERS = {
    "admin": "admin123",
    "user": "user123",
    "demo": "demo123"
}

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(username, password):
    """Verify username and password"""
    if username in USERS:
        return USERS[username] == password
    return False

def login_form():
    """Display professional login form"""
    # Custom CSS for professional styling
    st.markdown("""
    <style>
    .login-container {
        max-width: 420px;
        margin: 0 auto;
        padding: 3rem 2.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        margin-top: 8vh;
        color: white;
    }
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .login-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        background: linear-gradient(45deg, #fff, #f0f8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .login-subtitle {
        font-size: 1rem;
        opacity: 0.9;
        margin-bottom: 0;
    }
    .demo-card {
        background: rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 1.5rem;
        margin-top: 2rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    .demo-title {
        color: #fff;
        font-weight: 600;
        margin-bottom: 1rem;
        text-align: center;
    }
    .demo-creds {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.9);
        border: 2px solid transparent;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #4CAF50;
        box-shadow: 0 0 0 3px rgba(76,175,80,0.1);
    }
    .stButton > button {
        background: linear-gradient(45deg, #4CAF50, #45a049);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
        margin-top: 1rem;
    }
    .stButton > button:hover {
        background: linear-gradient(45deg, #45a049, #4CAF50);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(76,175,80,0.3);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-container">
            <div class="login-header">
                <div class="login-title">🔐 IntelliSurf AI</div>
                <div class="login-subtitle">RFP Research Platform</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown('<p style="color: #333; font-weight: 600; margin-bottom: 1rem; text-align: center;">Please enter your credentials</p>', unsafe_allow_html=True)
            
            username = st.text_input("Username", placeholder="Enter username", label_visibility="collapsed")
            st.markdown('<div style="margin-bottom: 1rem;"></div>', unsafe_allow_html=True)
            
            password = st.text_input("Password", type="password", placeholder="Enter password", label_visibility="collapsed")
            
            submit = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if submit:
                if verify_password(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("✅ Login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
        

def logout():
    """Logout function"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()

def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get("authenticated", False)

def require_auth():
    """Decorator-like function to require authentication"""
    if not is_authenticated():
        login_form()
        st.stop()
