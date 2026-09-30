"""Integración segura con Gemini para proponer objetivo y articulación pedagógica."""

import json
import os
from urllib import error, request


GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/{model}:generateContent"
)

DEFAULT_MODEL = "gemini-3.5-flash-lite"


class GeminiPlanningError(RuntimeError):
    """Error controlado al solicitar o validar una propuesta de planeación."""


def _build_prompt(subject, clei, theme, previous_examples):
    examples = previous_examples or []

    example_text = "\n".join(
        f"Ejemplo {index}:\n"
        f"Objetivo: {item.get('objetivo', '')}\n"
        f"Articulación con el monitor: "
        f"{item.get('articulacion_monitor', '')}"
        for index, item in enumerate(examples[:5], start=1)
    ) or "No hay ejemplos anteriores disponibles."

    return f"""Actúa como docente experto en educación flexible para jóvenes y adultos.

Materia: {subject}
CLEI: {clei}
Tema oficial de la malla curricular: {theme}

Genera únicamente dos campos para una planeación de clase:
1. objetivo: objetivo de aprendizaje.
2. articulacion_monitor: cómo el monitor acompaña, orienta y verifica el aprendizaje.

Reglas obligatorias:
- No cambies ni reemplaces el tema oficial.
- No inventes otra materia, otro CLEI ni contenidos ajenos al tema.
- Relaciona directamente el objetivo y la articulación con el tema recibido.
- Usa lenguaje claro, concreto y apropiado para jóvenes y adultos.
- Mantén una redacción similar a los ejemplos, sin copiarlos literalmente.
- La articulación debe describir acciones concretas del monitor.
- No incluyas títulos, explicaciones, markdown ni campos adicionales.

Ejemplos de redacción usados anteriormente:
{example_text}

Responde exclusivamente con un objeto JSON válido con esta estructura:
{{
  "objetivo": "...",
  "articulacion_monitor": "..."
}}"""


def _validate_proposal(payload):
    if not isinstance(payload, dict):
        raise GeminiPlanningError(
            "Gemini no devolvió un objeto JSON."
        )

    objective = " ".join(
        str(payload.get("objetivo", "")).split()
    ).strip()

    articulation = " ".join(
        str(payload.get("articulacion_monitor", "")).split()
    ).strip()

    if not objective or not articulation:
        raise GeminiPlanningError(
            "La propuesta de Gemini no contiene "
            "objetivo y articulación completos."
        )

    if len(objective) > 1200:
        raise GeminiPlanningError(
            "El objetivo generado por Gemini excede "
            "la longitud permitida."
        )

    if len(articulation) > 1600:
        raise GeminiPlanningError(
            "La articulación generada por Gemini excede "
            "la longitud permitida."
        )

    return {
        "objetivo": objective,
        "articulacion_monitor": articulation,
    }


