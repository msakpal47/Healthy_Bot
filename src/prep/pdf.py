 from datetime import datetime
 from pathlib import Path
 from typing import List
 from fpdf import FPDF
 from .models import IntakeAnswers
 from .logic import symptom_summary, symptom_timeline, test_history, detect_red_flags
 from src.config import BASE_DIR
 
 OUTPUT_DIR = BASE_DIR / "output"
 
 def ensure_output() -> None:
     OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
 
 def build_pdf(ans: IntakeAnswers, brand: str | None = None, logo_path: str | None = None) -> Path:
     ensure_output()
     pdf = FPDF()
     pdf.set_auto_page_break(auto=True, margin=15)
     pdf.add_page()
     pdf.set_font("Arial", "B", 16)
     title = brand or "Smart Prep"
     pdf.cell(0, 10, f"{title} - Visit Prep", ln=True)
     if logo_path:
         try:
             pdf.image(logo_path, x=170, y=10, w=25)
         except Exception:
             pass
     pdf.set_font("Arial", size=12)
     pdf.cell(0, 10, f"Patient: {ans.patient.name}, Age: {ans.patient.age}", ln=True)
     pdf.cell(0, 10, "Symptom Summary", ln=True)
     for line in symptom_summary(ans).splitlines():
         pdf.multi_cell(0, 8, line)
     pdf.cell(0, 10, "Timeline", ln=True)
     for line in symptom_timeline(ans).splitlines():
         pdf.multi_cell(0, 8, line)
     pdf.cell(0, 10, "Test History", ln=True)
     for line in test_history(ans).splitlines():
         pdf.multi_cell(0, 8, line)
     alerts = detect_red_flags(ans)
     pdf.cell(0, 10, "Red Flags", ln=True)
     if alerts:
         for a in alerts:
             pdf.multi_cell(0, 8, f"- {a}")
     else:
         pdf.multi_cell(0, 8, "None detected")
     pdf.cell(0, 10, "Notes", ln=True)
     pdf.multi_cell(0, 8, ans.notes or "None")
     ts = datetime.now().strftime("%Y%m%d_%H%M%S")
     out_path = OUTPUT_DIR / f"prep_{ts}.pdf"
     pdf.output(out_path.as_posix())
     return out_path
