import streamlit as st
import base64
from pathlib import Path

st.set_page_config(
    page_title="Login/Signup Dashboard",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize session state variables if they don't exist
if 'page' not in st.session_state:
    st.session_state.page = 'signin'  # Default to signin page
    
# Function to convert image to base64 HTML
def img_to_bytes(img_path):
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded

def img_to_html(img_path):
    img_html = "<img src='data:image/png;base64,{}' class='chatbot-icon'>".format(
        img_to_bytes(img_path)
    )
    return img_html

# Custom CSS
def load_css():
    with open('style.css', 'r') as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    
# Helper to switch page
def switch_page(target):
    st.session_state.page = target
    st.rerun()

def signin_page():
    st.markdown(f"""
        <div class="auth-container">
            <div class="auth-header">
                <div class="auth-left">
                    {img_to_html("static/Yeecy_ai_icon.png")}
                </div>
                <div class="auth-right">
                    <h1>Welcome Back!</h1>
                    <p>Talk to your EC documents.<br>Get instant summaries and insights.</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form(key="signin_form"):
        email = st.text_input("Email", placeholder="Enter your email", key="signin_email")
        password = st.text_input("Password", placeholder="Enter your password", type="password", key="signin_password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        submit_button = st.form_submit_button(label="Sign In")
        
        if submit_button:
            if email and password:
                st.markdown("""
                <div class="notification success">
                    <p>Successfully signed in!</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="notification error">
                    <p>Please fill in all fields.</p>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown('<div class="toggle-link">', unsafe_allow_html=True)
    if st.button("Don't have an account? Sign Up", key="to_signup", help="Click here to switch to sign up page"):
        switch_page("signup")
    st.markdown("</div>", unsafe_allow_html=True)

def signup_page():
    st.markdown(f"""
        <div class="auth-container">
            <div class="auth-header">
                <div class="auth-left">
                    {img_to_html("static/Yeecy_ai_icon.png")}
                </div>
                <div class="auth-right">
                    <h1>Get Started :)</h1>
                    <p>Create an account to chat with <br>your EC docs in seconds!</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form(key="signup_form"):
        username = st.text_input("Username", placeholder="Choose a username", key="signup_username")
        email = st.text_input("Email", placeholder="Enter your email", key="signup_email")
        password = st.text_input("Password", placeholder="Create a password", type="password", key="signup_password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        submit_button = st.form_submit_button(label="Sign Up")
        
        if submit_button:
            if username and email and password:
                st.markdown("""
                <div class="notification success">
                    <p>Account created successfully!</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="notification error">
                    <p>Please fill in all fields.</p>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown('<div class="toggle-link">', unsafe_allow_html=True)
    if st.button("Already have an account? Sign In", key="to_signup", help="Click here to switch to sign in page"):
        switch_page("signin")
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    load_css()
    
    st.markdown("""
    <h1 style="text-align: center; color: #6a11cb; animation: slideIn 0.5s ease forwards;">
        🌟 Yeecy.ai ✨
    </h1>
    """, unsafe_allow_html=True)
    
    # SignUp/SignIn
    if st.session_state.page == 'signin':
        signin_page()
    else:
        signup_page()
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; color: #666; font-size: 1.0rem; animation: fadeIn 1s ease forwards 1s; opacity: 0;">
        <a href="https://yeecy-ai.streamlit.app/" target="_blank" style="color: #6a11cb; text-decoration: none; font-weight: 600;">
            Yeecy.ai ❤️ 
        </a> | Copyrights Reserved © 2025
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()