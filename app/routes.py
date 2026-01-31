from flask import Blueprint, render_template, request, send_file, redirect, url_for
import os

from .services.report_generator import generate_report

main = Blueprint("main", __name__)

LAST_REPORT = {}


# -------------------------
# Dashboard
# -------------------------
@main.route("/")
def dashboard():
    return render_template("dashboard.html")


# -------------------------
# Analyze page
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

        global LAST_REPORT
        LAST_REPORT = data

        return render_template("details.html", data=data)

    return render_template("analyze.html")


# -------------------------
# Results hub (NEW — safe empty state)
# -------------------------
@main.route("/results")
def results_home():
    return render_template("details.html", data=LAST_REPORT)


# -------------------------
# Commit similarity
# -------------------------
@main.route("/commit-diff")
def commit_diff_page():
    return render_template(
        "commit_diff.html",
        rows=LAST_REPORT.get("suspicious_commits", [])
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
# Side by side compare (SAFE EMPTY STATE)
# -------------------------
@main.route("/compare")
def compare_view():
    return render_template(
        "compare.html",
        left_html=LAST_REPORT.get("code_left", "<p>No comparison yet</p>"),
        right_html=LAST_REPORT.get("code_right", "<p>No comparison yet</p>")
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
