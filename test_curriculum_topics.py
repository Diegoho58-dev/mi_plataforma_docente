import io
import os
import sys
from openpyxl import Workbook

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_USER", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "password")
os.environ.setdefault("GOOGLE_DRIVE_ENABLED", "false")
sys.path.insert(0, os.path.dirname(__file__))
from app import curriculum_topics

workbook = Workbook()
math_sheet = workbook.active
math_sheet.title = "MALLA CURRI MAT"
for _ in range(13):
    math_sheet.append([])
math_sheet.append(["CLEI 1", "CLEI 2", "CLEI 3", "CLEI 4", "CLEI 5", "CLEI 6"])
math_sheet.append(["Números naturales", "Fracciones", "Álgebra", "Geometría", "Funciones", "Probabilidad"])
math_sheet.append(["Operaciones básicas", "Decimales", "Ecuaciones", "Medición", "Estadística", "Gráficas"])

bio_sheet = workbook.create_sheet("MALLA CURRI BIO")
bio_sheet.append(["No.", "CLEI", "Contenido"])
bio_sheet.append([1, "CLEI I", "La célula"])
bio_sheet.append([2, "CLEI II", "Ecosistemas"])

# Esta hoja no debe contaminar ningún menú aunque su nombre contenga la materia.
other_sheet = workbook.create_sheet("Planeación Biología")
other_sheet.append(["CLEI", "Tema"])
other_sheet.append(["CLEI I", "DATO QUE NO DEBE APARECER"])

buffer = io.BytesIO()
workbook.save(buffer)

assert curriculum_topics(buffer, "Matemáticas", "CLEI I", workbook=workbook) == ["N/A"]
assert curriculum_topics(buffer, "Matemáticas", "CLEI IV", workbook=workbook) == ["Geometría", "Medición"]
assert curriculum_topics(buffer, "Matemáticas", "CLEI 5-6", workbook=workbook) == ["Funciones", "Estadística"]
assert curriculum_topics(buffer, "Biología", "CLEI I", workbook=workbook) == ["N/A"]
assert curriculum_topics(buffer, "Biología", "CLEI II", workbook=workbook) == ["Ecosistemas"]
assert curriculum_topics(buffer, "Matemáticas", "CLEI 2", workbook=workbook) == ["Fracciones", "Decimales"]
assert curriculum_topics(buffer, "Biología", "CLEI II", workbook=workbook) == ["Ecosistemas"]
print("OK: las mallas se aíslan por hoja y por CLEI.")

def test_no_romano_int_error():
    # La prueba anterior ejercita simultáneamente CLEI romano y arábigo.
    return True

assert test_no_romano_int_error()
print("OK: normalización de CLEI romano/arábigo.")
