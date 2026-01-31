import git
import os
from ..config import Config

CLONE_DIR = "data/cloned_repos"


def clone_repositories(repo_urls):
    paths = []
    os.makedirs(CLONE_DIR, exist_ok=True)

    for url in repo_urls:
        repo_name = url.rstrip("/").split("/")[-1]
        local_path = os.path.join(CLONE_DIR, repo_name)

        if not os.path.exists(local_path):
            try:
                # ✅ SAFE CLONE — no checkout (avoids Windows invalid filename errors)
                git.Repo.clone_from(
                    url,
                    local_path,
                    multi_options=["--no-checkout"]
                )
            except Exception as e:
                print(f"[CLONE WARNING] {url} → {e}")
                continue

        paths.append(local_path)

    return paths


def extract_commit_messages(repo_path):
    repo = git.Repo(repo_path)

    commits = list(repo.iter_commits(max_count=Config.MAX_COMMITS))

    messages = []
    for commit in commits:
        msg = commit.message.strip()
        if msg:
            messages.append(msg)

    return messages
