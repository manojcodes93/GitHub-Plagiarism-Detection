import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uuid
import json
import shutil
import logging
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import analyzers
from analyzer.github import GitHubAnalyzer
from analyzer.embeddings import EmbeddingGenerator
from analyzer.similarity import SimilarityAnalyzer
from analyzer.llm_reasoner import LLMReasoner
from analyzer.preprocess import CodePreprocessor

# Determine root directory (parent of backend)
ROOT_DIR = Path(__file__).parent.parent
TEMPLATE_DIR = ROOT_DIR / 'templates'
STATIC_DIR = ROOT_DIR / 'static'

app = Flask(__name__, template_folder=str(TEMPLATE_DIR), static_folder=str(STATIC_DIR))

# Global job storage (in-memory)
jobs = {}
jobs_lock = threading.Lock()

# Report output directory
REPORT_DIR = Path(__file__).parent / 'reports'
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def generate_job_id():
    """Generate unique job ID."""
    return str(uuid.uuid4())


def update_job_status(job_id, status, progress=None, data=None, error=None):
    """Thread-safe job status update."""
    with jobs_lock:
        if job_id in jobs:
            jobs[job_id]['status'] = status
            jobs[job_id]['timestamp'] = datetime.now().isoformat()
            if progress is not None:
                jobs[job_id]['progress'] = progress
            if data is not None:
                jobs[job_id]['data'] = data
            if error is not None:
                jobs[job_id]['error'] = error
            logger.info(f"Job {job_id}: {status} (progress: {progress})")


