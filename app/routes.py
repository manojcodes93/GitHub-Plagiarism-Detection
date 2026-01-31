from flask import Blueprint, render_template, request, send_file
from .services.report_generator import generate_report

main = Blueprint("main", __name__)

LAST_REPORT = {}


@main.route("/", methods=["GET", "POST"])
def index():
    global LAST_REPORT

    if request.method == "POST":
        repo_urls = request.form["repo_urls"].splitlines()
        language = request.form["language"]
        threshold = float(request.form["threshold"])

        data = generate_report(repo_urls, language, threshold)
        LAST_REPORT = data

        return render_template("details.html", data=data)

    return render_template("index.html")


@main.route("/compare")
def compare_view():
    if not LAST_REPORT:
        return "Run analysis first"

    return render_template(
        "compare.html",
        left_html=LAST_REPORT["code_left"],
        right_html=LAST_REPORT["code_right"]
    )


@main.route("/download/<type>")
def download_report(type):
    if type == "csv":
        return send_file("data/reports/plagiarism_report.csv", as_attachment=True)
    if type == "pdf":
        return send_file("data/reports/plagiarism_report.pdf", as_attachment=True)

    return "Invalid type"
