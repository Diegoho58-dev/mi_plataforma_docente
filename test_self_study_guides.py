import os

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_USER", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "password")
os.environ.setdefault("GOOGLE_DRIVE_ENABLED", "false")

from app import latest_planned_topic_by_clei
from gemini_planning import _validate_self_study_guide

planning = [
    {
        "group": "CLEI 2",
        "subject": "Matemáticas",
        "theme": "Fracciones",
        "week": "Semana 2",
        "week_number": 2,
        "date_label": "2 al 6 de febrero",
    },
    {
        "group": "CLEI 2",
        "subject": "Matemáticas",
        "theme": "Ecuaciones",
        "week": "Semana 4",
        "week_number": 4,
        "date_label": "16 al 20 de febrero",
    },
]

latest = latest_planned_topic_by_clei(planning)
assert latest["CLEI 2"]["theme"] == "Ecuaciones"
assert "CLEI 1" not in latest

guide = _validate_self_study_guide({
    "title": "Guía de ecuaciones",
    "introduction": "Introducción",
    "objective": "Resolver ecuaciones sencillas.",
    "explanation": "Explicación del tema.",
    "activities": ["Actividad 1", "Actividad 2", "Actividad 3"],
    "reflection_questions": ["Pregunta 1", "Pregunta 2", "Pregunta 3"],
    "evaluation": ["Criterio 1", "Criterio 2", "Criterio 3"],
    "answer_key": ["Respuesta 1", "Respuesta 2", "Respuesta 3"],
    "materials": ["Cuaderno"],
    "closing": "Cierre",
})
assert guide["title"] == "Guía de ecuaciones"
assert len(guide["activities"]) == 3

print("OK: la guía usa el último tema planeado y valida su estructura completa.")