def generate_planning_proposal(
    subject,
    clei,
    theme,
    previous_examples=None,
    timeout=30,
):
    """Genera una propuesta sin escribirla en Drive.

    La clave se toma exclusivamente de GEMINI_API_KEY.
    La función devuelve solo objetivo y articulación validados
    para que la capa web decida cuándo guardar.
    """

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise GeminiPlanningError(
            "Falta configurar GEMINI_API_KEY "
            "en el entorno del servidor."
        )

    if not str(theme).strip():
        raise GeminiPlanningError(
            "No se puede generar una propuesta "
            "sin tema curricular."
        )

    model = (
        os.environ.get("GEMINI_MODEL", DEFAULT_MODEL).strip()
        or DEFAULT_MODEL
    )

    prompt = _build_prompt(
        subject,
        clei,
        theme,
        previous_examples,
    )

    body = {
        "system_instruction": {
            "parts": [
                {
                    "text": (
                        "Devuelve únicamente JSON válido "
                        "y no inventes información curricular."
                    )
                }
            ]
        },
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.35,
            "candidateCount": 1,
            "maxOutputTokens": 700,
            "responseMimeType": "application/json",
        },
    }

    endpoint = (
        GEMINI_API_URL.format(model=model)
        + "?key="
        + api_key
    )

    http_request = request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(
            http_request,
            timeout=timeout,
        ) as response:
            response_payload = json.loads(
                response.read().decode("utf-8")
            )

    except error.HTTPError as exc:
        detail = exc.read().decode(
            "utf-8",
            errors="replace",
        )[:1000]

        if exc.code == 400:
            raise GeminiPlanningError(
                f"Gemini rechazó la solicitud (400). "
                f"Detalle: {detail}"
            ) from exc

        if exc.code == 401:
            raise GeminiPlanningError(
                "Gemini rechazó la API KEY (401). "
                "Revisa GEMINI_API_KEY en Render."
            ) from exc

        if exc.code == 403:
            raise GeminiPlanningError(
                f"Gemini rechazó el acceso (403). "
                f"Revisa permisos de la API KEY. "
                f"Detalle: {detail}"
            ) from exc

        if exc.code == 404:
            raise GeminiPlanningError(
                f"Gemini no encontró el recurso solicitado (404). "
                f"Modelo utilizado: {model}. "
                f"Detalle: {detail}"
            ) from exc

        if exc.code == 429:
            raise GeminiPlanningError(
                "Gemini alcanzó el límite de solicitudes (429). "
                "Intenta nuevamente más tarde. "
                f"Detalle: {detail}"
            ) from exc

        raise GeminiPlanningError(
            f"Gemini rechazó la solicitud ({exc.code}). "
            f"Detalle: {detail}"
        ) from exc

    except error.URLError as exc:
        raise GeminiPlanningError(
            "No fue posible conectarse con Gemini. "
            f"Detalle: {exc.reason}"
        ) from exc

    except TimeoutError as exc:
        raise GeminiPlanningError(
            "La conexión con Gemini agotó el tiempo de espera."
        ) from exc

    except json.JSONDecodeError as exc:
        raise GeminiPlanningError(
            "Gemini devolvió una respuesta que no es JSON válido."
        ) from exc

    try:
        text = (
            response_payload["candidates"][0]
            ["content"]["parts"][0]["text"]
        )

        generated = json.loads(text)

    except (
        KeyError,
        IndexError,
        TypeError,
        json.JSONDecodeError,
    ) as exc:
        raise GeminiPlanningError(
            "Gemini no devolvió el JSON esperado. "
            f"Respuesta recibida: "
            f"{str(response_payload)[:1000]}"
        ) from exc

    return _validate_proposal(generated)


def _validate_self_study_guide(payload):
    if not isinstance(payload, dict):
        raise GeminiPlanningError("Gemini no devolvió una guía válida.")

    def text(name, required=True, limit=5000):
        value = " ".join(str(payload.get(name, "")).split()).strip()
        if required and not value:
            raise GeminiPlanningError(f"La guía no contiene el campo {name}.")
        if len(value) > limit:
            raise GeminiPlanningError(f"El campo {name} de la guía es demasiado extenso.")
        return value

    def text_list(name, minimum=1, limit=12):
        values = payload.get(name, [])
        if not isinstance(values, list):
            raise GeminiPlanningError(f"El campo {name} de la guía no es una lista.")
        cleaned = [" ".join(str(value).split()).strip() for value in values if str(value).strip()]
        if len(cleaned) < minimum:
            raise GeminiPlanningError(f"La guía no contiene suficientes elementos en {name}.")
        if len(cleaned) > limit:
            cleaned = cleaned[:limit]
        return cleaned

    return {
        "title": text("title", limit=300),
        "introduction": text("introduction", limit=2500),
        "objective": text("objective", limit=1200),
        "explanation": text("explanation", limit=10000),
        "key_concepts": text_list("key_concepts", minimum=4, limit=10),
        "worked_examples": text_list("worked_examples", minimum=3, limit=8),
        "activities": text_list("activities", minimum=6, limit=10),
        "reflection_questions": text_list("reflection_questions", minimum=5, limit=8),
        "evaluation": text_list("evaluation", minimum=5, limit=8),
        "answer_key": text_list("answer_key", minimum=5, limit=10),
        "materials": text_list("materials", minimum=1, limit=8),
        "common_mistakes": text_list("common_mistakes", minimum=3, limit=8),
        "study_plan": text_list("study_plan", minimum=4, limit=8),
        "closing": text("closing", limit=1200),
    }


def generate_self_study_guide(
    subject,
    clei,
    theme,
    week="",
    context="",
    timeout=45,
):
    """Genera una guía autodidacta sin escribir datos en Drive."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise GeminiPlanningError("Falta configurar GEMINI_API_KEY en el entorno del servidor.")
    if not str(theme).strip():
        raise GeminiPlanningError("No se puede generar una guía sin tema curricular.")

    model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    prompt = f"""Actúa como docente experto en educación flexible para jóvenes y adultos en Colombia.

