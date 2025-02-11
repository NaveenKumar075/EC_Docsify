import sys
import streamlit as st

st.set_page_config(layout="wide")

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
    "boundaries": "Boundaries (வரம்புகள்)"
}

def process_section(title, prompt):
    return f"🔍 **Processed {title}**\n\n📝 **Prompt:** {prompt}"

def get_section_prompt(section_key):
    section_prompts = {
        "General Information (பொதுவான தகவல்)": "Extract the General Information details",
        "Land Details (நில விவரங்கள்)": "Extract the Land Details",
        "Transaction Details (பரிமாற்ற விவரங்கள்)": "Extract the Transaction Details",
        "Boundaries (வரம்புகள்)": "Extract the Boundaries"
    }
    
    return section_prompts.get(section_key, "")

def initialize_session_state():
    if "processed_results" not in st.session_state:
        st.session_state.processed_results = {section: None for section in summarization_sections.keys()}

def run_summarization(content):
    initialize_session_state()
    
    st.write("### Select Sections to Summarize:")

    # Full-width 4-column layout
    cols = st.columns(4, gap="large")
    
    for idx, (section_key, section_title) in enumerate(summarization_sections.items()):
        with cols[idx]:  # Place buttons inside columns
            if st.button(section_title, key=f"btn_{section_key}"):
                with st.spinner(f"📝 Processing {section_title}..."):
                    prompt = get_section_prompt(section_key)
                    result = process_section(section_title, prompt, content)
                    st.session_state.processed_results[section_key] = result

    # Display results inside a container
    st.write("### 📋 Summarized Results:")
    with st.container():
        for section_key, section_title in summarization_sections.items():
            result = st.session_state.processed_results[section_key]
            if result:
                with st.expander(section_title, expanded=True):
                    st.markdown(result)
                

if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        st.error("⚠ No input file provided!")
        sys.exit(1)
    file_path = sys.argv[1]
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
    except FileNotFoundError:
        st.error("⚠ Failed to load the document.")
        sys.exit(1)
    
    run_summarization(content)