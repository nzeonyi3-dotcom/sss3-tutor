import os
import time
import streamlit as st
from google import genai
from google.genai import types

# Page setup for mobile responsiveness
st.set_page_config(page_title="SSS 3 Automated Tutor", page_icon="🎓", layout="wide")

st.title("🎓 SSS 3 WAEC / NECO / UTME Automated Tutor")
st.caption("Preloaded Curricula • Timed MCQs • Topic Mastery • Past Questions")

# Retrieve API Key from Secrets
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ API Key missing in Streamlit Secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# ---------------------------------------------------------
# PRELOADED RESOURCE MAPPING (Add your public file URLs here)
# ---------------------------------------------------------
PRELOADED_RESOURCES = {
    "Physics": {
        "textbook": "https://drive.google.com/uc?export=download&id=YOUR_PHYSICS_FILE_ID",
        "syllabus": "WAEC SSS 3 Physics Syllabus: Mechanics, Waves, Electricity, Atomic Physics.",
        "topics": ["Projectiles & Motion", "Current Electricity", "Waves & Optics", "Electromagnetism", "Nuclear Physics"]
    },
    "Mathematics": {
        "textbook": "https://drive.google.com/uc?export=download&id=YOUR_MATH_FILE_ID",
        "syllabus": "WAEC SSS 3 Math Syllabus: Quadratic Eq, Trigonometry, Calculus, Statistics, Matrices.",
        "topics": ["Quadratic & Simultaneous Equations", "Trigonometric Ratios", "Calculus (Differentiation & Integration)", "Statistics & Probability", "Circle Theorems"]
    },
    "Chemistry": {
        "textbook": "https://drive.google.com/uc?export=download&id=YOUR_CHEMISTRY_FILE_ID",
        "syllabus": "WAEC SSS 3 Chem Syllabus: Organic Chemistry, Stoichiometry, Electrochemistry, Periodic Table.",
        "topics": ["Organic Chemistry & Hydrocarbons", "Electrolysis & Redox", "Chemical Equilibrium", "Rates of Reaction", "Periodic Table Trends"]
    },
    "Biology": {
        "textbook": "",
        "syllabus": "WAEC SSS 3 Bio Syllabus: Cell Biology, Genetics, Ecology, Human Physiology.",
        "topics": ["Genetics & Heredity", "Ecosystems & Ecology", "Digestive & Excretory Systems", "Plant Transport & Photosynthesis"]
    }
}

# Sidebar Options
st.sidebar.header("1. Learning Hub Setup")
subject = st.sidebar.selectbox("Select Subject", list(PRELOADED_RESOURCES.keys()))
topic = st.sidebar.selectbox("Select Topic", PRELOADED_RESOURCES[subject]["topics"])

mode = st.sidebar.radio(
    "Select Study Area",
    [
        "📖 1. Study & Learn New Topic",
        "🎯 2. Assess Understanding",
        "✍️ 3. Guided Past Question P&A",
        "⏱️ 4. Timed 10-MCQ Quiz (15 Mins)"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(f"📌 **Subject:** {subject}\n\n📌 **Topic:** {topic}\n\n✅ Preloaded Content Active")

# Base instructions for LaTeX and examination grounding
BASE_SYSTEM_INSTRUCTION = (
    f"You are an expert Nigerian SSS 3 Tutor for WAEC, NECO, and UTME in {subject}. "
    f"Current Topic under review: '{topic}'. "
    "Formatting rule: Render ALL mathematical and chemical equations in clear LaTeX ($...$ for inline, $$...$$ for block). "
    "Always cite the preloaded textbook chapter/page when explaining concepts."
)

# ---------------------------------------------------------
# MODE 1: STUDY & LEARN NEW TOPIC
# ---------------------------------------------------------
if mode == "📖 1. Study & Learn New Topic":
    st.subheader(f"📖 Reading & Learning: {topic}")
    st.write("This section introduces new concepts step-by-step according to the WAEC/NECO syllabus.")
    
    if st.button("Generate Topic Overview & Reading Notes"):
        prompt = f"Provide a complete structured reading guide for the SSS 3 topic '{topic}'. Break it into 3 sub-sections, provide clear definitions, real-world examples, and cite relevant textbook pages."
        with st.spinner("Preparing learning material..."):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt],
                config=types.GenerateContentConfig(system_instruction=BASE_SYSTEM_INSTRUCTION, temperature=0.3)
            )
            st.markdown(response.text)

