import os
import sys
import tempfile
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DEFAULT_HF_TOKEN = os.getenv("HF_TOKEN")

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(project_root)

# Tools — import safely
from tools.pdf_parser_tool import PDFParserTool
from utils.pdf_exporter import export_to_pdf

# Lazy-import heavy logic
@st.cache_resource(show_spinner="Setting up agents...")
def get_interview_runner():
    from crew.mycrew import run_interview_process
    return run_interview_process

# Extract text from uploaded PDF
def extract_text_from_pdf(file_path):
    parser = PDFParserTool()
    return parser._run(file_path=file_path)

# Page setup
st.set_page_config(page_title="Interview Generator", layout="wide")
st.title("🎯 Custom Interview Question Generator")

# Sidebar: optional Hugging Face token
with st.sidebar:
    st.markdown("### 🔑 Hugging Face Token (optional)")
    user_token = st.text_input("Enter your token", type="password", placeholder="hf_...")
    effective_token = user_token.strip() or DEFAULT_HF_TOKEN
    if not effective_token:
        st.warning("⚠️ No Hugging Face token set. Please add one to use the app.")

# Upload + inputs
col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("📄 Upload CV (PDF)", type="pdf")
with col2:
    job_title = st.text_input("🧑‍💻 Job Title", placeholder="e.g., AI Engineer")
    job_description = st.text_area("📋 Job Description (optional)")

# Generate Button
if st.button("🚀 Generate Interview Questions"):
    if not uploaded_file or not job_title:
        st.error("❗ Please upload a CV and enter a job title.")
        st.stop()

    with st.spinner("Reading and processing CV..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getvalue())
            pdf_path = tmp.name

        try:
            cv_text = extract_text_from_pdf(pdf_path)
            os.remove(pdf_path)
        except Exception as e:
            st.error(f"❌ Failed to extract text: {str(e)}")
            st.stop()

    if len(cv_text.strip()) < 50:
        st.error("❌ CV text is too short or empty.")
        st.stop()

    with st.spinner("Generating questions..."):
        try:
            runner = get_interview_runner()
            questions = runner(cv_text, job_title, job_description, hf_token=effective_token)
        except Exception as e:
            st.error(f"❌ Agent failed: {str(e)}")
            st.stop()

    if not questions or not isinstance(questions, list):
        st.error("⚠️ No questions generated.")
        st.stop()

    st.success("✅ Questions generated!")
    st.subheader("📋 Interview Questions")

    for i, q in enumerate(questions, 1):
        if isinstance(q, dict):
            st.markdown(f"**Q{i}.** {q.get('question', 'Unknown')} ({q.get('category', 'General')})")
        else:
            st.markdown(f"**Q{i}.** {q}")

    # Download buttons
    try:
        pdf_data = export_to_pdf(questions)
        st.download_button("📄 Download as PDF", data=pdf_data, file_name="interview_questions.pdf", mime="application/pdf")
    except Exception as e:
        st.error(f"Failed to generate PDF: {str(e)}")

    try:
        import json
        json_data = json.dumps({"questions": questions}, indent=2)
        st.download_button("📊 Download as JSON", data=json_data, file_name="interview_questions.json", mime="application/json")
    except Exception as e:
        st.error(f"Failed to generate JSON: {str(e)}")

# Info section
with st.expander("ℹ️ How this works"):
    st.markdown("""
    This app analyzes a candidate's CV and generates interview questions tailored to the job title and description using AI agents powered by Hugging Face LLMs.

    **Steps:**
    1. Upload a resume
    2. Enter the job title (and optionally job description)
    3. Click "Generate"
    4. Download as PDF or JSON

    If the default token is out of quota, enter your own Hugging Face token in the sidebar.
    """)
