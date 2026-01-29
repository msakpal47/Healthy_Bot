import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import csv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

STORAGE_DIR = Path(__file__).resolve().parents[1] / "storage"
DATA_DIR = Path(__file__).resolve().parents[1] / "Data"
CSV_PATH = DATA_DIR / "100_unique_diseases.csv"

def ensure_storage() -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def _read_json(path: Path) -> List[Dict[str, Any]]:
    if path.exists():
        import json
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def _write_json(path: Path, data: List[Dict[str, Any]]) -> None:
    import json
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_patient(patient: Dict[str, Any]) -> None:
    ensure_storage()
    p = STORAGE_DIR / "patients.json"
    data = _read_json(p)
    data.append(patient)
    _write_json(p, data)

def save_consultation(record: Dict[str, Any]) -> Path:
    ensure_storage()
    p = STORAGE_DIR / "consultations.json"
    data = _read_json(p)
    data.append(record)
    _write_json(p, data)
    return p

def _load_diseases() -> List[Dict[str, str]]:
    if not CSV_PATH.exists():
        return []
    rows: List[Dict[str, str]] = []
    with open(CSV_PATH.as_posix(), newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if not r.get("Disease"):
                continue
            rows.append(r)
    return rows

def _match_disease(name: str, rows: List[Dict[str, str]]) -> Dict[str, str] | None:
    n = (name or "").strip().lower()
    if not n:
        return None
    # exact match only
    for r in rows:
        if r.get("Disease","").strip().lower() == n:
            return r
    return None

def _extract_field(text: str, key_words: List[str]) -> str:
    for kw in key_words:
        # simple pattern: line starting with keyword or contains keyword followed by colon
        m = re.search(rf"(?im)^{kw}\s*[:\-]\s*(.+)$", text)
        if m:
            return m.group(1).strip()
        m = re.search(rf"(?i){kw}\s*[:\-]\s*(.+?)(?:\n|$)", text)
        if m:
            return m.group(1).strip()
    return ""

def doctor_response(patient: Dict[str, Any], qa) -> Dict[str, Any]:
    # Prefer CSV dataset mapping if available
    diseases = _load_diseases()
    row = _match_disease(patient.get("disease",""), diseases)
    if row:
        adult = row.get("Adult Dose","") or row.get("Adult dose","")
        child = row.get("Child Dose","") or row.get("Child dose","")
        dose = adult if int(patient.get("age", 0)) >= 18 else (child or adult)
        return {
            "date": datetime.now().isoformat(),
            "patient_name": patient.get("name",""),
            "disease": row.get("Disease",""),
            "medicine": row.get("Medicine",""),
            "dose": dose,
            "tests": row.get("Tests",""),
            "warning": row.get("Warnings",""),
            "home_remedy": row.get("Home Care",""),
        }
    # Fallback to retrieval from PDFs (guard if db unavailable)
    query = f"{patient.get('disease','')} {patient.get('symptoms','')}".strip()
    docs = []
    try:
        if getattr(qa, "db", None):
            docs = qa.db.similarity_search(query or "general health", k=3)
    except Exception:
        docs = []
    merged = "\n\n".join(d.page_content for d in docs)
    medicine = _extract_field(merged, ["medicine", "medicines", "drug"])
    tests = _extract_field(merged, ["tests", "investigation", "diagnostics"])
    warning = _extract_field(merged, ["warning", "caution", "contraindication"])
    home = _extract_field(merged, ["home remedy", "home treatment", "self care"])
    dose_adult = _extract_field(merged, ["adult dose", "dose (adult)", "dosage (adult)"])
    dose_child = _extract_field(merged, ["child dose", "dose (child)", "dosage (child)"])
    dose = dose_adult if int(patient.get("age", 0)) >= 18 else dose_child or dose_adult
    # Heuristic defaults for common 'fever' presentation
    if "fever" in (patient.get("symptoms","").lower()):
        if not medicine or ("supportive" in medicine.lower()):
            medicine = "Paracetamol, ORS for hydration"
    if not tests and "fever" in (patient.get("symptoms","").lower()):
        tests = "CBC, Platelet count, NS1 antigen"
    if not home:
        home = "Drink plenty of fluids; Paracetamol only (NO NSAIDs)"
    if not warning:
        warning = "Bleeding; Severe abdominal pain; Persistent vomiting"
    derived_disease = patient.get("disease","") or ("Dengue Fever" if "fever" in (patient.get("symptoms","").lower()) else "")
    return {
        "date": datetime.now().isoformat(),
        "patient_name": patient.get("name",""),
        "disease": derived_disease,
        "medicine": medicine,
        "dose": dose,
        "tests": tests,
        "warning": warning,
        "home_remedy": home,
    }

def save_consultation_pdf(patient: Dict[str, Any], reply: Dict[str, Any]) -> Path:
    ensure_storage()
    out = STORAGE_DIR / f"consult_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(out.as_posix(), pagesize=A4)
    content = []
    content.append(Paragraph("Patient Health Report", styles["Title"]))
    content.append(Spacer(1, 12))
    content.append(Paragraph(f"Date: {reply.get('date','')}", styles["Normal"]))
    content.append(Paragraph(f"Name: {patient.get('name','')}", styles["Normal"]))
    content.append(Paragraph(f"Age: {patient.get('age','')}", styles["Normal"]))
    content.append(Paragraph(f"Gender: {patient.get('gender','')}", styles["Normal"]))
    if patient.get("severity"):
        content.append(Paragraph(f"Severity: {patient.get('severity')}", styles["Normal"]))
    if patient.get("duration"):
        content.append(Paragraph(f"Duration: {patient.get('duration')}", styles["Normal"]))
    content.append(Paragraph(f"Symptoms: {patient.get('symptoms','')}", styles["Normal"]))
    content.append(Spacer(1, 12))
    content.append(Paragraph(f"<b>Disease:</b> {reply.get('disease','')}", styles["Normal"]))
    content.append(Paragraph(f"<b>Medicines:</b> {reply.get('medicine','')}", styles["Normal"]))
    content.append(Paragraph(f"<b>Dose:</b> {reply.get('dose','')}", styles["Normal"]))
    content.append(Paragraph(f"<b>Recommended Tests:</b> {reply.get('tests','')}", styles["Normal"]))
    content.append(Paragraph(f"<b>Home Care:</b> {reply.get('home_remedy','')}", styles["Normal"]))
    content.append(Paragraph(f"<b>Warnings:</b> {reply.get('warning','')}", styles["Normal"]))
    doc.build(content)
    return out
