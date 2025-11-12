import os, json
from typing import Tuple
from openai import AzureOpenAI
from src.domain.summary_contract import Summary, AIReport, TokenUsage
from src.application.ai_prompt_builder import build_system_prompt, build_user_prompt

def _client_or_none():
    ep  = os.getenv("AZURE_OPENAI_ENDPOINT")
    key = os.getenv("AZURE_OPENAI_API_KEY")
    dep = os.getenv("AZURE_OPENAI_DEPLOYMENT") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    ver = os.getenv("AZURE_OPENAI_API_VERSION") or "2024-08-01-preview"
    if not (ep and key and dep):
        return None, None, None
    client = AzureOpenAI(api_key=key, api_version=ver, azure_endpoint=ep)
    return client, dep, ver

def _parse_ai_json(content: str) -> AIReport:
    data = json.loads(content)
    data.setdefault("highlights", [])
    data.setdefault("risks", [])
    data.setdefault("recommendations", [])
    data.setdefault("next_steps", [])
    return AIReport(**data)

def generate_ai_report(summary: Summary) -> Tuple[AIReport, TokenUsage, str]:
    client, deployment, _ = _client_or_none()
    if client is None:
        # Modo MOCK: informe básico sin costos de tokens
        ai_report = AIReport(
            title="Resumen Ejecutivo (mock)",
            overview="Ejecución local sin AI configurada. Conecta AZURE_* para informe enriquecido.",
            key_metrics={
                "requests": summary.overall.requests,
                "error_rate_pct": round(summary.overall.error_rate * 100.0, 2),
                "p95_ms": round(summary.overall.latency_ms.p95, 2),
                "throughput_rps": round(summary.overall.throughput_rps, 2),
                "duration_ms": summary.overall.duration_ms
            },
            highlights=["Pipeline OK", "Parsers operativos", "Contrato uniforme"],
            risks=[], recommendations=[], next_steps=[]
        )
        usage = TokenUsage()
        return ai_report, usage, "mock"

    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(summary)

    # Intento con JSON puro (json_object) para máxima compatibilidad
    resp = client.chat.completions.create(
        model=deployment,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    msg = resp.choices[0].message.content
    ai_report = _parse_ai_json(msg)
    usage = TokenUsage(
        prompt_tokens=getattr(resp.usage, "prompt_tokens", 0),
        completion_tokens=getattr(resp.usage, "completion_tokens", 0),
        total_tokens=getattr(resp.usage, "total_tokens", 0),
        model=deployment,
    )
    return ai_report, usage, "azure-json-object"