from fastapi.responses import JSONResponse

def problem(status: int, title: str, detail: str, extra: dict | None = None):
    payload = {
        "type": "about:blank",
        "title": title,
        "status": status,
        "detail": detail,
        "extra": extra or {}
    }
    return JSONResponse(status_code=status, content=payload)