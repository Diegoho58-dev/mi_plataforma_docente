"""Lectura de materias externas desde las planillas operativas de Google Drive.

La salida es de solo lectura y conserva la diferencia entre la hoja/bloque
administrativo y la fecha escrita en el encabezado de cada materia. No lee ni
calcula columnas PROM., ASIST. de resumen ni TOTALES/PROMEDIOS del grupo.
"""

import re
import unicodedata
from datetime import date

from openpyxl import load_workbook


OWN_SUBJECT_MARKERS = {
    "matematicas",
    "matematicas fisica",
    "fisica",
    "ciencias naturales",
}

EXTERNAL_SUBJECTS = {
    "espanol": "Español",
    "lengua castellana": "Español",
    "ciencias sociales": "Ciencias Sociales",
    "sociales": "Ciencias Sociales",
    "ingles": "Inglés",
}

CLEI_LABELS = (
    "CLEI 5-6", "CLEI 5", "CLEI 6", "CLEI 3A", "CLEI 3B",
    "CLEI 4", "CLEI 2", "CLEI 1", "MULTIGRADO", "ALF",
)

DATE_RE = re.compile(
    r"(?<!\d)(\d{1,2})\s*(?:/|-|–)\s*(\d{1,2})"
    r"(?:\s*(?:/|-|–)\s*(\d{2,4}))?(?!\d)"
)


def clean(value):
    if value is None:
        return ""
    return " ".join(str(value).replace("\n", " ").split()).strip()


def normalize(value):
    text = clean(value).lower()
    return "".join(
        char for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )


def subject_name(value):
    key = normalize(value).replace("/", " ")
    key = re.sub(r"\s+", " ", key).strip()
    for marker, label in EXTERNAL_SUBJECTS.items():
        if marker in key:
            return label
    return ""


def is_own_subject(value):
    key = normalize(value).replace("/", " ")
    return any(marker in key for marker in OWN_SUBJECT_MARKERS)


def parse_date_token(day, month, year=None):
    try:
        day = int(day)
        month = int(month)
        if year is None:
            return None
        year = int(year)
        if year < 100:
            year += 2000
        return date(year, month, day)
    except (TypeError, ValueError):
        return None


def extract_dates(text, default_year=2026):
    """Extrae fechas tolerando /, -, espacios y años de dos dígitos."""
    result = []
    for match in DATE_RE.finditer(clean(text)):
        year = match.group(3) or str(default_year)
        parsed = parse_date_token(match.group(1), match.group(2), year)
        if parsed and parsed not in result:
            result.append(parsed)
    return result


def clei_key(value):
    key = normalize(value).replace(" ", "")
    aliases = {
        "clei1": "CLEI 1", "clei2": "CLEI 2", "clei3a": "CLEI 3A",
        "clei3b": "CLEI 3B", "clei4": "CLEI 4", "clei5": "CLEI 5-6",
        "clei6": "CLEI 5-6", "clei5-6": "CLEI 5-6",
        "multigrado": "MULTIGRADO", "alf": "ALF",
    }
    return aliases.get(key, clean(value).upper())


def context_for(source, group, clei):
    text = normalize(f"{source} {group} {clei}")
    if "multigrado" in text or "mediana" in text:
        return "Multigrado / Mediana"
    if "alf" in text or "alta" in text:
        return "Alta"
    return "CLEI normal"


def sheet_block_label(title, source):
    title_text = clean(title)
    match = re.search(r"semana\s*[-:]?\s*(\d+)", normalize(title_text))
    if match:
        return f"Semana {match.group(1)}"
    return f"Hoja: {title_text or source}"


def _header_row(rows):
    for index, row in enumerate(rows):
        text = " ".join(normalize(cell) for cell in row[:8] if cell)
        if "apellidos y nombres" in text and "identificacion" in text:
            return index
    return None


def _subject_columns(rows, header_index):
    """Encuentra la columna inicial de cada materia en el encabezado visual."""
    found = []
    for row_index in range(max(0, header_index - 12), header_index + 1):
        for column, value in enumerate(rows[row_index]):
            label = subject_name(value)
            if not label or is_own_subject(value):
                continue
            if not any(item[0] == label and item[1] == column for item in found):
                found.append((label, column, row_index))
    # Una materia puede aparecer en más de una celda por el formato visual;
    # se conserva la primera columna de su bloque.
    result = {}
    for label, column, row_index in found:
        result.setdefault(label, (column, row_index))
    return result


def _teacher_map(rows, header_index):
    mapping = {}
    subject_tokens = sorted(
        set(EXTERNAL_SUBJECTS) | {"matematicas", "ciencias naturales", "fisica"},
        key=len,
        reverse=True,
    )
    subject_pattern = re.compile("|".join(re.escape(item) for item in subject_tokens))
    for row in rows[:header_index]:
        cells = [clean(cell) for cell in row if clean(cell)]
        joined = " ".join(cells)
        if "areas docente" not in normalize(joined):
            continue
        marker_match = re.search(r"areas\s+docente\s+(.+)", normalize(joined))
        if not marker_match:
            continue
        # Usamos el texto original de la fila para conservar tildes en el nombre.
        original = joined
        marker = re.search(r"áreas\s+docente\s+", original, re.IGNORECASE)
        if not marker:
            marker = re.search(r"areas\s+docente\s+", original, re.IGNORECASE)
        if not marker:
            continue
        tail = original[marker.end():].strip()
        first_subject = subject_pattern.search(normalize(tail))
        teacher = tail[:first_subject.start()].strip(" -:") if first_subject else tail
        if not teacher:
            continue
        for token in subject_tokens:
            if token in normalize(tail):
                label = subject_name(token)
                if label:
                    mapping[label] = teacher
    return mapping


