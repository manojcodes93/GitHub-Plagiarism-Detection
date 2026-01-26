"""
GitHub repository cloning and commit extraction module.
Handles cloning repos and extracting commit history with diffs.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from git import Repo
from git.exc import InvalidGitRepositoryError, GitCommandError
import logging

logger = logging.getLogger(__name__)


class GitHubAnalyzer:
    """
    Clones GitHub repositories and extracts commit information.
    Uses GitPython for efficient git operations.
    """
    
    def __init__(self, temp_dir: str = None):
        """
        Initialize GitHub analyzer.
        
        Args:
            temp_dir: Custom temp directory for clones. If None, uses system temp.
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.cloned_repos = {}
    
    def clone_repository(self, repo_url: str, branch: str = "main") -> str:
        """
        Clone a GitHub repository to a temporary directory.
        
        Args:
            repo_url: GitHub repository URL
            branch: Branch name to clone (default: main)
            
        Returns:
            Local path to cloned repository
            
        Raises:
            GitCommandError: If cloning fails
        """
        try:
            # Create unique directory for this repo
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            local_path = os.path.join(self.temp_dir, f"repo_{hash(repo_url) % 10000}")
            
            # Remove if exists
            if os.path.exists(local_path):
                shutil.rmtree(local_path)
            
            logger.info(f"Cloning {repo_url} to {local_path}...")
            
            # Try to clone with specified branch
            try:
                repo = Repo.clone_from(
                    repo_url, 
                    local_path, 
                    branch=branch,
                    multi_options=["--depth=50"]  # Limit history for performance
                )
            except GitCommandError as branch_error:
                # If specified branch doesn't exist, try 'master'
                if "not found in upstream" in str(branch_error) and branch != "master":
                    logger.warning(f"Branch '{branch}' not found, trying 'master'...")
                    repo = Repo.clone_from(
                        repo_url, 
                        local_path, 
                        branch="master",
                        multi_options=["--depth=50"]
                    )
                else:
                    raise
            
            self.cloned_repos[repo_url] = local_path
            logger.info(f"Successfully cloned {repo_url}")
            
            return local_path
            
        except GitCommandError as e:
            logger.error(f"Failed to clone {repo_url}: {str(e)}")
            raise
    
    def get_commits(self, repo_path: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Extract commit history from a repository.
        
        Args:
            repo_path: Path to local repository
            limit: Maximum number of commits to extract
            
        Returns:
            List of commit dictionaries with metadata
        """
        try:
            repo = Repo(repo_path)
            commits = []
            
            for i, commit in enumerate(repo.iter_commits()):
                if i >= limit:
                    break
                
                commits.append({
                    "hash": commit.hexsha[:8],
                    "message": commit.message.strip(),
                    "author": commit.author.name,
                    "timestamp": commit.committed_datetime.isoformat(),
                    "files_changed": len(commit.stats.files),
                    "insertions": sum(stat["insertions"] for stat in commit.stats.files.values()),
                    "deletions": sum(stat["deletions"] for stat in commit.stats.files.values()),
                })
            
            logger.info(f"Extracted {len(commits)} commits from {repo_path}")
            return commits
            
        except InvalidGitRepositoryError:
            logger.error(f"Invalid git repository: {repo_path}")
            return []
    
    def get_commit_diff(self, repo_path: str, commit_hash: str) -> str:
        """
        Get the diff for a specific commit.
        
        Args:
            repo_path: Path to local repository
            commit_hash: Commit hash or ref
            
        Returns:
            Unified diff string
        """
        try:
            repo = Repo(repo_path)
            commit = repo.commit(commit_hash)
            
            # Get diff against parent
            if commit.parents:
                diff = commit.parents[0].diff(commit)
            else:
                # Initial commit
                diff = commit.tree.diff(None)
            
            diff_str = ""
            for item in diff:
                if item.a_path:
                    diff_str += f"--- {item.a_path}\n"
                if item.b_path:
                    diff_str += f"+++ {item.b_path}\n"
                diff_str += item.diff.decode(errors="ignore") if isinstance(item.diff, bytes) else item.diff
            
            return diff_str
            
        except Exception as e:
            logger.error(f"Failed to get diff for {commit_hash}: {str(e)}")
            return ""
    
    def extract_files_by_language(
        self, 
        repo_path: str, 
        language: str = "python"
    ) -> Dict[str, str]:
        """
        Extract all source files of a specific language from repository.
        
        Args:
            repo_path: Path to local repository
            language: Programming language (python, java, js, etc.)
            
        Returns:
            Dictionary mapping file paths to file contents
        """
        language_extensions = {
            "python": [".py"],
            "java": [".java"],
            "javascript": [".js"],
            "typescript": [".ts", ".tsx"],
            "csharp": [".cs"],
            "cpp": [".cpp", ".h", ".cc"],
            "c": [".c", ".h"],
            "go": [".go"],
            "rust": [".rs"],
        }
        
        extensions = language_extensions.get(language.lower(), [])
        files = {}
        
        try:
            for file_path in Path(repo_path).rglob("*"):
                # Skip hidden and special directories
                if any(part.startswith(".") for part in file_path.parts):
                    continue
                
                # Check if file has target extension
                if file_path.is_file() and file_path.suffix in extensions:
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            # Store relative path as key
                            rel_path = str(file_path.relative_to(repo_path))
                            files[rel_path] = content
                    except Exception as e:
                        logger.warning(f"Failed to read {file_path}: {str(e)}")
            
            logger.info(f"Extracted {len(files)} {language} files from {repo_path}")
            return files
            
        except Exception as e:
            logger.error(f"Failed to extract files: {str(e)}")
            return {}
    
    def cleanup(self):
        """Clean up temporary directories."""
        for repo_path in self.cloned_repos.values():
            try:
                if os.path.exists(repo_path):
                    shutil.rmtree(repo_path)
                    logger.info(f"Cleaned up {repo_path}")
            except Exception as e:
                logger.error(f"Failed to cleanup {repo_path}: {str(e)}")
