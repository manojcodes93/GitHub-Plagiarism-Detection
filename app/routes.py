from flask import Blueprint, render_template, request, send_file
from app.services.report_generator import generate_report

main = Blueprint("main", __name__)

@main.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        repo_urls = request.form.get("repo_urls").splitlines()
        language = request.form.get("language")
        threshold = float(request.form.get("threshold"))

        data = generate_report(repo_urls, language, threshold)
        return render_template("details.html", data=data)

    return render_template("index.html")


@main.route("/download/csv")
def download_csv():
    return send_file(
        "data/reports/plagiarism_report.csv",
        as_attachment=True
    )


@main.route("/download/pdf")
def download_pdf():
    return send_file(
        "data/reports/plagiarism_report.pdf",
        as_attachment=True
    )
