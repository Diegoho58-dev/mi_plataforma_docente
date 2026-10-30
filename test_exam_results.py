import os

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_USER", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "password")
os.environ.setdefault("GOOGLE_DRIVE_ENABLED", "false")

from app import build_integrated_students
from external_subjects import parse_exam_results

rows = [
    ["PLANILLA DE SEGUIMIENTO EXÁMENES"],
    ["Centro"],
    ["Fecha (DD/MM/AAAA)"],
    ["Examen Inicial/intermedio/final"],
    ["Monitor Aula"],
    ["Profesor que acompaña la prueba"],
    ["", "APELLIDOS Y NOMBRES / INTERNO", "IDENTIFICACIÓN", "GRUPO ASIGNADO", "CLEI ASIGNADO", "CIENCIAS NATURALES", "", "", "MATEMÁTICAS / FÍSICA", "", "", "ESPAÑOL", "", "", "CIENCIAS SOCIALES", "", "", "INGLÉS", "", ""],
    ["N°", "", "", "", "", "TOTAL PREGUNTAS", "TOTAL RESPUESTAS", "CORTE 1", "TOTAL PREGUNTAS", "TOTAL RESPUESTAS", "CORTE 1", "TOTAL PREGUNTAS", "TOTAL RESPUESTAS", "CORTE 1", "TOTAL PREGUNTAS", "TOTAL RESPUESTAS", "CORTE 1", "TOTAL PREGUNTAS", "TOTAL RESPUESTAS", "CORTE 1"],
    [],
    ["1", "ANA PEREZ", "123", "GRUPO 4", "4", 5, 2, 4, 5, 3, 6, 5, 4, 8, 5, 1, 2, 5, 0, 0],
]

results = parse_exam_results(rows, "E", "Alta y CLEI normal")
assert len(results) == 1
result = results[0]
assert result["subjects"]["Ciencias Naturales"]["total_questions"] == 5
assert result["subjects"]["Ciencias Naturales"]["correct_answers"] == 2
assert result["total_questions"] == 25
assert result["correct_answers"] == 10

students = build_integrated_students([], [], exam_results=results)
exam = students[0]["exam_results"]
assert exam["total_questions"] == 25
assert exam["correct_answers"] == 10
assert exam["percentage"] == 40.0
assert exam["subjects"][0]["percentage"] is not None
print("OK: resultados de la pestaña E y total de pruebas correctos.")

complementary = parse_exam_results(rows, "10", "Alta y CLEI normal")
assert complementary[0]["exam_label"] == "Prueba complementaria"
assert complementary[0]["exam_period"] == "Prueba complementaria · 28 y 29 de octubre de 2026"
all_attempts = build_integrated_students([], [], exam_results=results + complementary)
assert len(all_attempts[0]["exam_results"]["attempts"]) == 2
assert [item["label"] for item in all_attempts[0]["exam_results"]["attempts"]] == ["Prueba anterior", "Prueba complementaria"]
print("OK: la hoja 10 se conserva como segunda prueba junto a la hoja E.")

sheet10_rows = [
    ["Prueba complementaria 28/10/2026 y 29/10/2026"],
    ["", "APELLIDOS Y NOMBRES", "IDENTIFICACIÓN", "GRUPO ASIGNADO", "CLEI ASIGNADO", "CIENCIAS NATURALES", "", "MATEMÁTICAS / FÍSICA", "", "ESPAÑOL", ""],
    ["N°", "", "", "", "", "ASISTENCIA", "NOTA", "ASISTENCIA", "NOTA", "ASISTENCIA", "NOTA"],
    [1, "ANA PEREZ", "123", "GRUPO 4", "4", "", "", "Sí", 4.7, "", ""],
]
complementary_grade_only = parse_exam_results(sheet10_rows, "10", "Alta y CLEI normal")
assert complementary_grade_only[0]["exam_type"] == "grade_only"
assert complementary_grade_only[0]["exam_period"] == "Prueba complementaria · 28 y 29 de octubre de 2026"
assert complementary_grade_only[0]["subjects"]["Matemáticas"]["grade"] == 4.7
assert complementary_grade_only[0]["subjects"]["Ciencias Naturales"]["pending"] is True
print("OK: hoja 10 muestra solo notas por materia y marca pendientes sin nota.")
