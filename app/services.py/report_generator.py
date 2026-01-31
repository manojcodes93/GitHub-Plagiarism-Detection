from app.services.github_service import clone_repositories
from app.services.preprocessing import preprocess_code
from app.services.similarity import compute_similarity

def generate_report(repo_urls, language, threshold):
    paths = clone_repositories(repo_urls)

    documents = []
    repo_map = []

    for path in paths:
        for root, _, files in os.walk(path):
            for f in files:
                if f.endswith(language):
                    with open(os.path.join(root, f), "r", errors="ignore") as file:
                        documents.append(preprocess_code(file.read()))
                        repo_map.append(path)

    similarity_matrix = compute_similarity(documents)

    return {
        "similarity_matrix": similarity_matrix.tolist(),
        "repositories": repo_urls
    }
