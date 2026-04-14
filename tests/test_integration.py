import pytest
from agents.graph import create_review_graph
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from worker import celery_app
import io
import zipfile
import os
import subprocess
import tempfile
import time

from api import app as fastapi_app

load_dotenv()

def create_dummy_zip_repo():
    """Creates a dummy git repository in a temporary directory, adds a commit,
    makes a change, and zips it up. Returns the zip content as bytes."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=temp_dir, check=True)
        
        # Create a file and commit it
        file_path = os.path.join(temp_dir, "test_file.py")
        with open(file_path, "w") as f:
            f.write("def hello_world():\n    print('Hello, world!')\n")
        
        subprocess.run(["git", "add", "."], cwd=temp_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_dir, check=True)
        
        # Modify the file to create a diff
        with open(file_path, "a") as f:
            f.write("\n# A buggy comment\n")
            
        # Create a zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path_in_zip = os.path.relpath(os.path.join(root, file), temp_dir)
                    zipf.write(os.path.join(root, file), file_path_in_zip)
        
        zip_buffer.seek(0)
        return zip_buffer.read()

def test_full_graph_integration():
    """Run actual code review agent graph utilizing given LLM API key."""
    app = create_review_graph()
    fake_diff = "def buggy_code():\n    print 'missing parens'"
    
    initial_state = {
        "diff": fake_diff,
        "repo_path": None,
        "modified_files": [],
        "file_contexts": {},
    }
    
    # Run the graph
    result = app.invoke(initial_state)
    
    assert result["diff"] == fake_diff
    assert len(result.get("required_checks", [])) > 0
    
    # Check if synthesizer output is present
    assert "final_review" in result
    assert len(result["final_review"]) > 0
    print("\n\n--- REAL LLM OUTPUT FROM METIS API ---\n")
    print(result["final_review"])
    print("\n---------------------------------------\n")

def test_full_api_review_flow():
    """
    Tests the full API flow:
    Instead of simulating Celery with eager mode (which is complex without Redis),
    we directly execute the celery task function (which runs the graph) to verify
    the end-to-end processing of a zip file.
    """
    # Import the actual task function
    from worker import run_review_agent
    
    zip_content = create_dummy_zip_repo()
    
    # Execute the worker function directly
    result = run_review_agent(zip_content)
    
    # Verify the final result
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 10 # Check for a meaningful report

    print("\n\n--- REAL LLM OUTPUT FROM WORKER ---\n")
    print(result)
    print("\n---------------------------------------\n")
