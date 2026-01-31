from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def compute_commit_message_similarity(commit_messages, threshold=0.8):
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(commit_messages)

    similarity_matrix = cosine_similarity(tfidf_matrix)

    suspicious_pairs = []

    for i in range(len(commit_messages)):
        for j in range(i + 1, len(commit_messages)):
            score = similarity_matrix[i][j]
            if score >= threshold:
                suspicious_pairs.append({
                    "commit_1": commit_messages[i],
                    "commit_2": commit_messages[j],
                    "similarity": round(score, 2)
                })

    return suspicious_pairs
