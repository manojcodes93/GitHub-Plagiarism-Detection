import os

from .github_service import clone_repositories, extract_commit_messages
from .commit_message_similarity import compute_commit_message_similarity
from .code_diff import generate_side_by_side_diff
from .report_exporter import generate_csv_report, generate_pdf_report
from ..config import Config


def generate_report(repo_urls, language, threshold):
    repo_paths = clone_repositories(repo_urls)

    # -------------------------
    # Commit message analysis
    # -------------------------
    all_commit_messages = []

    for path in repo_paths:
        all_commit_messages.extend(extract_commit_messages(path))

    suspicious_commits = compute_commit_message_similarity(
        all_commit_messages,
        threshold=0.8
    )

    # -------------------------
    # SAFE file sampling
    # -------------------------
    collected_files = []

    for repo_path in repo_paths:
        file_count = 0

        for root, dirs, files in os.walk(repo_path):

            # skip heavy folders
            dirs[:] = [d for d in dirs if d not in Config.SKIP_DIRS]

            for file in files:
                if not file.endswith(language):
                    continue

                full_path = os.path.join(root, file)

                # skip very large files
                size_kb = os.path.getsize(full_path) / 1024
                if size_kb > Config.MAX_FILE_SIZE_KB:
                    continue

                try:
                    with open(full_path, "r", errors="ignore") as f:
                        collected_files.append(f.read())
                        file_count += 1
                except:
                    continue

                if file_count >= Config.MAX_FILES_PER_REPO:
                    break

            if file_count >= Config.MAX_FILES_PER_REPO:
                break

    # -------------------------
    # Side‑by‑side demo diff
    # -------------------------
    if len(collected_files) >= 2:
        left_code = collected_files[0]
        right_code = collected_files[1]
    else:
        left_code = "print('sample A')"
        right_code = "print('sample B')"

    left_html, right_html = generate_side_by_side_diff(left_code, right_code)

    # -------------------------
    # Export reports
    # -------------------------
    csv_path = generate_csv_report(suspicious_commits)
    pdf_path = generate_pdf_report(suspicious_commits)

    return {
        "suspicious_commits": suspicious_commits,
        "code_left": left_html,
        "code_right": right_html,
        "csv_report": csv_path,
        "pdf_report": pdf_path,
        "analysis_note": "Large repositories analyzed with bounded sampling for performance."
    }
