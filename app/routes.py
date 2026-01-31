from flask import Blueprint, render_template, request
from app.services.github_service import clone_repositories
from app.services.report_generator import generate_report

main = Blueprint("main", __name__)

@main.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        repo_urls = request.form.get("repo_urls").splitlines()
        language = request.form.get("language")
        threshold = float(request.form.get("threshold"))

        analysis_data = generate_report(repo_urls, language, threshold)
        return render_template("dashboard.html", data=analysis_data)

    return render_template("index.html")