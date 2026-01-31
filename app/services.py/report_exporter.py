import csv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

REPORT_DIR = "data/reports"
os.makedirs(REPORT_DIR, exist_ok=True)

def generate_csv_report(suspicious_commits):
    csv_path = os.path.join(REPORT_DIR, "plagiarism_report.csv")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Commit Message A", "Commit Message B", "Similarity"])

        for item in suspicious_commits:
            writer.writerow([
                item["commit_1"],
                item["commit_2"],
                item["similarity"]
            ])

    return csv_path


def generate_pdf_report(suspicious_commits):
    pdf_path = os.path.join(REPORT_DIR, "plagiarism_report.pdf")

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "GitHub Plagiarism Detection Report")

    c.setFont("Helvetica", 10)
    y = height - 90

    if not suspicious_commits:
        c.drawString(50, y, "No suspicious commit similarities detected.")
    else:
        for item in suspicious_commits:
            text = (
                f"Similarity: {item['similarity']} | "
                f"A: {item['commit_1'][:60]} | "
                f"B: {item['commit_2'][:60]}"
            )
            c.drawString(50, y, text)
            y -= 15

            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = height - 50

    c.save()
    return pdf_path
