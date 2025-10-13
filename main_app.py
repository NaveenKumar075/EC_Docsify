import re, time, json, shortuuid, requests
import pyrebase
import streamlit as st
import tempfile
import base64
from pathlib import Path
from datetime import datetime, timedelta
from io import BytesIO
from streamlit_lottie import st_lottie
from streamlit_option_menu import option_menu
from streamlit_cookies_controller import CookieController
from hydralit_components import HyLoader, Loaders
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
from legalgpt_EC import pdf_extraction, retrieving_process, rerank_documents, extract_meta_details, EC_ChatBot, extract_all_document_remarks
from custom_styles import apply_custom_css
import warnings
warnings.filterwarnings('ignore')


st.set_page_config(
        page_title="Yeecy.ai", 
        page_icon="🏡", 
        layout="centered", 
        initial_sidebar_state="expanded")

apply_custom_css()


# Firebase configuration
firebase_config = st.secrets["firebase"]
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
database = firebase.database()
cookie_controller = CookieController() # Initialize the cookies controller


# Google Drive API Setup
parent_folder_id = st.secrets["gdrive"]["parent_folder_id"]
service_account_json_str = st.secrets["gdrive"]["service_account_json"]

# Write the JSON to a temporary file
with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as temp_file:
    temp_file.write(service_account_json_str)
    SERVICE_ACCOUNT_FILE_TEMP = temp_file.name

SCOPES = ['https://www.googleapis.com/auth/drive.file']
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE_TEMP, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)


