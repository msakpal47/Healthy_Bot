 from dataclasses import dataclass, field
 from typing import List, Optional
 from datetime import date
 
 @dataclass
 class PatientInfo:
     name: str
     age: int
     sex: Optional[str] = None
 
 @dataclass
 class Symptom:
     description: str
     onset_date: Optional[str] = None
     severity: Optional[str] = None
     progression: Optional[str] = None
     associated: List[str] = field(default_factory=list)
 
 @dataclass
 class TestRecord:
     name: str
     date_performed: Optional[str] = None
     result: Optional[str] = None
 
 @dataclass
 class IntakeAnswers:
     patient: PatientInfo
     symptoms: List[Symptom]
     conditions: List[str]
     medications: List[str]
     allergies: List[str]
     tests: List[TestRecord]
     notes: Optional[str] = None
