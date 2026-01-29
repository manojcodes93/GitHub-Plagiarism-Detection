🚨 GitHub Commit Plagiarism Detection System

A web-based system to detect potential code plagiarism across multiple GitHub repositories using file-level and commit-level analysis with semantic embeddings and structural similarity.

This project is designed for internship hiring, academic project reviews, and hackathons, where candidates submit GitHub repositories and plagiarism is difficult to detect manually.

🎯 Problem Statement

When multiple candidates submit GitHub repositories:

Code may be renamed, reformatted, or split across commits

Manual review fails to detect semantic plagiarism

Commit history is often ignored

This system automatically analyzes repositories, files, and commits to identify suspicious similarities and presents clear, explainable results through a web UI.

✅ Key Features
🔍 Repository-Level Analysis

Computes repository-to-repository similarity

Uses median of best file matches for robustness

Displays results in a similarity matrix

📄 File-Level Plagiarism Detection

Preprocesses code (comments, imports, identifiers)

Combines:

Token-based similarity (Jaccard)

Semantic similarity (Sentence-BERT embeddings)

Flags highly similar files with scores

🧾 Commit-Level Analysis

Analyzes commit diffs (added/removed lines only)

Detects:

Large similar commits

Similar commit messages

Similar code changes across repositories

🧠 Explainability Layer

Rule-based LLM reasoning

Generates human-readable explanations

Helps reviewers understand why something is flagged

🌐 Web Application

Input GitHub repo URLs

Select language, branch, similarity threshold

Interactive dashboard:

Similarity matrix

Flagged repository pairs

File-level and commit-level details

Downloadable JSON plagiarism report

🧠 How It Works (Pipeline)

Clone GitHub repositories

Extract source code files (language-specific)

Preprocess code

Remove comments & imports

Normalize whitespace

Normalize identifiers (aggressive mode)

Generate embeddings

Code is chunked into small blocks

Sentence-BERT embeddings

Mean pooling per file

Similarity computation

File-level: token + embedding similarity

Repo-level: median best-match similarity

Commit-level analysis

Diff-based embeddings

Cross-repo commit comparison

Reasoning & report generation

🛠 Tech Stack

Backend

Python

Flask

GitPython

SentenceTransformers (MiniLM)

NumPy

Frontend

HTML, CSS, JavaScript

Interactive dashboard

Progress tracking & modal views

📥 Input
{
  "repos": [
    "https://github.com/user/repo1",
    "https://github.com/user/repo2"
  ],
  "language": "python",
  "branch": "main",
  "threshold": 0.75
}

📤 Output

Repository similarity matrix

Flagged repository pairs

File-level similarity scores

Commit-level plagiarism indicators

Explainable reasoning

Downloadable JSON report

🚀 How to Run
1️⃣ Clone the repository
git clone https://github.com/manojcodes93/GitHub-Plagiarism-Detection.git
cd GitHub-Plagiarism-Detection/backend

2️⃣ Install dependencies
pip install -r requirements.txt

3️⃣ Run the app
python app.py

4️⃣ Open in browser
http://localhost:5000

⚠️ Constraints & Design Choices

Supports one programming language at a time

Max 10 repositories per analysis

Focuses on detection & explanation, not enforcement

Uses semantic similarity, not exact matching

Synchronous processing (safe for hackathon scale)

🧪 Example Use Cases

Internship hiring plagiarism checks

Academic project evaluation

Detecting copied GitHub assignments

Code originality analysis

📌 Future Improvements

Async background jobs (Celery / Redis)

AST-based structural similarity

Cross-language plagiarism detection

Visual side-by-side code diff viewer

User authentication & history tracking