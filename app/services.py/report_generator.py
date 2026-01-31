from app.services.github_service import clone_repositories, extract_commit_messages
from app.services.commit_message_similarity import compute_commit_message_similarity
from app.services.code_diff import generate_side_by_side_diff
from app.services.report_exporter import generate_csv_report, generate_pdf_report

def generate_report(repo_urls, language, threshold):
    repo_paths = clone_repositories(repo_urls)

    all_commit_messages = []
    for path in repo_paths:
        all_commit_messages.extend(extract_commit_messages(path))

    suspicious_commits = compute_commit_message_similarity(
        all_commit_messages, threshold=0.8
    )

    csv_path = generate_csv_report(suspicious_commits)
    pdf_path = generate_pdf_report(suspicious_commits)

    # Demo code proof (kept simple & explainable)
    left_code = "def example():\n    print('hello')"
    right_code = "def example():\n    print('hello world')"
    left_html, right_html = generate_side_by_side_diff(left_code, right_code)

    return {
        "suspicious_commits": suspicious_commits,
        "code_left": left_html,
        "code_right": right_html,
        "csv_report": csv_path,
        "pdf_report": pdf_path
    }
