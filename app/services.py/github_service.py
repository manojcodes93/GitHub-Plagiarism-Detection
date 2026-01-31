import git
import os

CLONE_DIR = "data/cloned_repos"

def clone_repositories(repo_urls):
    local_paths = []

    for url in repo_urls:
        repo_name = url.split("/")[-1]
        path = os.path.join(CLONE_DIR, repo_name)

        if not os.path.exists(path):
            git.Repo.clone_from(url, path)

        local_paths.append(path)

    return local_paths
