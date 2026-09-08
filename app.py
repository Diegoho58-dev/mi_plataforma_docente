import io
import json
import os
import re
import unicodedata
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
DRIVE_ENABLED = os.environ.get("GOOGLE_DRIVE_ENABLED", "false").strip().lower() == "true"


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


def normalize_header(value):
    text = clean_text(value).lower()
    return "".join(
        character for character in unicodedata.normalize("NFD", text)
        if unicodedata.category(character) != "Mn"
    )


def find_column(headers, aliases, fallback=None):
    aliases = [normalize_header(alias) for alias in aliases]
    for index, header in enumerate(headers):
        normalized = normalize_header(header)
        if any(alias in normalized for alias in aliases):
            return index
    return fallback


def read_student_records(buffer):
    from openpyxl import load_workbook

    buffer.seek(0)
    workbook = load_workbook(buffer, data_only=True, read_only=True)
    records = []
    for worksheet in workbook.worksheets:
        sheet_name = clean_text(worksheet.title)
        normalized_sheet = normalize_header(sheet_name)
        if normalized_sheet not in STUDENT_SHEETS:
            continue
        rows = worksheet.iter_rows(values_only=True)
        header = list(next(rows, ()))
        # The old fixed positions remain fallbacks, but headers take priority.
        date_col = find_column(header, ["fecha"], 0)
        name_col = find_column(header, ["nombre", "estudiante", "alumno"], 2)
        identification_col = find_column(header, ["identificacion", "documento", "cedula", "doc"], 3)
        clei_col = find_column(header, ["clei", "nivel"], 4)
        group_col = find_column(header, ["grupo"], 5)
        math_attendance_col = find_column(header, ["asistencia matematicas", "asistio matematicas", "matematicas asistencia", "matematicas asistio", "matematicas presente", "mate asistencia"], 8)
        math_grade_col = find_column(header, ["nota matematicas", "calificacion matematicas", "matematicas nota", "matematicas calificacion", "matematicas promedio"], 9)
        science_attendance_col = find_column(header, ["asistencia ciencias", "asistio ciencias", "ciencias asistencia", "ciencias asistio", "ciencias presente", "ciencias naturales asistencia"], 6)
        science_grade_col = find_column(header, ["nota ciencias", "calificacion ciencias", "ciencias nota", "ciencias calificacion", "ciencias naturales nota", "ciencias naturales promedio"], 7)
        observation_col = find_column(header, ["observacion", "observaciones"], 10)
        for row in rows:
            values = list(row)
            if not any(clean_text(value) for value in values):
                continue
            get = lambda index: values[index] if index is not None and index < len(values) else ""
            name = clean_text(get(name_col))
            identification = clean_text(get(identification_col))
            group = clean_text(get(group_col)) or sheet_name
            if not name and not identification:
                continue
            clei_label = {
                "clei 2": "2", "clei 3a": "3A", "clei3b": "3B",
                "clei 4": "4", "clei 5-6": "5-6", "mult. asistencia": "Multigrado",
            }.get(normalized_sheet, clean_text(get(clei_col)))
            class_date = get(date_col)
            records.append({
                "sheet": sheet_name, "name": name, "identification": identification,
                "group": group,
                "context": "Multigrado" if normalized_sheet == "mult. asistencia" or "multigrado" in group.lower() else "Alta",
                "date": parse_date(class_date),
                "date_label": format_date(class_date) if parse_date(class_date) else "",
                "clei": clei_label,
                "science_attendance": clean_text(get(science_attendance_col)),
                "science_grade": clean_text(get(science_grade_col)),
                "math_attendance": clean_text(get(math_attendance_col)),
                "math_grade": clean_text(get(math_grade_col)),
                "observation": clean_text(get(observation_col)),
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
    if not DRIVE_ENABLED:
        return {
            "classes": [],
            "context_filter": context_filter,
            "current_cycle": current_cycle(),
            "total_classes": 0,
            "total_students": "—",
            "total_groups": 0,
            "drive_updated": "",
            "data_error": "La conexión con Google Drive está pausada. La activaremos nuevamente con el archivo nuevo.",
        }
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
    if not DRIVE_ENABLED:
        return render_template(
            "grupos.html",
            current_user=session.get("user"),
            matrix=[],
            dates=[],
            cleis=["2", "3A", "3B", "4", "5-6", "Multigrado"],
            clei_filter="",
            cycles=[],
            weeks=[1, 2, 3],
            cycle_filter="",
            week_filter="",
            total_records=0,
            data_error="La conexión con Google Drive está pausada. La activaremos nuevamente con el archivo nuevo.",
            drive_updated="",
        )
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


@app.route("/estudiantes")
@login_required
def estudiantes():
    page_data = {
        "students": [],
        "cleis": ["2", "3A", "3B", "4", "5-6", "Multigrado"],
        "contexts": ["Alta", "Multigrado"],
        "clei_filter": "",
        "context_filter": "",
        "search": "",
        "total_students": 0,
        "data_error": None,
    }
    if not DRIVE_ENABLED:
        page_data["data_error"] = "La conexión con Google Drive está pausada."
        return render_template("estudiantes.html", current_user=session.get("user"), **page_data)
    try:
        buffer, metadata = download_excel_from_drive()
        records = read_student_records(buffer)
        search = request.args.get("buscar", "").strip().lower()
        clei_filter = request.args.get("clei", "").strip()
        context_filter = request.args.get("contexto", "").strip()
        cleis = ["2", "3A", "3B", "4", "5-6", "Multigrado"]
        contexts = ["Alta", "Multigrado"]
        if clei_filter not in cleis:
            clei_filter = ""
        if context_filter not in contexts:
            context_filter = ""
        unique = {}
        for item in records:
            if search and search not in f"{item['name']} {item['group']}".lower():
                continue
            if clei_filter and item["clei"] != clei_filter:
                continue
            if context_filter and item["context"] != context_filter:
                continue
            key = (item["name"], item["identification"], item["group"])
            student = unique.setdefault(key, {
                "name": item["name"], "group": item["group"], "clei": item["clei"],
                "context": item["context"], "dates": set(), "math_grades": [], "science_grades": [],
            })
            if item["date"]:
                student["dates"].add(item["date"])
            for field, target in (("math_grade", "math_grades"), ("science_grade", "science_grades")):
                try:
                    student[target].append(float(item[field].replace(",", ".")))
                except (AttributeError, TypeError, ValueError):
                    pass
        students = []
        for student in unique.values():
            student["date_count"] = len(student.pop("dates"))
            student["math_average"] = round(sum(student["math_grades"]) / len(student["math_grades"]), 2) if student["math_grades"] else None
            student["science_average"] = round(sum(student["science_grades"]) / len(student["science_grades"]), 2) if student["science_grades"] else None
            students.append(student)
        page_data.update({
            "students": sorted(students, key=lambda item: item["name"].lower()),
            "cleis": cleis, "contexts": contexts, "clei_filter": clei_filter,
            "context_filter": context_filter, "search": request.args.get("buscar", "").strip(),
            "total_students": len(students), "drive_updated": metadata.get("modifiedTime", ""),
        })
        return render_template("estudiantes.html", current_user=session.get("user"), **page_data)
    except Exception:
        app.logger.exception("No se pudo leer estudiantes")
        page_data["data_error"] = "No se pudo leer el Excel desde Google Drive."
        return render_template("estudiantes.html", current_user=session.get("user"), **page_data)



def attendance_value(value):
    text = clean_text(value).lower()
    if text in {"si", "sí", "s", "asistio", "asistió", "presente", "p"}:
        return "Asistió"
    if text in {"no", "n", "ausente", "inasistente", "i"}:
        return "No asistió"
    return clean_text(value) or "Sin registro"


@app.route("/asistencia")
@login_required
def asistencia():
    page_data = {
        "rows": [], "cleis": ["2", "3A", "3B", "4", "5-6", "Multigrado"],
        "cycles": [], "weeks": [1, 2, 3],
        "clei_filter": [], "cycle_filter": [], "week_filter": [],
        "start_date": "", "end_date": "", "total_present": 0, "total_absent": 0, "total_rows": 0,
        "attendance_stats": [], "total_never_attended": 0,
        "data_error": None,
    }
    if not DRIVE_ENABLED:
        page_data["data_error"] = "La conexión con Google Drive está pausada."
        return render_template("asistencia.html", current_user=session.get("user"), **page_data)
    try:
        buffer, metadata = download_excel_from_drive()
        records = read_student_records(buffer)
        clei_filter = request.args.getlist("clei")
        cycle_filter = request.args.getlist("ciclo")
        week_filter = request.args.getlist("semana")
        start_date_text = request.args.get("desde", "").strip()
        end_date_text = request.args.get("hasta", "").strip()
        try:
            start_date = datetime.strptime(start_date_text, "%Y-%m-%d").date() if start_date_text else None
        except ValueError:
            start_date_text, start_date = "", None
        try:
            end_date = datetime.strptime(end_date_text, "%Y-%m-%d").date() if end_date_text else None
        except ValueError:
            end_date_text, end_date = "", None
        if start_date and end_date and start_date > end_date:
            start_date, end_date = end_date, start_date
            start_date_text, end_date_text = end_date_text, start_date_text
        cleis = ["2", "3A", "3B", "4", "5-6", "Multigrado"]
        cycles = sorted({cycle_for_date(item["date"])["cycle"] for item in records if cycle_for_date(item["date"])})
        weeks = [1, 2, 3]
        clei_filter = [value for value in clei_filter if value in cleis]
        cycle_filter = [value for value in cycle_filter if value in {str(item) for item in cycles}]
        week_filter = [value for value in week_filter if value in {str(item) for item in weeks}]

        rows = []
        attendance_by_student = {}
        for item in records:
            cycle = cycle_for_date(item["date"])
            if clei_filter and item["clei"] not in clei_filter:
                continue
            if cycle_filter and (not cycle or str(cycle["cycle"]) not in cycle_filter):
                continue
            if week_filter and (not cycle or str(cycle["week"]) not in week_filter):
                continue
            if start_date and (not item["date"] or item["date"] < start_date):
                continue
            if end_date and (not item["date"] or item["date"] > end_date):
                continue

            math_status = attendance_value(item["math_attendance"]) if (item["math_attendance"] or item["math_grade"]) else "Sin registro"
            science_status = attendance_value(item["science_attendance"]) if (item["science_attendance"] or item["science_grade"]) else "Sin registro"
            if math_status == "Sin registro" and science_status == "Sin registro":
                continue
            rows.append({
                "name": item["name"], "group": item["group"], "clei": item["clei"],
                "context": item["context"], "date_label": item["date_label"], "date": item["date"],
                "math_status": math_status, "science_status": science_status,
                "cycle": cycle["cycle"] if cycle else "—", "week": cycle["week"] if cycle else "—",
            })

            key = (item["name"], item["identification"], item["group"])
            summary = attendance_by_student.setdefault(key, {
                "name": item["name"], "group": item["group"], "clei": item["clei"], "context": item["context"],
                "math_sessions": 0, "math_present": 0, "math_absent": 0,
                "science_sessions": 0, "science_present": 0, "science_absent": 0,
            })
            for prefix, raw_status, grade in (
                ("math", item["math_attendance"], item["math_grade"]),
                ("science", item["science_attendance"], item["science_grade"]),
            ):
                if not (raw_status or grade):
                    continue
                status = attendance_value(raw_status)
                summary[f"{prefix}_sessions"] += 1
                if status == "Asistió":
                    summary[f"{prefix}_present"] += 1
                elif status == "No asistió":
                    summary[f"{prefix}_absent"] += 1

        rows.sort(key=lambda item: (item["date"] or date.min, item["name"].lower()), reverse=True)
        attendance_stats = []
        for summary in attendance_by_student.values():
            summary["total_sessions"] = summary["math_sessions"] + summary["science_sessions"]
            summary["total_present"] = summary["math_present"] + summary["science_present"]
            summary["total_absent"] = summary["math_absent"] + summary["science_absent"]
            summary["math_rate"] = round(summary["math_present"] * 100 / summary["math_sessions"], 1) if summary["math_sessions"] else 0
            summary["science_rate"] = round(summary["science_present"] * 100 / summary["science_sessions"], 1) if summary["science_sessions"] else 0
            summary["total_rate"] = round(summary["total_present"] * 100 / summary["total_sessions"], 1) if summary["total_sessions"] else 0
            summary["never_attended"] = summary["total_present"] == 0
            attendance_stats.append(summary)
        attendance_stats.sort(key=lambda item: (not item["never_attended"], -item["total_absent"], item["total_present"], item["name"].lower()))
        page_data.update({
            "rows": rows, "cleis": cleis, "cycles": cycles, "weeks": weeks,
            "clei_filter": clei_filter, "cycle_filter": cycle_filter, "week_filter": week_filter,
            "start_date": start_date_text, "end_date": end_date_text,
            "total_present": sum(row["math_status"] == "Asistió" for row in rows) + sum(row["science_status"] == "Asistió" for row in rows),
            "total_absent": sum(row["math_status"] == "No asistió" for row in rows) + sum(row["science_status"] == "No asistió" for row in rows),
            "total_rows": len(rows), "data_error": None,
            "attendance_stats": attendance_stats,
            "total_never_attended": sum(item["never_attended"] for item in attendance_stats),
            "drive_updated": metadata.get("modifiedTime", ""),
        })
        return render_template("asistencia.html", current_user=session.get("user"), **page_data)
    except Exception:
        app.logger.exception("No se pudo leer asistencia")
        page_data["data_error"] = "No se pudo leer el Excel desde Google Drive."
        return render_template("asistencia.html", current_user=session.get("user"), **page_data)


@app.route("/materiales")
@login_required
def materiales():
    page_data = {
        "materials": [],
        "contexts": ["Alta", "Multigrado", "Técnico Laboral", "Comunidad Terapéutica"],
        "context_filter": "",
        "group_filter": "",
        "search": "",
        "groups": [],
        "data_error": None,
    }
    if not DRIVE_ENABLED:
        page_data["data_error"] = "La conexión con Google Drive está pausada."
        return render_template("materiales.html", current_user=session.get("user"), **page_data)
    try:
        buffer, metadata = download_excel_from_drive()
        classes = read_planning_rows(buffer)
        context_filter = request.args.get("contexto", "").strip()
        group_filter = request.args.get("grupo", "").strip()
        search = request.args.get("buscar", "").strip()
        contexts = page_data["contexts"]
        if context_filter not in contexts:
            context_filter = ""
        groups = sorted({item["group"] for item in classes if item["group"]})
        if group_filter not in groups:
            group_filter = ""
        search_lower = search.lower()
        materials = [
            item for item in classes
            if item["drive_link"]
            and (not context_filter or item["context"] == context_filter)
            and (not group_filter or item["group"] == group_filter)
            and (not search_lower or search_lower in f"{item['subject']} {item['theme']} {item['group']} {item['observations']}".lower())
        ]
        page_data.update({
            "materials": materials,
            "context_filter": context_filter,
            "group_filter": group_filter,
            "search": search,
            "groups": groups,
            "drive_updated": metadata.get("modifiedTime", ""),
        })
        return render_template("materiales.html", current_user=session.get("user"), **page_data)
    except Exception:
        app.logger.exception("No se pudieron leer los materiales")
        page_data["data_error"] = "No se pudo leer el Excel desde Google Drive."
        return render_template("materiales.html", current_user=session.get("user"), **page_data)


@app.route("/seguimiento")
@login_required
def seguimiento():
    page_data = {
        "stats": {
            "classes": 0, "students": 0, "groups": 0, "attendance_rate": 0,
            "math_rate": 0, "science_rate": 0, "math_average": None, "science_average": None,
            "risk_count": 0,
        },
        "chart_data": json.dumps({"dates": [], "math": [], "science": [], "contexts": [], "risks": []}),
        "interpretations": [], "risk_students": [], "data_error": None,
    }
    if not DRIVE_ENABLED:
        page_data["data_error"] = "La conexión con Google Drive está pausada."
        return render_template("seguimiento.html", current_user=session.get("user"), **page_data)
    try:
        buffer, metadata = download_excel_from_drive()
        classes = read_planning_rows(buffer)
        records = read_student_records(buffer)
        valid_records = [item for item in records if item["date"]]
        unique_students = {(item["name"], item["identification"], item["group"]) for item in valid_records if item["name"]}
        attendance = {"math": {"sessions": 0, "present": 0, "absent": 0}, "science": {"sessions": 0, "present": 0, "absent": 0}}
        grades = {"math": [], "science": []}
        dates = {}
        student_stats = {}
        for item in valid_records:
            student_key = (item["name"], item["identification"], item["group"])
            student = student_stats.setdefault(student_key, {"name": item["name"], "group": item["group"], "clei": item["clei"], "present": 0, "absent": 0, "sessions": 0})
            day = item["date"].isoformat()
            date_entry = dates.setdefault(day, {"label": item["date"].strftime("%d/%m/%Y"), "math_present": 0, "math_absent": 0, "science_present": 0, "science_absent": 0})
            for prefix, attendance_value_raw, grade_raw in (("math", item["math_attendance"], item["math_grade"]), ("science", item["science_attendance"], item["science_grade"])):
                if not (attendance_value_raw or grade_raw):
                    continue
                status = attendance_value(attendance_value_raw)
                attendance[prefix]["sessions"] += 1
                student["sessions"] += 1
                if status == "Asistió":
                    attendance[prefix]["present"] += 1
                    student["present"] += 1
                    date_entry[f"{prefix}_present"] += 1
                elif status == "No asistió":
                    attendance[prefix]["absent"] += 1
                    student["absent"] += 1
                    date_entry[f"{prefix}_absent"] += 1
                try:
                    grades[prefix].append(float(grade_raw.replace(",", ".")))
                except (AttributeError, TypeError, ValueError):
                    pass
        def rate(data):
            return round(data["present"] * 100 / data["sessions"], 1) if data["sessions"] else 0
        math_rate, science_rate = rate(attendance["math"]), rate(attendance["science"])
        total_sessions = attendance["math"]["sessions"] + attendance["science"]["sessions"]
        total_present = attendance["math"]["present"] + attendance["science"]["present"]
        overall_rate = round(total_present * 100 / total_sessions, 1) if total_sessions else 0
        risk_students = []
        for item in student_stats.values():
            item["rate"] = round(item["present"] * 100 / item["sessions"], 1) if item["sessions"] else 0
            if item["sessions"] and (item["rate"] < 70 or item["absent"] > item["present"]):
                risk_students.append(item)
        risk_students.sort(key=lambda item: (-item["absent"], item["rate"], item["name"].lower()))
        risk_students = risk_students[:12]
        date_items = sorted(dates.items())
        context_counts = {}
        for item in classes:
            context_counts[item["context"]] = context_counts.get(item["context"], 0) + 1
        interpretations = []
        if total_sessions:
            interpretations.append(f"La asistencia global registrada es de {overall_rate}%, calculada sobre {total_sessions} sesiones de Matemáticas y Ciencias Naturales.")
        if math_rate and science_rate:
            better = "Matemáticas" if math_rate >= science_rate else "Ciencias Naturales"
            difference = abs(math_rate - science_rate)
            interpretations.append(f"El mejor comportamiento de asistencia se observa en {better}; la diferencia entre materias es de {difference:.1f} puntos porcentuales.")
        if risk_students:
            interpretations.append(f"Se identifican {len(risk_students)} estudiantes en seguimiento prioritario por una asistencia inferior al 70% o por tener más inasistencias que asistencias.")
        else:
            interpretations.append("No se identifican estudiantes en riesgo alto con los registros disponibles.")
        if classes:
            busiest = max(context_counts, key=context_counts.get)
            interpretations.append(f"El contexto con mayor número de clases registradas es {busiest}, con {context_counts[busiest]} clases.")
        if grades["math"] or grades["science"]:
            averages = []
            if grades["math"]: averages.append(f"Matemáticas {sum(grades['math']) / len(grades['math']):.2f}")
            if grades["science"]: averages.append(f"Ciencias Naturales {sum(grades['science']) / len(grades['science']):.2f}")
            interpretations.append("Promedios de calificación registrados: " + " y ".join(averages) + ".")
        chart_data = {
            "dates": [item[1]["label"] for item in date_items],
            "math": [{"present": item[1]["math_present"], "absent": item[1]["math_absent"]} for item in date_items],
            "science": [{"present": item[1]["science_present"], "absent": item[1]["science_absent"]} for item in date_items],
            "contexts": [{"label": key, "value": value} for key, value in sorted(context_counts.items())],
            "risks": [{"label": item["name"], "value": item["absent"]} for item in risk_students[:8]],
        }
        page_data.update({
            "stats": {"classes": len(classes), "students": len(unique_students), "groups": len({item["group"] for item in classes}), "attendance_rate": overall_rate, "math_rate": math_rate, "science_rate": science_rate, "math_average": round(sum(grades["math"]) / len(grades["math"]), 2) if grades["math"] else None, "science_average": round(sum(grades["science"]) / len(grades["science"]), 2) if grades["science"] else None, "risk_count": len(risk_students)},
            "chart_data": json.dumps(chart_data, ensure_ascii=False), "interpretations": interpretations, "risk_students": risk_students, "drive_updated": metadata.get("modifiedTime", ""),
        })
        return render_template("seguimiento.html", current_user=session.get("user"), **page_data)
    except Exception:
        app.logger.exception("No se pudo generar seguimiento estadístico")
        page_data["data_error"] = "No se pudo generar el análisis desde Google Drive."
        return render_template("seguimiento.html", current_user=session.get("user"), **page_data)
