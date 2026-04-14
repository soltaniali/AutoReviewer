import os
import shutil
import tempfile
import zipfile
import pytest
from core.workspace import WorkspaceManager

def test_extract_zip_workspace():
    # Setup: Create a dummy zip file
    with tempfile.TemporaryDirectory() as temp_dir:
        dummy_dir = os.path.join(temp_dir, "dummy_project")
        os.makedirs(dummy_dir)
        test_file = os.path.join(dummy_dir, "app.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("print('hello world')")
            
        zip_path = os.path.join(temp_dir, "dummy.zip")
        # Create a zip of the dummy directory
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.write(test_file, arcname="dummy_project/app.py")
            
        # Test the WorkspaceManager
        wm = WorkspaceManager()
        extracted_path = wm.load_from_zip(zip_path)
        
        assert os.path.exists(extracted_path)
        assert os.path.exists(os.path.join(extracted_path, "dummy_project", "app.py"))
        
        # Cleanup
        wm.cleanup()
        assert not os.path.exists(extracted_path)
