import os
from datetime import date

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_USER", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "password")
os.environ.setdefault("GOOGLE_DRIVE_ENABLED", "false")

from app import external_absence_totals, matches_attendance_scope, person_key


external_record = {
    "source": "Alta y CLEI normal",
    "clei": "CLEI 2",
    "student": "PEREZ PRUEBA",
    "identification": "1.234.567",
    "attendance": "No asistió",
    "class_date": date(2026, 7, 6),
}
base_record = {
    "clei": "2",
    "date": date(2026, 7, 6),
    "context": "Alta",
}

assert matches_attendance_scope(base_record, ["2"])
assert matches_attendance_scope(external_record, ["2"])

filtered = [
    external_record
    for item in [external_record]
    if matches_attendance_scope(item, ["2"])
]
totals = external_absence_totals(filtered)
assert totals[person_key("PEREZ PRUEBA", "1234567")] == 1

for identification, attendance in (
    ("1234567.0", "No asistió"),
    ("CC 1234567", "No asistió a la clase"),
    ("1234567", "F"),
):
    totals = external_absence_totals([{
        "student": "PEREZ PRUEBA",
        "identification": identification,
        "attendance": attendance,
    }])
    assert totals[person_key("PEREZ PRUEBA", "1234567")] == 1

totals = external_absence_totals([{
    "student": "PEREZ PRUEBA",
    "identification": "",
    "attendance": "No",
}])
assert totals[person_key("PEREZ PRUEBA", "")] == 1

print("OK: el filtro CLEI del archivo base conserva la falta de la planilla externa.")
