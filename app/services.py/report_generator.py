import os
from app.services.github_service import clone_repositories
from app.services.preprocessing import preprocess_code
from app.services.similarity import compute_similarity

def generate_report(repo_urls, language, threshold):
    repo_paths = clone_repositories(repo_urls)

    documents = []
    repo_names = []

    for path in repo_paths:
        repo_name = os.path.basename(path)
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(language):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", errors="ignore") as f:
                            documents.append(preprocess_code(f.read()))
                            repo_names.append(repo_name)
                    except:
                        continue

    similarity_matrix = compute_similarity(documents)

    return {
        "repositories": repo_names,
        "similarity_matrix": similarity_matrix.tolist(),
        "flagged_pairs": []  # will fill later
    }
