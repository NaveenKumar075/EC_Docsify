import streamlit as st

def apply_custom_css():
    
    st.markdown("""
        <style>
            /* Dark blue background */
            body {
                background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
                color: white;
                font-family: 'Poppins', sans-serif;
            }

            /* Sidebar styling */
            .sidebar .sidebar-content {
                background: #1a1f2b;
                color: white;
                border-right: 2px solid rgba(255, 255, 255, 0.2);
            }
            .sidebar .sidebar-content:hover {
                background: #222a35;
            }
            .sidebar .sidebar-content h2 {
                color: #4da8da;
                text-align: center;
                font-weight: bold;
                margin-bottom: 20px;
            }

            /* Sidebar menu */
            .main-menu-title {
                display: flex;
                align-items: center;
                font-size: 22px;
                font-weight: bold;
                color: #ffffff;
                padding: 10px;
                border-bottom: 2px solid #4da8da;
            }
            .main-menu-title span {
                font-size: 24px;
                color: #4da8da;
            }

            /* Navigation button styles */
            .stButton > button {
                background-image: linear-gradient(to right, #4da8da 0%, #41c7c7 51%, #1282a2 100%);
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 12px 30px;
                border: none;
                border-radius: 12px;
                transition: all 0.4s ease-in-out;
                cursor: pointer;
            }

            .stButton > button:hover {
                background-position: right center;
                transform: scale(1.1);
                box-shadow: 6px 6px 16px rgba(41, 172, 172, 0.6);
                color: #1a1f2b;
            }

            /* Chat input box */
            .stChatInput > div {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 10px;
                padding: 10px;
                color: white;
                font-size: 16px;
            }

            /* Chatbot messages */
            .stChatMessage {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 8px;
            }

            /* Smooth animations */
            * {
                transition: all 0.3s ease-in-out;
            }

            /* Scrollbar customization */
            ::-webkit-scrollbar {
                width: 8px;
            }
            ::-webkit-scrollbar-track {
                background: #1a1f2b;
            }
            ::-webkit-scrollbar-thumb {
                background: #4da8da;
                border-radius: 10px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: #41c7c7;
            }
        </style>
    """, unsafe_allow_html=True)