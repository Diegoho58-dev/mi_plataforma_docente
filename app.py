import hmac
import os
from functools import wraps

from flask import Flask, redirect, render_template, request, session, url_for


app = Flask(__name__)

# Clave utilizada por Flask para proteger las sesiones
SECRET_KEY = os.environ.get("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "Falta la variable de entorno SECRET_KEY."
    )

app.config["SECRET_KEY"] = SECRET_KEY

# Datos del único usuario autorizado
ADMIN_USER = os.environ.get("ADMIN_USER")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

if not ADMIN_USER or not ADMIN_PASSWORD:
    raise RuntimeError(
        "Faltan las variables ADMIN_USER o ADMIN_PASSWORD."
    )


def login_required(view_function):
    """
    Permite acceder a una página solamente
    si el usuario ya inició sesión.
    """

    @wraps(view_function)
    def protected_view(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))

        return view_function(*args, **kwargs)

    return protected_view


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        valid_username = hmac.compare_digest(username, ADMIN_USER)
        valid_password = hmac.compare_digest(password, ADMIN_PASSWORD)

        if valid_username and valid_password:
            session.clear()
            session["user"] = username

            return redirect(url_for("home"))

        error = "El usuario o la contraseña no son correctos."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def home():
    return render_template(
        "index.html",
        current_user=session.get("user")
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
