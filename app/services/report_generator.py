import os

from .github_service import clone_repositories, extract_commit_messages
from .commit_message_similarity import compute_commit_message_similarity
from .code_diff import generate_side_by_side_diff
from .report_exporter import generate_csv_report, generate_pdf_report
from .similarity import (
    compute_repo_similarity_matrix,
    compute_file_similarity_pairs,
)
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
    # SAFE file sampling per repo
    # -------------------------
    repo_file_texts = {}
    repo_names = []

    for repo_path in repo_paths:
        repo_name = os.path.basename(repo_path)
        repo_names.append(repo_name)

        collected = []
        file_count = 0

        for root, dirs, files in os.walk(repo_path):

            dirs[:] = [d for d in dirs if d not in Config.SKIP_DIRS]

            for file in files:
                if not file.endswith(language):
                    continue

                full_path = os.path.join(root, file)

                size_kb = os.path.getsize(full_path) / 1024
                if size_kb > Config.MAX_FILE_SIZE_KB:
                    continue

                try:
                    with open(full_path, "r", errors="ignore") as f:
                        collected.append(f.read())
                        file_count += 1
                except:
                    continue

                if file_count >= Config.MAX_FILES_PER_REPO:
                    break

            if file_count >= Config.MAX_FILES_PER_REPO:
                break

        repo_file_texts[repo_name] = collected

    # -------------------------
    # Repo similarity matrix
    # -------------------------
    matrix_names, sim_matrix = compute_repo_similarity_matrix(repo_file_texts)

    # build table structure for template
    matrix_table = []
    for i, name in enumerate(matrix_names):
        row = []
        for j in range(len(matrix_names)):
            if i == j:
                row.append(None)
            else:
                row.append(round(float(sim_matrix[i][j]), 3))
        matrix_table.append(row)

    # -------------------------
    # File‑level similarity pairs
    # -------------------------
    file_pairs = compute_file_similarity_pairs(
        repo_file_texts,
        threshold=threshold
    )

    # -------------------------
    # Side‑by‑side demo diff (reuse best pair if exists)
    # -------------------------
    if file_pairs:
        ra, rb, fa, fb, score = file_pairs[0]
        left_code = repo_file_texts[ra][fa]
        right_code = repo_file_texts[rb][fb]
    else:
        left_code = "print('sample A')"
        right_code = "print('sample B')"

    left_html, right_html = generate_side_by_side_diff(left_code, right_code)

    # -------------------------
    # Aggregate repo plagiarism score (avg similarity)
    # -------------------------
    repo_pair_scores = {}

    for ra, rb, _, _, score in file_pairs:
        key = tuple(sorted([ra, rb]))
        repo_pair_scores.setdefault(key, []).append(score)

    repo_pair_confidence = {
        f"{a} ↔ {b}": round(sum(vals) / len(vals), 3)
        for (a, b), vals in repo_pair_scores.items()
    }

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
        "analysis_note": "Large repositories analyzed with bounded sampling.",

        # NEW FEATURES
        "repo_names": matrix_names,
        "similarity_matrix": matrix_table,
        "file_similarity_pairs": file_pairs,
        "repo_pair_confidence": repo_pair_confidence,
    }
