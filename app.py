import io
import json
import os
from datetime import date, datetime
from functools import wraps

from flask import Flask, redirect, render_template, request, session, url_for
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY")
ADMIN_USER = os.environ.get("ADMIN_USER")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

if not SECRET_KEY:
    raise RuntimeError("Falta la variable de entorno SECRET_KEY.")
if not ADMIN_USER or not ADMIN_PASSWORD:
    raise RuntimeError("Faltan las variables ADMIN_USER o ADMIN_PASSWORD.")

app.config["SECRET_KEY"] = SECRET_KEY

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
PLANNING_SHEETS = {"tecnico laboral", "comunidad terapeutica", "maxima", "multigrado"}
STUDENT_SHEETS = {"clei 2", "clei 3a", "clei3b", "clei 4", "clei 5-6", "mult. asistencia"}


def login_required(view_function):
    @wraps(view_function)
    def protected_view(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return view_function(*args, **kwargs)
    return protected_view


def clean_text(value):
    if value is None:
        return ""
    return " ".join(str(value).replace("\n", " ").split()).strip()


def format_date(value):
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        months = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
        return f"{value.day} {months[value.month - 1]} {value.year}"
    return clean_text(value)


def parse_date(value):
    return value if isinstance(value, (datetime, date)) else None


def classify_context(sheet_name, group):
    text = f"{sheet_name} {group}".lower()
    return "Multigrado" if "multigrado" in text else "Alta"


def get_drive_service():
    file_id = os.environ.get("GOOGLE_DRIVE_FILE_ID")
    service_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not file_id or not service_json:
        raise RuntimeError("Faltan GOOGLE_DRIVE_FILE_ID o GOOGLE_SERVICE_ACCOUNT_JSON en Render.")
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(service_json), scopes=DRIVE_SCOPES
    )
    service = build("drive", "v3", credentials=credentials, cache_discovery=False)
    return service, file_id


def download_excel_from_drive():
    service, file_id = get_drive_service()
    metadata = service.files().get(fileId=file_id, fields="id,name,modifiedTime").execute()
    request_download = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request_download)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buffer.seek(0)
    return buffer, metadata


def read_planning_rows(buffer):
    from openpyxl import load_workbook

    buffer.seek(0)
    workbook = load_workbook(buffer, data_only=True, read_only=True)
    classes = []
    for worksheet in workbook.worksheets:
        sheet_name = clean_text(worksheet.title)
        normalized_sheet = sheet_name.lower()
        if normalized_sheet not in PLANNING_SHEETS:
            continue
        rows = list(worksheet.iter_rows(values_only=True))
        for row in rows[1:]:
            values = list(row)
            if not any(clean_text(value) for value in values):
                continue
            if normalized_sheet in {"tecnico laboral", "comunidad terapeutica"}:
                group = clean_text(values[0]) if len(values) > 0 else sheet_name
                subject = clean_text(values[0]) if len(values) > 0 else ""
                class_date = values[1] if len(values) > 1 else None
                theme = clean_text(values[2]) if len(values) > 2 else ""
                observations = clean_text(values[3]) if len(values) > 3 else ""
                week = clean_text(values[4]) if len(values) > 4 else ""
                drive_link = clean_text(values[6]) if len(values) > 6 else ""
            else:
                group = clean_text(values[0]) if len(values) > 0 else ""
                subject = clean_text(values[1]) if len(values) > 1 else ""
                class_date = values[2] if len(values) > 2 else None
                theme = clean_text(values[3]) if len(values) > 3 else ""
                observations = clean_text(values[4]) if len(values) > 4 else ""
                week = clean_text(values[5]) if len(values) > 5 else ""
                drive_link = clean_text(values[7]) if len(values) > 7 else ""
            if not parse_date(class_date):
                continue
            context = classify_context(sheet_name, group)
            classes.append({
                "date": parse_date(class_date),
                "date_label": format_date(class_date),
                "context": context,
                "context_class": "multi" if context == "Multigrado" else "alta",
                "group": group or sheet_name,
                "subject": subject or "Sin asignatura",
                "theme": theme or "Sin tema registrado",
                "observations": observations,
                "week": week,
                "drive_link": drive_link,
                "source": sheet_name,
            })
    classes.sort(key=lambda item: item["date"], reverse=True)
    return classes


def read_student_records(buffer):
    from openpyxl import load_workbook

    buffer.seek(0)
    workbook = load_workbook(buffer, data_only=True, read_only=True)
    records = []
    for worksheet in workbook.worksheets:
        sheet_name = clean_text(worksheet.title)
        normalized_sheet = sheet_name.lower()
        if normalized_sheet not in STUDENT_SHEETS:
            continue
        for row in worksheet.iter_rows(min_row=2, values_only=True):
            values = list(row)
            if not any(clean_text(value) for value in values):
                continue
            name = clean_text(values[2]) if len(values) > 2 else ""
            identification = clean_text(values[3]) if len(values) > 3 else ""
            group = clean_text(values[5]) if len(values) > 5 else sheet_name
            if not name and not identification:
                continue
            records.append({
                "sheet": sheet_name,
                "name": name,
                "identification": identification,
                "group": group,
                "context": "Multigrado" if normalized_sheet == "mult. asistencia" or "multigrado" in group.lower() else "Alta",
            })
    return records


def get_dashboard_data():
    try:
        buffer, metadata = download_excel_from_drive()
        classes = read_planning_rows(buffer)
        student_records = read_student_records(buffer)
        return {
            "classes": classes,
            "total_classes": len(classes),
            "total_students": len(student_records),
            "total_groups": len({item["group"] for item in classes}),
            "drive_updated": metadata.get("modifiedTime", ""),
            "data_error": None,
        }
    except Exception:
        app.logger.exception("No se pudo leer el Excel privado de Google Drive")
        return {
            "classes": [],
            "total_classes": 0,
            "total_students": "—",
            "total_groups": 0,
            "drive_updated": "",
            "data_error": "No se pudo actualizar el Excel desde Google Drive. Revisa la configuración de Render.",
        }


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == ADMIN_USER and password == ADMIN_PASSWORD:
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
    data = get_dashboard_data()
    return render_template("index.html", current_user=session.get("user"), **data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
