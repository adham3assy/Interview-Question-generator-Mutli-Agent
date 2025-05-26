# ui/streamlit_app.py - Fixed to handle CrewOutput properly
import sys
import os
import streamlit as st
import tempfile
import json
from typing import List, Dict

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# Import project modules
from crew.mycrew import run_interview_process
from utils.pdf_exporter import export_to_pdf
from tools.pdf_parser_tool import PDFParserTool

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file using our custom tool."""
    tool = PDFParserTool()
    return tool._run(file_path=file_path)

def serialize_questions_for_json(questions: List[Dict]) -> str:
    """
    Safely serialize questions to JSON, handling any non-serializable objects.
    """
    try:
        # Create a clean version of questions with only serializable data
        clean_questions = []
        for q in questions:
            if isinstance(q, dict):
                clean_q = {
                    "question": str(q.get("question", "")),
                    "category": str(q.get("category", "General"))
                }
                clean_questions.append(clean_q)
            else:
                # Handle unexpected question format
                clean_questions.append({
                    "question": str(q),
                    "category": "General"
                })
        
        return json.dumps({"questions": clean_questions}, indent=2)
    except Exception as e:
        st.error(f"Error serializing questions: {str(e)}")
        return json.dumps({"questions": [], "error": str(e)}, indent=2)

def main():
    """Main Streamlit application."""
        
    st.set_page_config(
        page_title="AI Interview Question Generator",
        page_icon="🎯",
        layout="wide"
    )


    st.title("🎯 Custom Interview Question Generator Multi-Agent")
    st.write("Upload a resume and specify a job title to generate tailored technical interview questions.")
    
    # Layout for input form
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Upload CV (PDF)", type="pdf")
        
    with col2:
        job_title = st.text_input("Enter Job Title", placeholder="e.g., Machine Learning Engineer")
        job_description = st.text_area("Optional Job Description", placeholder="Paste job description here...")
    
    # Process button
    if st.button("Generate Questions", type="primary"):
        if not uploaded_file:
            st.error("Please upload a CV file.")
            return
            
        if not job_title:
            st.error("Please enter a job title.")
            return
        
        # Show processing message
        with st.spinner("Processing CV and generating questions... This may take a few minutes."):
            # Save uploaded file to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            try:
                # Extract text from PDF
                st.info("📄 Extracting text from PDF...")
                cv_text = extract_text_from_pdf(tmp_file_path)
                
                # Clean up temporary file
                os.unlink(tmp_file_path)
                
                if not cv_text or len(cv_text.strip()) < 50:
                    st.error("Could not extract meaningful text from the PDF. Please ensure the PDF contains readable text.")
                    return
                
                st.info("🤖 Running AI agents to analyze CV and generate questions...")
                
                # Run the crew to generate questions
                questions = run_interview_process(cv_text, job_title, job_description)
                
                # Validate questions format
                if not questions or not isinstance(questions, list):
                    st.error("Failed to generate questions in the expected format.")
                    return
                
                # Display results
                st.success("✅ Successfully generated interview questions!")
                
                # Group questions by category for display
                categories = {}
                for q in questions:
                    # Handle different question formats
                    if isinstance(q, dict):
                        question_text = q.get("question", str(q))
                        category = q.get("category", "General")
                    else:
                        question_text = str(q)
                        category = "General"
                    
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(question_text)
                
                # Display questions grouped by category
                st.subheader("📋 Generated Interview Questions")
                for category, qs in categories.items():
                    with st.expander(f"{category} Questions ({len(qs)} questions)"):
                        for i, question in enumerate(qs, 1):
                            st.markdown(f"**Q{i}.** {question}")
                
                # Export options
                col1, col2 = st.columns([1, 1])
                with col1:
                    # Create PDF and provide download button
                    try:
                        pdf_data = export_to_pdf(questions)
                        st.download_button(
                            label="📄 Download as PDF",
                            data=pdf_data,
                            file_name="interview_questions.pdf",
                            mime="application/pdf"
                        )
                    except Exception as pdf_error:
                        st.error(f"Error creating PDF: {str(pdf_error)}")
                
                with col2:
                    # Provide JSON download with safe serialization
                    try:
                        json_data = serialize_questions_for_json(questions)
                        st.download_button(
                            label="📊 Download as JSON",
                            data=json_data,
                            file_name="interview_questions.json",
                            mime="application/json"
                        )
                    except Exception as json_error:
                        st.error(f"Error creating JSON: {str(json_error)}")
                
                # Debug information (expandable)
                with st.expander("🔍 Debug Information"):
                    st.write("**Questions data structure:**")
                    st.code(str(questions), language="python")
                    st.write("**Number of questions generated:**", len(questions))
                    st.write("**Categories found:**", list(categories.keys()))
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                # Show more detailed error information
                with st.expander("🔍 Error Details"):
                    st.code(str(e), language="python")
                    import traceback
                    st.code(traceback.format_exc(), language="python")
    
    # Documentation section
    with st.expander("📖 How It Works"):
        st.markdown("""
        ### How This App Works
        
        1. **Upload Resume**: First, upload the candidate's resume in PDF format.
        2. **Specify Job**: Enter the job title and optionally paste the full job description.
        3. **Generate Questions**: Our AI analyzes both documents to create tailored interview questions.
        4. **Review & Export**: Review the generated questions and download them as PDF or JSON.
        
        The system uses a multi-agent approach powered by CrewAI and Hugging Face models to:
        - Parse and analyze the resume structure and content
        - Extract key requirements from the job specification
        - Generate relevant technical questions matching the candidate's background to the job
        
        ### Troubleshooting
        - **PDF Issues**: Ensure your PDF contains readable text (not just images)
        - **Generation Errors**: Try with a shorter job description or simpler job title
        - **Download Issues**: If exports fail, try refreshing the page and generating again
        """)

if __name__ == "__main__":
    main()