Materia: {subject}
CLEI: {clei}
Contexto: {context or 'Educación flexible'}
Semana planeada vigente: {week or 'No especificada'}
Tema oficial de la planeación: {theme}

Diseña una guía autodidacta extensa, equivalente a varias páginas de trabajo, para que un estudiante pueda aprender sin acompañamiento permanente.
La guía debe ser clara, gradual, práctica, inclusiva y apropiada para jóvenes y adultos. Debe partir únicamente del tema oficial recibido.
No inventes otro tema, materia o CLEI. No menciones que fue generada por una IA.
Explica desde lo más básico hasta una aplicación práctica. Incluye ejemplos resueltos paso a paso y conecta el aprendizaje con situaciones cotidianas.

Devuelve exclusivamente un objeto JSON válido con estos campos:
- title: título concreto de la guía.
- introduction: presentación y conexión del tema con situaciones cotidianas.
- objective: objetivo de aprendizaje observable.
- explanation: explicación amplia y detallada del tema, con definiciones, procedimiento y ejemplos.
- key_concepts: lista de mínimo 4 conceptos clave explicados en una frase.
- worked_examples: lista de mínimo 3 ejemplos resueltos paso a paso.
- activities: lista de mínimo 6 actividades progresivas, desde comprensión hasta aplicación práctica.
- reflection_questions: lista de mínimo 5 preguntas de comprensión y reflexión.
- evaluation: lista de mínimo 5 criterios o preguntas de autoevaluación.
- answer_key: lista de mínimo 5 respuestas orientadoras para actividades o preguntas.
- materials: lista de materiales sencillos y accesibles.
- common_mistakes: lista de mínimo 3 errores frecuentes y cómo corregirlos.
- study_plan: lista de mínimo 4 pasos para organizar el trabajo autónomo.
- closing: recomendaciones finales para revisar y demostrar lo aprendido.

