# Project Status – GitHub Plagiarism Detection System

This document describes the current working status of the system.

---

## Features That Are Working

- GitHub repository cloning
- Repository-level similarity analysis
- Commit message similarity detection
- Similarity threshold configuration
- Plagiarism confidence levels (Low / Medium / High)
- Repository similarity matrix
- Commit similarity comparison view
- CSV report generation
- PDF report generation
- Clean and responsive web UI
- Input validation for minimum repositories
- Loading spinner during analysis
- Empty state handling when no analysis is present

---

## Features Partially Implemented

- Side-by-side code comparison  
  - UI is present  
  - Comparison logic is limited to sample files  

---

## Features Not Implemented (Known Limitations)

- Real-time analysis cancellation
- User authentication
- Analysis history persistence
- Progress percentage indicator
- Token-level or AST-based similarity
- Multi-language code analysis

---

## Known Limitations

- Analysis is synchronous (Flask-based)
- Large repositories may take longer to process
- Similarity is based on textual preprocessing
- Results are stored in memory (not database-backed)

---

## Overall Status

The project is **stable, functional, and suitable for academic demonstration and evaluation**.
