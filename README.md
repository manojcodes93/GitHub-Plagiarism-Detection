# GitHub Plagiarism Detection System

A web-based application designed to analyze GitHub repositories and detect potential source code plagiarism using repository similarity analysis and commit message comparison.

This project helps identify code reuse patterns across multiple repositories and provides an overall plagiarism confidence score to assist in academic and learning evaluations.

---

## Project Overview

The GitHub Plagiarism Detection System allows users to submit multiple GitHub repository URLs and analyze them for similarity.  
It compares repositories at different levels and highlights potential plagiarism indicators in a clear and structured manner.

This system is intended for:
- Academic projects
- Learning and experimentation

---

## Key Features

### Repository Analysis
- Accepts multiple GitHub repository URLs
- Requires a minimum of two repositories for comparison
- Prevents deletion below the minimum repository requirement
- Clones repositories locally for analysis

### Similarity Detection
- Repository-level similarity analysis
- Commit message similarity detection
- Configurable similarity threshold
- Plagiarism confidence classification:
  - Low
  - Medium
  - High

### Results and Visualization
- Repository similarity matrix
- Commit message similarity comparison
- Clear “No Analysis Data” state when no analysis is available
- Results persist during navigation within the results section

### Report Generation
- Downloadable CSV report
- Downloadable PDF report

### User Interface
- Clean and responsive UI
- Step-by-step analysis workflow
- Loading spinner during analysis
- Automatic scroll to analysis progress section

---

## How the System Works

1. User enters at least two GitHub repository URLs  
2. User configures the similarity threshold  
3. The system clones the repositories  
4. Source code files are preprocessed  
5. Similarity scores are computed  
6. Plagiarism confidence is determined  
7. Results and reports are displayed  

---

## Technology Stack

### Backend
- Python
- Flask

### Frontend
- HTML
- CSS
- JavaScript

### Analysis and Reporting
- Custom preprocessing logic
- Similarity computation
- CSV and PDF report generation

### Version Control
- Git
- GitHub

---

## Installation and Setup

### Prerequisites
- Python 3.9 or higher
- Git

### Local Setup

```bash
git clone https://github.com/manojcodes93/GitHub-Plagiarism-Detection.git
cd GitHub-Plagiarism-Detection

python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

pip install -r requirements.txt
python app.py
```

---

### Open the application in your browser:

http://127.0.0.1:5000

## Usage Guide

### Step 1: Add Repositories
Enter at least two GitHub repository URLs

Additional repositories can be added if required

### Step 2: Configure Similarity Threshold
Adjust threshold to control strictness of detection

### Step 3: Run Analysis
Click Run Analysis

A loading spinner indicates processing

### Step 4: View Results
Review plagiarism confidence

Explore repository and commit similarities

Download reports if required

---

## Testing

The project has been tested using:

- Small Python projects
- Medium-sized applications
- Large open-source frameworks
- Domain-diverse repositories

Test Coverage

- Positive test cases (expected similarity)
- Negative test cases (unrelated repositories)

- Edge cases:
  -> Minimum repository enforcement
  -> Large repositories
  -> Empty analysis runs

Detailed test cases are documented in `TEST_CASES.md.`

## Future Enhancements

- Side-by-side comparison for multiple files
- AST-based and semantic similarity detection
- Background task processing
- Progress indicators
- Multi-language code support
- User authentication and analysis history