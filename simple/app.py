from flask import Flask, request, jsonify, render_template, send_file
from pathlib import Path
import os
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from simple.gen_ai import get_llm
from simple.consult import save_patient, save_consultation, doctor_response, save_consultation_pdf

DATA_PATH = os.getenv("DATA_PATH", str(Path(__file__).resolve().parents[1] / "Data"))
chatbot = get_llm(DATA_PATH)

app = Flask(__name__, template_folder="../src/web/templates", static_folder="../src/web/static")

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
        save_patient(patient)
        reply = doctor_response(patient, chatbot)
        save_consultation(reply)
        pdf_path = save_consultation_pdf(patient, reply)
        return jsonify({"reply": reply, "pdf": str(pdf_path)})
    except Exception as e:
        app.logger.error(f"/consult failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.get("/download-report")
def download_report():
    # Serve the most recent generated consultation PDF
    storage = Path(__file__).resolve().parents[1] / "storage"
    if not storage.exists():
        return jsonify({"error": "No report found"}), 404
    pdfs = sorted(storage.glob("consult_*.pdf"), reverse=True)
    if not pdfs:
        return jsonify({"error": "No report found"}), 404
    return send_file(pdfs[0].as_posix(), as_attachment=True)

def run():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    run()
