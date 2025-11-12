import os, httpx
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv(".env")

EP   = os.getenv("AZURE_OPENAI_ENDPOINT")
KEY  = os.getenv("AZURE_OPENAI_API_KEY")
DEP  = os.getenv("AZURE_OPENAI_DEPLOYMENT")
VER  = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
PROXY = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")

http_client = httpx.Client(proxies=PROXY, timeout=30) if PROXY else None
client = AzureOpenAI(api_key=KEY, api_version=VER, azure_endpoint=EP, http_client=http_client)

resp = client.chat.completions.create(
    model=DEP,
    messages=[
        {"role": "system", "content": "Responde solo 'OK'. Sé conciso. No incluyas explicaciones."},
        {"role": "user", "content": "Di solo: OK"}
    ],
    max_completion_tokens=1000  # <-- subimos el budget
)
print("RAW usage:", resp.usage)
print("Salida:", repr(resp.choices[0].message.content))
