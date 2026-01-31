import os

from .github_service import clone_repositories, extract_commit_messages
from .commit_message_similarity import compute_commit_message_similarity
from .similarity import compute_repo_similarity_matrix, compute_file_similarity_pairs
from .report_exporter import generate_csv_report, generate_pdf_report
from .code_diff import generate_side_by_side_diff
from .preprocessing import preprocess_code
from ..config import Config


IGNORE_KEYWORDS = [
    "merge",
    "dependabot",
    "bot",
    "skip ci",
    "release",
    "changelog",
    "version",
    "bump",
    "ci"
]


def is_noise_commit(msg: str) -> bool:
    msg = msg.lower().strip()
    if len(msg.split()) < 3:
        return True
    return any(k in msg for k in IGNORE_KEYWORDS)


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

                except Exception:
                    continue

                if count >= Config.MAX_FILES_PER_REPO:
                    break

            if count >= Config.MAX_FILES_PER_REPO:
                break

        repo_file_texts[repo_name] = raw_list
        repo_processed_joined[repo_name] = "\n".join(processed_list)

    # -------------------------
    # Repo similarity matrix
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
    # Commit collection (repo-aware)
    # -------------------------
    repo_commit_pairs = []   # (repo, message)
    flat_commit_messages = []

    for path in repo_paths:
        repo = os.path.basename(path)
        commits = extract_commit_messages(path)

        for msg in commits:
            if is_noise_commit(msg):
                continue

            repo_commit_pairs.append((repo, msg))
            flat_commit_messages.append(msg)

    # -------------------------
    # Existing commit similarity (UNCHANGED)
    # -------------------------
    suspicious_commits = compute_commit_message_similarity(
        flat_commit_messages,
        threshold=threshold
    )

    # -------------------------
    # NEW: repo-aware commit similarity
    # -------------------------
    suspicious_commits_with_repo = []

    for i in range(len(repo_commit_pairs)):
        repo_a, msg_a = repo_commit_pairs[i]

        for j in range(i + 1, len(repo_commit_pairs)):
            repo_b, msg_b = repo_commit_pairs[j]

            if repo_a == repo_b:
                continue

            score = compute_commit_message_similarity(
                [msg_a, msg_b],
                threshold=threshold
            )

            if score:
                _, _, s = score[0]
                suspicious_commits_with_repo.append(
                    (repo_a, msg_a, repo_b, msg_b, round(float(s), 3))
                )

    # -------------------------
    # File similarity pairs
    # -------------------------
    raw_file_pairs = compute_file_similarity_pairs(
        repo_file_texts,
        threshold=threshold
    )

    file_similarity_table = []
    for ra, rb, fa, fb, score in raw_file_pairs:
        file_similarity_table.append({
            "repo_a": ra,
            "file_a_index": fa,
            "repo_b": rb,
            "file_b_index": fb,
            "similarity": round(float(score), 3)
        })

    # -------------------------
    # Side-by-side code
    # -------------------------
    left_html = None
    right_html = None

    if raw_file_pairs:
        try:
            ra, rb, fa, fb, _ = raw_file_pairs[0]
            left_code = repo_file_texts[ra][fa]
            right_code = repo_file_texts[rb][fb]

            left_html, right_html = generate_side_by_side_diff(
                left_code,
                right_code
            )
        except Exception:
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
        "suspicious_commits": suspicious_commits,  # untouched
        "suspicious_commits_with_repo": suspicious_commits_with_repo,
        "file_similarity_table": file_similarity_table,
        "code_left": left_html,
        "code_right": right_html,
        "csv_report": csv_path,
        "pdf_report": pdf_path,
    }
