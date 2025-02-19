import streamlit as st

def apply_custom_css():
    
    st.markdown("""
        <style>
            /* 🌟 Light Theme Background */
            body {
                background: linear-gradient(to right, #f8f9fa, #e3e7eb, #dde4eb);
                color: #2c3e50;
                font-family: 'Poppins', sans-serif;
                animation: fadeIn 1s ease-in-out;
            }

            /* Smooth Fade-in Animation */
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            /* 📌 Light Sidebar */
            [data-testid="stSidebar"] {
                background: linear-gradient(to bottom, #f1f3f5, #ffffff);
                color: #2c3e50;
                border-right: 2px solid rgba(0, 0, 0, 0.1);
                padding: 20px;
            }

            /* Sidebar Header */
            [data-testid="stSidebar"] h2 {
                color: #4da8da;
                text-align: center;
                font-weight: bold;
                margin-bottom: 20px;
            }
            
            /* Ensure Sidebar Uses Only Necessary Space */
            [data-testid="stSidebar"] {
                display: flex;
                flex-direction: column;
                justify-content: start; /* Align content at the top */
                height: 100vh; /* Full height */
                overflow-y: auto; /* Enable vertical scrolling */
                padding-bottom: 0 !important; /* Remove extra padding */
            }

            /* Sidebar Menu Container */
            .sidebar-content {
                flex-grow: 0 !important; /* Prevents unnecessary stretching */
            }
            
            /* Remove Extra Space Below Last Button */
            .sidebar-menu {
                margin-bottom: 0 !important; 
                padding-bottom: 0 !important; 
            }

            /* Fix for Logout Button */
            .logout-button {
                margin-top: auto !important; /* Pushes it to the bottom */
            }
            
             /* Remove Empty Divs */
            .sidebar-content > div:last-child {
                display: none !important;
            }

            /* Sidebar Menu Title */
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

            /* Material Icon Color */
            .material-symbols-outlined {
                font-variation-settings:
                'FILL' 0,
                'wght' 400,
                'GRAD' 0,
                'opsz' 24;
                color: #2c3e50;
            }

            /* 📍 Elegant Button Styling */
            .stButton > button {
                background: linear-gradient(to right, #ff9a9e 0%, #fad0c4 51%, #a18cd1 100%);
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 12px 30px;
                border: none;
                border-radius: 12px;
                background-size: 200% auto;
                transition: 0.4s ease-in-out;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                display: block;
                width: 100%;
                cursor: pointer;
            }

            /* 🌟 Hover Glow Effect */
            .stButton > button:hover {
                background-position: right center;
                box-shadow: 0px 0px 20px rgba(255, 154, 158, 0.7);
                transform: scale(1.05);
                color: black;
            }

            /* 🔥 Swipe Right Animation */
            .stButton > button:active {
                transform: translateX(5px);
                transition: 0.1s ease-in-out;
            }

            /* 🗨️ Chat Input Box */
            .stChatInput > div {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 10px;
                padding: 10px;
                color: white;
                font-size: 16px;
                animation: fadeIn 1s ease-in-out;
            }

            /* 📩 Chat Messages */
            .stChatMessage {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 8px;
                animation: popIn 0.6s ease-in-out;
            }

            /* Pop-in Chat Message Animation */
            @keyframes popIn {
                from { transform: scale(0.8); opacity: 0; }
                to { transform: scale(1); opacity: 1; }
            }

            /* 🖱️ Smooth Animations */
            * {
                transition: all 0.3s ease-in-out;
            }
            
            /* 🖥️ Enable Scrollbar on the Main Application Page */
            .main {
                overflow-y: auto !important;
                max-height: 100vh; /* Ensure scrolling is only for the main page */
            }
            /* Custom Scrollbar Styling for Main Page */
            [data-testid="stSidebar"]::-webkit-scrollbar,
            .main::-webkit-scrollbar {
                width: 8px;
            }
            [data-testid="stSidebar"]::-webkit-scrollbar-track,
            .main::-webkit-scrollbar-track {
                background: #f1f3f5;
            }
            [data-testid="stSidebar"]::-webkit-scrollbar-thumb,
            .main::-webkit-scrollbar-thumb {
                background: #4da8da;
                border-radius: 10px;
            }
            [data-testid="stSidebar"]::-webkit-scrollbar-thumb:hover,
            .main::-webkit-scrollbar-thumb:hover {
                background: #41c7c7;
            }

            /* 📱 Mobile Responsiveness */
            @media screen and (max-width: 768px) {
                body {
                    font-size: 16px;
                    padding: 10px;
                }

                [data-testid="stSidebar"] {
                    width: 100%;
                    position: fixed;
                    top: 0;
                    left: 0;
                    height: auto;
                    border-right: none;
                    border-bottom: 2px solid rgba(0, 0, 0, 0.1);
                }

                .stButton > button {
                    font-size: 16px;
                    padding: 10px 20px;
                }

                .main-menu-title {
                    font-size: 18px;
                }
            }
        </style>

    """, unsafe_allow_html=True)