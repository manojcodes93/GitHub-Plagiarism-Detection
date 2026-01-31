import os
from app.services.github_service import clone_repositories, extract_commit_messages
from app.services.preprocessing import preprocess_code
from app.services.similarity import compute_similarity
from app.services.code_diff import generate_side_by_side_diff
from app.services.commit_message_similarity import compute_commit_message_similarity

def generate_report(repo_urls, language, threshold):
    repo_paths = clone_repositories(repo_urls)

    all_commit_messages = []

    for path in repo_paths:
        all_commit_messages.extend(extract_commit_messages(path))

    suspicious_commits = compute_commit_message_similarity(
        all_commit_messages, threshold=0.8
    )

    # Dummy code comparison (kept for UI continuity)
    left_code = "def example():\n    print('hello')"
    right_code = "def example():\n    print('hello world')"

    left_html, right_html = generate_side_by_side_diff(left_code, right_code)

    return {
        "suspicious_commits": suspicious_commits,
        "code_left": left_html,
        "code_right": right_html
    }
