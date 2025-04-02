import re, time, json, shortuuid, requests
import pyrebase
import streamlit as st
import tempfile
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
        page_title="EC Docsify", 
        page_icon="🚀", 
        initial_sidebar_state="expanded",
        layout="wide")

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
        'chat_history': []
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
    
    if "page_loaded" not in st.session_state:
        st.session_state.page_loaded = False  # Handles login
    if "logout_triggered" not in st.session_state:
        st.session_state.logout_triggered = False  # Handles logout
        
    if user_data:
        st.session_state['authenticated'] = True
        st.session_state['user'] = user_data
        
        if not st.session_state.page_loaded: # Show loader on first login
            st.session_state.page_loaded = True
    else:
        st.session_state['authenticated'] = False
        st.session_state['user'] = {}
        
        # Reset page_loaded on logout so it triggers again
        if st.session_state.logout_triggered:
            st.session_state.page_loaded = False
            st.session_state.logout_triggered = False  # Reset logout flag


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
            /* Center-align buttons */
            .stButton {
                display: flex;
                justify-content: center;
            }
            .stButton > button {
                background-image: linear-gradient(to right, #ff9a9e 0%, #fad0c4 51%, #a18cd1 100%);
                color: white;
                font-size: 20px;
                font-weight: bold;
                padding: 15px 45px;
                text-transform: none;
                border: none;
                border-radius: 15px;
                background-size: 200% auto;
                transition: 0.5s ease-in-out;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                display: block;
                width: 100%;
                cursor: pointer;
            }

            .stButton > button:hover {
                background-position: right center;
                transform: scale(1.07);
                box-shadow: 6px 6px 16px rgba(161, 140, 209, 0.6);
                transition: 0.3s ease-in-out;
                color: black;
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
    cols = st.columns(5, gap="large")
    
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
    check_session() # Call session check
    
    st.title("EC Docsify 🤖")
    
    if not st.session_state.page_loaded:
        with HyLoader('', Loaders.pretty_loaders,index=[0]):
            time.sleep(2)
        
    if not st.session_state.get('authenticated', False):
        st.sidebar.header("Authentication")
        choice = st.sidebar.radio("Choose an option", ["Login", "Signup"])
        with st.sidebar.form(key="auth_form"):
            email = st.text_input("Email", key="email")
            password = st.text_input("Password", type="password", key="password")
            
            if choice == "Signup":
                username = st.text_input("Username")
            else:
                username = None  # No username needed for login

            submit_button = st.form_submit_button(label="Submit")
            if submit_button:
                if choice == "Login":
                    login(email, password)                
                elif choice == "Signup":
                    if username:
                        signup(email, password, username)
                        st.info("Please do login to access your account.")
                    else:
                        st.warning("Please provide a username to complete the signup.")

    else:
        username = st.session_state['user'].get('username', 'User')
        st.sidebar.success(f"Welcome back, {username} ✨")
        
        st.title("Welcome to EC Docsify!")
        st.write("This is the new interface for logged-in users.")
        
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
                uploaded_file = st.file_uploader("Upload your PDF 📑", type=["pdf"])
                
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
                        st.session_state.meta_details = extract_meta_details(st.session_state.content[-4:-1])
                        status.update(label="✅ Metadetails are extracted! Process completed...", state="complete")

                    st.success("✅ PDF Processed Successfully! You can now use ChatBot and Summarization mode!✨")

                # Display extracted metadata if available
                if st.session_state.meta_details:
                    st.subheader("📌 Extracted Metadata:")
                    st.json(st.session_state.meta_details)
                    
            # Don't ask for re-upload if content is already in session_state
            if "uploaded_file" not in st.session_state:
                st.warning("🚨 Please upload a PDF file to proceed.")
                st.stop()  # Prevent further execution

            # Show chat history and input
            display_chat_history()
            
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


if __name__ == "__main__":
    main()