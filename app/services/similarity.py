from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def compute_repo_similarity_matrix(repo_file_texts):
    """
    repo_file_texts = {
        repo_name: [file_text1, file_text2, ...]
    }
    """

    repo_names = list(repo_file_texts.keys())
    repo_docs = []

    for name in repo_names:
        # merge sampled files into one doc per repo
        merged = "\n".join(repo_file_texts[name])
        repo_docs.append(merged if merged.strip() else "empty")

    vectorizer = TfidfVectorizer(max_features=5000)
    tfidf = vectorizer.fit_transform(repo_docs)

    sim_matrix = cosine_similarity(tfidf)

    return repo_names, sim_matrix


def compute_file_similarity_pairs(repo_file_texts, threshold=0.8):
    """
    Returns list of:
    (repoA, repoB, fileA_index, fileB_index, similarity)
    """

    results = []

    repo_names = list(repo_file_texts.keys())

    for i in range(len(repo_names)):
        for j in range(i + 1, len(repo_names)):

            repo_a = repo_names[i]
            repo_b = repo_names[j]

            files_a = repo_file_texts[repo_a]
            files_b = repo_file_texts[repo_b]

            if not files_a or not files_b:
                continue

            docs = files_a + files_b

            vectorizer = TfidfVectorizer(max_features=3000)
            tfidf = vectorizer.fit_transform(docs)
            sim = cosine_similarity(tfidf)

            split = len(files_a)

            for fa in range(len(files_a)):
                for fb in range(len(files_b)):
                    score = sim[fa][split + fb]
                    if score >= threshold:
                        results.append(
                            (repo_a, repo_b, fa, fb, float(score))
                        )

    return results
