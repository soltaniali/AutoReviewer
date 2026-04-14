import os
import shutil
import tempfile
import zipfile

class WorkspaceManager:
    """
    Manages temporary workspaces initialized from compressed archives (ZIP) or uploaded files
    specifically for Chainlit / UI applications.
    """
    def __init__(self):
        self.workspace_dir = None

    def load_from_zip(self, zip_path: str) -> str:
        """
        Extracts a provided zip file to a temporary directory and returns the path.
        """
        self.workspace_dir = tempfile.mkdtemp(prefix="agent_review_")
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(self.workspace_dir)
            
        return self.workspace_dir

    def cleanup(self):
        """
        Removes the temporary directory and all its contents.
        """
        if self.workspace_dir and os.path.exists(self.workspace_dir):
            shutil.rmtree(self.workspace_dir)
            self.workspace_dir = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