def cleanup_temp_directories(*paths):
    """Safely clean up temporary directories."""
    for path in paths:
        if path and Path(path).exists():
            try:
                logger.info(f"Cleaning up {path}")
                shutil.rmtree(path, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Failed to clean {path}: {e}")


def _perform_analysis(repositories, language, branch, threshold, job_id):
    """
    Perform plagiarism analysis.
    
    Expected format:
    {
        "candidate": {"url": "...", "branch": "..."},
        "references": [{"url": "...", "branch": "..."}, ...]
    }
    """
    temp_dirs = []
    try:
        logger.info(f"Job {job_id}: Starting analysis with {len(repositories['references'])} reference repos")
        update_job_status(job_id, 'analyzing', progress=0)
        
        # Step 1: Clone candidate repo
        logger.info(f"Job {job_id}: Step 1 - Cloning candidate repository")
        update_job_status(job_id, 'analyzing', progress=5)
        
        git_analyzer = GitHubAnalyzer()
        candidate_url = repositories['candidate']['url']
        candidate_branch = repositories['candidate'].get('branch', 'main')
        
        candidate_path = git_analyzer.clone_repository(candidate_url, candidate_branch)
        temp_dirs.append(candidate_path)
        logger.info(f"Job {job_id}: Cloned candidate from {candidate_url}")
        
        # Step 2: Clone reference repos
        logger.info(f"Job {job_id}: Step 2 - Cloning {len(repositories['references'])} reference repositories")
        update_job_status(job_id, 'analyzing', progress=10)
        
        reference_paths = {}
        for i, ref in enumerate(repositories['references']):
            ref_url = ref['url']
            ref_branch = ref.get('branch', 'main')
            ref_path = git_analyzer.clone_repository(ref_url, ref_branch)
            reference_paths[ref_url] = ref_path
            temp_dirs.append(ref_path)
            logger.info(f"Job {job_id}: Cloned reference {i+1}/{len(repositories['references'])} from {ref_url}")
            update_job_status(job_id, 'analyzing', progress=10 + (10 * (i + 1) / len(repositories['references'])))
        
        # Step 3: Extract commits before deleting repos
        logger.info(f"Job {job_id}: Step 3 - Extracting commits")
        update_job_status(job_id, 'analyzing', progress=21)
        
        candidate_commits = git_analyzer.extract_commits(candidate_path, limit=50)
        logger.info(f"Job {job_id}: Extracted {len(candidate_commits)} candidate commits")
        
        reference_commits = {}
        for ref_url, ref_path in reference_paths.items():
            commits = git_analyzer.extract_commits(ref_path, limit=50)
            reference_commits[ref_url] = commits
            logger.info(f"Job {job_id}: Extracted {len(commits)} commits from {ref_url}")
        
        # Step 4: Extract source files before deleting repos
        logger.info(f"Job {job_id}: Step 4 - Extracting source files")
        update_job_status(job_id, 'analyzing', progress=25)
        
        candidate_files = git_analyzer.extract_source_files(candidate_path, language)
        logger.info(f"Job {job_id}: Extracted {len(candidate_files)} source files from candidate")
        
        reference_files = {}
        for ref_url, ref_path in reference_paths.items():
            files = git_analyzer.extract_source_files(ref_path, language)
            reference_files[ref_url] = files
            logger.info(f"Job {job_id}: Extracted {len(files)} source files from {ref_url}")
        
        # CRITICAL: Clean up cloned repos BEFORE anything else (all data extracted)
        logger.info(f"Job {job_id}: Step 5 - Cleaning up temporary repositories")
        cleanup_temp_directories(*temp_dirs)
        temp_dirs = []  # Clear list since we cleaned them
        
        # Verify we have files to analyze
        if not candidate_files:
            raise RuntimeError(f"No {language} source files found in candidate repository")
        
        if not reference_files:
            raise RuntimeError(f"No {language} source files found in reference repositories")
        
        # Step 6: Preprocess code
        logger.info(f"Job {job_id}: Step 6 - Preprocessing code")
        update_job_status(job_id, 'analyzing', progress=30)
        
        preprocessor = CodePreprocessor()
        
        candidate_preprocessed = {
            name: preprocessor.preprocess(content)
            for name, content in candidate_files.items()
        }
        
        reference_preprocessed = {}
        for ref_url, files in reference_files.items():
            reference_preprocessed[ref_url] = {
                name: preprocessor.preprocess(content)
                for name, content in files.items()
            }
        
        logger.info(f"Job {job_id}: Preprocessing complete")
        
        # Step 7: Generate embeddings
        logger.info(f"Job {job_id}: Step 7 - Generating embeddings")
        update_job_status(job_id, 'analyzing', progress=35)
        
        embedding_gen = EmbeddingGenerator()
        
        candidate_embeddings = embedding_gen.embed_code_files(candidate_preprocessed)
        candidate_commit_embeddings = embedding_gen.embed_commit_diffs(candidate_commits)
        
        reference_embeddings = {}
        reference_commit_embeddings = {}
        for i, (ref_url, files) in enumerate(reference_preprocessed.items()):
            reference_embeddings[ref_url] = embedding_gen.embed_code_files(files)
            reference_commit_embeddings[ref_url] = embedding_gen.embed_commit_diffs(
                reference_commits[ref_url]
            )
            logger.info(f"Job {job_id}: Generated embeddings for reference {i+1}/{len(reference_preprocessed)}")
            update_job_status(job_id, 'analyzing', progress=35 + (10 * (i + 1) / len(reference_preprocessed)))
        
        # Step 8: Compare embeddings
        logger.info(f"Job {job_id}: Step 8 - Computing similarity scores")
        update_job_status(job_id, 'analyzing', progress=50)
        
        similarity_analyzer = SimilarityAnalyzer()
        comparisons = {}
        
        for i, ref_url in enumerate(reference_embeddings.keys()):
            # Compare file-level embeddings
            file_comparisons = similarity_analyzer.compare_files(
                candidate_embeddings,
                reference_embeddings[ref_url]
            )
            
            # Compute repository-level similarity
            repo_similarity = similarity_analyzer.compute_repository_similarity(
                file_comparisons
            )
            
            comparisons[ref_url] = {
                'files': file_comparisons,
                'repository_similarity': repo_similarity,
                'candidate_url': candidate_url,
                'reference_url': ref_url
            }
            
            logger.info(f"Job {job_id}: Repo similarity {ref_url}: {repo_similarity:.2f}")
            update_job_status(job_id, 'analyzing', progress=50 + (20 * (i + 1) / len(reference_embeddings)))
        
        # Step 9: LLM reasoning
        logger.info(f"Job {job_id}: Step 9 - Running plagiarism detection")
        update_job_status(job_id, 'analyzing', progress=75)
        
        llm_reasoner = LLMReasoner()
        plagiarism_reports = {}
        
        for ref_url, comparison in comparisons.items():
            file_judgments = {
                file_name: llm_reasoner.judge_file_similarity(
                    comparison['files'].get(file_name, 0)
                )
                for file_name in candidate_files.keys()
            }
            
            repo_judgment = llm_reasoner.judge_file_similarity(
                comparison['repository_similarity']
            )
            
            explanation = llm_reasoner.generate_plagiarism_explanation(
                comparison['repository_similarity'],
                file_judgments
            )
            
            plagiarism_reports[ref_url] = {
                'file_judgments': file_judgments,
                'repository_judgment': repo_judgment,
                'explanation': explanation,
                'similarity_score': comparison['repository_similarity']
            }
            
            logger.info(f"Job {job_id}: Plagiarism verdict for {ref_url}: {repo_judgment}")
        
        # Step 10: Generate final report
        logger.info(f"Job {job_id}: Step 10 - Generating final report")
        update_job_status(job_id, 'analyzing', progress=90)
        
        final_report = {
            'job_id': job_id,
            'timestamp': datetime.now().isoformat(),
            'candidate': {
                'url': candidate_url,
                'branch': candidate_branch,
                'files_count': len(candidate_files),
                'commits_count': len(candidate_commits)
            },
            'analysis_config': {
                'language': language,
                'threshold': threshold,
                'branch': branch,
                'total_references': len(repositories['references'])
            },
            'comparisons': comparisons,
            'plagiarism_reports': plagiarism_reports,
            'overall_plagiarism_verdict': 'PLAGIARISM DETECTED' if any(
                report.get('repository_judgment') == 'PLAGIARISM' 
                for report in plagiarism_reports.values()
            ) else 'CLEAN'
        }
        
        # Save report to JSON
        report_file = REPORT_DIR / f"report_{job_id}.json"
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        logger.info(f"Job {job_id}: Analysis complete. Report saved to {report_file}")
        update_job_status(job_id, 'completed', progress=100, data=final_report)
        
        return final_report
        
    except Exception as e:
        logger.error(f"Job {job_id}: Analysis failed - {str(e)}", exc_info=True)
        update_job_status(job_id, 'failed', error=str(e))
        cleanup_temp_directories(*temp_dirs)
        raise


def run_analysis(repositories, language, branch, threshold, job_id):
    """Wrapper to run analysis in background thread."""
    try:
        _perform_analysis(repositories, language, branch, threshold, job_id)
    except Exception as e:
        logger.error(f"Job {job_id}: Background thread exception: {str(e)}", exc_info=True)
        with jobs_lock:
            if job_id in jobs:
                jobs[job_id]['status'] = 'failed'
                jobs[job_id]['error'] = str(e)


# Routes
@app.route('/')
def index():
    """Serve main page."""
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Start analysis job."""
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('candidate') or not data.get('references'):
            return jsonify({'error': 'Missing candidate or references'}), 400
        
        references = data.get('references', [])
        if len(references) < 2 or len(references) > 10:
            return jsonify({'error': 'Please provide 2-10 reference repositories'}), 400
        
        language = data.get('language', 'python')
        branch = data.get('branch', 'main')
        threshold = float(data.get('threshold', 0.7))
        
        # Create job
        job_id = generate_job_id()
        with jobs_lock:
            jobs[job_id] = {
                'job_id': job_id,
                'status': 'queued',
                'progress': 0,
                'timestamp': datetime.now().isoformat(),
                'data': None,
                'error': None
            }
        
        # Start background thread
        thread = threading.Thread(
            target=run_analysis,
            args=(data, language, branch, threshold, job_id),
            daemon=True
        )
        thread.start()
        
        logger.info(f"Started job {job_id}")
        return jsonify({'job_id': job_id}), 200
        
    except Exception as e:
        logger.error(f"Error in /api/analyze: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/results/<job_id>', methods=['GET'])
def get_results(job_id):
    """Get job status and results."""
    with jobs_lock:
        if job_id not in jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job = jobs[job_id].copy()
    
    return jsonify(job), 200


@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all jobs."""
    with jobs_lock:
        job_list = list(jobs.values())
    
    return jsonify(job_list), 200


@app.route('/api/download/<job_id>', methods=['GET'])
def download_report(job_id):
    """Download JSON report."""
    report_file = REPORT_DIR / f"report_{job_id}.json"
    
    if not report_file.exists():
        return jsonify({'error': 'Report not found'}), 404
    
    try:
        return send_file(
            report_file,
            mimetype='application/json',
            as_attachment=True,
            download_name=f"plagiarism_report_{job_id}.json"
        )
    except Exception as e:
        logger.error(f"Error downloading report {job_id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting Plagiarism Detection Server")
    app.run(debug=False, host='127.0.0.1', port=5000, threaded=True, use_reloader=False)

