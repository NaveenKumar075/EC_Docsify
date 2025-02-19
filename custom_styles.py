import streamlit as st

def apply_custom_css():
    
    st.markdown("""
        <style>
            /* Dark blue gradient background */
            body {
                background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
                color: white;
                font-family: 'Poppins', sans-serif;
                animation: fadeIn 1s ease-in-out;
            }

            /* Smooth Fade-in Animation */
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            /* Sidebar Animation */
            [data-testid="stSidebar"] {
                background: #1a1f2b;
                color: white;
                border-right: 2px solid rgba(255, 255, 255, 0.2);
                padding: 20px;
                transform: translateX(-100%);
                animation: slideIn 0.8s ease-in-out forwards;
            }

            @keyframes slideIn {
                from { transform: translateX(-100%); }
                to { transform: translateX(0); }
            }

            /* Sidebar Header */
            [data-testid="stSidebar"] h2 {
                color: #4da8da;
                text-align: center;
                font-weight: bold;
                margin-bottom: 20px;
            }

            /* Sidebar menu title */
            .main-menu-title {
                display: flex;
                align-items: center;
                font-size: 22px;
                font-weight: bold;
                color: #ffffff;
                padding: 10px;
                border-bottom: 2px solid #4da8da;
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
                animation: buttonPulse 2s infinite;
            }

            /* Button hover & click effect */
            .stButton > button:hover {
                background-position: right center;
                transform: scale(1.1);
                box-shadow: 6px 6px 16px rgba(41, 172, 172, 0.6);
                color: #1a1f2b;
            }

            /* Button Pulse Animation */
            @keyframes buttonPulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); box-shadow: 0px 0px 10px rgba(41, 172, 172, 0.6); }
                100% { transform: scale(1); }
            }

            /* Chat input box */
            .stChatInput > div {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 10px;
                padding: 10px;
                color: white;
                font-size: 16px;
                animation: fadeIn 1s ease-in-out;
            }

            /* Chatbot messages */
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
                    border-bottom: 2px solid rgba(255, 255, 255, 0.2);
                    animation: slideIn 0.8s ease-in-out forwards;
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