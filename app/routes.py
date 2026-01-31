from flask import Blueprint, render_template, request, send_from_directory
import os

from .services.report_generator import generate_report

main = Blueprint("main", __name__)

@main.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        repo_urls = request.form["repo_urls"].splitlines()
        language = request.form["language"]
        threshold = float(request.form["threshold"])

        data = generate_report(repo_urls, language, threshold)
        return render_template("details.html", data=data)

    return render_template("index.html")


@main.route("/download/<filename>")
def download_file(filename):
    reports_dir = os.path.abspath("data/reports")
    return send_from_directory(reports_dir, filename, as_attachment=True)
