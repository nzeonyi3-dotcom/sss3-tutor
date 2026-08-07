import os
import time
import requests
import streamlit as st
from google import genai
from google.genai import types

# Page Setup
st.set_page_config(page_title="SSS 3 Automated Tutor", page_icon="🎓", layout="wide")

st.title("🎓 SSS 3 WAEC / NECO / UTME Automated Tutor")
st.caption("Permanent Preloaded Textbooks • Timed MCQs • Topic Mastery • Past Questions")

# Retrieve API Key
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ API Key missing in Streamlit Secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# Permanent Google Drive Links from Streamlit Secrets
SUBJECT_URLS = {
    "Physics": st.secrets.get("PHYSICS_PDF_URL"),
    "Mathematics": st.secrets.get("MATH_PDF_URL"),
    "Chemistry": st.secrets.get("CHEMISTRY_PDF_URL"),
    "Biology": st.secrets.get("BIOLOGY_PDF_URL"),
    "Geography": st.secrets.get("GEOGRAPHY_PDF_URL"),
    "English Language": st.secrets.get("ENGLISH_PDF_URL"),
    "Food & Nutrition": st.secrets.get("FOOD_NUT_PDF_URL"),
}

SUBJECT_TOPICS = {
    "Physics": ["Projectiles & Motion", "Current Electricity", "Waves & Optics", "Electromagnetism", "Nuclear Physics"],
    "Mathematics": ["Quadratic & Simultaneous Equations", "Trigonometric Ratios", "Calculus", "Statistics & Probability", "Circle Theorems"],
    "Chemistry": ["Organic Chemistry & Hydrocarbons", "Electrolysis & Redox", "Chemical Equilibrium", "Rates of Reaction"],
    "Biology": ["Genetics & Heredity", "Ecosystems & Ecology", "Digestive & Excretory Systems", "Photosynthesis"],
    "Geography": ["Map Reading", "Physical Geography", "Human & Economic Geography of Nigeria"],
    "English Language": ["Grammar & Lexis", "Comprehension Strategies", "Oral English & Phonetics", "Essay Writing"],
    "Food & Nutrition": ["Nutrient Classification", "Meal Planning", "Food Preservation", "Culinary Terms & Practicals"]
}

# Sidebar Controls
st.sidebar.header("1. Learning Hub Setup")
subject = st.sidebar.selectbox("Select Subject", list(SUBJECT_TOPICS.keys()))
topic = st.sidebar.selectbox("Select Topic", SUBJECT_TOPICS[subject])

mode = st.sidebar.radio(
    "2. Choose Learning Area",
    [
        "📖 1. Study & Learn New Topic",
        "🎯 2. Assess Understanding",
        "✍️ 3. Guided Past Question P&A",
        "⏱️ 4. Timed 10-MCQ Quiz (15 Mins)"
    ]
)

def get_direct_gdrive_url(url):
    """Appends confirm parameter to bypass Google Drive virus scan warning on large files."""
    if not url:
        return None
    if "confirm=t" not in url:
        if "?" in url:
            return f"{url}&confirm=t"
        else:
            return f"{url}?confirm=t"
    return url

# Cache PDF download & Gemini upload (ttl=86400 refreshes automatically every 24h)
@st.cache_resource(ttl=86400, show_spinner="Loading permanent textbook resources...")
def load_permanent_textbook(subj_name, download_url):
    if not download_url:
        return None
    
    local_filename = f"temp_{subj_name}.pdf"
    direct_url = get_direct_gdrive_url(download_url)
    
    # Download file using requests session to handle redirects and large files
    session = requests.Session()
    response = session.get(direct_url, allow_redirects=True, stream=True)
    
    with open(local_filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)
    
    # Validate that the downloaded file is a valid PDF (starts with %PDF)
    with open(local_filename, "rb") as f:
        header = f.read(4)
        if header != b"%PDF":
            os.remove(local_filename)
            raise ValueError("Downloaded file is not a valid PDF. Verify Google Drive access permissions ('Anyone with link').")

    # Upload file to Gemini Session
    file_ref = client.files.upload(file=local_filename)
    
    while file_ref.state.name == "PROCESSING":
        time.sleep(2)
        file_ref = client.files.get(name=file_ref.name)
        
    os.remove(local_filename)
    return file_ref

# Load Active Textbook
file_ref = None
pdf_url = SUBJECT_URLS.get(subject)

if pdf_url:
    try:
        file_ref = load_permanent_textbook(subject, pdf_url)
        st.sidebar.success(f"✅ {subject} Textbook Loaded permanently!")
    except Exception as e:
        st.sidebar.warning(f"⚠️ Textbook loading note: {e}. Operating in standard AI mode.")

# Base Instructions for Gemini
BASE_SYSTEM_INSTRUCTION = (
    f"You are an expert Nigerian SSS 3 Tutor for WAEC, NECO, and UTME in {subject}. "
    f"Current Topic under review: '{topic}'. "
    "STRICT BEHAVIORS:\n"
    "1. Ground explanations directly in the preloaded textbook and WAEC/NECO syllabus.\n"
    "2. Render ALL mathematical and chemical equations in LaTeX ($...$ for inline, $$...$$ for block).\n"
    "3. Cite textbook page numbers or chapters whenever explaining concepts: [Source: Textbook, Page X / Chapter Y].\n"
    "4. Highlight WAEC/NECO marking scheme traps and examiner tips."
)

