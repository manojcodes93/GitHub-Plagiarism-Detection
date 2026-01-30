"""GitHub repository analyzer and cloner."""

import os
import stat
import shutil
import logging
import tempfile
from pathlib import Path
from git import Repo
from git.exc import GitCommandError

logger = logging.getLogger(__name__)


class GitHubAnalyzer:
    """Clone GitHub repositories and extract code/commit information."""

    SUPPORTED_LANGUAGES = {
        'python': ['.py'],
        'javascript': ['.js', '.ts', '.jsx', '.tsx'],
        'java': ['.java'],
        'cpp': ['.cpp', '.cc', '.cxx', '.h', '.hpp'],
        'c': ['.c', '.h'],
        'go': ['.go'],
        'rust': ['.rs']
    }

    def __init__(self):
        self.temp_base = Path(tempfile.gettempdir()) / 'plagiarism_detection'
        self.temp_base.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized GitHubAnalyzer with temp dir: {self.temp_base}")

    def _handle_remove_readonly(self, func, path, exc):
        """Handle permission errors during file removal."""
        if not os.access(path, os.W_OK):
            os.chmod(path, stat.S_IWUSR | stat.S_IREAD)
            func(path)
        else:
            raise

    def _safe_cleanup(self, path):
        """Safely remove directory on all platforms including Windows."""
        if not Path(path).exists():
            return

        try:
            # Windows: make all files writable before deletion
            for item in Path(path).rglob('*'):
                try:
                    if item.is_file():
                        item.chmod(stat.S_IWUSR | stat.S_IREAD)
                except Exception:
                    pass
            
            # Remove directory
            shutil.rmtree(path, ignore_errors=False)
            logger.info(f"Cleaned up: {path}")
        except Exception as e:
            logger.warning(f"Cleanup failed for {path}: {e}, retrying with ignore_errors")
            try:
                shutil.rmtree(path, ignore_errors=True)
            except Exception as e2:
                logger.error(f"Final cleanup failed: {e2}")

    def clone_repository(self, repo_url, branch='main'):
        """
        Clone a repository and return local path.
        
        Args:
            repo_url: GitHub repository URL
            branch: Branch to clone (default: main)
            
        Returns:
            Path to cloned repository
            
        Raises:
            RuntimeError: If clone fails
        """
        # Generate unique temp directory
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        unique_id = os.urandom(8).hex()
        local_path = self.temp_base / f"{repo_name}_{unique_id}"

        # Ensure path doesn't exist
        if local_path.exists():
            self._safe_cleanup(str(local_path))

        try:
            logger.info(f"Cloning {repo_url} to {local_path}")
            
            # Try with specified branch first
            try:
                Repo.clone_from(
                    repo_url,
                    str(local_path),
                    branch=branch,
                    depth=50,
                    timeout=120
                )
                logger.info(f"Successfully cloned {repo_url} (branch: {branch})")
                return str(local_path)
            except GitCommandError as e:
                # If branch doesn't exist, try master
                if 'not found in upstream' in str(e).lower() or 'unknown revision' in str(e).lower():
                    logger.info(f"Branch {branch} not found, trying master")
                    if local_path.exists():
                        self._safe_cleanup(str(local_path))
                    
                    Repo.clone_from(
                        repo_url,
                        str(local_path),
                        branch='master',
                        depth=50,
                        timeout=120
                    )
                    logger.info(f"Successfully cloned {repo_url} (branch: master)")
                    return str(local_path)
                else:
                    raise

        except Exception as e:
            logger.error(f"Clone failed for {repo_url}: {str(e)}")
            if local_path.exists():
                self._safe_cleanup(str(local_path))
            raise RuntimeError(f"Failed to clone {repo_url}: {str(e)}")

    def extract_commits(self, repo_path, limit=50):
        """
        Extract commit history from repository.
        
        Args:
            repo_path: Path to cloned repository
            limit: Maximum commits to extract
            
        Returns:
            List of commit info dicts
        """
        try:
            repo = Repo(repo_path)
            commits = []

            for i, commit in enumerate(repo.iter_commits()):
                if i >= limit:
                    break

                try:
                    commits.append({
                        'hash': commit.hexsha,
                        'author': commit.author.name,
                        'message': commit.message,
                        'diff': commit.diff(commit.parents[0] if commit.parents else 'HEAD^').raw_string if commit.parents else ''
                    })
                except Exception as e:
                    logger.warning(f"Failed to extract commit {i}: {e}")
                    continue

            logger.info(f"Extracted {len(commits)} commits from {repo_path}")
            return commits

        except Exception as e:
            logger.error(f"Failed to extract commits: {e}")
            return []

    def extract_source_files(self, repo_path, language='python'):
        """
        Extract source files from repository.
        
        Args:
            repo_path: Path to cloned repository
            language: Programming language filter
            
        Returns:
            Dict of {filename: content}
        """
        files = {}
        extensions = self.SUPPORTED_LANGUAGES.get(language.lower(), ['.py'])

        try:
            repo_path = Path(repo_path)
            
            # Skip common directories
            skip_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build', '.github'}

            for file_path in repo_path.rglob('*'):
                if not file_path.is_file():
                    continue

                # Skip if in skip directory
                if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                    continue

                # Check extension
                if file_path.suffix.lower() not in extensions:
                    continue

                # Skip large files (>1MB)
                if file_path.stat().st_size > 1_000_000:
                    logger.warning(f"Skipping large file: {file_path.name}")
                    continue

                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    if content.strip():  # Only include non-empty files
                        files[str(file_path.relative_to(repo_path))] = content
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")
                    continue

            logger.info(f"Extracted {len(files)} source files from {repo_path}")
            return files

        except Exception as e:
            logger.error(f"Failed to extract source files: {e}")
            return {}
