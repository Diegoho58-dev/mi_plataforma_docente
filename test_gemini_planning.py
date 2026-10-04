import os

from gemini_planning import GeminiPlanningError, _build_prompt, _validate_proposal, generate_planning_proposal

prompt = _build_prompt(
    "Matemáticas",
    "CLEI 4",
    "Operaciones con números enteros",
    [{"objetivo": "Resolver situaciones sencillas.", "articulacion_monitor": "El monitor orienta y verifica los procedimientos."}],
)
assert "Operaciones con números enteros" in prompt
assert "CLEI 4" in prompt
assert '"objetivo"' in prompt
assert '"articulacion_monitor"' in prompt

proposal = _validate_proposal({
    "objetivo": "Relacionar las operaciones con situaciones cotidianas.",
    "articulacion_monitor": "El monitor acompaña la resolución y verifica los procedimientos.",
})
assert proposal["objetivo"].startswith("Relacionar")
assert proposal["articulacion_monitor"].startswith("El monitor")

long_proposal = _validate_proposal({
    "objetivo": "Objetivo amplio. " * 300,
    "articulacion_monitor": "El monitor acompaña. " * 300,
})
assert len(long_proposal["objetivo"]) <= 1801
assert len(long_proposal["articulacion_monitor"]) <= 2201
assert long_proposal["objetivo"].endswith("…")

try:
    _validate_proposal({"objetivo": "", "articulacion_monitor": ""})
except GeminiPlanningError:
    pass
else:
    raise AssertionError("Debe rechazar una propuesta incompleta")

os.environ.pop("GEMINI_API_KEY", None)
try:
    generate_planning_proposal("Matemáticas", "CLEI 4", "Tema de prueba")
except GeminiPlanningError as error:
    assert "GEMINI_API_KEY" in str(error)
else:
    raise AssertionError("Debe exigir la clave en el servidor")

print("OK: prompt y validaciones de Gemini funcionan sin llamar a la API.")
