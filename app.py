"""
Main entry point for the AI Interview Question Generator application.
This runs the Streamlit UI and sets up the environment.
"""
import os
import sys
from dotenv import load_dotenv

# Ensure the project root is in the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

def main():
    
    load_dotenv()
    
    # Check if required environment variables are set
    if not os.getenv("HF_TOKEN"):
        print("ERROR: HF_TOKEN environment variable not set in .env file")
        print("Please create a .env file with your Hugging Face API token")
        print("Example: HF_TOKEN=your_token_here")
        sys.exit(1)
    
    # Import here to ensure environment is set up before importing app modules
    from ui.streamlit_app import main as run_streamlit_app
    
    
    run_streamlit_app()

if __name__ == "__main__":
    # Run the app directly when this script is executed
    #import streamlit.web.cli as stcli
    
    # Prepare Streamlit args
    sys.argv = ["streamlit", "run", 
                os.path.join(project_root, "ui", "streamlit_app.py"),
                "--server.port=8501", 
                "--server.address=localhost"]
    
    # Run the Streamlit CLI
    sys.exit(stcli.main())
