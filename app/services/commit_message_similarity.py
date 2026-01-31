from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def compute_commit_message_similarity(records, threshold=0.6):
    """
    Accepts:
    - list[str]
    - list[{"repo": name, "message": msg}]
    Returns tuples compatible with exporter + template
    """

    if not records or len(records) < 2:
        return []

    # -------------------------
    # Normalize input safely
    # -------------------------
    messages = []
    repos = []

    for r in records:
        if isinstance(r, dict):
            msg = str(r.get("message", "")).strip()
            repo = r.get("repo", "unknown")
        else:
            msg = str(r).strip()
            repo = "unknown"

        if msg:
            messages.append(msg)
            repos.append(repo)

    if len(messages) < 2:
        return []

    # -------------------------
    # Vectorize
    # -------------------------
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2)
    )

    tfidf = vectorizer.fit_transform(messages)
    sim = cosine_similarity(tfidf)

    # -------------------------
    # Build results
    # -------------------------
    results = []

    for i in range(len(messages)):
        for j in range(i + 1, len(messages)):

            score = float(sim[i][j])

            if score >= threshold:
                results.append((
                    messages[i],
                    messages[j],
                    round(score, 3)
                ))

    results.sort(key=lambda x: x[2], reverse=True)

    return results
