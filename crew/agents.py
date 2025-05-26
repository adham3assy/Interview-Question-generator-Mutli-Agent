# crew/agents.py
from crewai import Agent
from models.huggingface_llm import HuggingFaceLLM
from tools.job_profile_tool import JobProfileTool
from tools.pdf_parser_tool import PDFParserTool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
hf_token = os.getenv("HF_TOKEN")

# Initialize the custom LLM
myllm = HuggingFaceLLM(
    model_name="mistralai/Mistral-7B-Instruct-v0.3",
    api_token=hf_token,
    max_new_tokens=1024,
    temperature=0.5
)

# Initialize tools
pdf_parser_tool = PDFParserTool()
job_profile_tool = JobProfileTool()

# Define agents
cv_agent = Agent(
    role="CV Analyzer",
    goal="Deeply analyze the candidate's resume and extract structured data including skills, projects, internships, courses, education, and work experience.",
    backstory="An AI assistant specializing in parsing technical resumes.",
    tools=[pdf_parser_tool],
    llm=myllm,
    allow_delegation=False,
    verbose=True
)

role_agent = Agent(
    role="Job Role Profiler",
    goal="Analyze a job title and description to extract a comprehensive technical profile expected from the candidate.",
    backstory="A job market analyst who understands job trends and technical prerequisites for various roles.",
    tools=[job_profile_tool],
    llm=myllm,
    allow_delegation=False,
    verbose=True
)

question_agent = Agent(
    role="Technical Interview Question Creator",
    goal="Generate challenging, relevant, and contextualized technical questions tailored to the candidate's resume and the target job role.",
    backstory="A senior technical interviewer who tailors questions to the job and candidate.",
    llm=myllm,
    allow_delegation=False,
    verbose=True
)