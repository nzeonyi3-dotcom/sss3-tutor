import os
import time
import requests
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="SSS 3 Automated Tutor", page_icon="🎓", layout="wide")

st.title("🎓 SSS 3 WAEC / NECO / UTME Automated Tutor")

api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ API Key missing in Streamlit Secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# Permanent Google Drive Links from Secrets
SUBJECT_URLS = {
    "Physics": st.secrets.get("PHYSICS_PDF_URL"),
    "Mathematics": st.secrets.get("MATH_PDF_URL"),
    "Chemistry": st.secrets.get("CHEMISTRY_PDF_URL"),
}

SUBJECT_TOPICS = {
    "Physics": ["Projectiles & Motion", "Current Electricity", "Waves & Optics", "Electromagnetism"],
    "Mathematics": ["Quadratic Equations", "Trigonometry", "Calculus", "Statistics"],
    "Chemistry": ["Organic Chemistry", "Electrolysis", "Chemical Equilibrium"]
}

st.sidebar.header("1. Learning Hub Setup")
subject = st.sidebar.selectbox("Select Subject", list(SUBJECT_TOPICS.keys()))
topic = st.sidebar.selectbox("Select Topic", SUBJECT_TOPICS[subject])

# Cache PDF download & Gemini upload so it runs once per server session
@st.cache_resource(show_spinner="Loading permanent textbook resources...")
def load_permanent_textbook(subj_name, download_url):
    if not download_url:
        return None
    
    local_filename = f"temp_{subj_name}.pdf"
    
    # Download from Google Drive if not already local
    response = requests.get(download_url, allow_redirects=True)
    with open(local_filename, "wb") as f:
        f.write(response.content)
    
    # Upload to Gemini session
    file_ref = client.files.upload(file=local_filename)
    
    while file_ref.state.name == "PROCESSING":
        time.sleep(2)
        file_ref = client.files.get(name=file_ref.name)
        
    os.remove(local_filename)
    return file_ref

# Fetch active file reference automatically
file_ref = None
pdf_url = SUBJECT_URLS.get(subject)

if pdf_url:
    try:
        file_ref = load_permanent_textbook(subject, pdf_url)
        st.sidebar.success(f"✅ {subject} Textbook Loaded permanently!")
    except Exception as e:
        st.sidebar.warning(f"⚠️ Could not load textbook: {e}")

st.info("App is configured permanently. No 48-hour re-uploads needed!")
