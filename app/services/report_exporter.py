import csv
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


REPORT_DIR = os.path.join("app", "data", "reports")
os.makedirs(REPORT_DIR, exist_ok=True)


# --------------------------------------------------
# CSV EXPORT
# --------------------------------------------------

def generate_csv_report(rows):
    path = os.path.join(REPORT_DIR, "plagiarism_report.csv")

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not rows:
            writer.writerow(["No suspicious commits found"])
            return path

        first = rows[0]

        # -------- CASE A — new format (5 columns) --------
        if len(first) == 5:
            writer.writerow([
                "Repo A",
                "Commit A",
                "Repo B",
                "Commit B",
                "Similarity"
            ])
            for row in rows:
                writer.writerow(row)

        # -------- CASE B — old format (3 columns) --------
        elif len(first) == 3:
            writer.writerow([
                "Commit A",
                "Commit B",
                "Similarity"
            ])
            for row in rows:
                writer.writerow(row)

        # -------- fallback --------
        else:
            writer.writerow(["Row Data"])
            for row in rows:
                writer.writerow([str(row)])

    return path


# --------------------------------------------------
# PDF EXPORT
# --------------------------------------------------

def generate_pdf_report(rows):
    path = os.path.join(REPORT_DIR, "plagiarism_report.pdf")

    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter

    y = height - 40
    c.setFont("Helvetica", 10)

    if not rows:
        c.drawString(40, y, "No suspicious commits found")
        c.save()
        return path

    for row in rows:
        text = " | ".join(str(x)[:80] for x in row)
        c.drawString(40, y, text)
        y -= 18

        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 40

    c.save()
    return path
