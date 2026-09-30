import io
import os

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_USER", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "password")
os.environ.setdefault("GOOGLE_DRIVE_ENABLED", "false")

from app import app, enrich_guide_illustrations, latest_planned_topics_by_subject_clei
from gemini_planning import _validate_self_study_guide

planning = [
    {"group": "CLEI 2", "subject": "Matemáticas", "theme": "Fracciones", "week": "Semana 2", "week_number": 2, "date_label": "2 al 6 de febrero"},
    {"group": "CLEI 2", "subject": "Matemáticas", "theme": "Ecuaciones", "week": "Semana 4", "week_number": 4, "date_label": "16 al 20 de febrero"},
    {"group": "CLEI 2", "subject": "Biología", "theme": "Ecosistemas", "week": "Semana 3", "week_number": 3, "date_label": "9 al 13 de febrero"},
]

latest = latest_planned_topics_by_subject_clei(planning)
assert latest["Matemáticas"]["CLEI 2"]["theme"] == "Ecuaciones"
assert latest["Ciencias Naturales"]["CLEI 2"]["theme"] == "Ecosistemas"
assert "CLEI 1" not in latest["Matemáticas"]

guide = _validate_self_study_guide({
    "title": "Guía de ecuaciones",
    "introduction": "Introducción",
    "objective": "Resolver ecuaciones sencillas.",
    "explanation": "Explicación amplia del tema.",
    "key_concepts": ["Concepto 1", "Concepto 2", "Concepto 3", "Concepto 4"],
    "worked_examples": ["Ejemplo 1", "Ejemplo 2", "Ejemplo 3"],
    "activities": ["Actividad 1", "Actividad 2", "Actividad 3", "Actividad 4", "Actividad 5", "Actividad 6"],
    "reflection_questions": ["Pregunta 1", "Pregunta 2", "Pregunta 3", "Pregunta 4", "Pregunta 5"],
    "evaluation": ["Criterio 1", "Criterio 2", "Criterio 3", "Criterio 4", "Criterio 5"],
    "answer_key": ["Respuesta 1", "Respuesta 2", "Respuesta 3", "Respuesta 4", "Respuesta 5"],
    "materials": ["Cuaderno"],
    "common_mistakes": ["Error 1", "Error 2", "Error 3"],
    "study_plan": ["Paso 1", "Paso 2", "Paso 3", "Paso 4"],
    "closing": "Cierre",
})
assert guide["title"] == "Guía de ecuaciones"
assert len(guide["activities"]) == 6
enrich_guide_illustrations(guide)
assert len(guide["illustrations"]) == 3
assert all(item["labels"] for item in guide["illustrations"])

app.testing = True
app.config["TESTING"] = True
with app.test_client() as client:
    with client.session_transaction() as session:
        session["user"] = "admin"
    response = client.post("/materiales/guia-autodidacta/pdf", data={"guide_json": __import__("json").dumps({**guide, "subject": "Matemáticas", "clei": "CLEI 2", "theme": "Ecuaciones", "week": "Semana 4", "date_label": "16 al 20 de febrero"})})
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")

print("OK: selección por materia/CLEI, guía extensa, ilustraciones y PDF funcionan.")
