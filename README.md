# Performance Analyzer AI (MVP)

API FastAPI que:
1) Recibe resultados de performance (K6 JSON o JMeter CSV),
2) Calcula un summary consistente (global y por método),
3) (Opcional) Genera informe ejecutivo no técnico vía Azure OpenAI (si hay .env).

## Run local
```powershell
cd "C:\ruta\InformAI-2"
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env  # edita .env si usarás Azure; si no, se usa modo mock
python -m uvicorn src.api.app:app --reload

Health: http://127.0.0.1:8000/health
Docs: http://127.0.0.1:8000/docs

curl -X POST "http://127.0.0.1:8000/summary" -F "file=@samples/k6_sample.json"
curl -X POST "http://127.0.0.1:8000/summary" -F "file=@samples/jmeter_sample.csv"
