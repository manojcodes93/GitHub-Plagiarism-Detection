"""
Flask web application for GitHub Commit Plagiarism Detection.
LLM-first approach: Uses embeddings and semantic analysis for accurate plagiarism detection.
"""

import os
import threading
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
        
        # Expect first repo to be the candidate, remaining to be references
        if not repos or len(repos) < 3:
            return jsonify({"error": "Provide candidate repo (first) and at least 2 reference repositories"}), 400
        
        # Allow up to 10 reference repos (candidate + up to 10 references)
        if len(repos) - 1 > 10:
            return jsonify({"error": "Maximum 10 reference repositories allowed"}), 400
        
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
            def run_analysis():
                try:
                    results = _perform_analysis(repos, language, branch, threshold, job_id)
                    jobs[job_id]["status"] = "completed"
                    jobs[job_id]["results"] = results
                    jobs[job_id]["progress"] = 100
                
                except Exception as e:
                    logger.error(f"Analysis failed: {str(e)}")
                    jobs[job_id]["status"] = "failed"
                    jobs[job_id]["error"] = str(e)
                    
            thread = threading.Thread(target=run_analysis, daemon=True)
            thread.start()

        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = str(e)
        
        return jsonify({
            "job_id": job_id,
            "status": "processing"
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
    logger.info(f"Starting analysis job {job_id} for {len(repo_urls)} repositories (candidate + references)")

    jobs[job_id]["progress"] = 5
    jobs[job_id]["status"] = "processing"
    logger.info("Job started, progress set to 5%")
    
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

    jobs[job_id]["progress"] = 20
    
    # Step 2: Extract source files for target language
    all_files = {}
    for i, (url, path) in enumerate(cloned_paths.items()):
        jobs[job_id]["progress"] = 20 + int((i / len(cloned_paths)) * 20)
        files = git_analyzer.extract_code_files(path, language)

        if not files:
            logger.warning(f"No {language} files found for {url}")
            continue

        MAX_FILES = 40
        files = dict(list(files.items())[:MAX_FILES])

        all_files[url] = files
        logger.info(f"Extracted {len(files)} {language} files from {url}")

    if len(all_files) < 2:
        raise RuntimeError("Not enough repositories with valid source files")
    
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
        logger.info(f"Embedding {len(files)} files for {url}")
        embeddings = embedding_generator.embed_code_files(files)
        all_embeddings[url] = embeddings
        logger.info(f"Generated {len(embeddings)} embeddings for {url}")

        try:
            git_analyzer.delete_repo(cloned_paths[url])
            logger.info(f"Deleted cloned repo for {url}")
        except Exception as e:
            logger.warning(f"Failed to delete repo {url}: {e}")
    
    # Step 5: Compute similarity only between candidate -> each reference (one-to-many)
    jobs[job_id]["progress"] = 75
    comparison_results = []
    repo_list = list(all_embeddings.keys())

    # Candidate is the first repo in the original request order
    candidate_url = repo_urls[0]
    if candidate_url not in all_embeddings:
        raise RuntimeError("Candidate repository has no files in selected language")

    reference_urls = [u for u in repo_urls[1:] if u in all_embeddings]
    if not reference_urls:
        raise RuntimeError("No reference repositories with valid source files found")

    for idx, ref_url in enumerate(reference_urls):
        jobs[job_id]["progress"] = 75 + int((idx / max(1, len(reference_urls))) * 10)

        # Compare files (candidate -> reference)
        file_comparisons = similarity_analyzer.compare_files(
            all_embeddings[candidate_url],
            all_embeddings[ref_url],
            preprocessed_files[candidate_url],
            preprocessed_files[ref_url],
            threshold
        )

        # Compute repo similarity (how closely reference matches candidate)
        repo_similarity = similarity_analyzer.compute_repository_similarity(
            all_embeddings[candidate_url],
            all_embeddings[ref_url]
        )

        # Commit-level quick checks: compare recent commit diffs/messages
        commit_flags = []
        try:
            candidate_commits = git_analyzer.extract_commits(cloned_paths[candidate_url], limit=50)
            ref_commits = git_analyzer.extract_commits(cloned_paths[ref_url], limit=50)

            # Embedded diffs for candidate and ref (keep small to limit cost)
            cand_diffs = [git_analyzer.extract_commit_diff(cloned_paths[candidate_url], c['hash'], language) for c in candidate_commits[:20]]
            ref_diffs = [git_analyzer.extract_commit_diff(cloned_paths[ref_url], c['hash'], language) for c in ref_commits[:20]]

            # Flatten diffs text lists
            cand_diff_texts = ["\n".join(d.values()) for d in cand_diffs if d]
            ref_diff_texts = ["\n".join(d.values()) for d in ref_diffs if d]

            if cand_diff_texts and ref_diff_texts:
                cand_emb = embedding_generator.embed_commit_diffs(cand_diff_texts)
                ref_emb = embedding_generator.embed_commit_diffs(ref_diff_texts)

                # Compare commit embeddings for suspicious similarities
                for i_c, ce in enumerate(cand_emb):
                    best = 0.0
                    for re in ref_emb:
                        sim = similarity_analyzer.cosine_similarity(ce, re)
                        best = max(best, sim)

                    if best >= 0.9:
                        commit_flags.append({
                            "candidate_commit_index": i_c,
                            "best_similarity": best,
                            "reason": "High commit-diff similarity"
                        })

            # Also check identical commit messages for quick signal
            for c in candidate_commits[:20]:
                for r in ref_commits[:20]:
                    if c['message'].strip() and c['message'].strip() == r['message'].strip():
                        commit_flags.append({
                            "candidate_commit": c['hash'],
                            "reference_commit": r['hash'],
                            "reason": "Identical commit messages"
                        })

        except Exception as e:
            logger.debug(f"Commit-level checks skipped for {ref_url}: {e}")

        comparison_results.append({
            "candidate": candidate_url,
            "reference": ref_url,
            "repo_similarity": repo_similarity,
            "file_pairs": file_comparisons,
            "commit_flags": commit_flags,
            "suspicious": repo_similarity > threshold or bool(commit_flags)
        })
    
    # Step 6: LLM reasoning on flagged references (candidate vs each reference)
    jobs[job_id]["progress"] = 85
    flagged_refs = [r for r in comparison_results if r["suspicious"]]

    for pair in flagged_refs:
        # Add LLM judgment (limit to top 5 file pairs for brevity)
        judgments = llm_reasoner.batch_judge_files(pair["file_pairs"][:5])
        pair["file_judgments"] = judgments
        pair["explanation"] = llm_reasoner.generate_plagiarism_explanation(
            pair["candidate"].split("/")[-1],
            pair["reference"].split("/")[-1],
            pair["file_pairs"],
            pair["repo_similarity"]
        )
    
    # Step 7: Generate report
    jobs[job_id]["progress"] = 95
    # Aggregate final verdict for candidate repository
    max_similarity = max((r['repo_similarity'] for r in comparison_results), default=0.0)
    overall_confidence = min(0.95, max_similarity + 0.05)
    verdict = "No plagiarism detected" if max_similarity < threshold else "Potential plagiarism detected"

    report = {
        "job_id": job_id,
        "timestamp": datetime.now().isoformat(),
        "parameters": {
            "candidate": repo_urls[0],
            "references": repo_urls[1:],
            "language": language,
            "branch": branch,
            "threshold": threshold,
        },
        "summary": {
            "candidate": repo_urls[0],
            "total_references": len(reference_urls),
            "suspicious_references": len([r for r in comparison_results if r['suspicious']]),
            "total_file_pairs_compared": sum(len(r['file_pairs']) for r in comparison_results),
        },
        "verdict": verdict,
        "confidence": overall_confidence,
        "comparisons": comparison_results,
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
    
    for i in range(n):
        matrix[i][i] = 1.0
    
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


def _validate_dependencies():
    """Validate all required dependencies are installed."""
    try:
        import torch
        import sentence_transformers
        import git
        logger.info("All dependencies validated successfully")
        return True
    except ImportError as e:
        logger.error(f"Missing required dependency: {str(e)}")
        logger.error("Please install requirements: pip install -r requirements.txt")
        return False


if __name__ == "__main__":
    logger.info("Starting Plagiarism Detection Application")
    
    # Validate dependencies before starting
    if not _validate_dependencies():
        logger.error("Failed to start: Missing dependencies")
        exit(1)
    
    app.run(debug=True, host="0.0.0.0", port=5000)
