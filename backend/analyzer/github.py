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
        import stat
        
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        repo_hash = hashlib.md5(repo_url.encode()).hexdigest()[:8]

        # Use mkdtemp directly with a unique prefix; this ensures isolation
        # Windows-safe: use full temp directory as clone target
        local_path = tempfile.mkdtemp(prefix=f"plagiarism_{repo_name}_{repo_hash}_")

        # Robust cleanup of any stale content (Windows file lock handling)
        def force_remove_tree(path):
            """Remove tree with Windows file lock handling."""
            if not os.path.exists(path):
                return
            for root, dirs, files in os.walk(path, topdown=False):
                for name in files:
                    try:
                        file_path = os.path.join(root, name)
                        os.chmod(file_path, stat.S_IWUSR | stat.S_IRUSR)
                        os.remove(file_path)
                    except Exception:
                        pass
                for name in dirs:
                    try:
                        dir_path = os.path.join(root, name)
                        os.chmod(dir_path, stat.S_IWUSR | stat.S_IRUSR)
                        os.rmdir(dir_path)
                    except Exception:
                        pass
            try:
                os.rmdir(path)
            except Exception:
                pass

        # Attempt to clean the directory if it has remnants
        try:
            if os.path.exists(local_path) and os.listdir(local_path):
                force_remove_tree(local_path)
                # Recreate empty directory
                os.makedirs(local_path, exist_ok=True)
        except Exception as e:
            # If cleanup fails, use a new unique path
            import uuid
            local_path = os.path.join(tempfile.gettempdir(), f"plagiarism_repo_{uuid.uuid4().hex[:8]}")
            os.makedirs(local_path, exist_ok=True)

        try:
            Repo.clone_from(repo_url, local_path, branch=branch, depth=50)
        except Exception as e:
            # Fallback for repos using 'master'
            try:
                Repo.clone_from(repo_url, local_path, branch="master", depth=50)
            except Exception as fallback_error:
                # Clean up on full failure
                try:
                    force_remove_tree(local_path)
                except Exception:
                    pass
                raise fallback_error

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
    
    def delete_repo(self, path: str):
        import shutil, stat, os
        
        def onerror(func, p, exc):
            os.chmod(p, stat.S_IWUSR)
            func(p)
            
        if os.path.exists(path):
            shutil.rmtree(path, onerror=onerror)
    
    def clean_up(self):
        ## Removing all the cloned repos with robust Windows handling
        import stat

        def force_remove_tree(path):
            """Remove tree with Windows file lock handling."""
            if not os.path.exists(path):
                return
            for root, dirs, files in os.walk(path, topdown=False):
                for name in files:
                    try:
                        file_path = os.path.join(root, name)
                        os.chmod(file_path, stat.S_IWUSR | stat.S_IRUSR)
                        os.remove(file_path)
                    except Exception:
                        pass
                for name in dirs:
                    try:
                        dir_path = os.path.join(root, name)
                        os.chmod(dir_path, stat.S_IWUSR | stat.S_IRUSR)
                        os.rmdir(dir_path)
                    except Exception:
                        pass
            try:
                os.rmdir(path)
            except Exception:
                pass

        for path in self.cloned_paths:
            if os.path.exists(path):
                try:
                    force_remove_tree(path)
                except Exception as e:
                    # Log but don't fail on cleanup errors
                    import logging
                    logging.warning(f"Failed to clean up {path}: {e}")

        self.cloned_paths = []
