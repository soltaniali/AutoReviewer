import os
import git

class GitManager:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = git.Repo(self.repo_path)
        
    def get_diff(self) -> str:
        """
        Extract the combined uncommitted (staged and unstaged) git diff.
        """
        diff_unstaged = self.repo.git.diff()
        diff_staged = self.repo.git.diff('--cached')
        
        combined_diff = ""
        if diff_staged:
            combined_diff += diff_staged + "\n"
        if diff_unstaged:
            combined_diff += diff_unstaged
            
        return combined_diff.strip()
        
    def get_modified_files(self) -> list[str]:
        """
        Get a list of file paths that have been modified (staged or unstaged).
        """
        diff = self.repo.git.diff('--name-only')
        diff_cached = self.repo.git.diff('--cached', '--name-only')
        
        files = set(diff.splitlines() + diff_cached.splitlines())
        return [f for f in files if f.strip()]
        
    def get_file_content(self, file_path: str) -> str:
        """
        Read the entire raw content of a file from the local disk.
        """
        full_path = os.path.join(self.repo_path, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {file_path}: {e}"
            
    def get_all_context(self) -> dict:
        """
        Orchestrator function returning the diff and the full contents of any modified files.
        """
        diff = self.get_diff()
        modified_files = self.get_modified_files()
        
        file_contexts = {}
        for f in modified_files:
            file_contexts[f] = self.get_file_content(f)
            
        return {
            "diff": diff,
            "modified_files": modified_files,
            "file_contexts": file_contexts
        }
