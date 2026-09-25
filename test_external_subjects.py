import io
from openpyxl import Workbook

from external_subjects import _subject_date_map, parse_workbook, summarize

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
assert {item["class_date"].isoformat() for item in records if item["subject"] == "Español"} == {"2026-08-01"}
print("OK: parser externo excluye Matemáticas/Ciencias y conserva registros detallados.")
print("OK: parser externo conserva todas las fechas del encabezado.")


