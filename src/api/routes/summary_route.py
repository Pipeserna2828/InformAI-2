import os, uuid
from fastapi import APIRouter, UploadFile
from src.core.errors import problem
from src.application.summary_service import detect_and_build_summary
from src.infrastructure.ai.azure_openai_service import generate_ai_report
from src.domain.summary_contract import AnalyzeResponse

router = APIRouter()

try:
    MAX_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))
except ValueError:
    MAX_MB = 50

@router.post("/summary", response_model=AnalyzeResponse)
async def summary(file: UploadFile):
    if not file:
        return problem(400, "Archivo requerido", "Adjunta un único archivo.")

    if file.content_type not in ("application/json", "text/csv", "application/vnd.ms-excel"):
        return problem(415, "Tipo no soportado",
                       "Solo se aceptan JSON (k6) o CSV (JMeter).",
                       {"content_type": file.content_type})

    content = await file.read()
    if len(content) > MAX_MB * 1024 * 1024:
        return problem(413, "Archivo demasiado grande",
                       f"Máximo permitido: {MAX_MB}MB.",
                       {"size_bytes": len(content)})

    try:
        summary_obj, flags = detect_and_build_summary(content, file.filename, file.content_type)
    except KeyError as e:
        return problem(422, "Estructura incompleta", str(e))
    except ValueError as e:
        return problem(400, "Archivo ilegible", str(e))
    except Exception as e:
        return problem(500, "Error procesando archivo", f"{type(e).__name__}: {e}")

    try:
        ai_report, usage, ai_mode = generate_ai_report(summary_obj)
    except Exception as e:
        return problem(502, "Fallo consultando AI", f"{type(e).__name__}: {e}")

    return AnalyzeResponse(
        summary=summary_obj,
        ai_report=ai_report,
        token_usage=usage,
        metadata={
            "request_id": str(uuid.uuid4()),
            "tool_detected": summary_obj.tool,
            "input_size_bytes": len(content),
            "flags": flags,
            "ai_mode": ai_mode
        }
    )
