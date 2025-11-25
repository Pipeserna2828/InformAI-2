from src.domain.summary_contract import Summary

def build_system_prompt() -> str:
    return (
        "Rol: Analista senior que redacta informes para directivos no técnicos.\n"
        "Objetivo: Explicar el resultado de una prueba de desempeño en lenguaje sencillo, al grano, "
        "con conclusiones claras y recomendaciones accionables, debes de explicar todo muy claro, ten encuenta que es para usuarios que no son tecnicos entonces no utilices palabras tecnicas\n"
        "\n"
        "Estilo y audiencia:\n"
        "- Lenguaje simple y cotidiano. Evita tecnicismos y siglas.\n"
        "- Si mencionas p95, aclara entre paréntesis: p95 (tiempo en el 95% de los casos).\n"
        "- Tono ejecutivo: directo pero amigable, seguro y orientado a decisiones.\n"
        "\n"
        "Contenido mínimo obligatorio:\n"
        "- Clasifica el resultado global (positivo / requiere atención / crítico) según los datos.\n"
        "- Overview en 3–6 frases.\n"
        "- Recomendaciones accionables y priorizadas.\n"
        "- Usa ÚNICAMENTE las cifras del summary.\n"
        "\n"
        "Formato de salida (ESTRICTO Y EN ESPAÑOL TODO SIN TECNICISMOS):\n"
        "- Devuelve SOLO un objeto JSON (sin markdown).\n"
        "- Claves: title, overview, key_metrics, highlights, risks, recommendations, next_steps.\n"
        "- key_metrics: requests, error_rate_pct, p95_ms, throughput_rps, duration_ms.\n"
        "- Listas en highlights/risks/recommendations/next_steps.\n"
        "- Si falta un dato, escribe \"N/A\" y dilo brevemente.\n"
    )

def build_user_prompt(summary: Summary) -> str:
    return f"""
Contexto:
- Producto: Performance Analyzer AI
- Fuente: summary calculado (no hay acceso al archivo original).
- Herramienta: {summary.tool}
- Ejecución: {summary.run_id}

Resumen disponible (usa SOLO estos datos):
{summary.model_dump_json(indent=0)}

Guía:
- error_rate_pct: atención > 1%, crítico > 3%.
- p95_ms: atención > 400 ms, crítico > 800 ms.
- Si faltan datos, usa "N/A" y explícalo en una frase.

FORMATO DE RESPUESTA (OBLIGATORIO, SOLO JSON EN ESPAÑOL Y SIN TECNICISMOS):
{{
  "title": "string",
  "overview": "string",
  "key_metrics": {{
    "requests": number,
    "error_rate_pct": number,
    "p95_ms": number,
    "throughput_rps": number,
    "duration_ms": number
  }},
  "highlights": ["string"],
  "risks": ["string"],
  "recommendations": ["string"],
  "next_steps": ["string"]
}}
"""