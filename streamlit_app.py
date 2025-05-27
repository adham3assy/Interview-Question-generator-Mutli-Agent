# streamlit_app.py
import os
import sys
import tempfile
import json
from typing import List, Dict
# Import project modules
from crew.mycrew import run_interview_process
from utils.pdf_exporter import export_to_pdf
from tools.pdf_parser_tool import PDFParserTool
import streamlit as st
from dotenv import load_dotenv

# Setup environment
load_dotenv()
DEFAULT_HF_TOKEN = os.getenv("HF_TOKEN")  # 🔧 Default token from .env

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
sys.path.append(project_root)


def extract_text_from_pdf(file_path):
    tool = PDFParserTool()
    return tool._run(file_path=file_path)


def serialize_questions_for_json(questions: List[Dict]) -> str:
    try:
        clean_questions = []
        for q in questions:
            clean_questions.append({
                "question": str(q.get("question", "")),
                "category": str(q.get("category", "General"))
            } if isinstance(q, dict) else {
                "question": str(q),
                "category": "General"
            })
        return json.dumps({"questions": clean_questions}, indent=2)
    except Exception as e:
        st.error(f"Error serializing questions: {str(e)}")
        return json.dumps({"questions": [], "error": str(e)}, indent=2)


@st.cache_resource(show_spinner="Initializing agents...")
def get_question_generator():
    return run_interview_process


def main():
    st.set_page_config(
        page_title="AI Interview Question Generator",
        page_icon="🎯",
        layout="wide"
    )

    st.title("🎯 Custom Interview Question Generator")
    st.write("Upload a resume and specify a job title to generate tailored technical interview questions.")

    # 🔧 Hugging Face Token Input (Sidebar)
    with st.sidebar:
        st.markdown("### 🔑 Hugging Face Token")
        user_token = st.text_input(
            "Enter your Hugging Face API token",
            type="password",
            help="This is optional. Used only if you run out of the default token quota.",
            placeholder="hf_..."
        )
        effective_token = user_token.strip() or DEFAULT_HF_TOKEN
        if not effective_token:
            st.warning("⚠️ No Hugging Face token provided. App may not work without it.")

    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded_file = st.file_uploader("Upload CV (PDF)", type="pdf")

    with col2:
        job_title = st.text_input("Enter Job Title", placeholder="e.g., Machine Learning Engineer")
        job_description = st.text_area("Optional Job Description", placeholder="Paste job description here...")

    if st.button("Generate Questions", type="primary"):
        if not uploaded_file:
            st.error("Please upload a CV file.")
            return

        if not job_title:
            st.error("Please enter a job title.")
            return

        with st.spinner("Processing CV and generating questions..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name

            try:
                st.info("📄 Extracting text from PDF...")
                cv_text = extract_text_from_pdf(tmp_file_path)
                os.unlink(tmp_file_path)

                if not cv_text or len(cv_text.strip()) < 50:
                    st.error("Could not extract meaningful text from the PDF. Ensure it contains readable text.")
                    return

                st.info("🤖 Generating interview questions...")
                question_generator = get_question_generator()

                # 🔧 Pass the token into the function call (adjust this line if your agent setup takes the token)
                questions = question_generator(cv_text, job_title, job_description, hf_token=effective_token)

                if not questions or not isinstance(questions, list):
                    st.error("Failed to generate questions.")
                    return

                st.success("✅ Interview questions generated successfully!")

                categories = {}
                for q in questions:
                    question_text = q.get("question", str(q)) if isinstance(q, dict) else str(q)
                    category = q.get("category", "General") if isinstance(q, dict) else "General"
                    categories.setdefault(category, []).append(question_text)

                st.subheader("📋 Generated Questions")
                for category, qs in categories.items():
                    with st.expander(f"{category} Questions ({len(qs)} questions)"):
                        for i, question in enumerate(qs, 1):
                            st.markdown(f"**Q{i}.** {question}")

                col1, col2 = st.columns([1, 1])
                with col1:
                    try:
                        pdf_data = export_to_pdf(questions)
                        st.download_button(
                            label="📄 Download as PDF",
                            data=pdf_data,
                            file_name="interview_questions.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"PDF export failed: {str(e)}")

                with col2:
                    try:
                        json_data = serialize_questions_for_json(questions)
                        st.download_button(
                            label="📊 Download as JSON",
                            data=json_data,
                            file_name="interview_questions.json",
                            mime="application/json"
                        )
                    except Exception as e:
                        st.error(f"JSON export failed: {str(e)}")

                with st.expander("🔍 Debug Info"):
                    st.code(str(questions), language="python")
                    st.write(f"Number of questions: {len(questions)}")
                    st.write("Categories:", list(categories.keys()))

            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
                import traceback
                with st.expander("🔍 Error Details"):
                    st.code(traceback.format_exc(), language="python")

    with st.expander("📖 How It Works"):
        st.markdown("""
        ### How This App Works
        1. **Upload Resume**: Upload the candidate's resume as a PDF.
        2. **Specify Job**: Provide a job title (and optionally a job description).
        3. **Generate Questions**: The system uses AI agents to analyze and generate custom interview questions.
        4. **Download**: Export the questions as PDF or JSON.

        ⚠️ PDF must have actual text (not just scanned images).

        Powered by [CrewAI](https://github.com/joaomdmoura/crewAI) and [Hugging Face Transformers](https://huggingface.co).
        """)


if __name__ == "__main__":
    main()
