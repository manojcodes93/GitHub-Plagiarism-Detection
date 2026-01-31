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
            git.Repo.clone_from(url, local_path)

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
