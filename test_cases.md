# Test Cases – GitHub Plagiarism Detection System

This document describes the test cases used to validate the GitHub Plagiarism Detection System.  
The project has been tested using real-world open-source repositories.

---

## Repositories Used for Testing

### Medical / Domain-Specific Projects
- https://github.com/entbappy/Build-a-Complete-Medical-Chatbot-with-LLMs-LangChain-Pinecone-Flask-AWS
- https://github.com/manojcodes93/Medical-Chatbot

### Python Learning & Mini Projects
- https://github.com/geekcomputers/Python
- https://github.com/AutomationPanda/python-testing-101
- https://github.com/ndleah/python-mini-project
- https://github.com/thegeekyb0y/pythonprojects
- https://github.com/king04aman/All-In-One-Python-Projects
- https://github.com/iamshaunjp/python-basics
- https://github.com/iamshaunjp/python-tutorial
- https://github.com/iamshaunjp/python-projects

### Frameworks & Large Repositories
- https://github.com/pallets/flask
- https://github.com/pallets-eco/flask-admin
- https://github.com/tiangolo/fastapi
- https://github.com/fastapi/full-stack-fastapi-template
- https://github.com/scikit-learn/scikit-learn
- https://github.com/facebook/react

### Algorithm & Interview Repositories
- https://github.com/keon/algorithms
- https://github.com/TheAlgorithms/Python
- https://github.com/yangshun/tech-interview-handbook
- https://github.com/karan/Projects

---

## Test Case Categories

### 1. Positive Test Cases (Expected Similarity)

| Scenario | Description | Result |
|--------|-------------|--------|
| Similar Python projects | Multiple Python project collections | Similarity detected |
| Algorithm repositories | Common algorithm implementations | Medium to High similarity |
| Flask-based projects | Shared framework patterns | Medium similarity |
| Fork-like structures | Reused logic across repos | High similarity |

---

### 2. Negative Test Cases (Expected No Similarity)

| Scenario | Description | Result |
|--------|-------------|--------|
| Python vs React | Different languages | No similarity |
| Medical chatbot vs Algorithms | Different domains | Low similarity |
| Framework vs Mini projects | Different code purpose | Low similarity |

---

### 3. Edge Case Testing

| Edge Case | Handling |
|---------|----------|
| Less than 2 repositories | Prevented at UI level |
| Large repositories | File limits applied |
| Binary / non-code files | Ignored |
| Very small files | Ignored |
| Duplicate repo URLs | Handled safely |
| Empty analysis run | Shows “No Analysis Data” |

---

## Summary

The system was tested using:
- Small repositories
- Medium-sized projects
- Large open-source frameworks
- Domain-diverse codebases

This ensures robust evaluation across real-world scenarios.
