import os

os.environ["SECRET_KEY"] = "test-secret"
os.environ["ADMIN_USER"] = "admin"
os.environ["ADMIN_PASSWORD"] = "password"
os.environ["GOOGLE_DRIVE_ENABLED"] = "false"

from app import app

app.testing = True
with app.test_client() as client:
    with client.session_transaction() as session:
        session["user"] = "admin"
    response = client.get("/actualizar-planeacion")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Generar propuesta con IA" in html
    assert "Objetivo de aprendizaje" in html
    assert "Articulación con el monitor" in html

print("OK: la pantalla de actualización incluye los controles de IA.")
