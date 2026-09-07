import io
import json
import os
import re
import pandas as pd
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
CYCLE_START = date(2026, 7, 6)


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
        days = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        return f"{days[value.weekday()]} {value.day} de {months[value.month - 1]} de {value.year}"
    return clean_text(value)


def parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = clean_text(value).lower()
    match = re.search(r"(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})", text)
    if not match:
        return None
    months = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}
    month = months.get(match.group(2))
    if not month:
        return None
    try:
        return date(int(match.group(3)), month, int(match.group(1)))
    except ValueError:
        return None


def cycle_for_date(value):
    class_date = parse_date(value)
    if not class_date or class_date < CYCLE_START:
        return None
    week_number = ((class_date - CYCLE_START).days // 7) + 1
    return {"cycle": ((week_number - 1) // 3) + 1, "week": ((week_number - 1) % 3) + 1}


def current_cycle():
    info = cycle_for_date(date.today())
    return info or {"cycle": 1, "week": 1}


def is_no_class(theme, observations):
    text = f"{theme} {observations}".lower()
    markers = ("no hubo clase", "no hay clase", "sin clase", "no se realizó", "no se realizo", "no se dictó", "no se dicto", "suspendida")
    return any(marker in text for marker in markers)


def classify_context(sheet_name, group):
    text = f"{sheet_name} {group}".lower()
    if "tecnico laboral" in text:
        return "Técnico Laboral"
    if "comunidad terapeutica" in text:
        return "Comunidad Terapéutica"
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
                group = sheet_name
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
            normalized_date = parse_date(class_date)
            if not normalized_date:
                continue
            context = classify_context(sheet_name, group)
            no_class = is_no_class(theme, observations)
            cycle = cycle_for_date(normalized_date)
            classes.append({
                "date": normalized_date,
                "date_label": format_date(normalized_date),
                "context": context,
                "context_class": {
                    "Multigrado": "multi",
                    "Técnico Laboral": "tecnico",
                    "Comunidad Terapéutica": "terapeutica",
                    "Alta": "alta",
                }[context],
                "group": group or sheet_name,
                "subject": subject or "Sin asignatura",
                "theme": theme or "Sin tema registrado",
                "observations": observations,
                "week": week,
                "cycle": cycle["cycle"] if cycle else None,
                "cycle_week": cycle["week"] if cycle else None,
                "no_class": no_class,
                "novelty": observations if no_class and observations else (theme if no_class else ""),
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
            clei_label = {
                "clei 2": "2",
                "clei 3a": "3A",
                "clei3b": "3B",
                "clei 4": "4",
                "clei 5-6": "5-6",
                "mult. asistencia": "Multigrado",
            }.get(normalized_sheet, clean_text(values[4]) if len(values) > 4 else "")
            records.append({
                "sheet": sheet_name,
                "name": name,
                "identification": identification,
                "group": group,
                "context": "Multigrado" if normalized_sheet == "mult. asistencia" or "multigrado" in group.lower() else "Alta",
                "date": parse_date(values[0]) if len(values) > 0 else None,
                "date_label": format_date(values[0]) if len(values) > 0 and parse_date(values[0]) else "",
                "clei": clei_label,
                "science_attendance": clean_text(values[6]) if len(values) > 6 else "",
                "science_grade": clean_text(values[7]) if len(values) > 7 else "",
                "math_attendance": clean_text(values[8]) if len(values) > 8 else "",
                "math_grade": clean_text(values[9]) if len(values) > 9 else "",
                "observation": clean_text(values[10]) if len(values) > 10 else "",
            })
    return records


def build_student_matrix(records, clei_filter="", cycle_filter="", week_filter=""):
    filtered = [
        item for item in records
        if (not clei_filter or item["clei"] == clei_filter)
        and (not cycle_filter or (cycle_for_date(item["date"]) and cycle_for_date(item["date"])["cycle"] == int(cycle_filter)))
        and (not week_filter or (cycle_for_date(item["date"]) and cycle_for_date(item["date"])["week"] == int(week_filter)))
    ]
    date_map = {}
    students = {}
    for item in filtered:
        if not item["date"]:
            continue
        date_key = item["date"].isoformat()
        date_map[date_key] = item["date_label"]
        student_key = (item["name"], item["identification"], item["group"])
        student = students.setdefault(student_key, {
            "name": item["name"],
            "group": item["group"],
            "clei": item["clei"],
            "dates": {},
            "math_grades": [],
            "science_grades": [],
        })
        cell = student["dates"].setdefault(date_key, {
            "science_attendance": "",
            "science_grade": "",
            "math_attendance": "",
            "math_grade": "",
        })
        cell["science_attendance"] = item["science_attendance"] or cell["science_attendance"]
        cell["science_grade"] = item["science_grade"] or cell["science_grade"]
        cell["math_attendance"] = item["math_attendance"] or cell["math_attendance"]
        cell["math_grade"] = item["math_grade"] or cell["math_grade"]
        for field, target in (("science_grade", "science_grades"), ("math_grade", "math_grades")):
            try:
                student[target].append(float(item[field].replace(",", ".")))
            except (AttributeError, TypeError, ValueError):
                pass

    dates = sorted(date_map.items(), reverse=True)
    matrix = []
    for student in sorted(students.values(), key=lambda value: value["name"].lower()):
        student["math_average"] = round(sum(student["math_grades"]) / len(student["math_grades"]), 2) if student["math_grades"] else None
        student["science_average"] = round(sum(student["science_grades"]) / len(student["science_grades"]), 2) if student["science_grades"] else None
        matrix.append(student)
    return matrix, dates


def get_dashboard_data(context_filter=""):
    try:
        buffer, metadata = download_excel_from_drive()
        all_classes = read_planning_rows(buffer)
        student_records = read_student_records(buffer)
        valid_filters = {"Alta", "Multigrado", "Técnico Laboral", "Comunidad Terapéutica"}
        if context_filter not in valid_filters:
            context_filter = ""
        classes = [
            item for item in all_classes
            if not context_filter or item["context"] == context_filter
        ]
        return {
            "classes": classes,
            "context_filter": context_filter,
            "current_cycle": current_cycle(),
            "total_classes": len(all_classes),
            "total_students": len(student_records),
            "total_groups": len({item["group"] for item in all_classes}),
            "drive_updated": metadata.get("modifiedTime", ""),
            "data_error": None,
        }
    except Exception:
        app.logger.exception("No se pudo leer el Excel privado de Google Drive")
        return {
            "classes": [],
            "context_filter": context_filter,
            "current_cycle": current_cycle(),
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
    context_filter = request.args.get("context", "").strip()
    data = get_dashboard_data(context_filter)
    return render_template("index.html", current_user=session.get("user"), **data)


@app.route("/grupos")
@login_required
def grupos():
    try:
        buffer, metadata = download_excel_from_drive()
        records = read_student_records(buffer)
        clei_filter = request.args.get("clei", "").strip()
        cycle_filter = request.args.get("ciclo", "").strip()
        week_filter = request.args.get("semana", "").strip()
        cleis = ["2", "3A", "3B", "4", "5-6", "Multigrado"]
        cycles = sorted({cycle_for_date(item["date"])["cycle"] for item in records if cycle_for_date(item["date"])})
        weeks = [1, 2, 3]
        if clei_filter not in cleis:
            clei_filter = ""
        if cycle_filter not in {str(value) for value in cycles}:
            cycle_filter = ""
        if week_filter not in {str(value) for value in weeks}:
            week_filter = ""
        matrix, dates = build_student_matrix(records, clei_filter, cycle_filter, week_filter)
        return render_template(
            "grupos.html",
            current_user=session.get("user"),
            matrix=matrix,
            dates=dates,
            cleis=cleis,
            clei_filter=clei_filter,
            cycles=cycles,
            weeks=weeks,
            cycle_filter=cycle_filter,
            week_filter=week_filter,
            total_records=len(matrix),
            data_error=None,
            drive_updated=metadata.get("modifiedTime", ""),
        )
    except Exception:
        app.logger.exception("No se pudo leer estudiantes para Mis grupos")
        return render_template(
            "grupos.html",
            current_user=session.get("user"),
            matrix=[],
            dates=[],
            cleis=[],
            clei_filter="",
            cycles=[],
            weeks=[1, 2, 3],
            cycle_filter="",
            week_filter="",
            total_records=0,
            data_error="No se pudo leer el Excel desde Google Drive.",
            drive_updated="",
        )

@app.route("/estudiantes")
@login_required
def estudiantes():
    try:
        buffer, metadata = download_excel_from_drive()
        buffer.seek(0)  # importante para que pandas lea desde el inicio
        sheets = pd.read_excel(buffer, sheet_name=None)

        records = []
        for name, df in sheets.items():
            if name.lower() in STUDENT_SHEETS:
                df = df.dropna(how="all")
                df["CLEI"] = name
                records.append(df)

        if not records:
            return render_template(
                "estudiantes.html",
                current_user=session.get("user"),
                data_error="No se encontraron registros de estudiantes.",
                summary=[],
                drive_updated=""
            )

        df_all = pd.concat(records, ignore_index=True)

        # Convertir columnas de notas a numéricas
        df_all["math_grade"] = pd.to_numeric(df_all.iloc[:, 9], errors="coerce")
        df_all["science_grade"] = pd.to_numeric(df_all.iloc[:, 7], errors="coerce")

        # Promedios por CLEI
        summary = (
            df_all.groupby("CLEI")[["math_grade", "science_grade"]]
            .mean()
            .reset_index()
            .to_dict(orient="records")
        )

        return render_template(
            "estudiantes.html",
            current_user=session.get("user"),
            summary=summary,
            drive_updated=metadata.get("modifiedTime", ""),
            data_error=None
        )
    except Exception:
        app.logger.exception("Error en análisis de estudiantes")
        return render_template(
            "estudiantes.html",
            current_user=session.get("user"),
            summary=[],
            drive_updated="",
            data_error="No se pudo leer el Excel desde Google Drive."
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
