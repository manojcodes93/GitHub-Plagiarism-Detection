def analyze_commits(commits):
    suspicious = []

    for commit in commits:
        if commit.stats.total['lines'] > 300:
            suspicious.append(commit.hexsha)

    return suspicious