Usa español claro. No incluyas markdown, HTML ni campos adicionales."""

    body = {
        "system_instruction": {"parts": [{"text": "Devuelve únicamente JSON válido y respeta exactamente los campos solicitados."}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.45,
            "candidateCount": 1,
            "maxOutputTokens": 8000,
            "responseMimeType": "application/json",
        },
    }
    endpoint = GEMINI_API_URL.format(model=model) + "?key=" + api_key
    http_request = request.Request(endpoint, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(http_request, timeout=timeout) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise GeminiPlanningError(f"Gemini rechazó la guía ({exc.code}). Detalle: {detail}") from exc
    except error.URLError as exc:
        raise GeminiPlanningError(f"No fue posible conectarse con Gemini. Detalle: {exc.reason}") from exc
    except TimeoutError as exc:
        raise GeminiPlanningError("La conexión con Gemini agotó el tiempo de espera.") from exc
    except json.JSONDecodeError as exc:
        raise GeminiPlanningError("Gemini devolvió una respuesta que no es JSON válido.") from exc

    try:
        text_response = response_payload["candidates"][0]["content"]["parts"][0]["text"]
        generated = json.loads(text_response)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise GeminiPlanningError("Gemini no devolvió la estructura JSON esperada para la guía.") from exc
    return _validate_self_study_guide(generated)


def _validate_followup_analysis(payload):
    if not isinstance(payload, dict):
        raise GeminiPlanningError("Gemini no devolvió un análisis de seguimiento válido.")

    def clean_text(value, field, limit=5000):
        result = " ".join(str(value or "").split()).strip()
        if not result:
            raise GeminiPlanningError(f"El análisis no contiene el campo {field}.")
        if len(result) > limit:
            raise GeminiPlanningError(f"El campo {field} del análisis es demasiado extenso.")
        return result

    def clean_list(value, field, minimum=2, limit=10):
        if not isinstance(value, list):
            raise GeminiPlanningError(f"El campo {field} del análisis no es una lista.")
        result = [" ".join(str(item or "").split()).strip() for item in value if str(item or "").strip()]
        if len(result) < minimum:
            raise GeminiPlanningError(f"El análisis no contiene suficientes elementos en {field}.")
        return result[:limit]

    def section(name):
        data = payload.get(name)
        if not isinstance(data, dict):
            raise GeminiPlanningError(f"Falta la sección {name} del análisis.")
        return {
            "title": clean_text(data.get("title"), f"{name}.title", 300),
            "summary": clean_text(data.get("summary"), f"{name}.summary", 3000),
            "findings": clean_list(data.get("findings"), f"{name}.findings", 3),
            "possible_situations": clean_list(data.get("possible_situations"), f"{name}.possible_situations", 2),
            "actions": clean_list(data.get("actions"), f"{name}.actions", 3),
        }

    return {
        "teacher_overview": section("teacher_overview"),
        "subjects_analysis": section("subjects_analysis"),
        "padrino_analysis": section("padrino_analysis"),
        "limitations": clean_list(payload.get("limitations"), "limitations", 2, 6),
    }


def generate_followup_analysis(summary, timeout=60):
    """Analiza el consolidado de Drive sin modificar ninguna fuente."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise GeminiPlanningError("Falta configurar GEMINI_API_KEY para el análisis de seguimiento.")
    model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    compact_summary = json.dumps(summary, ensure_ascii=False, separators=(",", ":"))
    prompt = f"""Actúa como coordinador pedagógico experto en educación flexible para jóvenes y adultos en Colombia.

Analiza el siguiente consolidado real de registros de Google Drive. Incluye Matemáticas, Ciencias Naturales y las otras materias registradas por docentes. El tercer apartado debe concentrarse exclusivamente en los grupos apadrinados CLEI 3B y CLEI 5-6.

DATOS CONSOLIDADOS:
{compact_summary}

Entrega un análisis profesional, prudente y accionable. Diferencia hechos observados de posibles situaciones. No diagnostiques problemas personales ni inventes causas. Cuando propongas una situación posible, usa lenguaje como "podría estar relacionado con" y recomienda verificarla con observación, conversación o seguimiento.

Devuelve exclusivamente JSON válido con esta estructura exacta:
{{
  "teacher_overview": {{"title":"...","summary":"...","findings":["mínimo 3"],"possible_situations":["mínimo 2"],"actions":["mínimo 3"]}},
  "subjects_analysis": {{"title":"...","summary":"...","findings":["mínimo 3"],"possible_situations":["mínimo 2"],"actions":["mínimo 3"]}},
  "padrino_analysis": {{"title":"...","summary":"...","findings":["mínimo 3"],"possible_situations":["mínimo 2"],"actions":["mínimo 3"]}},
  "limitations":["mínimo 2 limitaciones o verificaciones necesarias"]
}}

La primera sección debe interpretar todos los CLEI en el rol docente de Matemáticas y Ciencias Naturales.
La segunda debe comparar las dos materias propias con las otras materias, señalando patrones de asistencia, cobertura, desempeño y coincidencias.
La tercera debe analizar CLEI 3B y CLEI 5-6 con prioridad, incluyendo estudiantes, grupos, asistencia, ausencias, materias, fuentes, observaciones nominales y cualquier patrón repetido. Redacta un informe completo: situación de cada grupo, prioridades individuales, posibles explicaciones prudentes, acciones inmediatas, acciones de aula y un plan de verificación para las próximas semanas.
Escribe en español profesional, con lenguaje claro para tomar decisiones pedagógicas."""
    body = {
        "system_instruction": {"parts": [{"text": "Devuelve únicamente JSON válido y no inventes datos que no estén en el consolidado."}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.25, "candidateCount": 1, "maxOutputTokens": 7000, "responseMimeType": "application/json"},
    }
    endpoint = GEMINI_API_URL.format(model=model) + "?key=" + api_key
    http_request = request.Request(endpoint, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(http_request, timeout=timeout) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise GeminiPlanningError(f"Gemini rechazó el análisis ({exc.code}). Detalle: {detail}") from exc
    except error.URLError as exc:
        raise GeminiPlanningError(f"No fue posible conectarse con Gemini para el seguimiento. Detalle: {exc.reason}") from exc
    except TimeoutError as exc:
        raise GeminiPlanningError("El análisis de seguimiento agotó el tiempo de espera.") from exc
    except json.JSONDecodeError as exc:
        raise GeminiPlanningError("Gemini devolvió una respuesta no válida para el seguimiento.") from exc
    try:
        text_response = response_payload["candidates"][0]["content"]["parts"][0]["text"]
        generated = json.loads(text_response)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise GeminiPlanningError("Gemini no devolvió la estructura esperada para el seguimiento.") from exc
    return _validate_followup_analysis(generated)
