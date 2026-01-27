import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict
from git import Repo

class GitHubAnalyzer:

    def __init__(self, base_dir: str = None):
        ## Deciding where the repos will be cloned

        self.base_dir = base_dir or tempfile.gettempdir()
        self.cloned_paths = []
    
    def clone_repository(self, repo_url: str, branch: str = "main") -> str:
        ## Cloning the GitHub repository locally

        repo_name = repo_url.split("/")[-1].replace(".git", "")
        unique_name = f"{repo_name}_{abs(hash(repo_url)) % 10000}"
        local_path = os.path.join(self.base_dir, unique_name)

        if os.path.exists(local_path):
            shutil.rmtree(local_path)

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
                "hash": commit.hexsha[:8],
                "message": commit.message.strip(),
                "author": commit.author.name,
                "timestamp": commit.committed_datetime.isoformat(),
                "files_changed": len(commit.stats.files),
                "insertions": sum(f["insertions"] for f in commit.stats.files.values()),
                "deletions": sum(f["deletions"] for f in commit.stats.files.values()),
            })

        return commits
    
    def extract_commit_diff(self, repo_path: str, commit_hash: str) -> str:
        ## Extracting the unified diff for a commit
        repo = Repo(repo_path)
        commit = repo.commit(commit_hash)

        ## Comparing with parent commit
        if commit.parents:
            diffs = commit.parents[0].diff(commit)
        else:
            diffs = commit.tree.diff(None)
            
        diff_text = ""
        
        for diff in diffs:
            if diff.a_path:
                diff_text += f"--- {diff.a_path}\n"
            if diff.b_path:
                diff_text += f"+++ {diff.b_path}\n"
                
            if isinstance(diff.diff, bytes):
                diff_text += diff.diff.decode(errors="ignore")
            else:
                diff_text += diff.diff

        return diff_text
    
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
