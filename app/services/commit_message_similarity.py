from difflib import SequenceMatcher

def is_automated_commit(message: str) -> bool:
    """
    Returns True if the commit message is likely automated
    (dependabot, bot, merge, version bump).
    """
    if not message:
        return True

    msg = message.lower().strip()

    return (
        msg.startswith("merge")
        or msg.startswith("bump ")
        or "dependabot" in msg
        or "bot" in msg
    )


def compute_commit_message_similarity(commits, threshold=0.6):
    """
    Compare commit messages and return suspiciously similar pairs.
    Automated commits are ignored.
    """

    filtered = []

    # ---- FILTER AUTOMATED COMMITS ----
    for c in commits:
        # c may be dict or string depending on extractor
        if isinstance(c, dict):
            msg = c.get("message", "")
        else:
            msg = str(c)

        if is_automated_commit(msg):
            continue

        filtered.append(msg.strip())

    results = []
    n = len(filtered)

    for i in range(n):
        for j in range(i + 1, n):
            a = filtered[i]
            b = filtered[j]

            score = SequenceMatcher(None, a, b).ratio()

            if score >= threshold:
                results.append((a, b, round(score, 2)))

    return results


from difflib import SequenceMatcher

def compare_two_commit_messages(a: str, b: str) -> float:
    """
    Compare exactly TWO commit messages and return similarity score.
    """
    return SequenceMatcher(None, a, b).ratio()
