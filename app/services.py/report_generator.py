import os
from app.services.github_service import clone_repositories
from app.services.preprocessing import preprocess_code
from app.services.similarity import compute_similarity
from app.services.code_diff import generate_side_by_side_diff

def generate_report(repo_urls, language, threshold):
    repo_paths = clone_repositories(repo_urls)

    code_files = []

    for path in repo_paths:
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(language):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, "r", errors="ignore") as f:
                            code_files.append(f.read())
                    except:
                        pass

    # DEMO: compare first two files (safe for hackathon)
    left_code = preprocess_code(code_files[0])
    right_code = preprocess_code(code_files[1])

    left_html, right_html = generate_side_by_side_diff(left_code, right_code)

    similarity_matrix = compute_similarity([left_code, right_code])

    return {
        "repositories": repo_urls,
        "similarity_matrix": similarity_matrix.tolist(),
        "code_left": left_html,
        "code_right": right_html
    }
