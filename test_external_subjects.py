import io
from openpyxl import Workbook

from external_subjects import parse_workbook, summarize

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
assert len({item["class_date"] for item in records if item["subject"] == "Español"}) == 2
print("OK: parser externo excluye Matemáticas/Ciencias y conserva registros detallados.")
print("OK: parser externo conserva todas las fechas del encabezado.")

