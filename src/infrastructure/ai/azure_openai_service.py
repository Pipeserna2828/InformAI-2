    # Servicio de integración con Azure OpenAI para generar el informe ejecutivo

import os
import json
from typing import Tuple, Optional

import httpx
from openai import AzureOpenAI
from openai import APIConnectionError, APIError, AuthenticationError, RateLimitError

from src.domain.summary_contract import Summary, AIReport, TokenUsage
from src.application.ai_prompt_builder import build_system_prompt, build_user_prompt


# ------------------------------- Helpers ------------------------------------ #

def _strict() -> bool:
    """Devuelve True si debemos fallar en cualquier inconsistencia (modo estricto)."""
    return os.getenv("AI_STRICT", "true").strip().lower() in ("1", "true", "yes", "y")


def _max_tokens() -> int:
    """Lee el presupuesto máximo de tokens de salida para la IA."""
    try:
        return int(os.getenv("AI_MAX_TOKENS", "1024"))
    except ValueError:
        return 1024


def _client_or_raise() -> Tuple[AzureOpenAI, str]:
    """
    Construye el cliente de Azure OpenAI y devuelve (client, deployment).
    Lanza RuntimeError si faltan variables de entorno.
    """
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    # Permitimos dos nombres de variable por compatibilidad:
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview"

    if not endpoint or not api_key or not deployment:
        raise RuntimeError(
            "Azure OpenAI sin configurar: faltan AZURE_OPENAI_ENDPOINT, "
            "AZURE_OPENAI_API_KEY o AZURE_OPENAI_DEPLOYMENT"
        )

    proxies = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
    http_client = httpx.Client(proxies=proxies, timeout=60.0) if proxies else None

    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=endpoint,
        http_client=http_client,
    )
    return client, deployment


def _parse_ai_json_strict(content: str) -> AIReport:
    """
    Parsea la respuesta JSON de la IA a nuestro contrato AIReport.
    Si faltan campos, los rellena con defaults.
    """
    data = json.loads(content)

    # Garantiza llaves esperadas por el contrato (por si el modelo no las envía todas).
    data.setdefault("summary_title", "")
    data.setdefault("summary_text", "")
    data.setdefault("highlights", [])
    data.setdefault("risks", [])
    data.setdefault("recommendations", [])
    data.setdefault("next_steps", [])

    return AIReport(**data)


def _is_o4_family(deployment: str) -> bool:
    """Detecta si el deployment pertenece a la familia o4* (razonamiento)."""
    return deployment.lower().startswith("o4")


# ------------------------------ API Principal ------------------------------- #

def generate_ai_report(summary: Summary) -> Tuple[AIReport, TokenUsage, str]:
    """
    Genera el informe ejecutivo usando Azure OpenAI.
    Retorna: (AIReport, TokenUsage, "azure")

    Comportamiento:
    - Si AI_ENFORCE_JSON=true y el modelo NO es o4*, se envía response_format=json_object.
    - Si el modelo es o4* (p. ej. o4-mini), NO se envía response_format.
      En ese caso el prompt exige JSON y validamos con json.loads().
      Si AI_STRICT=true y no es JSON válido, se lanza excepción (FastAPI responderá 502).
    """
    client, deployment = _client_or_raise()

    # Prompts
    system_prompt = build_system_prompt()     # enfoque ejecutivo, no técnico
    user_prompt = build_user_prompt(summary)  # JSON del summary + instrucciones

    # Presupuesto de salida (para evitar que reasoning consuma todo).
    budget = _max_tokens()

    # ¿Forzamos JSON? (solo si NO es o4*)
    enforce_json = os.getenv("AI_ENFORCE_JSON", "false").strip().lower() in ("1", "true", "yes", "y")
    is_o4 = _is_o4_family(deployment)

    params = {
        "model": deployment,  # nombre EXACTO del deployment en Azure
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        # ¡OJO! o4-mini no acepta temperature != default, así que NO lo enviamos.
        "max_completion_tokens": budget,
    }

    # Solo forzamos response_format cuando NO es o4* (los o4* suelen ignorarlo o rechazarlo)
    if enforce_json and not is_o4:
        params["response_format"] = {"type": "json_object"}

    try:
        resp = client.chat.completions.create(**params)

        # Uso de tokens (si el SDK lo entrega)
        usage = TokenUsage(
            prompt_tokens=getattr(resp.usage, "prompt_tokens", 0),
            completion_tokens=getattr(resp.usage, "completion_tokens", 0),
            total_tokens=getattr(resp.usage, "total_tokens", 0),
            model=getattr(resp, "model", deployment),
        )

        content: Optional[str] = None
        if resp.choices and resp.choices[0].message:
            content = resp.choices[0].message.content

        if not content:
            # Muchos o4* pueden gastar el budget en reasoning dejando content vacío.
            # En modo estricto, fallamos explícitamente con un mensaje claro.
            raise ValueError(
                "La IA devolvió contenido vacío (posible 'finish_reason=length' con razonamiento). "
                "Incrementa AI_MAX_TOKENS o endurece el prompt para respuestas más cortas."
            )

        # Si forzamos JSON y no es o4*, parseamos directo.
        if enforce_json and not is_o4:
            ai_report = _parse_ai_json_strict(content)
        else:
            # En o4*, pedimos JSON por prompt y validamos aquí.
            try:
                ai_report = _parse_ai_json_strict(content)
            except Exception:
                if _strict():
                    raise ValueError("La IA respondió en formato no JSON y AI_STRICT=true.")
                # Si no es estricto, se podría hacer un fallback a texto plano:
                # ai_report = AIReport(summary_title="Informe", summary_text=content, highlights=[], risks=[], recommendations=[], next_steps=[])
                raise

        return ai_report, usage, "azure"

    except (APIConnectionError, AuthenticationError, RateLimitError, APIError) as e:
        # Errores propios de red/autenticación/rate. Dejar que FastAPI los maneje con 502/401/etc.
        raise
    except Exception:
        # Cualquier otra excepción también se propaga; el controlador HTTP la mapea a 5xx con detalle.
        raise
