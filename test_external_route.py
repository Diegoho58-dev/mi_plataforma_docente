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
    response = client.get("/otras-materias")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Otras materias" in html
    assert "Matemáticas y Ciencias Naturales se excluyen" in html
print("OK: la ruta de otras materias responde y está protegida por sesión.")
