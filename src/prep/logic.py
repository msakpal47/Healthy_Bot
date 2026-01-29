 from typing import List
 from .models import IntakeAnswers, Symptom
 
 RED_FLAGS = [
     ("chest pain", "Chest pain with shortness of breath or sweating"),
     ("shortness of breath", "Shortness of breath at rest or worsening"),
     ("suicidal", "Suicidal thoughts or self-harm"),
     ("stroke", "Sudden weakness, facial droop, speech trouble"),
     ("severe abdominal pain", "Severe abdominal pain with persistent vomiting"),
     ("fever", "High fever or confusion"),
 ]
 
 def symptom_summary(ans: IntakeAnswers) -> str:
     parts: List[str] = []
     for s in ans.symptoms:
         assoc = ", ".join(s.associated) if s.associated else "none"
         parts.append(
             f"- {s.description}; onset {s.onset_date or 'unknown'}; severity {s.severity or 'unknown'}; progression {s.progression or 'unknown'}; associated {assoc}"
         )
     return "\n".join(parts) or "No symptoms recorded"
 
 def symptom_timeline(ans: IntakeAnswers) -> str:
     items = []
     for s in ans.symptoms:
         items.append(f"{s.onset_date or 'unknown'}: {s.description}")
     return "\n".join(items) or "No timeline available"
 
 def test_history(ans: IntakeAnswers) -> str:
     if not ans.tests:
         return "No tests recorded"
     items = []
     for t in ans.tests:
         items.append(f"- {t.name} on {t.date_performed or 'unknown'}: {t.result or 'pending'}")
     return "\n".join(items)
 
 def detect_red_flags(ans: IntakeAnswers) -> List[str]:
     text_blob = " ".join([s.description.lower() for s in ans.symptoms])
     alerts: List[str] = []
     for keyword, message in RED_FLAGS:
         if keyword in text_blob:
             alerts.append(message)
     return alerts
