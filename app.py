import os
import streamlit as st
from google import genai
from google.genai import types

# Page Config
st.set_page_config(page_title="SSS 3 AI Tutor", page_icon="🎓", layout="wide")

st.title("🎓 SSS 3 WAEC / NECO / UTME Interactive Tutor")
st.caption("Physics • Chemistry • Biology • Food & Nut • Math • English • Geography")

# Automatically retrieve API Key from Streamlit Secrets or Environment
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("⚠️ API Key not found. Please set `GEMINI_API_KEY` in Streamlit Secrets.")
    st.stop()

# Initialize Client automatically using the secret key
client = genai.Client(api_key=api_key)

# Sidebar Options
st.sidebar.header("Study Configuration")
subject = st.sidebar.selectbox(
    "Select Subject",
    ["Physics", "Chemistry", "Biology", "Food & Nutrition", "Mathematics", "English Language", "Geography"]
)

# Upload Section
st.sidebar.header("Upload Study Materials")
uploaded_file = st.sidebar.file_uploader("Upload Textbook / Syllabus / Past Qs (PDF or TXT)", type=["pdf", "txt"])

# Subject-Specific System Prompts
SUBJECT_PROMPTS = {
    "Physics": "Solve problems step-by-step. Render all equations in LaTeX (e.g., $v^2 = u^2 + 2as$). Emphasize WAEC calculation units and standard constants.",
    "Chemistry": "Render all chemical equations and reactions in LaTeX (e.g., $\\text{2NaOH} + \\text{H}_2\\text{SO}_4 \\rightarrow \\text{Na}_2\\text{SO}_4 + \\text{2H}_2\\text{O}$). Detail IUPAC nomenclature.",
    "Biology": "Provide clear anatomical definitions, biological systems breakdowns, key terms, and textbook page citations.",
    "Food & Nutrition": "Highlight nutrient classifications, meal planning rules, culinary terms, food preservation principles, and WAEC practical exam tips.",
    "Mathematics": "Format all formulas, proofs, and algebraic steps in LaTeX. Highlight common arithmetic and geometric pitfalls.",
    "English Language": "Focus on WAEC/UTME grammar structures, essay formats (argumentative, formal letters), comprehension strategies, and oral English phonetics.",
    "Geography": "Explain physical and human geography concepts with structured step-by-step breakdowns, map reading techniques, and local Nigerian case studies."
}

# File Upload Processing via Gemini API
if "file_ref" not in st.session_state and uploaded_file is not None:
    with st.spinner("Processing document..."):
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        file_ref = client.files.upload(file=temp_path)
        st.session_state.file_ref = file_ref
        os.remove(temp_path)
        st.sidebar.success("Study Material Processed!")

# Chat History Setup
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_prompt = st.chat_input(f"Ask any {subject} question, past question, or request a practice quiz...")

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    contents = []
    if "file_ref" in st.session_state:
        contents.append(st.session_state.file_ref)
    
    for msg in st.session_state.messages:
        contents.append(msg["content"])

    full_system_instruction = (
        f"You are an expert Nigerian Senior Secondary School (SSS 3) tutor specializing in {subject}. "
        "You are helping a student prepare for WAEC, NECO, and UTME exams.\n\n"
        "STRICT BEHAVIORS:\n"
        "1. Ground your answers directly in the uploaded syllabus and textbook.\n"
        "2. Cite textbook page numbers or chapters for every concept: [Source: Textbook, Page X / Chapter Y].\n"
        f"3. {SUBJECT_PROMPTS[subject]}\n"
        "4. When solving past questions, show step-by-step working and point out common errors."
    )

    with st.chat_message("assistant"):
        with st.spinner(f"Analyzing {subject} materials..."):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=full_system_instruction,
                    temperature=0.2,
                )
            )
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
