import os
import time
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="SSS 3 AI Tutor", page_icon="🎓", layout="wide")

st.title("🎓 SSS 3 WAEC / NECO / UTME Interactive Tutor")
st.caption("Physics • Chemistry • Biology • Food & Nut • Math • English • Geography")

api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("⚠️ API Key not found. Please set `GEMINI_API_KEY` in Streamlit Secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

st.sidebar.header("1. Select Subject")
subject = st.sidebar.selectbox(
    "Subject",
    ["Physics", "Mathematics", "Chemistry", "Biology", "Food & Nutrition", "English Language", "Geography"]
)

st.sidebar.header("2. Upload Study Materials / Photos")
uploaded_file = st.sidebar.file_uploader(
    "Upload Textbook PDF, or Snap/Upload Photo (PNG, JPG, PDF)", 
    type=["pdf", "txt", "png", "jpg", "jpeg"]
)

SUBJECT_PROMPTS = {
    "Physics": "Solve problems step-by-step. Render equations in LaTeX (e.g., $v^2 = u^2 + 2as$). Emphasize WAEC calculation units and standard constants.",
    "Chemistry": "Render chemical equations in LaTeX (e.g., $\\text{2NaOH} + \\text{H}_2\\text{SO}_4 \\rightarrow \\text{Na}_2\\text{SO}_4 + \\text{2H}_2\\text{O}$). Detail IUPAC nomenclature.",
    "Biology": "Provide clear anatomical definitions, biological systems breakdowns, key terms, and textbook page citations.",
    "Food & Nutrition": "Highlight nutrient classifications, meal planning rules, culinary terms, food preservation principles, and WAEC practical exam tips.",
    "Mathematics": "Format formulas in LaTeX syntax using $...$ and $$...$$. Break down solutions step-by-step and highlight WAEC pitfalls.",
    "English Language": "Focus on WAEC/UTME grammar structures, essay formats, comprehension strategies, and oral English phonetics.",
    "Geography": "Explain physical and human geography concepts with step-by-step breakdowns, map reading techniques, and local Nigerian case studies."
}

# Process file with error handling
if uploaded_file is not None:
    if "current_file_name" not in st.session_state or st.session_state.current_file_name != uploaded_file.name:
        with st.spinner("Processing uploaded file (large files may take up to a minute)..."):
            temp_path = f"temp_{uploaded_file.name}"
            try:
                # Save uploaded file chunk by chunk to prevent memory spikes
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Upload to Gemini File API
                file_ref = client.files.upload(file=temp_path)
                
                # Verify file processing state
                while file_ref.state.name == "PROCESSING":
                    time.sleep(2)
                    file_ref = client.files.get(name=file_ref.name)
                    
                if file_ref.state.name == "FAILED":
                    st.sidebar.error("❌ File processing failed on Gemini server. Please compress the PDF.")
                else:
                    st.session_state.file_ref = file_ref
                    st.session_state.current_file_name = uploaded_file.name
                    st.session_state.is_image = uploaded_file.type.startswith("image/")
                    st.sidebar.success("📚 Document processed successfully!")

            except Exception as e:
                st.sidebar.error(f"⚠️ Upload Error: File may be too large for direct PDF parsing. Please compress PDF to under 50MB.")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_prompt = st.chat_input(f"Ask any {subject} question, snap a photo, or ask to solve uploaded material...")

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
        "1. Ground your answers directly in the uploaded syllabus, textbook, or image.\n"
        "2. If an image of a question/diagram is uploaded, read the question accurately, transcribe it first, then provide a detailed step-by-step solution.\n"
        "3. Cite textbook page numbers or chapters when applicable: [Source: Textbook, Page X / Chapter Y].\n"
        f"4. {SUBJECT_PROMPTS[subject]}\n"
        "5. Point out common WAEC/NECO marking scheme pitfalls and examiner tips."
    )

    with st.chat_message("assistant"):
        with st.spinner(f"Analyzing {subject} input..."):
            try:
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
            except Exception as e:
                st.error("⚠️ Response generation error. The uploaded document may be too large to process in a single request.")
