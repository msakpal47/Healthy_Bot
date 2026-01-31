from flask import Flask, request, jsonify, render_template, send_file
from pathlib import Path
import os
import sys

# Core logic imports
from core.gen_ai import get_llm
from core.consult import save_patient, save_consultation, doctor_response, save_consultation_pdf

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = os.getenv("DATA_PATH", str(BASE_DIR / "Data"))
STORAGE_PATH = BASE_DIR / "storage"

# Initialize Chatbot
print(f"Loading LLM from {DATA_PATH}...")
chatbot = get_llm(DATA_PATH)
print("LLM loaded.")

app = Flask(__name__, template_folder="templates", static_folder="static", static_url_path="/static")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get_answer", methods=["POST"])
def get_answer():
    q = request.form.get("question") or (request.json or {}).get("question") or ""
    ans = chatbot.invoke({"question": q, "chat_history": []})
    return jsonify({"answer": ans})

@app.route("/consult", methods=["POST"])
def consult():
    try:
        payload = request.json or {}
        patient = {
            "name": payload.get("name",""),
            "age": int(payload.get("age",0)),
            "gender": payload.get("gender",""),
            "symptoms": payload.get("symptoms",""),
            "disease": payload.get("disease",""),
            "severity": payload.get("severity",""),
            "duration": payload.get("duration",""),
        }
        # Pass STORAGE_PATH if needed, or rely on core.consult defaults (which might need update)
        save_patient(patient)
        reply = doctor_response(patient, chatbot)
        save_consultation(reply)
        
        pdf_path = ""
        try:
            pdf_path = save_consultation_pdf(patient, reply)
        except Exception as e:
            app.logger.error(f"PDF generation failed: {e}")
            pdf_path = "Error generating PDF"

        return jsonify({"reply": reply, "pdf": str(pdf_path)})
    except Exception as e:
        app.logger.error(f"/consult failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.get("/download-report")
def download_report():
    if not STORAGE_PATH.exists():
        return jsonify({"error": "No report found"}), 404
    pdfs = sorted(STORAGE_PATH.glob("consult_*.pdf"), reverse=True)
    if not pdfs:
        return jsonify({"error": "No report found"}), 404
    return send_file(pdfs[0].as_posix(), as_attachment=True)

def run():
    app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    run()
