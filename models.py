from app import db

class Docente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))

class Estudiante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfil_academico.id'))

class Contenido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200))
    descripcion = db.Column(db.Text)

class PerfilAcademico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fortalezas = db.Column(db.Text)
    debilidades = db.Column(db.Text)
