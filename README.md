### GitHub Plagiarism Detection System
A web-based system to analyze GitHub repositories and detect potential code plagiarism using repository-level similarity, commit message analysis, and comparison metrics.

This project is designed for academic evaluation, demos, and learning purposes, with a clean UI and clear plagiarism confidence indicators.

## What does this project do?
This system helps identify code similarity and potential plagiarism across multiple GitHub repositories.

You provide:

- GitHub repository URLs
- A similarity threshold

The system analyzes:

- Repository-to-repository similarity
- Commit message patterns
- Code similarity signals

And produces:

- A plagiarism confidence score (Low / Medium / High)
- Visual similarity comparisons
- Downloadable reports

## Key Features
# Plagiarism Detection
- Compares multiple GitHub repositories
- Calculates similarity using configurable thresholds
- Assigns Low / Medium / High plagiarism confidence

# Similarity Analysis
- Repository Similarity Matrix to visualize repo-to-repo similarity
- Commit Message Similarity to detect suspicious commit patterns
- Confidence summary derived from analysis results

# Navigation-Friendly Results
- Results persist while navigating between comparison views
- Results reset on fresh start to avoid stale data
- Clear “No Analysis Data” state when no analysis is run

# Report Downloads
- Download analysis results as:

-> CSV
-> PDF

# Web Interface
- Clean, modern UI
- Step-by-step workflow:
1. Add repositories
2. Set similarity threshold
3. Run analysis
4. View results and comparisons

## How the confidence levels work
The system uses three confidence levels:
- Low – Minimal similarity detected
- Medium – Moderate similarity, requires review
- High – Strong similarity, possible plagiarism

These levels help users quickly interpret results without analyzing raw similarity values.

## Tech Stack
- Backend: Python, Flask
- Frontend: HTML, CSS, JavaScript
- Data Processing: Custom similarity analysis logic
- Reports: CSV and PDF generation
- Styling: Custom UI components
- Version Control: Git and GitHub

## How to Run the Project
# Option 1: Local Setup (Recommended)

git clone https://github.com/manojcodes93/GitHub-Plagiarism-Detection.git
cd GitHub-Plagiarism-Detection

python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

pip install -r requirements.txt
python app.py

### Open your browser and go to:

http://127.0.0.1:5000

### How to Use
## Step 1: Add Repositories
- Enter GitHub repository URLs you want to compare
- Add or remove repositories as needed

## Step 2: Set Similarity Threshold
- Adjust how strict the plagiarism detection should be
- Higher threshold means stricter detection

## Step 3: Run Analysis
- Click Run Analysis
- A loading indicator shows processing

## Step 4: View Results
- See plagiarism confidence
- Explore:
-> Commit Message Similarity
-> Repository Similarity Matrix
-> Download reports if required

### Project Structure (High-Level)

`GitHub-Plagiarism-Detection/
│
├── app.py
├── routes.py
├── services/
│   ├── report_generator.py
│   └── similarity_analysis.py
│
├── templates/
│   ├── dashboard.html
│   ├── analyze.html
│   ├── details.html
│   ├── commit_diff.html
│   └── repo_matrix.html
│
├── static/
│   ├── css/
│   └── img/
│
├── requirements.txt
└── README.md`

### Academic Note

This project is intended for:

- Academic submissions
- Learning and experimentation
- Demonstrating plagiarism detection concepts
- It should not be used as a sole authority for plagiarism decisions in production environments.

## Future Improvements

- Side-by-side code comparison
- Token-level similarity visualization
- User authentication
- Per-user analysis history
- Improved similarity algorithms

## License
This project is provided for educational purposes.
You are free to modify and extend it for learning or academic use.