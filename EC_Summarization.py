import streamlit as st

st.set_page_config(layout="wide")

# Custom CSS for a spacious layout
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
summarization_sections = [
    "General Information (பொதுவான தகவல்)",
    "Land Details (நில விவரங்கள்)",
    "Transaction Details (பரிமாற்ற விவரங்கள்)",
    "Boundaries (வரம்புகள்)"
]

def get_general_info_prompt():
    return "Extract the General Information details"

def get_land_details_prompt():
    return "Extract the Land Details"

def get_transaction_details_prompt():
    return "Extract the Transaction Details"

def get_boundaries_prompt():
    return "Extract the Boundaries"

# Mapping sections to their respective processing functions
process_functions = {
    "General Information": lambda: process_section("General Information", get_general_info_prompt(), st.session_state.content),
    "Land Details (நில விவரங்கள்)": lambda: process_section("Land Details", get_land_details_prompt(), st.session_state.content),
    "Transaction Details (பரிமாற்ற விவரங்கள்)": lambda: process_section("Transaction Details", get_transaction_details_prompt(), st.session_state.content),
    "Boundaries (வரம்புகள்)": lambda: process_section("Boundaries", get_boundaries_prompt(), st.session_state.content)
}

# Initialize session state for processed results
if "processed_results" not in st.session_state:
    st.session_state.processed_results = None  # Store only one result at a time

def process_section(title, prompt):
    return f"🔍 Processed **{title}** with prompt: {prompt}"

def run_summarization(extracted_text):
    st.write("### Select Sections to Summarize:")

    # Full-width 4-column layout
    cols = st.columns(4, gap="large")
    
    for idx, section in enumerate(summarization_sections):
        with cols[idx]:  # Place buttons inside columns
            if st.button(section, use_container_width=True):
                st.session_state.processed_results = process_functions[section]()  # Store only the latest processed result

    # Display results inside a container
    st.write("### Processed Results:")
    with st.container():
        if st.session_state.processed_results:
            st.info(st.session_state.processed_results)