# ---------------------------------------------------------
# MODE 2: ASSESS UNDERSTANDING
# ---------------------------------------------------------
elif mode == "🎯 2. Assess Understanding":
    st.subheader(f"🎯 Diagnostic Exercises: {topic}")
    st.write("Generate diagnostic questions to gauge how well you understand the topic.")
    
    if st.button("Generate Diagnostic Questions"):
        prompt = f"Generate 3 diagnostic conceptual exercises for '{topic}'. Ask the student to solve them or explain the concepts, but DO NOT provide answers yet until requested."
        with st.spinner("Building exercises..."):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt],
                config=types.GenerateContentConfig(system_instruction=BASE_SYSTEM_INSTRUCTION, temperature=0.3)
            )
            st.markdown(response.text)

# ---------------------------------------------------------
# MODE 3: GUIDED PAST QUESTION P&A
# ---------------------------------------------------------
elif mode == "✍️ 3. Guided Past Question P&A":
    st.subheader(f"✍️ WAEC/NECO Past Question Solver: {topic}")
    st.write("The AI picks actual WAEC/NECO past questions on this topic and guides you step-by-step through the marking scheme.")
    
    if st.button("Fetch & Solve Past Question"):
        prompt = f"Pick a realistic WAEC/NECO Section B theory past question related to '{topic}'. Show the full question, then show a step-by-step marking guide with examiner tips on common student traps."
        with st.spinner("Fetching past question..."):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt],
                config=types.GenerateContentConfig(system_instruction=BASE_SYSTEM_INSTRUCTION, temperature=0.2)
            )
            st.markdown(response.text)

# ---------------------------------------------------------
# MODE 4: TIMED 10-MCQ QUIZ (15 MINS)
# ---------------------------------------------------------
elif mode == "⏱️ 4. Timed 10-MCQ Quiz (15 Mins)":
    st.subheader(f"⏱️ 15-Minute MCQ Exam: {topic}")
    st.warning("You have **10 Questions** to answer in **15 Minutes**. Click Start when ready!")

    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False

    if st.button("🚀 Start 15-Minute Quiz") and not st.session_state.quiz_started:
        st.session_state.quiz_started = True
        st.session_state.start_time = time.time()
        
        prompt = f"Generate 10 UTME/WAEC style Multiple Choice Questions on '{topic}'. Number them 1 to 10 with options A, B, C, D. Include an Answer Key at the VERY END hidden under a clear section."
        with st.spinner("Generating exam paper..."):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt],
                config=types.GenerateContentConfig(system_instruction=BASE_SYSTEM_INSTRUCTION, temperature=0.3)
            )
            st.session_state.quiz_content = response.text

    if st.session_state.get("quiz_started", False):
        # Countdown Timer Logic
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, 900 - int(elapsed))  # 900 seconds = 15 mins
        mins, secs = divmod(remaining, 60)
        
        st.metric("⏳ Time Remaining", f"{mins:02d}:{secs:02d}")
        
        if remaining == 0:
            st.error("⏰ Time is up! Submit your answers below to check your score.")
        
        st.markdown(st.session_state.quiz_content)

# Freeform Ask-Anything Input (Chat Bar)
st.markdown("---")
user_query = st.chat_input(f"Ask any follow-up question regarding {topic}...")
if user_query:
    with st.chat_message("user"):
        st.markdown(user_query)
    with st.chat_message("assistant"):
        with st.spinner("Searching topic resources..."):
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[user_query],
                config=types.GenerateContentConfig(system_instruction=BASE_SYSTEM_INSTRUCTION, temperature=0.3)
            )
            st.markdown(res.text)
