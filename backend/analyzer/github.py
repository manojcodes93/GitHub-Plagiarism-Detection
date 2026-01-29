import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict
from git import Repo
import hashlib

class GitHubAnalyzer:

    def __init__(self, base_dir: str = None):
        ## Deciding where the repos will be cloned

        self.base_dir = base_dir or tempfile.gettempdir()
        self.cloned_paths = []
    
    def clone_repository(self, repo_url: str, branch: str = "main") -> str:
        ## Cloning the GitHub repository locally

        repo_name = repo_url.split("/")[-1].replace(".git", "")
        repo_hash = hashlib.md5(repo_url.encode()).hexdigest()[:8]
        unique_name = f"{repo_name}_{repo_hash}"

        repo_name = repo_url.split("/")[-1].replace(".git", "")
        repo_hash = hashlib.md5(repo_url.encode()).hexdigest()[:8]
        
        # Always create a fresh temp directory
        local_path = tempfile.mkdtemp(prefix=f"{repo_name}_{repo_hash}_")

        ## Cloning
        try:
            Repo.clone_from(repo_url, local_path, branch=branch, depth=50)
        except Exception:
            Repo.clone_from(repo_url, local_path, branch="master", depth=50)
        
        self.cloned_paths.append(local_path)
        return local_path
    
    def extract_commits(self, repo_path: str, limit: int = 100) -> List[Dict]:
        ## Extracting the commit metadata from repository
        repo = Repo(repo_path)
        commits = []

        for commit in repo.iter_commits(max_count=limit):
            commits.append({
                "hash": commit.hexsha,
                "message": commit.message.strip(),
                "author": commit.author.name,
                "timestamp": commit.committed_datetime.isoformat(),
                "files_changed": len(commit.stats.files),
                "insertions": sum(f["insertions"] for f in commit.stats.files.values()),
                "deletions": sum(f["deletions"] for f in commit.stats.files.values()),
                "files": list(commit.stats.files.keys()),
            })

        return commits
    
    def extract_commit_diff(self, repo_path: str, commit_hash: str, language: str = "python") -> Dict[str, str]:
        ## Extract per-file diffs for a commit, filtered by language.
        ## Returns: {file_path: diff_text}
        repo = Repo(repo_path)
        commit = repo.commit(commit_hash)

        extensions = {
            "python": [".py"],
            "java": [".java"],
            "javascript": [".js"],
            "typescript": [".ts"],
            "csharp": [".cs"],
            "cpp": [".cpp", ".cc", ".cxx", ".c++", ".h"],
        }.get(language, [])

        diffs_by_file = {}

        ## Comparing with parent commit
        if commit.parents:
            diffs = commit.parents[0].diff(commit, create_patch=True)
        else:
            diffs = commit.diff(None, create_patch=True)
            
        for diff in diffs:
            file_path = diff.b_path or diff.a_path
            if not file_path:
                continue

            if extensions and not any(file_path.endswith(ext) for ext in extensions):
                continue
                
            if diff.diff is None:
                # Skip binary files (images, compiled objects, etc.)
                continue

            diff_text = diff.diff.decode(errors="ignore")
            if diff_text.strip():
                diffs_by_file[file_path] = diff_text

        return diffs_by_file
    
    def extract_code_files(self, repo_path: str, language: str = "python") -> Dict[str, str]:
        ## Extracting the source code files of a given language

        extensions = {
            "python": [".py"],
            "java": [".java"],
            "javascript": [".js"],
            "typescript": [".ts"],
            "csharp": [".cs"],
            "cpp": [".cpp", ".cc", ".cxx", ".c++", ".h"],
        }.get(language, [])

        code_files = {}

        for file_path in Path(repo_path).rglob("*"):
            if not file_path.is_file():
                continue

            if file_path.suffix not in extensions:
                continue

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                relative_path = str(file_path.relative_to(repo_path))
                code_files[relative_path] = f.read()

        return code_files
    
    def clean_up(self):
        ## Removing all the cloned repos
        import stat

        def handle_remove_error(func, path, exc_info):
            """Error handler for shutil.rmtree on Windows with locked files."""
            if not os.access(path, os.W_OK):
                os.chmod(path, stat.S_IWUSR | stat.S_IRUSR)
                func(path)
            else:
                raise

        for path in self.cloned_paths:
            if os.path.exists(path):
                shutil.rmtree(path, onerror=handle_remove_error)

        self.cloned_paths = []
