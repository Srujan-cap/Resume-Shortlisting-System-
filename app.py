from flask import Flask, render_template, request
import re
import pdfplumber
import os

app = Flask(__name__)

UPLOAD_FOLDER = "resume_uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("form.html")

# Global lists
priority_list = []
shortlisted = []
not_selected = []

# ---------------- ANALYZE ----------------
@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/analyze", methods=["GET", "POST"])
def analyze():

    # ✅ FIX 1: Prevent direct access
    if request.method == "GET":
        return "⚠️ Please submit the form from home page"

    try:
        # ✅ FIX 2: Safe access (prevents 400 error)
        file = request.files.get("resume")
        skills_input = request.form.get("skills")

        if not file or file.filename == "":
            return "❌ No file selected"

        if not skills_input:
            return "❌ Skills input missing"

        # Save file
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)

        resume_data = ""

        # TXT
        if file.filename.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                resume_data = f.read()

        # PDF
        elif file.filename.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf_file:
                for page in pdf_file.pages:
                    text = page.extract_text()
                    if text:
                        resume_data += text
        else:
            return "❌ Only .txt and .pdf allowed"

        resume_data = resume_data.lower()
        skills_input = skills_input.lower()

        required_skills = [skill.strip() for skill in skills_input.split(",") if skill.strip()]
        total_skills = len(required_skills)

        matched_skills = 0
        results = []

        for skill in required_skills:
            pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"

            if re.search(pattern, resume_data):
                results.append((skill, "✅ Found"))
                matched_skills += 1
            else:
                results.append((skill, "❌ Not Found"))

        score = (matched_skills / total_skills) * 100 if total_skills > 0 else 0

        # Classification
        if score > 90:
            status = "🔥 Priority Candidate"
            priority_list.append([file.filename, score])
        elif score >= 70:
            status = "✅ Shortlisted"
            shortlisted.append([file.filename, score])
        else:
            status = "❌ Not Selected"
            not_selected.append([file.filename, score])

        return render_template(
            "result.html",
            results=results,
            matched=matched_skills,
            total=total_skills,
            score=round(score, 2),
            status=status,
            filename=file.filename
        )

    except Exception as e:
        return f"❌ Error: {e}"

# ---------------- DATA ----------------
@app.route("/data")
def results():
    return render_template(
        "resume_data.html",
        priority=priority_list,
        short_listed=shortlisted,
        not_selected=not_selected
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)