 import json
 from pathlib import Path
 from typing import List
 from .models import IntakeAnswers, PatientInfo, Symptom, TestRecord
 from .pdf import build_pdf
 
 def parse_list(text: str) -> List[str]:
     if not text:
         return []
     return [t.strip() for t in text.split(",") if t.strip()]
 
 def interactive() -> IntakeAnswers:
     name = input("Patient name: ").strip()
     age = int(input("Age: ").strip())
     symptom_desc = input("Main symptoms (comma-separated): ").strip()
     symptoms = []
     for d in parse_list(symptom_desc):
         onset = input(f"Onset for '{d}' (YYYY-MM-DD or text): ").strip()
         severity = input(f"Severity for '{d}': ").strip()
         progression = input(f"Progression for '{d}': ").strip()
         associated = parse_list(input(f"Associated with '{d}' (comma-separated): ").strip())
         symptoms.append(Symptom(description=d, onset_date=onset, severity=severity, progression=progression, associated=associated))
     conditions = parse_list(input("Known conditions (comma-separated): ").strip())
     medications = parse_list(input("Medications (comma-separated): ").strip())
     allergies = parse_list(input("Allergies (comma-separated): ").strip())
     tests = []
     while True:
         add = input("Add a test? (y/n): ").strip().lower()
         if add != "y":
             break
         tname = input("Test name: ").strip()
         tdate = input("Date performed: ").strip()
         tres = input("Result: ").strip()
         tests.append(TestRecord(name=tname, date_performed=tdate, result=tres))
     notes = input("Additional notes: ").strip()
     return IntakeAnswers(
         patient=PatientInfo(name=name, age=age),
         symptoms=symptoms,
         conditions=conditions,
         medications=medications,
         allergies=allergies,
         tests=tests,
         notes=notes or None,
     )
 
 def from_json(path: str | Path) -> IntakeAnswers:
     data = json.loads(Path(path).read_text(encoding="utf-8"))
     patient = PatientInfo(**data["patient"])
     symptoms = [Symptom(**s) for s in data.get("symptoms", [])]
     tests = [TestRecord(**t) for t in data.get("tests", [])]
     return IntakeAnswers(
         patient=patient,
         symptoms=symptoms,
         conditions=data.get("conditions", []),
         medications=data.get("medications", []),
         allergies=data.get("allergies", []),
         tests=tests,
         notes=data.get("notes"),
     )
 
 def run(answers_path: str | None = None, brand: str | None = None, logo: str | None = None) -> Path:
     ans = from_json(answers_path) if answers_path else interactive()
     return build_pdf(ans, brand=brand, logo_path=logo)
