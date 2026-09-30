import os
from datetime import date

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_USER", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "password")
os.environ.setdefault("GOOGLE_DRIVE_ENABLED", "false")

from app import build_followup_summary, fallback_followup_analysis

base = [{
    "date": date(2026, 9, 1), "name": "Ana Pérez", "identification": "123.0", "group": "Grupo 3", "clei": "3B",
    "math_attendance": "No asistió", "math_grade": "2,8", "science_attendance": "Asistió", "science_grade": "3,5", "observation": "Requiere contacto familiar",
}]
external = [{
    "student": "Ana Perez", "identification": "123", "group": "Grupo 3", "clei": "CLEI 3B", "subject": "Inglés",
    "attendance": "No asistió", "grade": "3,0", "source": "Alta y CLEI normal",
}]
summary = build_followup_summary(base, [{"context": "Alta"}], external)
assert summary["subjects"]["Matemáticas"]["absent"] == 1
assert summary["subjects"]["Inglés"]["absent"] == 1
assert summary["padrino"]["CLEI 3B"]["students"]
assert summary["source_counts"]["external_records"] == 1
assert summary["source_counts"]["observations"][0]["text"] == "Requiere contacto familiar"
assert summary["chart_data"]["padrino"][0]["absent"] >= 1
fallback = fallback_followup_analysis(summary)
assert fallback["teacher_overview"]["actions"]
assert fallback["padrino_analysis"]["title"]
print("OK: consolidado integral y padrinos CLEI 3B/CLEI 5-6 funcionan.")

