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
        
        # Process analysis in background thread with comprehensive error handling
        def run_analysis():
            """Run analysis with guaranteed state transitions and error capture."""
            try:
                results = _perform_analysis(repos, language, branch, threshold, job_id)
                jobs[job_id]["status"] = "completed"
                jobs[job_id]["results"] = results
                jobs[job_id]["progress"] = 100
                logger.info(f"Job {job_id} completed successfully")
            
            except Exception as e:
                logger.error(f"Analysis failed for job {job_id}: {str(e)}", exc_info=True)
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = str(e)
                jobs[job_id]["progress"] = 0  # Reset to terminal state
                
                # Ensure cleanup on failure
                try:
                    git_analyzer.clean_up()
                except Exception as cleanup_err:
                    logger.warning(f"Cleanup failed: {cleanup_err}")
        
        # Start thread (daemon=False to ensure proper shutdown)
        thread = threading.Thread(target=run_analysis, daemon=False)
        thread.start()
        
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
    Perform full plagiarism analysis with guaranteed repository lifecycle.
    
    Pipeline:
    1. Clone repos
    2. Extract commits (cached in memory)
    3. Extract source files
    4. Preprocess code
    5. Generate embeddings
    6. Delete cloned repos (repos no longer needed)
    7. Compute similarity using embeddings
    8. Perform commit-level analysis using cached commit data
    9. LLM reasoning
    10. Generate report
    """
    logger.info(f"Starting analysis job {job_id} for {len(repo_urls)} repositories (candidate + references)")

    jobs[job_id]["status"] = "running"
    jobs[job_id]["progress"] = 1
    
    cloned_paths = {}
    all_commits = {}  # Cache commits before deletion
    
    try:
        # Step 1: Clone repositories
        logger.info("Step 1: Cloning repositories...")
        for i, url in enumerate(repo_urls):
            jobs[job_id]["progress"] = int(5 + (i / len(repo_urls)) * 10)
            try:
                path = git_analyzer.clone_repository(url, branch)
                cloned_paths[url] = path
                logger.info(f"Cloned {url} to {path}")
            except Exception as e:
                logger.error(f"Failed to clone {url}: {str(e)}")
                raise RuntimeError(f"Clone failed for {url}: {str(e)}")

        # Step 2: Extract and cache commits BEFORE deletion
        logger.info("Step 2: Extracting commits from all repositories...")
        for i, url in enumerate(repo_urls):
            jobs[job_id]["progress"] = int(15 + (i / len(repo_urls)) * 5)
            try:
                if url not in cloned_paths:
                    logger.warning(f"Skipping commits for {url}: not cloned")
                    all_commits[url] = []
                    continue
                
                commits = git_analyzer.extract_commits(cloned_paths[url], limit=50)
                if not commits:
                    logger.warning(f"No commits found for {url}")
                    commits = []
                
                all_commits[url] = commits
                logger.info(f"Extracted {len(commits)} commits from {url}")
            except Exception as e:
                logger.warning(f"Failed to extract commits for {url}: {str(e)}")
                all_commits[url] = []  # Continue with empty commits
        
        # Step 3: Extract source files for target language
        logger.info("Step 3: Extracting source code files...")
        all_files = {}
        for i, url in enumerate(cloned_paths.items()):
            jobs[job_id]["progress"] = int(20 + (i / len(cloned_paths)) * 10)
            url_key, path = url
            try:
                files = git_analyzer.extract_code_files(path, language)
                if not files:
                    logger.warning(f"No {language} files found for {url_key}")
                    continue

                MAX_FILES = 40
                files = dict(list(files.items())[:MAX_FILES])
                all_files[url_key] = files
                logger.info(f"Extracted {len(files)} {language} files from {url_key}")
            except Exception as e:
                logger.error(f"Failed to extract files from {url_key}: {str(e)}")
                raise RuntimeError(f"File extraction failed for {url_key}: {str(e)}")

        if len(all_files) < 2:
            raise RuntimeError("Not enough repositories with valid source files")
        
        # Step 4: Preprocess code
        logger.info("Step 4: Preprocessing code...")
        preprocessed_files = {}
        for i, (url, files) in enumerate(all_files.items()):
            jobs[job_id]["progress"] = int(30 + (i / len(all_files)) * 10)
            try:
                preprocessed = CodePreprocessor.preprocess_files(files, language, aggressive=True)
                preprocessed_files[url] = preprocessed
                logger.info(f"Preprocessed {len(preprocessed)} files from {url}")
            except Exception as e:
                logger.error(f"Preprocessing failed for {url}: {str(e)}")
                raise RuntimeError(f"Preprocessing failed for {url}: {str(e)}")
        
        # Step 5: Generate embeddings
        logger.info("Step 5: Generating embeddings...")
        all_embeddings = {}
        for i, (url, files) in enumerate(preprocessed_files.items()):
            jobs[job_id]["progress"] = int(40 + (i / len(preprocessed_files)) * 20)
            try:
                if not files:
                    logger.warning(f"No files to embed for {url}")
                    all_embeddings[url] = {}
                    continue
                
                logger.info(f"Embedding {len(files)} files for {url}")
                embeddings = embedding_generator.embed_code_files(files)
                
                if not embeddings:
                    logger.warning(f"No embeddings generated for {url}")
                    embeddings = {}
                
                all_embeddings[url] = embeddings
                logger.info(f"Generated {len(embeddings)} embeddings for {url}")
            except Exception as e:
                logger.error(f"Embedding failed for {url}: {str(e)}")
                raise RuntimeError(f"Embedding failed for {url}: {str(e)}")

        # Step 6: Delete cloned repositories (all data extracted and cached)
        logger.info("Step 6: Cleaning up cloned repositories...")
        jobs[job_id]["progress"] = 60
        try:
            git_analyzer.clean_up()
            logger.info("Cloned repositories cleaned up successfully")
        except Exception as e:
            logger.warning(f"Cleanup incomplete: {str(e)}")
            # Continue anyway; data is already cached
        
        # Step 7: Compute similarity between candidate -> each reference
        logger.info("Step 7: Computing file-level similarity...")
        jobs[job_id]["progress"] = 65
        comparison_results = []
        repo_list = list(all_embeddings.keys())

        # Candidate is the first repo
        candidate_url = repo_urls[0]
        if candidate_url not in all_embeddings:
            raise RuntimeError(f"Candidate {candidate_url} has no files in selected language")

        reference_urls = [u for u in repo_urls[1:] if u in all_embeddings]
        if not reference_urls:
            raise RuntimeError("No reference repositories with valid source files")

        for idx, ref_url in enumerate(reference_urls):
            jobs[job_id]["progress"] = int(65 + (idx / max(1, len(reference_urls))) * 10)

            try:
                # Defensive: ensure embeddings exist
                if not all_embeddings.get(candidate_url) or not all_embeddings.get(ref_url):
                    logger.warning(f"Skipping comparison: missing embeddings for {candidate_url} or {ref_url}")
                    continue

                # Compare files
                file_comparisons = similarity_analyzer.compare_files(
                    all_embeddings[candidate_url],
                    all_embeddings[ref_url],
                    preprocessed_files[candidate_url],
                    preprocessed_files[ref_url],
                    threshold
                )

                # Compute repo similarity
                repo_similarity = similarity_analyzer.compute_repository_similarity(
                    all_embeddings[candidate_url],
                    all_embeddings[ref_url]
                )
                
                logger.info(f"Repo similarity {candidate_url} → {ref_url}: {repo_similarity:.3f}")

                # Step 8: Commit-level analysis using CACHED commit data
                commit_flags = []
                try:
                    candidate_commits = all_commits.get(candidate_url, [])
                    ref_commits = all_commits.get(ref_url, [])

                    if not candidate_commits or not ref_commits:
                        logger.debug(f"Skipping commit analysis: insufficient commit data")
                    else:
                        # Extract commit diffs on-demand (but we have commit metadata)
                        cand_diff_texts = []
                        ref_diff_texts = []
                        
                        for c in candidate_commits[:10]:  # Limit to 10
                            msg = c.get('message', '').strip()
                            if msg:
                                cand_diff_texts.append(msg)
                        
                        for r in ref_commits[:10]:  # Limit to 10
                            msg = r.get('message', '').strip()
                            if msg:
                                ref_diff_texts.append(msg)

                        if cand_diff_texts and ref_diff_texts:
                            # Lightweight commit message analysis (not full diffs)
                            cand_emb = embedding_generator.embed_commit_diffs(cand_diff_texts)
                            ref_emb = embedding_generator.embed_commit_diffs(ref_diff_texts)

                            if cand_emb is not None and ref_emb is not None and len(cand_emb) > 0 and len(ref_emb) > 0:
                                for i_c, ce in enumerate(cand_emb):
                                    best = 0.0
                                    for re in ref_emb:
                                        sim = similarity_analyzer.cosine_similarity(ce, re)
                                        best = max(best, sim)

                                    if best >= 0.85:
                                        commit_flags.append({
                                            "candidate_commit_index": i_c,
                                            "best_similarity": best,
                                            "reason": "High commit message similarity"
                                        })

                        # Check for identical commit messages
                        for c in candidate_commits[:20]:
                            for r in ref_commits[:20]:
                                c_msg = c.get('message', '').strip()
                                r_msg = r.get('message', '').strip()
                                if c_msg and c_msg == r_msg:
                                    commit_flags.append({
                                        "candidate_commit": c.get('hash', 'unknown'),
                                        "reference_commit": r.get('hash', 'unknown'),
                                        "reason": "Identical commit messages"
                                    })

                except Exception as e:
                    logger.debug(f"Commit-level checks skipped: {e}")

                comparison_results.append({
                    "candidate": candidate_url,
                    "reference": ref_url,
                    "repo_similarity": float(repo_similarity),
                    "file_pairs": file_comparisons,
                    "commit_flags": commit_flags,
                    "suspicious": float(repo_similarity) > threshold or bool(commit_flags)
                })
                
            except Exception as e:
                logger.error(f"Comparison failed for {ref_url}: {str(e)}")
                raise RuntimeError(f"Comparison failed: {str(e)}")
        
        # Step 9: LLM reasoning on flagged references
        logger.info("Step 9: Performing LLM-based reasoning...")
        jobs[job_id]["progress"] = 80
        flagged_refs = [r for r in comparison_results if r["suspicious"]]

        for pair in flagged_refs:
            try:
                # Defensive: ensure file pairs exist
                file_pairs_to_judge = pair.get("file_pairs", [])
                if not file_pairs_to_judge:
                    logger.debug(f"No file pairs to judge for {pair['reference']}")
                    pair["file_judgments"] = []
                    pair["explanation"] = "No similar files detected for detailed analysis"
                    continue

                judgments = llm_reasoner.batch_judge_files(file_pairs_to_judge[:5])
                pair["file_judgments"] = judgments
                pair["explanation"] = llm_reasoner.generate_plagiarism_explanation(
                    pair["candidate"].split("/")[-1],
                    pair["reference"].split("/")[-1],
                    file_pairs_to_judge,
                    pair["repo_similarity"]
                )
            except Exception as e:
                logger.warning(f"LLM reasoning failed: {str(e)}")
                pair["file_judgments"] = []
                pair["explanation"] = f"Analysis unavailable: {str(e)}"
        
        # Step 10: Generate final report
        logger.info("Step 10: Generating report...")
        jobs[job_id]["progress"] = 95
        
        max_similarity = max((r['repo_similarity'] for r in comparison_results), default=0.0)
        overall_confidence = min(0.95, float(max_similarity) + 0.05)
        verdict = "No plagiarism detected" if float(max_similarity) < threshold else "Potential plagiarism detected"

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
            "confidence": float(overall_confidence),
            "comparisons": comparison_results,
        }
        
        # Save report
        _save_report(report)
        
        jobs[job_id]["progress"] = 100
        logger.info(f"Analysis complete for job {job_id}: {verdict}")
        
        return report
    
    except Exception as e:
        logger.error(f"Critical analysis error: {str(e)}", exc_info=True)
        # Ensure cleanup on error
        try:
            git_analyzer.clean_up()
        except Exception:
            pass
        # Re-raise to be caught by run_analysis()
        raise


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
    
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)

