"""
Flask web application for GitHub Commit Plagiarism Detection.
LLM-first approach: Uses embeddings and semantic analysis for accurate plagiarism detection.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify
import numpy as np

# Import analyzer modules
from analyzer.github import GitHubAnalyzer
from analyzer.preprocess import CodePreprocessor
from analyzer.embeddings import EmbeddingGenerator
from analyzer.similarity import SimilarityAnalyzer
from analyzer.llm_reasoner import LLMReasoner

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['UPLOAD_FOLDER'] = "./backend/reports"

# Global analysis components
git_analyzer = GitHubAnalyzer()
embedding_generator = EmbeddingGenerator()
similarity_analyzer = SimilarityAnalyzer()
llm_reasoner = LLMReasoner()

# In-memory job tracking
jobs = {}


@app.route("/")
def index():
    """Render main UI page."""
    return render_template("index.html")


@app.route("/api/health")
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "embedding_model": embedding_generator.get_model_info(),
        "llm_model": llm_reasoner.model_name if llm_reasoner.model else "not_loaded",
    })


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """
    Start plagiarism analysis job.
    
    Request JSON:
    {
        "repos": ["https://github.com/user/repo1", ...],
        "language": "python",
        "branch": "main",
        "threshold": 0.75
    }
    """
    try:
        data = request.get_json()
        
        # Validate input
        repos = data.get("repos", [])
        language = data.get("language", "python")
        branch = data.get("branch", "main")
        threshold = float(data.get("threshold", 0.75))
        
        if not repos or len(repos) < 2:
            return jsonify({"error": "At least 2 repositories required"}), 400
        
        if len(repos) > 10:
            return jsonify({"error": "Maximum 10 repositories allowed"}), 400
        
        if not 0 <= threshold <= 1:
            return jsonify({"error": "Threshold must be between 0 and 1"}), 400
        
        # Create job
        job_id = str(uuid.uuid4())
        jobs[job_id] = {
            "id": job_id,
            "status": "processing",
            "repos": repos,
            "language": language,
            "branch": branch,
            "threshold": threshold,
            "created_at": datetime.now().isoformat(),
            "progress": 0,
            "error": None,
            "results": None,
        }
        
        # Process analysis in background (synchronously for now)
        try:
            results = _perform_analysis(repos, language, branch, threshold, job_id)
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["results"] = results
            jobs[job_id]["progress"] = 100
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = str(e)
        
        return jsonify({
            "job_id": job_id,
            "status": jobs[job_id]["status"]
        })
    
    except Exception as e:
        logger.error(f"Analysis request failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/results/<job_id>")
def get_results(job_id):
    """Get analysis results for a job."""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = jobs[job_id]
    return jsonify({
        "id": job["id"],
        "status": job["status"],
        "progress": job["progress"],
        "error": job["error"],
        "results": job["results"],
        "created_at": job["created_at"],
    })


@app.route("/api/jobs")
def list_jobs():
    """List all jobs."""
    return jsonify({
        "jobs": [
            {
                "id": job["id"],
                "status": job["status"],
                "repos": job["repos"],
                "progress": job["progress"],
                "created_at": job["created_at"],
            }
            for job in jobs.values()
        ]
    })


def _perform_analysis(
    repo_urls: list,
    language: str,
    branch: str,
    threshold: float,
    job_id: str
) -> dict:
    """
    Perform full plagiarism analysis.
    
    LLM-first pipeline:
    1. Clone repos
    2. Extract source files
    3. Preprocess code
    4. Generate embeddings
    5. Compute similarity
    6. LLM reasoning
    7. Generate report
    """
    logger.info(f"Starting analysis job {job_id} for {len(repo_urls)} repositories")
    
    # Step 1: Clone repositories
    cloned_paths = {}
    for i, url in enumerate(repo_urls):
        jobs[job_id]["progress"] = int((i / len(repo_urls)) * 20)
        try:
            path = git_analyzer.clone_repository(url, branch)
            cloned_paths[url] = path
            logger.info(f"Cloned {url}")
        except Exception as e:
            logger.error(f"Failed to clone {url}: {str(e)}")
            raise
    
    # Step 2: Extract source files for target language
    all_files = {}
    for i, (url, path) in enumerate(cloned_paths.items()):
        jobs[job_id]["progress"] = 20 + int((i / len(cloned_paths)) * 20)
        files = git_analyzer.extract_files_by_language(path, language)
        all_files[url] = files
        logger.info(f"Extracted {len(files)} {language} files from {url}")
    
    # Step 3: Preprocess code
    preprocessed_files = {}
    for i, (url, files) in enumerate(all_files.items()):
        jobs[job_id]["progress"] = 40 + int((i / len(all_files)) * 20)
        preprocessed = CodePreprocessor.preprocess_files(files, language, aggressive=True)
        preprocessed_files[url] = preprocessed
        logger.info(f"Preprocessed {len(preprocessed)} files from {url}")
    
    # Step 4: Generate embeddings
    all_embeddings = {}
    for i, (url, files) in enumerate(preprocessed_files.items()):
        jobs[job_id]["progress"] = 60 + int((i / len(preprocessed_files)) * 15)
        embeddings = embedding_generator.embed_code_files(files)
        all_embeddings[url] = embeddings
        logger.info(f"Generated {len(embeddings)} embeddings for {url}")
    
    # Step 5: Compute similarity between all repository pairs
    jobs[job_id]["progress"] = 75
    comparison_results = []
    repo_list = list(repo_urls)
    
    for i, url1 in enumerate(repo_list):
        for j, url2 in enumerate(repo_list):
            if i >= j:
                continue
            
            # Compare files
            file_comparisons = SimilarityAnalyzer.compare_files(
                all_embeddings[url1],
                all_embeddings[url2],
                threshold
            )
            
            # Compute repo similarity
            repo_similarity = SimilarityAnalyzer.compute_repository_similarity(
                all_embeddings[url1],
                all_embeddings[url2]
            )
            
            comparison_results.append({
                "repo1": url1,
                "repo2": url2,
                "repo_similarity": repo_similarity,
                "file_pairs": file_comparisons,
                "suspicious_pair": repo_similarity > threshold,
            })
    
    # Step 6: LLM reasoning on flagged pairs
    jobs[job_id]["progress"] = 85
    flagged_pairs = [r for r in comparison_results if r["suspicious_pair"]]
    
    for pair in flagged_pairs:
        # Add LLM judgment
        judgments = llm_reasoner.batch_judge_files(pair["file_pairs"][:5])
        pair["file_judgments"] = judgments
        pair["explanation"] = llm_reasoner.generate_plagiarism_explanation(
            pair["repo1"].split("/")[-1],
            pair["repo2"].split("/")[-1],
            pair["file_pairs"],
            pair["repo_similarity"]
        )
    
    # Step 7: Generate report
    jobs[job_id]["progress"] = 95
    report = {
        "job_id": job_id,
        "timestamp": datetime.now().isoformat(),
        "parameters": {
            "repositories": repo_urls,
            "language": language,
            "branch": branch,
            "threshold": threshold,
        },
        "summary": {
            "total_repos": len(repo_urls),
            "suspicious_pairs": len(flagged_pairs),
            "total_file_pairs_compared": sum(
                len(r["file_pairs"]) for r in comparison_results
            ),
        },
        "repository_matrix": {
            "repos": repo_list,
            "similarities": _build_similarity_matrix(comparison_results, repo_list),
        },
        "suspicious_pairs": flagged_pairs,
        "all_comparisons": comparison_results,
    }
    
    # Save report
    _save_report(report)
    
    jobs[job_id]["progress"] = 100
    logger.info(f"Analysis complete for job {job_id}")
    
    return report


def _build_similarity_matrix(comparisons: list, repo_list: list) -> list:
    """Build NxN similarity matrix from comparisons."""
    n = len(repo_list)
    matrix = [[0.0 for _ in range(n)] for _ in range(n)]
    
    for comp in comparisons:
        i = repo_list.index(comp["repo1"])
        j = repo_list.index(comp["repo2"])
        matrix[i][j] = comp["repo_similarity"]
        matrix[j][i] = comp["repo_similarity"]
    
    return matrix


def _save_report(report: dict):
    """Save report to file."""
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    filename = os.path.join(
        app.config['UPLOAD_FOLDER'],
        f"report_{report['job_id']}.json"
    )
    
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report saved to {filename}")


@app.route("/api/download/<job_id>")
def download_report(job_id):
    """Download report as JSON."""
    if job_id not in jobs or jobs[job_id]["status"] != "completed":
        return jsonify({"error": "Report not available"}), 404
    
    filename = os.path.join(
        app.config['UPLOAD_FOLDER'],
        f"report_{job_id}.json"
    )
    
    if not os.path.exists(filename):
        return jsonify({"error": "Report file not found"}), 404
    
    with open(filename, 'r') as f:
        report = json.load(f)
    
    return jsonify(report)


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info("Starting Plagiarism Detection Application")
    app.run(debug=True, host="0.0.0.0", port=5000)
