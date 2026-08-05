import os
import streamlit as st
from google import genai
from google.genai import types

# Page Config for Mobile and Desktop
st.set_page_config(page_title="SSS 3 AI Tutor", page_icon="🎓", layout="wide")

st.title("🎓 SSS 3 WAEC / NECO / UTME Interactive Tutor")
st.caption("Physics • Chemistry • Biology • Food & Nut • Math • English • Geography")

# Automatically retrieve API Key from Streamlit Secrets or Environment
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("⚠️ API Key not found. Please set `GEMINI_API_KEY` in Streamlit Secrets.")
    st.stop()

# Initialize Client automatically
client = genai.Client(api_key=api_key)

# Sidebar Options
st.sidebar.header("1. Select Subject")
subject = st.sidebar.selectbox(
    "Subject",
    ["Mathematics", "Physics", "Chemistry", "Biology", "Food & Nutrition", "English Language", "Geography"]
)

# Upload Section (Supports PDFs, Textbooks, and Camera Photos/Images)
st.sidebar.header("2. Upload Study Materials / Photos")
uploaded_file = st.sidebar.file_uploader(
    "Upload Textbook PDF, or Snap/Upload Photo of Math Question (PNG, JPG, PDF)", 
    type=["pdf", "txt", "png", "jpg", "jpeg"]
)

# Subject-Specific System Prompts with LaTeX Enforcement
SUBJECT_PROMPTS = {
    "Mathematics": "Format all formulas, proofs, and algebraic steps in LaTeX syntax using $...$ for inline math and $$...$$ for block equations. Break down solutions step-by-step. If an image of a math question or diagram is uploaded, analyze the visual diagram/text carefully before solving. Highlight common WAEC arithmetic and geometric pitfalls.",
    "Physics": "Solve problems step-by-step. Render all equations in LaTeX (e.g., $v^2 = u^2 + 2as$). Emphasize WAEC calculation units and standard constants. Analyze visual diagrams if uploaded.",
    "Chemistry": "Render all chemical equations and reactions in LaTeX (e.g., $\\text{2NaOH} + \\text{H}_2\\text{SO}_4 \\rightarrow \\text{Na}_2\\text{SO}_4 + \\text{2H}_2\\text{O}$). Detail IUPAC nomenclature.",
    "Biology": "Provide clear anatomical definitions, biological systems breakdowns, key terms, and textbook page citations.",
    "Food & Nutrition": "Highlight nutrient classifications, meal planning rules, culinary terms, food preservation principles, and WAEC practical exam tips.",
    "English Language": "Focus on WAEC/UTME grammar structures, essay formats (argumentative, formal letters), comprehension strategies, and oral English phonetics.",
    "Geography": "Explain physical and human geography concepts with structured step-by-step breakdowns, map reading techniques, and local Nigerian case studies."
}

# Handle File / Image Upload via Gemini API
if uploaded_file is not None:
    # Check if a new file is uploaded
    if "current_file_name" not in st.session_state or st.session_state.current_file_name != uploaded_file.name:
        with st.spinner("Processing uploaded file/photo..."):
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Upload file or photo to Gemini File API
            file_ref = client.files.upload(file=temp_path)
            st.session_state.file_ref = file_ref
            st.session_state.current_file_name = uploaded_file.name
            st.session_state.is_image = uploaded_file.type.startswith("image/")
            os.remove(temp_path)
            
            if st.session_state.is_image:
                st.sidebar.image(uploaded_file, caption="Uploaded Question Preview", use_container_width=True)
                st.sidebar.success("📸 Photo processed successfully!")
            else:
                st.sidebar.success("📚 Document processed successfully!")

# Chat History Setup
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_prompt = st.chat_input(f"Ask any {subject} question, snap a photo, or ask to solve the uploaded image...")

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    contents = []
    
    # Attach active uploaded file/photo reference
    if "file_ref" in st.session_state:
        contents.append(st.session_state.file_ref)
    
    # Add text chat history
    for msg in st.session_state.messages:
        contents.append(msg["content"])

    full_system_instruction = (
        f"You are an expert Nigerian Senior Secondary School (SSS 3) tutor specializing in {subject}. "
        "You are helping a student prepare for WAEC, NECO, and UTME exams.\n\n"
        "STRICT BEHAVIORS:\n"
        "1. Ground your answers directly in the uploaded syllabus, textbook, or image.\n"
        "2. If an image of a question/diagram is uploaded, read the handwritten or printed question accurately, transcribe it first, then provide a detailed step-by-step solution.\n"
        "3. Cite textbook page numbers or chapters when applicable: [Source: Textbook, Page X / Chapter Y].\n"
        f"4. {SUBJECT_PROMPTS[subject]}\n"
        "5. Point out common WAEC/NECO marking scheme pitfalls and examiner tips."
    )

    with st.chat_message("assistant"):
        with st.spinner(f"Analyzing {subject} input..."):
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
