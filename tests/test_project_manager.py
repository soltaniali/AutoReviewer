import os
import tempfile
import zipfile
import pytest
from core.project_manager import ProjectManager

def test_project_manager_all_context():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some files
        f1 = os.path.join(temp_dir, "main.py")
        f2 = os.path.join(temp_dir, "utils.py")
        bin_f = os.path.join(temp_dir, "data.bin")
        
        with open(f1, "w", encoding="utf-8") as f:
            f.write("def main(): pass")
        with open(f2, "w", encoding="utf-8") as f:
            f.write("def helper(): return True")
        with open(bin_f, "wb") as f:
            f.write(b'\x80\x81\x82') # binary garbage
            
        pm = ProjectManager(temp_dir)
        ctx = pm.get_all_context()
        
        assert "main.py" in ctx["modified_files"]
        assert "utils.py" in ctx["modified_files"]
        assert "data.bin" not in ctx["modified_files"] # should skip bins
        
        assert ctx["diff"] == "ZIP Upload - No Git Diff Available"
        assert ctx["file_contexts"]["main.py"] == "def main(): pass"
