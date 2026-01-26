# GitHub Commit Plagiarism Detection Web Application

## 🎯 Overview

An **LLM-first plagiarism detection system** that analyzes multiple GitHub repositories and identifies potential plagiarism using:

- **Semantic embeddings** (Hugging Face sentence-transformers)
- **Cosine similarity** for code comparison
- **LLM reasoning** for explainable plagiarism judgments
- **Flask** web UI for interactive analysis

## 🧠 Core Philosophy

Instead of traditional rule-heavy approaches (AST, string matching), this system uses:

1. **Embeddings** to understand code semantically
2. **LLMs** to reason about whether similarity indicates plagiarism
3. **Explainability** to show why code is flagged

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python + Flask |
| **Frontend** | HTML + CSS + JavaScript |
| **Git Handling** | GitPython |
| **Embeddings** | Hugging Face `sentence-transformers/all-MiniLM-L6-v2` |
| **LLM Reasoning** | `Qwen/Qwen2.5-Coder-7B-Instruct` (optional) |
| **Similarity** | Cosine similarity (scipy) |

## 📥 Features

### Inputs
- List of GitHub repository URLs (2-10 repositories)
- Target programming language (Python, Java, JavaScript, TypeScript, C#, C++)
- Branch name (default: `main`)
- Similarity threshold (0.5-1.0)

### Outputs
- ✅ Repository-to-repository similarity scores
- 📊 Similarity matrix visualization
- 🚨 Flagged repository pairs
- 📄 File-level similarity report
- 💾 Downloadable JSON report

### Detection Logic

**File-Level Analysis:**
1. Clone repositories
2. Extract source files of target language
3. Preprocess code (remove comments, normalize whitespace)
4. Generate embeddings for each file
5. Compute cosine similarity
6. Flag pairs above threshold

**Repository-Level Scoring:**
1. Aggregate file similarities
2. Compute average-max similarity between repositories
3. Use LLM to judge if patterns indicate plagiarism

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <this-repo>
cd plagiarism-detector
pip install -r requirements.txt
```

### 2. Run the Application

```bash
cd backend
python app.py
```

The app runs at `http://localhost:5000`

### 3. Use the Web UI

1. **Enter Repository URLs**: Paste GitHub URLs (one per line)
2. **Select Language**: Choose target language
3. **Set Threshold**: Adjust similarity threshold (default: 0.75)
4. **Analyze**: Click "Analyze Repositories"
5. **Review Results**: View similarity matrix and flagged pairs
6. **Download Report**: Export results as JSON

## 📁 Project Structure

```
plagiarism-detector/
├── backend/
│   ├── app.py                    # Flask web server
│   ├── analyzer/
│   │   ├── __init__.py
│   │   ├── github.py             # Repo cloning + commit extraction
│   │   ├── preprocess.py         # Code normalization
│   │   ├── embeddings.py         # Hugging Face embeddings
│   │   ├── similarity.py         # Cosine similarity
│   │   └── llm_reasoner.py       # LLM-based plagiarism judgment
│   └── reports/                  # Generated reports (JSON)
│
├── templates/
│   ├── index.html                # Main UI page
│   └── dashboard.html            # Results dashboard
│
├── static/
│   ├── styles.css                # Responsive styling
│   └── script.js                 # Frontend logic
│
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🤖 LLM Usage

### Embeddings (Mandatory)

**Model**: `sentence-transformers/all-MiniLM-L6-v2`
- Lightweight, efficient, 384-dimensional embeddings
- Pre-trained on 215M+ sentence pairs
- Perfect for code similarity tasks

**Purpose:**
- File-level similarity detection
- Repository-level aggregation
- Semantic code comparison (beyond string matching)

### LLM Reasoning (Optional but Recommended)

**Model**: `Qwen/Qwen2.5-Coder-7B-Instruct`
- Specialized in code understanding
- Makes explainable plagiarism judgments
- Explains why code is flagged

**Purpose:**
- Decides if high similarity = plagiarism
- Generates human-readable explanations
- Reduces false positives

## 🔍 How It Works

### Step 1: Code Preprocessing

```python
# Removes noise while preserving semantics
- Comments (Python #, Java //, etc.)
- Whitespace normalization
- Import statements
- Optionally: identifier renaming for aggressive detection
```

### Step 2: Embedding Generation

```python
# Convert code to semantic vectors
file_content → SentenceTransformer → 384-dim embedding
commit_diff → SentenceTransformer → 384-dim embedding
```

### Step 3: Similarity Computation

```python
# Cosine similarity: -1 to 1 (higher = more similar)
similarity = dot_product(normalized_vec1, normalized_vec2)

# Flagging thresholds
similarity > 0.95 → CRITICAL
similarity > 0.85 → HIGH SUSPICION
similarity > 0.75 → MEDIUM SUSPICION
similarity > 0.65 → LOW SUSPICION
```

### Step 4: LLM Reasoning

```python
# LLM analyzes:
- Commit message similarities
- Pattern of changes
- Code structure alignment
- Library/framework usage

# Output: Confidence score + explanation
```

## 🧪 API Endpoints

### Analysis

**POST** `/api/analyze`
```json
{
  "repos": ["https://github.com/user/repo1", "https://github.com/user/repo2"],
  "language": "python",
  "branch": "main",
  "threshold": 0.75
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "processing"
}
```

### Results

**GET** `/api/results/<job_id>`
```json
{
  "id": "job_id",
  "status": "completed",
  "progress": 100,
  "results": {
    "summary": {...},
    "suspicious_pairs": [...],
    "repository_matrix": {...}
  }
}
```

### Health

**GET** `/api/health`
```json
{
  "status": "healthy",
  "embedding_model": "loaded",
  "llm_model": "qwen2.5-coder-7b"
}
```

## 💡 Key Design Decisions

### Why Embeddings?
- **Semantic Understanding**: Detects copied logic, not just identical code
- **Language Agnostic**: Works across Python, Java, JavaScript, etc.
- **Efficient**: Pre-computed, no real-time processing needed
- **Explainable**: Can visualize similarities

### Why LLM?
- **Context Awareness**: Understands code intent, not just syntax
- **Explainability**: Provides reasoning for flagged code
- **Flexibility**: Can be customized for domain-specific rules
- **Better Accuracy**: Reduces false positives vs. rule-based systems

### Why Not Traditional Tools?
- ❌ AST-based: Too brittle, fails on variable renames
- ❌ String matching: Misses copied logic with different structure
- ❌ MOSS-style hashing: Can't detect semantic plagiarism
- ✅ Embeddings + LLM: Semantic similarity + explainability

## ⚙️ Configuration

### Supported Languages
- Python
- Java
- JavaScript
- TypeScript
- C#
- C++

### Similarity Thresholds
- **Recommended**: 0.75 (catches most plagiarism)
- **Conservative**: 0.85 (high confidence only)
- **Aggressive**: 0.65 (catch all similar code)

### Performance Tuning
- Max repositories: 10
- Max commit history: 50 commits per repo
- Max file size for embedding: 10,000 chars (truncated)

## 🔒 Security & Privacy

- ✅ Code is analyzed locally
- ✅ No external API calls (embeddings run locally)
- ✅ Reports are JSON-based
- ✅ No data stored beyond current session

## 🎯 Example Usage

```bash
# 1. Run the app
python backend/app.py

# 2. Open browser
http://localhost:5000

# 3. Enter repository URLs
https://github.com/student1/assignment
https://github.com/student2/assignment
https://github.com/student3/assignment

# 4. Select language: Python
# 5. Set threshold: 0.75
# 6. Click Analyze

# 7. Results show:
# - Similarity matrix
# - Flagged pairs with scores
# - File-level comparisons
# - LLM explanations
```

## 📊 Example Output

```json
{
  "job_id": "a1b2c3d4",
  "summary": {
    "total_repos": 3,
    "suspicious_pairs": 2,
    "total_file_pairs_compared": 45
  },
  "suspicious_pairs": [
    {
      "repo1": "https://github.com/alice/ml-project",
      "repo2": "https://github.com/bob/ml-project",
      "repo_similarity": 0.92,
      "file_pairs": [
        {
          "file1": "data_loader.py",
          "file2": "loader.py",
          "similarity": 0.96,
          "status": "critical"
        }
      ],
      "explanation": "Extremely high semantic similarity in data loading logic..."
    }
  ]
}
```

## 🚨 Important Constraints

- ✅ Limited to **one programming language** per analysis
- ✅ Supports **up to 10 repositories** per job
- ✅ Focus on **detection + explanation**, not enforcement
- ✅ Designed for **hackathon readiness** (clean, modular code)

## 🤝 Contributing

This is a hackathon-ready project. Feel free to:
- Add more languages
- Improve LLM reasoning
- Enhance UI/UX
- Add batch processing
- Integrate with CI/CD

## 📝 License

MIT License - Use freely for academic/research purposes

## 🎓 Academic Use

This tool is designed for:
- ✅ Academic integrity checking
- ✅ Assignment plagiarism detection
- ✅ Code similarity analysis
- ✅ Internship candidate screening

---

**Built with ❤️ for developers, by developers. LLM-first approach for better plagiarism detection.**