# Streamlit session state initialization
def initialize_session_state():
    defaults = {
        'authenticated': False,
        'user': {}, # To store the user details
        'choice': None,
        'uploaded_file': None,
        'content': None,
        'meta_details': None,
        'chat_history': [],
        'page': 'signin',
        'page_loaded': False,
        'logout_triggered': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()


# To display the chat conversations
def display_chat_history():
    for message in st.session_state.chat_history:
        with st.chat_message(message['role']):
            st.markdown(message['content'])


# Function to load a Lottie animation from a URL
@st.cache_resource
def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


# Helper function to validate email format
def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None


# Authentication functions
def signup(email, password, username):
    if not is_valid_email(email):
        st.error("Invalid email format. Please enter a valid email address.")
        return
    if not password:
        st.error("Password cannot be empty.")
        return
    try:
        user = auth.create_user_with_email_and_password(email, password)
        # database.child(user['localId']).child("Username").set(username)
        # database.child(user['localId']).child("ID").set(user['localId'])
        database.child(user['localId']).set({"Username": username, "ID": user['localId']})
        st.session_state['user'] = {
            'email': email,
            'username': username,
            'localId': user['localId']
        }
        st.success("Account created successfully! Please login.")
        st.balloons()
    except Exception as e:
        try:
            error_response = json.loads(e.args[1]) # Extract error message from response
            error_message = error_response.get("error", {}).get("message", "Unknown Error")
        except Exception:
            error_message = "An error occurred, please try again!"
        st.error(f"Signup failed: {error_message}")

def login(email, password):
    if not password:
        st.error("Password cannot be empty.")
        return
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        user_data = database.child(user['localId']).get().val()
        username = user_data.get("Username", "Unknown User")
        st.success(f"Logged in successfully as {username}!")
        # st.session_state['user']['Username'] = username
        store_auth_data(user)
        store_session(st.session_state['user'])  # Store session in cookies
        st.rerun()
    except Exception as e:
        try:
            error_response = json.loads(e.args[1]) # Firebase's error response is in args[1]
            error_message = error_response.get("error", {}).get("message", "Unknown Error")
        except Exception:
            error_message = "An error occurred, please try again!"
        st.warning("Please enter the valid credentials!")
        st.error(f"Login failed due to: {error_message}")

def logout():
    cookie_controller.set("user_session", "", max_age=0) # Clear cookie by setting it to an empty value with a past expiration
    st.session_state['authenticated'] = False
    st.session_state['logout_triggered'] = True
    st.session_state['user'] = {} # Clear user data safely
    st.session_state.clear()
    st.sidebar.success("Logged out successfully!")
    time.sleep(1)
    st.rerun()

def store_auth_data(user):
    expires_at = datetime.utcnow() + timedelta(seconds=3600)  # Set token expiry time
    st.session_state['authenticated'] = True
    st.session_state['user'] = {
        'email': user['email'],
        'localId': user['localId'],
        'idToken': user['idToken'],
        'refreshToken': user['refreshToken'],
        'expiresAt': expires_at.timestamp(),  # Use timestamp for better comparisons
        'username': database.child(user['localId']).child("Username").get().val()
    }
    store_session(st.session_state['user'])

# Function to store session in cookies
def store_session(user_data):
    cookie_controller.set("user_session", user_data, max_age=3600)  # 1 hour expiration
    st.session_state['authenticated'] = True
    st.session_state['user'] = user_data
    time.sleep(1)
    if not st.session_state.get('authenticated', False):
        st.rerun()

# Function to check session from cookies
def check_session():
    user_data = cookie_controller.get("user_session")
        
    if user_data:
        st.session_state['authenticated'] = True
        st.session_state['user'] = user_data
        
        if not st.session_state.page_loaded:
            st.session_state.page_loaded = True
    else:
        st.session_state['authenticated'] = False
        st.session_state['user'] = {}
        
        # Reset page_loaded on logout so it triggers again
        if st.session_state.logout_triggered:
            st.session_state.page_loaded = False
            st.session_state.logout_triggered = False  # Reset logout flag
            
# Utility for switching page
def switch_page(target):
    st.session_state.page = target
    st.rerun()

# Load custom CSS
def load_css():
    with open('style.css', 'r') as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Image utilities
def img_to_bytes(img_path):
    return base64.b64encode(Path(img_path).read_bytes()).decode()

def img_to_html(img_path):
    return f"<img src='data:image/png;base64,{img_to_bytes(img_path)}' class='chatbot-icon'>"


# --- Signin Page ---
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

        if st.form_submit_button(label="Sign In"):
            if email and password:
                login(email, password)
            else:
                st.markdown('<div class="notification error"><p>Please fill in all fields.</p></div>', unsafe_allow_html=True)

    if st.button("Don't have an account? Sign Up", key="to_signup"):
        switch_page("signup")


# --- Signup Page ---
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

        if st.form_submit_button(label="Sign Up"):
            if username and email and password:
                signup(email, password, username)
                st.info("Please log in to access your account.")
                switch_page("signin")
            else:
                st.markdown('<div class="notification error"><p>Please fill in all fields.</p></div>', unsafe_allow_html=True)

    if st.button("Already have an account? Sign In", key="to_signin"):
        switch_page("signin")


# Google Drive upload function
def upload_to_drive(file, username):
    try:
        unique_code = shortuuid.ShortUUID().random(length=7)
        new_file_name = f"{username}_{unique_code}"
        file_content = BytesIO(file.getbuffer())
        file_metadata = {'name': new_file_name, 'parents': [parent_folder_id]}
        media = MediaIoBaseUpload(file_content, mimetype='application/pdf', resumable=True)
        drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    except Exception as e:
        st.error(f"Failed to upload file to Google Drive: {e}")
        
# *** EC Summarization: ***
def summarization_custom_css():
    st.markdown("""
        <style>
            /* Force equal column widths */
            div[data-testid="column"] {
                flex: 1 1 0 !important;
                min-width: 0 !important;
                max-width: none !important;
            }
            
            /* Summarization buttons - PERMANENT FIX */
            div[data-testid="column"] .stButton {
                width: 100% !important;
                display: block !important;
            }
            
            div[data-testid="column"] .stButton > button {
                background-image: linear-gradient(to right, #ff9a9e 0%, #fad0c4 51%, #a18cd1 100%) !important;
                color: white !important;
                font-size: 13px !important;
                font-weight: bold !important;
                padding: 12px 8px !important;
                text-transform: none !important;
                border: none !important;
                border-radius: 15px !important;
                background-size: 200% auto !important;
                transition: 0.5s ease-in-out !important;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
                width: 100% !important;
                cursor: pointer !important;
                
                /* CRITICAL: Force horizontal text */
                white-space: normal !important;
                word-wrap: break-word !important;
                word-break: break-word !important;
                min-height: 70px !important;
                height: auto !important;
                line-height: 1.3 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                text-align: center !important;
                writing-mode: horizontal-tb !important;
                text-orientation: mixed !important;
                transform: none !important;
                vertical-align: middle !important;
            }

            div[data-testid="column"] .stButton > button:hover {
                background-position: right center !important;
                transform: scale(1.05) !important;
                box-shadow: 6px 6px 16px rgba(161, 140, 209, 0.6) !important;
                transition: 0.3s ease-in-out !important;
                color: black !important;
            }
        </style>
    """, unsafe_allow_html=True)


# Summarization Sections
summarization_sections = {
    "general_info": "General Information (பொதுவான தகவல்)",
    "land_details": "Land Details (நில விவரங்கள்)",
    "transaction_details": "Transaction Details (பரிமாற்ற விவரங்கள்)",
    "boundaries": "Boundaries (வரம்புகள்)",
    "document_remarks": "Document Remarks (ஆவணக் குறிப்புகள்)"
}


def get_section_prompt(section_key):
    section_prompts = {
        "General Information (பொதுவான தகவல்)": "Extract the General Information details",
        "Land Details (நில விவரங்கள்)": "Extract the Land Details",
        "Transaction Details (பரிமாற்ற விவரங்கள்)": "Extract the Transaction Details",
        "Boundaries (வரம்புகள்)": "Extract the Boundaries"
    }
    
    if section_key == "Document Remarks (ஆவணக் குறிப்புகள்)":
        return extract_all_document_remarks
    
    return section_prompts.get(section_key, "")


def initialize_sum_session_state():
    if "processed_results" not in st.session_state:
        st.session_state.processed_results = {section: None for section in summarization_sections.keys()}


def run_summarization(content):
    initialize_sum_session_state()
    
    st.write("### Select Sections to Summarize:")

    # Full-width 5-column layout
    cols = st.columns(5, gap="small")
    
    for idx, (section_key, section_title) in enumerate(summarization_sections.items()):
        with cols[idx]:  # Place buttons inside columns
            if st.button(section_title, key=f"btn_{section_key}"):
                with st.spinner(f"📝 Processing {section_title}..."):
                    section_value = get_section_prompt(section_title)
                    
                    if callable(section_value):
                        remarks_list = section_value(content)
                        response = "\n\n".join(remarks_list)
                    else:
                        retrieved_chunks = retrieving_process(content, section_value)
                        reranked_docs = rerank_documents(retrieved_chunks, section_value)
                        response = EC_ChatBot(reranked_docs, section_value)
                    
                    st.session_state.processed_results[section_key] = response

    st.write("### 📋 Summarized Results:")
    with st.container():
        for section_key, section_title in summarization_sections.items():
            result = st.session_state.processed_results.get(section_key, "")
            if result:
                with st.expander(section_title, expanded=True):
                    st.markdown(f"**🔍 Processed {section_title}**\n\n{result}")
        
        
# Streamlit UI setup
def main():
    load_css() # Loading the custom CSS
    check_session() # Call session check
    
    st.markdown("""
    <h1 style="text-align: center; color: #6a11cb; animation: slideIn 0.5s ease forwards;">
        🏠 Yeecy.ai ✨
    </h1>
    """, unsafe_allow_html=True)
    
    if not st.session_state.page_loaded:
        with HyLoader('', Loaders.pretty_loaders,index=[0]):
            time.sleep(1)
    
    if not st.session_state['authenticated']:
        if st.session_state.page == 'signin':
            signin_page()
        else:
            signup_page()

    else:
        username = st.session_state['user'].get('username', 'User')
        email_id = st.session_state['user'].get('email', 'user@gmail.com')
        st.sidebar.markdown(f"""
        <div style="padding: 10px; border-radius: 10px; background-color: #f0f0f0;">
            <h4>👋 Welcome, <span style="color:#8AAAE5;">{username}</span></h4>
            <p style="font-size: 13px;">Logged in with <code>{email_id}</code></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.title("Welcome to EC Docsify!")
        st.write("AI-Driven Accuracy, Simplified EC Verification.")
        
        with st.sidebar:
            st.sidebar.markdown(
            """
            <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&icon_names=widgets" />
            <style>
            .main-menu-title {
                display: flex;
                align-items: center;
                justify-content: flex-start;
                gap: 10px;
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 0 10px;
                margin-bottom: 15px;
            }
            .material-symbols-outlined {
                font-variation-settings:
                'FILL' 0,
                'wght' 400,
                'GRAD' 0,
                'opsz' 24;
                color: #2c3e50;
            }
            </style>
            <div class="main-menu-title">
            <span class="material-symbols-outlined">widgets</span>
            Main Menu</div>
            """,
            unsafe_allow_html=True)
            
            selected = option_menu(None, 
                ['Welcome', 'ChatBot', 'Summarization', 'Contact Us'], 
                icons=['person-raised-hand', 'robot', 'book', 'person-lines-fill'], 
                styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "red", "font-size": "25px"},
                "nav-link": {"font-size": "17px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#8AAAE5"}},
                default_index=0
            )
            
            # ADD THE SIDEBAR TOGGLE FIX
            st.markdown("""
                <script>
                // Ensure sidebar toggle button is always visible
                const style = document.createElement('style');
                style.innerHTML = `
                    [data-testid="collapsedControl"] {
                        display: block !important;
                        visibility: visible !important;
                        opacity: 1 !important;
                    }
                `;
                document.head.appendChild(style);
                </script>
            """, unsafe_allow_html=True)
        
        # Check before redirecting to Summarization mode
        if selected == "Summarization":
            if "content" not in st.session_state or not st.session_state["content"]:
                st.sidebar.warning("⚠️ No document uploaded! Please upload a PDF in the ChatBot mode before summarizing.")
                st.markdown("""
                    <div style="
                        padding: 15px; 
                        border-radius: 10px; 
                        background-color: #ffe6cc; 
                        color:rgb(0, 0, 0); 
                        font-size: 16px; 
                        font-weight: bold;">
                    🚀 **Whoa! You just skipped a step!** \n\n
                    You've been **redirected back to ChatBot Mode** because your PDF is missing 📄❌ \n\n
                    👉 **Upload your document here first**, then hop over to **Summarization Mode** for the magic! ✨
                    </div>
                """, unsafe_allow_html=True)
                selected = "ChatBot" # Force redirection to ChatBot mode
        
        
        if selected == 'ChatBot':
            st.header("Chatbot Mode")
            st.write("Ask questions about the uploaded document.")
            
            # Check if a PDF file is already uploaded
            if "content" in st.session_state and st.session_state["content"]:
                st.success("✅ PDF file uploaded. You can proceed with ChatBot and Summarization mode!")
            else:
                st.subheader("Upload Your Files Here!")
                uploaded_file = st.file_uploader("Upload your PDF 📑 and click '🔄 Process PDF'", type=["pdf"])
                
                if uploaded_file is not None:
                    if 'uploaded_filename' not in st.session_state or st.session_state.uploaded_filename != uploaded_file.name:
                        with st.spinner("📤 Uploading in progress..."):
                            upload_to_drive(uploaded_file, username)  # Upload to Google Drive

                        # Store filename to avoid reprocessing
                        st.session_state.uploaded_file = uploaded_file
                        st.session_state.uploaded_filename = uploaded_file.name
                        st.success("✅ File processed successfully. Click 'Process PDF' to extract content📜")
                        
                # "Process PDF" button
                if st.session_state.uploaded_file is not None and st.button("🔄 Process PDF"):
                    with st.status("📄 Extracting content...") as status:
                        # Step 1: Extract Content
                        st.session_state.content = pdf_extraction(st.session_state.uploaded_file)
                        status.update(label="✅ Content extracted! Now extracting metadata...", state="running")
                    
                        # Step 2: Extract Metadata
                        st.session_state.meta_details = extract_meta_details(st.session_state.content[-3:])
                        status.update(label="✅ Metadetails are extracted! Process completed...", state="complete")

                    st.success("✅ PDF Processed Successfully! You can now use ChatBot and Summarization mode!✨")
                    st.session_state.chat_enabled = True  # Enable chat input after processing

                # Display extracted metadata if available
                if st.session_state.meta_details:
                    st.subheader("📌 Extracted Metadata:")
                    st.json(st.session_state.meta_details)
                    
            # Don't ask for re-upload if content is already in session_state
            if "uploaded_file" not in st.session_state or st.session_state.uploaded_file is None:
                st.warning("🚨 Please upload a PDF file to proceed.")
                st.stop()  # Prevent further execution

            if st.session_state.get("chat_enabled", False):
                display_chat_history() # Show chat history and input
                if prompt := st.chat_input("Ask your question here:"):
                    st.session_state.chat_history.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)
                    with st.chat_message("assistant"):
                        with st.spinner("🌟 Generating Response..."):
                            retrieved_chunks = retrieving_process(st.session_state.content, prompt)
                            st.toast("📑 Retrieved Chunks")
                            reranked_docs = rerank_documents(retrieved_chunks, prompt)
                            st.toast("📚 Reranked Documents")
                            response = EC_ChatBot(reranked_docs, prompt)
                            st.toast("✔️ Response Generated")
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    st.rerun()
        
        
        elif selected == "Summarization":
            st.header("Summarization Mode")
            summarization_custom_css()
            
            # 🔄 Restore extracted text if session state lost it
            if 'content' not in st.session_state and 'uploaded_file' in st.session_state:
                st.session_state.content = pdf_extraction(st.session_state.uploaded_file)
            
            st.success("✅ Document loaded successfully! You can now summarize.")
            run_summarization(st.session_state.content)
        
        # Logout function          
        if st.sidebar.button("Logout"):
            logout()

    
    st.markdown("""
    <div style="text-align: center; margin-top: auto; color: #666; font-size: 1.0rem; padding: 1rem 0; animation: fadeIn 1s ease forwards 1s; opacity: 0;">
        <a href="https://yeecy-ai.streamlit.app/" style="color: #6a11cb; text-decoration: none; font-weight: 600;">
            Yeecy.ai ❤️ 
        </a> | Copyrights Reserved © 2025
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()