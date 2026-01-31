import os

from .github_service import clone_repositories, extract_commit_messages
from .commit_message_similarity import compute_commit_message_similarity
from .similarity import compute_repo_similarity_matrix, compute_file_similarity_pairs
from .report_exporter import generate_csv_report, generate_pdf_report
from .code_diff import generate_side_by_side_diff
from .preprocessing import preprocess_code
from ..config import Config


def generate_report(repo_urls, language, threshold):

    # -------------------------
    # Clone repos
    # -------------------------
    repo_paths = clone_repositories(repo_urls)

    repo_file_texts = {}
    repo_processed_joined = {}

    # -------------------------
    # Collect files
    # -------------------------
    for repo_path in repo_paths:

        repo_name = os.path.basename(repo_path)

        processed_list = []
        raw_list = []

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
                        processed_list.append(processed)
                        raw_list.append(raw)
                        count += 1

                except:
                    continue

                if count >= Config.MAX_FILES_PER_REPO:
                    break

            if count >= Config.MAX_FILES_PER_REPO:
                break

        repo_file_texts[repo_name] = raw_list
        repo_processed_joined[repo_name] = "\n".join(processed_list)

    # -------------------------
    # Repo similarity matrix ✅ FIXED (DICT INPUT)
    # -------------------------
    matrix_names, sim_matrix = compute_repo_similarity_matrix(
        repo_processed_joined
    )

    matrix_table = []
    for i in range(len(matrix_names)):
        row = []
        for j in range(len(matrix_names)):
            row.append(None if i == j else round(float(sim_matrix[i][j]), 3))
        matrix_table.append(row)

    # -------------------------
    # Commit similarity
    # -------------------------
    all_commits = []
    for path in repo_paths:
        all_commits.extend(extract_commit_messages(path))

    suspicious_commits = compute_commit_message_similarity(
        all_commits,
        threshold=0.6
    )

    # -------------------------
    # File similarity pairs
    # -------------------------
    file_pairs = compute_file_similarity_pairs(
        repo_file_texts,
        threshold=threshold
    )

    # -------------------------
    # Side‑by‑side code
    # -------------------------
    left_html = None
    right_html = None

    if file_pairs:
        try:
            ra, rb, fa, fb, score = file_pairs[0]
            left_code = repo_file_texts[ra][fa]
            right_code = repo_file_texts[rb][fb]

            left_html, right_html = generate_side_by_side_diff(
                left_code,
                right_code
            )
        except:
            pass

    # -------------------------
    # Export reports
    # -------------------------
    csv_path = generate_csv_report(suspicious_commits)
    pdf_path = generate_pdf_report(suspicious_commits)

    # -------------------------
    # Final dict
    # -------------------------
    return {
        "matrix_names": matrix_names,
        "similarity_matrix": matrix_table,
        "suspicious_commits": suspicious_commits,
        "file_similarity_pairs": file_pairs,

        "code_left": left_html,
        "code_right": right_html,

        "csv_report": csv_path,
        "pdf_report": pdf_path,
    }
