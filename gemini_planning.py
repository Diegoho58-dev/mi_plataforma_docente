"""Integración segura con Gemini para proponer objetivo y articulación pedagógica."""

import json
import os
from urllib import error, request


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-2.5-flash-lite"


class GeminiPlanningError(RuntimeError):
    """Error controlado al solicitar o validar una propuesta de planeación."""


def _build_prompt(subject, clei, theme, previous_examples):
    examples = previous_examples or []
    example_text = "\n".join(
        f"Ejemplo {index}:\nObjetivo: {item.get('objetivo', '')}\n"
        f"Articulación con el monitor: {item.get('articulacion_monitor', '')}"
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
        raise GeminiPlanningError("Gemini no devolvió un objeto JSON.")
    objective = " ".join(str(payload.get("objetivo", "")).split()).strip()
    articulation = " ".join(str(payload.get("articulacion_monitor", "")).split()).strip()
    if not objective or not articulation:
        raise GeminiPlanningError("La propuesta de Gemini no contiene objetivo y articulación completos.")
    if len(objective) > 1200 or len(articulation) > 1600:
        raise GeminiPlanningError("La propuesta de Gemini excede la longitud permitida.")
    return {"objetivo": objective, "articulacion_monitor": articulation}


def generate_planning_proposal(subject, clei, theme, previous_examples=None, timeout=30):
    """Genera una propuesta sin escribirla en Drive.

    La clave se toma exclusivamente de GEMINI_API_KEY. La función devuelve solo
    objetivo y articulación validados para que la capa web decida cuándo guardar.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise GeminiPlanningError("Falta configurar GEMINI_API_KEY en el entorno del servidor.")
    if not str(theme).strip():
        raise GeminiPlanningError("No se puede generar una propuesta sin tema curricular.")

    model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    prompt = _build_prompt(subject, clei, theme, previous_examples)
    body = {
        "system_instruction": {
            "parts": [{"text": "Devuelve únicamente JSON válido y no inventes información curricular."}]
        },
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.35,
            "candidateCount": 1,
            "maxOutputTokens": 700,
            "responseMimeType": "application/json",
        },
    }
    endpoint = GEMINI_API_URL.format(model=model) + "?key=" + api_key
    http_request = request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=timeout) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        if exc.code == 429:
            raise GeminiPlanningError("Gemini alcanzó el límite gratuito. Intenta nuevamente más tarde.") from exc
        raise GeminiPlanningError(f"Gemini rechazó la solicitud ({exc.code}).") from exc
    except (error.URLError, TimeoutError) as exc:
        raise GeminiPlanningError("No fue posible conectarse con Gemini.") from exc
    except json.JSONDecodeError as exc:
        raise GeminiPlanningError("Gemini devolvió una respuesta no válida.") from exc

    try:
        text = response_payload["candidates"][0]["content"]["parts"][0]["text"]
        generated = json.loads(text)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise GeminiPlanningError("Gemini no devolvió el JSON esperado.") from exc
    return _validate_proposal(generated)
