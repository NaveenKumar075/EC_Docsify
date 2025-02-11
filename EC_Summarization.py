import sys
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

def process_section(title, prompt):
    return f"🔍 **Processed {title}**\n\n📝 **Prompt:** {prompt}"

# Ensure session state is initialized
if "processed_results" not in st.session_state:
    st.session_state.processed_results = {section: None for section in summarization_sections}

# Mapping sections to their respective processing functions
process_functions = {
    "General Information (பொதுவான தகவல்)": lambda content: process_section("General Information", get_general_info_prompt(), content),
    "Land Details (நில விவரங்கள்)": lambda content: process_section("Land Details", get_land_details_prompt(), content),
    "Transaction Details (பரிமாற்ற விவரங்கள்)" : lambda content: process_section("Transaction Details", get_transaction_details_prompt(), content),
    "Boundaries (வரம்புகள்)": lambda content: process_section("Boundaries", get_boundaries_prompt(), content)
}

def run_summarization(content):
    st.write("### Select Sections to Summarize:")

    # Full-width 4-column layout
    cols = st.columns(4, gap="large")
    
    for idx, (section, process_fn) in enumerate(process_functions.items()):
        with cols[idx]:  # Place buttons inside columns
            if st.button(section, key=f"btn_{section}"):
                st.session_state.processed_results[section] = process_fn(content)  # Update only the respective section

    # Display results inside a container
    st.write("### Processed Results:")
    with st.container():
        for section, result in st.session_state.processed_results.items():
            if result:
                st.info(f"**{section}:**\n{result}")
                

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