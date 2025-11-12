from dotenv import load_dotenv
load_dotenv()  # lee .env en local

from fastapi import FastAPI
from src.api.routes.summary_route import router as summary_router

app = FastAPI(title="Performance Analyzer AI", version="1.0.0")

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(summary_router)