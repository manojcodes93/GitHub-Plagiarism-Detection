import os

from .github_service import clone_repositories, extract_commit_messages
from .commit_message_similarity import compute_commit_message_similarity
from .code_diff import generate_side_by_side_diff
from .report_exporter import generate_csv_report, generate_pdf_report
from .similarity import (
    compute_repo_similarity_matrix,
    compute_file_similarity_pairs,
)
from .preprocessing import preprocess_code
from ..config import Config


def generate_report(repo_urls, language, threshold):

    repo_paths = clone_repositories(repo_urls)

    # -------------------------
    # Commit messages
    # -------------------------
    all_commit_messages = []

    for path in repo_paths:
        all_commit_messages.extend(extract_commit_messages(path))

    suspicious_commits = compute_commit_message_similarity(
        all_commit_messages,
        threshold=0.6
    )

    # -------------------------
    # File sampling
    # -------------------------
    repo_file_texts = {}

    for repo_path in repo_paths:
        repo_name = os.path.basename(repo_path)
        collected = []
        count = 0

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in Config.SKIP_DIRS]

            for file in files:
                if not file.endswith(language):
                    continue

                full_path = os.path.join(root, file)

                try:
                    if os.path.getsize(full_path) / 1024 > Config.MAX_FILE_SIZE_KB:
                        continue

                    with open(full_path, "r", errors="ignore") as f:
                        raw = f.read()

                    processed = preprocess_code(raw)

                    if len(processed) > 30:
                        collected.append(processed)
                        count += 1

                except:
                    continue

                if count >= Config.MAX_FILES_PER_REPO:
                    break

            if count >= Config.MAX_FILES_PER_REPO:
                break

        repo_file_texts[repo_name] = collected

    # -------------------------
    # Repo matrix
    # -------------------------
    matrix_names, sim_matrix = compute_repo_similarity_matrix(repo_file_texts)

    matrix_table = []
    for i in range(len(matrix_names)):
        row = []
        for j in range(len(matrix_names)):
            row.append(None if i == j else round(float(sim_matrix[i][j]), 3))
        matrix_table.append(row)

    # -------------------------
    # File similarity pairs
    # -------------------------
    file_pairs = compute_file_similarity_pairs(
        repo_file_texts,
        threshold=threshold
    )

    # -------------------------
    # SAFE side‑by‑side selection (FIX)
    # -------------------------
    left_code = ""
    right_code = ""

    if file_pairs:
        try:
            ra, rb, fa, fb, score = file_pairs[0]
            left_code = repo_file_texts.get(ra, [""])[fa]
            right_code = repo_file_texts.get(rb, [""])[fb]
        except Exception:
            pass

    code_left_html, code_right_html = generate_side_by_side_diff(
        left_code,
        right_code
    )

    # -------------------------
    # Export reports
    # -------------------------
    csv_path = generate_csv_report(suspicious_commits)
    pdf_path = generate_pdf_report(suspicious_commits)

    return {
        "suspicious_commits": suspicious_commits,
        "matrix_names": matrix_names,
        "similarity_matrix": matrix_table,
        "file_similarity_pairs": file_pairs,
        "code_left": code_left_html,
        "code_right": code_right_html,
        "csv_report": csv_path,
        "pdf_report": pdf_path,
        "analysis_note": "Large repositories analyzed with bounded sampling.",
    }
