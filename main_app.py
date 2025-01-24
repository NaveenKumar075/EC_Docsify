import re, time, json, shortuuid, requests
import pyrebase
import streamlit as st
import tempfile
from io import BytesIO
from streamlit_lottie import st_lottie
from streamlit_option_menu import option_menu
from hydralit_components import HyLoader, Loaders
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
from legalgpt_EC import pdf_extraction, retrieving_process, rerank_documents, extract_meta_details, EC_ChatBot, EC_Summarization
import warnings
warnings.filterwarnings('ignore')


# Firebase configuration
firebase_config = st.secrets["firebase"]
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
database = firebase.database()


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
        'content': None,
        'meta_details': None,
        'chat_history': []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()


def display_chat_history():
    for message in st.session_state.chat_history:
        with st.chat_message(message['role']):
            st.markdown(message['content'])


# Function to load a Lottie animation from a URL
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
        database.child(user['localId']).child("Username").set(username)
        database.child(user['localId']).child("ID").set(user['localId'])
        st.session_state['user'] = {
            'email': email,
            'username': username
        }
        st.success("Account created successfully!")
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

        token = user['idToken']
        refresh_token = user['refreshToken']
        st.session_state['authenticated'] = True
        st.session_state['user'] = {
            'email': email,  
            'localId': user['localId'],  
            'idToken': token,  
            'refreshToken': refresh_token,  
            'expiresAt': datetime.utcnow() + timedelta(seconds=3600),  # Token expiry time
            'user': user  # Storing the full Firebase user object
        }
        if 'username' not in st.session_state['user']:
            user_data = database.child(user['localId']).get().val()
            username = user_data.get("Username", "Unknown User")
            st.session_state['user']['username'] = username
        st.success("Logged in successfully!")
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
    st.session_state['authenticated'] = False
    st.session_state['user'] = None
    st.success("Logged out successfully!")
    st.rerun()
    

# Function to check if user session is still valid
def check_authentication():
    if 'user' in st.session_state and st.session_state['user'] and 'idToken' in st.session_state['user']:
        if st.session_state['user']['expiresAt'] > datetime.utcnow():
            return True
        else:
            try:
                new_token = auth.refresh(st.session_state['user']['refreshToken']) # Refresh the token if expired
                st.session_state['user']['idToken'] = new_token['idToken']
                st.session_state['user']['expiresAt'] = datetime.utcnow() + timedelta(seconds=3600)
                return True
            except Exception:
                st.session_state.clear()
                st.warning("Session expired. Please log in again.")
                return False
    return False


# Google Drive upload function
def upload_to_drive(file, username):
    try:
        unique_code = shortuuid.ShortUUID().random(length=7)
        new_file_name = f"{username}_{unique_code}"
        file_content = BytesIO(file.getbuffer())
        file_metadata = {'name': new_file_name, 'parents': [parent_folder_id]}
        media = MediaIoBaseUpload(file_content, mimetype='application/pdf', resumable=True)
        drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        st.success(f"File uploaded successfully!")
    except Exception as e:
        st.error(f"Failed to upload file to Google Drive: {e}")
        
        
# Streamlit UI setup
def main():
    st.set_page_config(
        page_title="EC Docsify", 
        page_icon="🚀", 
        initial_sidebar_state="expanded"
    )
    st.title("EC Docsify 🤖")
    with HyLoader('', Loaders.pretty_loaders,index=[0]):
        time.sleep(2)

    if check_authentication():
        st.success(f"Welcome back, {st.session_state['user']['username']}!")
        if st.button("Logout"):
            logout()
    else:
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
                            st.warning("Please provide a nickname to complete the signup.")
    
        else:
            username = st.session_state['user']['username']
            st.sidebar.success(f"Welcome, {username}")
            
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
                
            if selected == 'ChatBot':
                st.header("Chatbot Mode")
                st.write("Ask questions about the uploaded document.")
                
                st.subheader("Upload Your Files Here!")
                uploaded_file = st.file_uploader("Choose a file 📑", type=["pdf"])
                
                if uploaded_file is not None:
                    if 'uploaded_filename' not in st.session_state or st.session_state.uploaded_filename != uploaded_file.name:
                        with st.spinner("📤 Uploading to Google Drive..."):
                            upload_to_drive(uploaded_file, username)  # Upload to Google Drive
    
                        # Store filename to avoid reprocessing
                        st.session_state.uploaded_filename = uploaded_file.name
                        st.session_state.content = pdf_extraction(uploaded_file)
                        st.success("File uploaded and processed successfully!")
                        
                # Ensure the content is available before displaying chat history and input box
                if 'content' in st.session_state:
                    display_chat_history()
                        
                    if prompt := st.chat_input("Ask your question here:"):
                        st.session_state.chat_history.append({"role": "user", "content": prompt})
                        with st.chat_message("user"):
                            st.markdown(prompt)
                        with st.chat_message("assistant"):
                            with st.spinner("Generating response..."):
                                retrieved_chunks = retrieving_process(st.session_state.content, prompt)
                                st.toast("Retrieved chunks")
                                reranked_docs = rerank_documents(retrieved_chunks, prompt)
                                st.toast("Reranked documents")
                                response = EC_ChatBot(reranked_docs, prompt)
                                st.toast("Response generated")
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                        st.rerun()
                else:
                    st.info("Please upload and process the document first.")
    
                if uploaded_file is None:
                    st.warning("Please upload a PDF file to proceed.")
            
            # Logout function          
            if st.sidebar.button("Logout"):
                logout()


if __name__ == "__main__":
    main()
