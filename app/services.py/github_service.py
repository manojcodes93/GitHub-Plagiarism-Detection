import git
import os

CLONE_DIR = "data/cloned_repos"

def clone_repositories(repo_urls):
    paths = []

    for url in repo_urls:
        repo_name = url.rstrip("/").split("/")[-1]
        local_path = os.path.join(CLONE_DIR, repo_name)

        if not os.path.exists(local_path):
            git.Repo.clone_from(url, local_path)

        paths.append(local_path)

    return paths

def extract_commit_messages(repo_path):
    repo = git.Repo(repo_path)
    commits = list(repo.iter_commits())

    messages = []
    for commit in commits:
        messages.append(commit.message.strip())

    return messages
