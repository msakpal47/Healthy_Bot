import json
import os
from pathlib import Path
import pandas as pd
from fpdf import FPDF

STORAGE = Path(__file__).resolve().parents[1] / "storage"

def _load_consults():
    p = STORAGE / "consultations.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))

def generate_excel():
    data = _load_consults()
    if not data:
        return None
    df = pd.DataFrame(data)
    out = STORAGE / "doctor_report.xlsx"
    df.to_excel(out.as_posix(), index=False)
    return out

def generate_pdf():
    data = _load_consults()
    if not data:
        return None
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, "Doctor Prescription Report", ln=True)
    for row in data:
        pdf.ln(3)
        for k, v in row.items():
            pdf.multi_cell(0, 7, f"{str(k).upper()}: {str(v)}")
        pdf.ln(2)
    out = STORAGE / "doctor_report.pdf"
    pdf.output(out.as_posix())
    return out

if __name__ == "__main__":
    STORAGE.mkdir(parents=True, exist_ok=True)
    xls = generate_excel()
    pdf = generate_pdf()
    print(str(xls) if xls else "No consultations")
    print(str(pdf) if pdf else "No consultations")
