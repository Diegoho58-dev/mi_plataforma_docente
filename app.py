from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave-secreta-temporal'  # Necesaria para manejar sesiones

# Credenciales fijas (solo para pruebas locales)
USUARIO = "diego"
CONTRASENA = "1234"

@app.route("/")
def home():
    if "usuario" in session:
        return render_template("index.html", usuario=session["usuario"])
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        contrasena = request.form["contrasena"]
        if usuario == USUARIO and contrasena == CONTRASENA:
            session["usuario"] = usuario
            return redirect(url_for("home"))
        else:
            return "Credenciales incorrectas"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
