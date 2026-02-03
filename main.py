from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
import google.generativeai as genai
from PyPDF2 import PdfReader
import json
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Gemini AI setup
genai.configure(api_key=os.getenv("api"))
model = genai.GenerativeModel("models/gemini-flash-latest")

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

@app.route("/", methods=["GET", "POST"])
def index():
    result = None

    if request.method == "POST":
        resume = request.files.get("resume")

        if resume and resume.filename.endswith(".pdf"):
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], resume.filename)
            resume.save(filepath)

            resume_text = extract_text_from_pdf(filepath)

            # Prompt for Gemini AI
            prompt = f"""
You are an ATS Resume Analyzer.
Return ONLY valid JSON with the following keys:
{{
  "ats": number,
  "matched": [string],
  "missing": [string],
  "extra": [string],
  "suggestions": [string]
}}
Resume Text:
{resume_text}
"""

            response = model.generate_content(prompt)

            # Try to parse JSON from Gemini
            try:
                clean_text = response.text.strip()
                clean_text = re.sub(r"```json|```", "", clean_text)
                result = json.loads(clean_text)
            except Exception as e:
                print("JSON Parse Error:", e)
                print("Raw Response:", response.text)
                result = {
                    "ats": 0,
                    "matched": [],
                    "missing": [],
                    "extra": [],
                    "suggestions": ["Unable to analyze resume properly"]
                }

    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)