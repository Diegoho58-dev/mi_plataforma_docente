import io
from openpyxl import Workbook

from external_subjects import _subject_date_map, build_external_matrix, clei_key, consolidate_records, parse_values, parse_workbook, sheet_block_label, student_clei, summarize

header_dates = _subject_date_map(
    "ESPAÑOL ALF: Comprensión 09-07-2026 / 16-07-2026 "
    "CLEI 2: 06/07/2026 CLEI 3A: 15/07/2026 "
    "CLEI 3B: 08/07/2026 CLEI 4: 21/07/2026 "
    "CLEI 5-6: 07/07/2026 MULTIGRADO: 09/07/2026"
)
assert "ALF" not in header_dates
assert header_dates["CLEI 2"][0].isoformat() == "2026-07-06"
assert header_dates["CLEI 3A"][0].isoformat() == "2026-07-15"
assert header_dates["CLEI 3B"][0].isoformat() == "2026-07-08"
assert header_dates["CLEI 4"][0].isoformat() == "2026-07-21"
assert header_dates["CLEI 5-6"][0].isoformat() == "2026-07-07"
assert header_dates["MULTIGRADO"][0].isoformat() == "2026-07-09"
assert clei_key("2") == "CLEI 2"
assert clei_key("3A") == "CLEI 3A"
assert clei_key("3B") == "CLEI 3B"
assert clei_key("4") == "CLEI 4"
assert clei_key("5-6") == "CLEI 5-6"
assert student_clei("3", "GRUPO 2") == "CLEI 3A"
assert student_clei("3", "GRUPO 3") == "CLEI 3B"
assert student_clei("4", "GRUPO 6 MULTIGRADO") == "MULTIGRADO"
assert sheet_block_label("1", "Multigrado / Mediana") == "Semana 1"
assert sheet_block_label("1", "Alta y CLEI normal") == "Hoja: 1"

duplicate = {
    "source": "Alta y CLEI normal", "sheet": "Semana 1", "subject": "Español",
    "clei": "CLEI 2", "group": "Grupo 1", "student": "PEREZ PRUEBA",
    "identification": "123", "class_date": header_dates["CLEI 2"][0],
    "attendance": "Si", "grade": "", "teacher": "Ana",
}
completed = dict(duplicate, grade="4.5")
merged = consolidate_records([duplicate, completed])
assert len(merged) == 1 and merged[0]["grade"] == "4.5"

matrix, dates = build_external_matrix([
    {"source": "Alta", "sheet": "1", "subject": "Español", "clei": "CLEI 3B", "group": "GRUPO 3", "student": "PEREZ", "identification": "123", "class_date": header_dates["CLEI 2"][0], "attendance": "No", "grade": "4,0", "block": "Hoja 1", "week_mismatch": False},
    {"source": "Alta", "sheet": "3", "subject": "Español", "clei": "CLEI 3B", "group": "GRUPO 3", "student": "PEREZ", "identification": "123", "class_date": header_dates["CLEI 3A"][0], "attendance": "Si", "grade": "5", "block": "Hoja 3", "week_mismatch": False},
])
assert len(matrix) == 1 and matrix[0]["absences"] == 1 and matrix[0]["subject_averages"]["Español"] == 4.5

multigrade_rows = [
    ["N°", "APELLIDOS Y NOMBRES", "IDENTIFICACIÓN", "CLEI ASIGNADO", "GRUPO ASIGNADO", "CIENCIAS NATURALES", "MATEMÁTICAS / FÍSICA", "ESPAÑOL", "CIENCIAS SOCIALES", "INGLÉS"],
    ["", "", "", "", "", "", "", "MULTIGRADO: 04/08/2026", "MULTIGRADO: 05/08/2026", "MULTIGRADO: 06/08/2026"],
    ["Asis.", "", "", "", "", "", "", "Nota", "Nota", "Nota"],
    [1, "MULTI PRUEBA", "123", "4", "GRUPO 6 MULTIGRADO", "", "", "Si", 8, "No", 0, "Si", 9],
]
multigrade_records = parse_values(multigrade_rows, "1", "Multigrado / Mediana")
assert {item["subject"] for item in multigrade_records} == {"Español", "Ciencias Sociales", "Inglés"}
assert {item["clei"] for item in multigrade_records} == {"MULTIGRADO"}

workbook = Workbook()
sheet = workbook.active
sheet.title = "Semana 4"
sheet.append(["", "", "", "", "", "", "", "", ""])
sheet.append(["", "Áreas docente Ana Maria Carvajal", "", "", "", "", "", "", ""])
sheet.append(["", "", "", "", "", "", "", "", ""])
sheet.append(["", "N°", "APELLIDOS Y NOMBRES", "IDENTIFICACIÓN", "CLEI ASIGNADO", "GRUPO ASIGNADO", "ESPAÑOL CLEI 3A: 01/08/2026 y 08/08/2026", "CIENCIAS NATURALES", "INGLÉS"])
sheet.append(["", "", "", "", "", "", "", "", ""])
sheet.append(["", "", "", "", "", "", "", "", ""])
sheet.append(["", "", "", "", "", "", "", "", ""])
sheet.append(["", "", "", "", "", "", "", "", ""])
sheet.append([1, "", "", "", "", "", "", "", ""])
sheet.append([1, "PEREZ PRUEBA", "123", "CLEI 3A", "GRUPO 3", "Si", 8, "No", "", "Si", 9])
# Reescribe con la posición esperada por el parser: nombre, identificación,
# CLEI, grupo y dos columnas por materia.
sheet.delete_rows(10, 1)
sheet.append([1, "PEREZ PRUEBA", "123", "CLEI 3A", "GRUPO 3", "Si", 8, "No", 0, "Si", 9])

buffer = io.BytesIO()
workbook.save(buffer)
records = parse_workbook(buffer, "Alta y CLEI normal", default_year=2026)
assert any(item["subject"] == "Español" for item in records)
assert not any(item["subject"] in {"Matemáticas", "Ciencias Naturales"} for item in records)
assert summarize(records)["records"] >= 1
assert {item["class_date"].isoformat() for item in records if item["subject"] == "Español"} == {"2026-08-01", "2026-08-08"}
print("OK: parser externo excluye Matemáticas/Ciencias y conserva registros detallados.")
print("OK: parser externo conserva todas las fechas del encabezado.")
