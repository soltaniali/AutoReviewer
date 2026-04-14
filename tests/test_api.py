import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import io

# This is a bit of a workaround to make the app importable.
# In a larger app, you might have a more structured package.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api import app, celery_app

@pytest.fixture
def client():
    """Create a FastAPI test client."""
    return TestClient(app)

def test_submit_review_success(client):
    """
    Test successful submission of a .zip file to the /review endpoint.
    """
    # Create a dummy zip file in memory
    zip_bytes = io.BytesIO()
    # In a real scenario, you'd use zipfile to create a proper zip archive.
    # For this unit test, just sending bytes is sufficient to test the endpoint logic.
    zip_bytes.write(b"dummy zip content")
    zip_bytes.seek(0)

    # Mock the celery task sending
    with patch('api.celery_app.send_task') as mock_send_task:
        mock_send_task.return_value = MagicMock(id="test-task-id")
        
        response = client.post(
            "/review",
            files={"file": ("test.zip", zip_bytes, "application/zip")}
        )
        
        assert response.status_code == 202
        assert response.json() == {"task_id": "test-task-id"}
        mock_send_task.assert_called_once_with("worker.run_review_agent", args=[b"dummy zip content"])

def test_submit_review_invalid_file_type(client):
    """
    Test that uploading a non-zip file returns a 400 error.
    """
    txt_bytes = io.BytesIO(b"this is not a zip file")
    
    response = client.post(
        "/review",
        files={"file": ("test.txt", txt_bytes, "text/plain")}
    )
    
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]

def test_get_review_result_pending(client):
    """
    Test retrieving the result for a task that is still pending.
    """
    with patch('api.AsyncResult') as mock_async_result:
        mock_instance = mock_async_result.return_value
        mock_instance.ready.return_value = False
        mock_instance.state = "PENDING"
        
        response = client.get("/results/pending-task-id")
        
        assert response.status_code == 200
        assert response.json() == {"status": "PENDING", "result": None}

def test_get_review_result_success(client):
    """
    Test retrieving the result for a successfully completed task.
    """
    with patch('api.AsyncResult') as mock_async_result:
        mock_instance = mock_async_result.return_value
        mock_instance.ready.return_value = True
        mock_instance.failed.return_value = False
        mock_instance.state = "SUCCESS"
        mock_instance.get.return_value = "This is the final review report."
        
        response = client.get("/results/success-task-id")
        
        assert response.status_code == 200
        assert response.json() == {
            "status": "SUCCESS",
            "result": "This is the final review report."
        }

def test_get_review_result_failed(client):
    """
    Test retrieving the result for a failed task.
    """
    with patch('api.AsyncResult') as mock_async_result:
        mock_instance = mock_async_result.return_value
        mock_instance.ready.return_value = True
        mock_instance.failed.return_value = True
        mock_instance.info = "Something went wrong"
        
        response = client.get("/results/failed-task-id")
        
        assert response.status_code == 500
        assert response.json() == {"detail": "Something went wrong"}
