import uuid
import os
from pathlib import Path
from flask import Flask, request, jsonify, render_template, make_response, send_file
from src.chat import ask
from src.web.history import ensure_db, save_message, get_history, find_cached_answer, save_cached_answer
from src.ingest import ingest_pdfs
from simple.gen_ai import get_llm
from simple.consult import save_patient, save_consultation, doctor_response, save_consultation_pdf

app = Flask(__name__, template_folder="templates", static_folder="static")
ensure_db()
DATA_PATH = os.getenv("DATA_PATH", str(Path(__file__).resolve().parents[2] / "Data"))
chatbot = get_llm(DATA_PATH)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get_answer", methods=["POST"])
def get_answer():
    question = request.form.get("question") or (request.json or {}).get("question") or ""
    session_id = request.cookies.get("sid") or str(uuid.uuid4())
    cached = find_cached_answer(question)
    if cached:
        resp = make_response(jsonify({"answer": cached, "cached": True}))
        resp.set_cookie("sid", session_id)
        return resp
    history = get_history(session_id)
    try:
        answer = ask(question, history)
    except Exception as e:
        app.logger.error(f"Error during ask: {e}")
        return jsonify({"answer": f"Error: {str(e)}"}), 500
    save_message(session_id, "user", question)
    save_message(session_id, "bot", answer)
    save_cached_answer(question, answer)
    resp = make_response(jsonify({"answer": answer, "cached": False}))
    resp.set_cookie("sid", session_id)
    return resp

@app.post("/ingest")
def ingest():
    try:
        ingest_pdfs()
        return jsonify({"status": "ok"})
    except Exception as e:
        app.logger.error(f"Error during ingest: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.post("/consult")
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
    storage = Path(__file__).resolve().parents[2] / "storage"
    if not storage.exists():
        return jsonify({"error": "No report found"}), 404
    pdfs = sorted(storage.glob("consult_*.pdf"), reverse=True)
    if not pdfs:
        return jsonify({"error": "No report found"}), 404
    return send_file(pdfs[0].as_posix(), as_attachment=True)

def run():
    app.run(host="127.0.0.1", port=5000, debug=True)

if __name__ == "__main__":
    run()
