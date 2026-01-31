from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def compute_repo_similarity_matrix(repo_file_texts):

    repo_names = list(repo_file_texts.keys())

    docs = []
    for name in repo_names:
        merged = "\n".join(repo_file_texts[name])
        docs.append(merged if merged.strip() else f"empty_{name}")

    vectorizer = TfidfVectorizer(max_features=8000)
    tfidf = vectorizer.fit_transform(docs)

    return repo_names, cosine_similarity(tfidf)


def compute_file_similarity_pairs(repo_file_texts, threshold=0.7):

    results = []
    repos = list(repo_file_texts.keys())

    for i in range(len(repos)):
        for j in range(i + 1, len(repos)):

            ra = repos[i]
            rb = repos[j]

            files_a = repo_file_texts[ra]
            files_b = repo_file_texts[rb]

            if not files_a or not files_b:
                continue

            docs = files_a + files_b

            vectorizer = TfidfVectorizer(max_features=4000)
            tfidf = vectorizer.fit_transform(docs)
            sim = cosine_similarity(tfidf)

            split = len(files_a)

            for fa in range(len(files_a)):
                for fb in range(len(files_b)):
                    score = float(sim[fa][split + fb])

                    if score >= threshold:
                        results.append((ra, rb, fa, fb, score))

    return results