def _subject_date_map(text, default_year=2026):
    """Mapea CLEI/MULTIGRADO a la fecha escrita en el encabezado de materia."""
    result = {}
    normalized_text = clean(text)
    label_pattern = "|".join(re.escape(normalize(label)) for label in CLEI_LABELS)
    pattern = re.compile(rf"({label_pattern})\s*:\s*(.*?)(?=(?:{'|'.join(re.escape(normalize(label)) for label in CLEI_LABELS)})\s*:|$)", re.IGNORECASE)
    for match in pattern.finditer(normalize(normalized_text)):
        label = clei_key(match.group(1))
        dates = extract_dates(match.group(2), default_year)
        if dates:
            result[label] = dates[0]
    # Si el encabezado no asigna fecha a un CLEI concreto, conservamos todas
    # las fechas como referencia, sin inventar la semana académica.
    if not result:
        dates = extract_dates(normalized_text, default_year)
        if dates:
            result["__default__"] = dates[0]
    return result


def _header_text(rows, column, header_index):
    values = []
    for row in rows[max(0, header_index - 12):header_index + 1]:
        if column < len(row) and clean(row[column]):
            values.append(clean(row[column]))
    return " ".join(values)


def _is_data_row(row):
    if len(row) < 5:
        return False
    name = clean(row[1] if len(row) > 1 else "")
    identification = clean(row[2] if len(row) > 2 else "")
    return bool(name and identification and not normalize(name).startswith("total"))


def parse_workbook(buffer, source, default_year=2026):
    """Devuelve registros detallados de materias externas de un XLSX exportado."""
    buffer.seek(0)
    workbook = load_workbook(buffer, data_only=True, read_only=True)
    records = []
    for worksheet in workbook.worksheets:
        rows = [[clean(value) for value in row] for row in worksheet.iter_rows(values_only=True)]
        header_index = _header_row(rows)
        if header_index is None:
            continue
        columns = _subject_columns(rows, header_index)
        teachers = _teacher_map(rows, header_index)
        block = sheet_block_label(worksheet.title, source)
        for subject, (start_column, _) in columns.items():
            if is_own_subject(subject):
                continue
            dates_by_clei = _subject_date_map(
                _header_text(rows, start_column, header_index),
                default_year,
            )
            teacher = teachers.get(subject, "No identificado")
            for row in rows[header_index + 1:]:
                if not _is_data_row(row):
                    continue
                clei = clean(row[3] if len(row) > 3 else "")
                group = clean(row[4] if len(row) > 4 else "")
                key = clei_key(clei)
                class_date = dates_by_clei.get(key) or dates_by_clei.get("__default__")
                attendance = clean(row[start_column] if start_column < len(row) else "")
                grade = clean(row[start_column + 1] if start_column + 1 < len(row) else "")
                # Las columnas PROM./ASIST. y los totales están después de las
                # materias y nunca se recorren como una materia adicional.
                if not attendance and not grade:
                    continue
                records.append({
                    "source": source,
                    "sheet": clean(worksheet.title),
                    "block": block,
                    "subject": subject,
                    "teacher": teacher,
                    "context": context_for(source, group, clei),
                    "clei": clei,
                    "group": group,
                    "student": clean(row[1]),
                    "identification": clean(row[2]),
                    "attendance": attendance,
                    "grade": grade,
                    "observation": "",
                    "class_date": class_date,
                    "class_date_label": class_date.strftime("%d/%m/%Y") if class_date else "No identificada",
                    "week_mismatch": False,
                })
    return records


def mark_week_mismatches(records, cycle_for_date=None):
    """Marca fechas fuera del bloque solo cuando el bloque tiene una semana explícita.

    No mueve registros ni cambia su fecha. Si no se puede determinar la semana
    desde el nombre de la hoja, se deja la marca en False para evitar inferencias.
    """
    if not cycle_for_date:
        return records
    for item in records:
        match = re.search(r"semana\s*(\d+)", normalize(item["block"]))
        if not match or not item.get("class_date"):
            continue
        cycle = cycle_for_date(item["class_date"])
        if cycle and str(cycle.get("week")) != match.group(1):
            item["week_mismatch"] = True
    return records


def summarize(records):
    return {
        "records": len(records),
        "teachers": len({item["teacher"] for item in records if item["teacher"] != "No identificado"}),
        "subjects": len({item["subject"] for item in records}),
        "students": len({item["identification"] for item in records if item["identification"]}),
        "dated": sum(bool(item.get("class_date")) for item in records),
        "undated": sum(not item.get("class_date") for item in records),
        "mismatches": sum(item.get("week_mismatch", False) for item in records),
    }


__all__ = [
    "parse_workbook", "mark_week_mismatches", "summarize",
    "EXTERNAL_SUBJECTS", "OWN_SUBJECT_MARKERS",
]


def _demo():
    """Solo para pruebas manuales; no se ejecuta al importar."""
    return True