def get_contents(user_prompt):
    contents = []
    if file_ref:
        contents.append(file_ref)
    contents.append(user_prompt)
    return contents

# ---------------------------------------------------------
# MODE 1: STUDY & LEARN NEW TOPIC
# ---------------------------------------------------------
if mode == "📖 1. Study & Learn New Topic":
    st.subheader(f"📖 Reading & Learning: {topic}")
    st.write("Introduces new concepts step-by-step according to the WAEC/NECO syllabus.")
    if st.button("Generate Reading Notes"):
        prompt = f"Provide a complete structured reading guide for '{topic}'. Break it into 3 sub-sections with clear definitions, real-world examples, and textbook citations."
        with st.spinner("Generating reading notes from preloaded textbook..."):
            try:
                res = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=get_contents(prompt),
                    config=types.GenerateContentConfig(system_instruction=BASE_SYSTEM_INSTRUCTION, temperature=0.3)
                )
                st.markdown(res.text)
            except Exception as err:
                st.error("⚠️ Response generation error. Re-indexing textbook...")
                st.cache_resource.clear()

# ---------------------------------------------------------
# MODE 2: ASSESS UNDERSTANDING
# ---------------------------------------------------------
elif mode == "🎯 2. Assess Understanding":
    st.subheader(f"🎯 Diagnostic Exercises: {topic}")
    st.write("Test how well you understood the reading before moving forward.")
    if st.button("Generate Diagnostic Questions"):
        prompt = f"Generate 3 diagnostic conceptual questions for '{topic}'. Ask the student to solve or explain them. DO NOT show answers until requested."
        with st.spinner("Generating diagnostic exercises..."):
            try:
                res = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=get_contents(prompt),
                    config=types.GenerateContentConfig(system_instruction=BASE_SYSTEM_INSTRUCTION, temperature=0.3)
                )
                st.markdown(res.text)
            except Exception as err:
                st.error("⚠️ Response generation error. Clear cache and try again.")
                st.cache_resource.clear()

# ---------------------------------------------------------
# MODE 3: GUIDED PAST QUESTION P&A
# ---------------------------------------------------------
elif mode == "✍️ 3. Guided Past Question P&A":
    st.subheader(f"✍️ WAEC/NECO Past Question Solver: {topic}")
    st.write("Pulls real past questions on this topic and guides you step-by-step through the solution.")
    if st.button("Fetch & Solve Past Question"):
        prompt = f"Pick a realistic WAEC/NECO Section B theory past question on '{topic}'. Provide the full question, then a step-by-step marking scheme answer with examiner tips."
        with st.spinner("Fetching past question..."):
            try:
                res = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=get_contents(prompt),
                    config=types.GenerateContentConfig(system_instruction=BASE_SYSTEM_INSTRUCTION, temperature=0.2)
                )
                st.markdown(res.text)
            except Exception as err:
                st.error("⚠️ Response generation error.")
                st.cache_resource.clear()

# ---------------------------------------------------------
# MODE 4: TIMED 10-MCQ QUIZ (15 MINS)
# ---------------------------------------------------------
elif mode == "⏱️ 4. Timed 10-MCQ Quiz (15 Mins)":
    st.subheader(f"⏱️ 15-Minute MCQ Exam: {topic}")
    st.warning("You have **10 Questions** to answer in **15 Minutes**.")

    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False

    if st.button("🚀 Start 15-Minute Quiz"):
        st.session_state.quiz_started = True
        st.session_state.start_time = time.time()
        
        prompt = f"Generate 10 UTME/WAEC style Multiple Choice Questions on '{topic}'. Number them 1 to 10 with options A, B, C, D. Put the Answer Key at the VERY END hidden under a clear section header."
        with st.spinner("Generating quiz..."):
            try:
                res = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=get_contents(prompt),
                    config=types.GenerateContentConfig(system_instruction=BASE_SYSTEM_INSTRUCTION, temperature=0.3)
                )
                st.session_state.quiz_content = res.text
            except Exception as err:
                st.error("⚠️ Error generating quiz questions.")
                st.cache_resource.clear()

    if st.session_state.get("quiz_started", False):
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, 900 - int(elapsed))
        mins, secs = divmod(remaining, 60)
        
        st.metric("⏳ Time Remaining", f"{mins:02d}:{secs:02d}")
        
        if remaining == 0:
            st.error("⏰ Time is up! Review your answers below.")
        
        st.markdown(st.session_state.quiz_content)

# Freeform Chat Query
st.markdown("---")
user_query = st.chat_input(f"Ask any question regarding {topic}...")
if user_query:
    with st.chat_message("user"):
        st.markdown(user_query)
    with st.chat_message("assistant"):
        with st.spinner("Analyzing preloaded materials..."):
            try:
                res = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=get_contents(user_query),
                    config=types.GenerateContentConfig(system_instruction=BASE_SYSTEM_INSTRUCTION, temperature=0.3)
                )
                st.markdown(res.text)
            except Exception as err:
                st.error("⚠️ Query error. Please refresh the page.")
                st.cache_resource.clear()
