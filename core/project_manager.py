import os
from typing import Dict

class ProjectManager:
    def __init__(self, directory: str):
        self.directory = directory
        
    def get_all_context(self) -> Dict:
        """
        Gather all text files in the project. If there is no Git repo,
        read all readable files as 'added/modified'.
        """
        files_content = {}
        for root, _, files in os.walk(self.directory):
            # extremely simple skip logic for binary/hidden folders
            if '.git' in root or '__pycache__' in root:
                continue
                
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.directory)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files_content[rel_path] = f.read()
                except UnicodeDecodeError:
                    pass # skip binaries
        
        return {
            "diff": "ZIP Upload - No Git Diff Available",
            "modified_files": list(files_content.keys()),
            "file_contexts": files_content
        }
