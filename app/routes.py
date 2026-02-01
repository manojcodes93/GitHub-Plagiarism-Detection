from flask import Blueprint, render_template, request, send_file, redirect, url_for
import os

from .services.report_generator import generate_report
from .services.code_diff import generate_side_by_side_diff

main = Blueprint("main", __name__)

LAST_REPORT = {}
ANALYSIS_ACTIVE = False

# -------------------------
# Dashboard
# -------------------------
@main.route("/")
def dashboard():
    global LAST_REPORT, ANALYSIS_ACTIVE
    LAST_REPORT = {}
    ANALYSIS_ACTIVE = False
    return render_template("dashboard.html")

# -------------------------
# Analyze
# -------------------------
@main.route("/analyze", methods=["GET", "POST"])
def analyze():

    if request.method == "POST":
        repo_urls = request.form.getlist("repo_urls[]")
        language = request.form.get("language", ".py")
        threshold = float(request.form.get("threshold", 0.8))

        repo_urls = [r.strip() for r in repo_urls if r.strip()]
        if not repo_urls:
            return redirect(url_for("main.analyze"))

        data = generate_report(repo_urls, language, threshold)

        # store threshold for templates
        data["threshold"] = threshold

        global LAST_REPORT, ANALYSIS_ACTIVE
        LAST_REPORT = data
        ANALYSIS_ACTIVE = True

        return redirect(url_for("main.results_home"))

    return render_template("analyze.html")

# -------------------------
# Results hub
# -------------------------
@main.route("/results")
def results_home():
    if not ANALYSIS_ACTIVE or not LAST_REPORT:
        return render_template(
            "details.html",
            empty=True
        )

    return render_template(
        "details.html",
        empty=False,
        data=LAST_REPORT
    )


# -------------------------
# Commit similarity (FIXED)
# -------------------------
@main.route("/commit-diff")
def commit_diff_page():
    return render_template(
        "commit_diff.html",
        rows=LAST_REPORT.get("suspicious_commits_with_repo", []),
        threshold=LAST_REPORT.get("threshold", 0.8)
    )

# -------------------------
# Repo matrix
# -------------------------
@main.route("/repo-matrix")
def repo_matrix_page():
    return render_template(
        "repo_matrix.html",
        names=LAST_REPORT.get("matrix_names", []),
        matrix=LAST_REPORT.get("similarity_matrix", [])
    )

# -------------------------
# Side-by-side compare
# -------------------------
@main.route("/compare")
def compare_view():

    left_html = LAST_REPORT.get("code_left")
    right_html = LAST_REPORT.get("code_right")

    if not left_html or not right_html:
        left_html = "<p>No comparison data yet</p>"
        right_html = "<p>No comparison data yet</p>"

    return render_template(
        "compare.html",
        left_html=left_html,
        right_html=right_html
    )

# -------------------------
# Downloads
# -------------------------
@main.route("/download/<type>")
def download_report(type):

    if type == "csv":
        path = LAST_REPORT.get("csv_report")
    elif type == "pdf":
        path = LAST_REPORT.get("pdf_report")
    else:
        return redirect(url_for("main.dashboard"))

    if not path:
        return "Report not generated yet."

    path = os.path.abspath(path)

    if not os.path.exists(path):
        return "Report file missing."

    return send_file(path, as_attachment=True)
