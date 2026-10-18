import os
from datetime import date

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_USER", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "password")
os.environ.setdefault("GOOGLE_DRIVE_ENABLED", "false")

from app import build_integrated_students

base_records = [
    {
        "name": "Ana Pérez", "identification": "123", "group": "Grupo 3",
        "clei": "3B", "context": "Alta", "date": date(2026, 8, 1),
        "date_label": "sábado 1 de agosto de 2026", "math_attendance": "Sí",
        "math_grade": "4,0", "science_attendance": "Sí", "science_grade": "3,0",
    },
    {
        "name": "Ana Pérez", "identification": "123", "group": "Grupo 3",
        "clei": "3B", "context": "Alta", "date": date(2026, 8, 8),
        "date_label": "sábado 8 de agosto de 2026", "math_attendance": "Sí",
        "math_grade": "5,0", "science_attendance": "No", "science_grade": "4,0",
    },
]
external_records = [
    {
        "student": "Ana Pérez", "identification": "123", "group": "Grupo 3",
        "clei": "CLEI 3B", "context": "Alta", "subject": "Inglés",
        "attendance": "Sí", "grade": "2,0", "class_date": date(2026, 8, 5),
        "class_date_label": "miércoles 5 de agosto de 2026",
        "source": "Alta y CLEI normal",
    },
    {
        "student": "Ana Pérez", "identification": "123", "group": "Grupo 3",
        "clei": "CLEI 3B", "context": "Alta", "subject": "Inglés",
        "attendance": "Sí", "grade": "4,0", "class_date": date(2026, 8, 12),
        "class_date_label": "miércoles 12 de agosto de 2026",
        "source": "Alta y CLEI normal",
    },
]

students = build_integrated_students(base_records, external_records)
assert len(students) == 1
student = students[0]
by_subject = {item["subject"]: item for item in student["subjects"]}
assert by_subject["Matemáticas"]["average"] == 4.5
assert by_subject["Ciencias Naturales"]["average"] == 3.5
assert by_subject["Inglés"]["average"] == 3.0
assert by_subject["Matemáticas"]["source"] == "Control de clase"
assert by_subject["Ciencias Naturales"]["source"] == "Control de clase"
assert by_subject["Inglés"]["source"] == "Alta y CLEI normal"
assert student["overall_average"] == 3.67
assert student["graded_sessions"] == 6
print("OK: promedios discriminados por materia, total y fuentes correctos.")
