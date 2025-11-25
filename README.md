# Performance Analyzer AI — README Único (Guía Integral para Copiar y Pegar)

## 1. Visión, Alcance y Propuesta de Valor
**Performance Analyzer AI** es un servicio **API** diseñado para transformar resultados de pruebas de rendimiento en **insumos claros para negocio**. Recibe **un archivo** por solicitud —**JSON de k6** o **CSV de JMeter**—, construye un **resumen (summary) compacto y confiable** por operación/etiqueta y, con base en ese summary, solicita a una **IA** un **informe ejecutivo en español**, sin tecnicismos, con **veredicto (Bueno/Regular/Malo)**, **riesgos**, **recomendaciones** y **próximos pasos**.  
La IA **no** recibe el archivo crudo, solo el summary. Esto **ahorra costos**, mejora la latencia y estandariza la salida para el front.

**Objetivos clave del MVP**
- Procesar k6 (JSON) y JMeter (CSV) con parsers desacoplados.
- Generar un summary **unificado** (contrato común) para IA y front.
- Producir informe de IA con lenguaje natural y entendible (no técnico).
- Controles de tamaño, reintentos y “bypass IA” para pruebas y costos.
- Entregable listo para ejecutarse localmente y versionarse en Git.

---

## 2. Arquitectura y Estructura del Proyecto

**Diseño simple, modular y desacoplado**
- **API (FastAPI)**: exposición HTTP, validación de entrada, orquestación.
- **Aplicación**: detección de tipo de archivo y armado de summary.
- **Servicios (parsers)**: k6 y JMeter por separado, ambos emiten el contrato de summary.
- **Dominio (contratos)**: estructura única de summary para IA y front.
- **Infraestructura (IA)**: cliente Azure OpenAI con control de longitudes y reintentos.
- **Core (utilidades)**: percentiles y tiempos si aplica.

**Árbol de carpetas (referencial)**

.
├─ .gitignore # Ignora .env, .venv, pycache, etc.
├─ .env.example # Plantilla de variables (sin secretos reales)
├─ requirements.txt # Dependencias mínimas del MVP
├─ README.md # Este documento
├─ samples/
│ ├─ k6_sample.json # Ejemplo de k6 (JSON)
│ └─ jmeter_sample.csv # Ejemplo de JMeter (CSV)
└─ src/
├─ init.py
├─ api/
│ ├─ init.py
│ ├─ app.py # Crea FastAPI, CORS y registra rutas
│ └─ routes/
│ ├─ init.py
│ └─ summary_route.py # POST /summary (carga archivo → summary → IA)
├─ application/
│ ├─ init.py
│ ├─ summary_service.py # Detecta tipo e invoca parser
│ └─ ai_prompt_builder.py # Prompts en español, no técnicos (modos: standard/concise/resilient)
├─ core/
│ ├─ init.py
│ ├─ percentiles.py # Cálculo/normalización de percentiles (si aplica)
│ └─ time_utils.py # Utilidades de tiempo (si aplica)
├─ domain/
│ ├─ init.py
│ └─ summary_contract.py # Contrato de summary unificado
├─ infrastructure/
│ ├─ init.py
│ └─ ai/
│ ├─ init.py
│ └─ azure_openai_service.py # Cliente Azure OpenAI (o4-mini), presupuesto y reintentos
└─ services/
├─ init.py
├─ k6_summary.py # Parser k6 → summary
└─ jmeter_summary.py # Parser JMeter → summary


**Rol de cada componente**
- `src/api/app.py`: instancia FastAPI, CORS (si aplica) y monta la ruta `/summary`.
- `src/api/routes/summary_route.py`: endpoint **POST /summary** (multipart/form-data con `file`):
  - Guarda el archivo por **chunks** (memoria controlada).
  - Llama `detect_and_build_summary(file_path, filename, content_type)`.
  - Si `AI_BYPASS=false`, invoca IA con **solo** el summary.
  - Devuelve `{ provider, ai_report, usage, debug, summary? }`.
- `src/application/summary_service.py`: lógica de negocio para detectar k6/JMeter y construir summary.
- `src/application/ai_prompt_builder.py`: construcción de prompts en **español no técnico** con estructura de salida fija; modos:
  - **standard** (140–200 palabras), **concise** (90–140 palabras) y **resilient** (dice “no disponible” si faltan datos).
- `src/services/k6_summary.py`: lectura/agrupación de métricas de k6 por operación (nombres legibles).
- `src/services/jmeter_summary.py`: lectura/agrupación de JMeter por `label` (nombre de operación).
- `src/domain/summary_contract.py`: definiciones de **summary** (campos esperados).
- `src/infrastructure/ai/azure_openai_service.py`: cliente Azure OpenAI (SDK `openai`), **sin** parámetros no soportados por o4-mini (p. ej., `temperature` ≠ 1), con reintentos y presupuestos de tokens.
- `src/core/*`: utilidades de percentiles/tiempos si son necesarias para el agregado.

---

## 3. Contrato del Summary (salida de los parsers)
El **summary** es el insumo que viaja a la IA y que puede exponerse al front en DEV. Debe ser **compacto**, **verificable** y **suficiente** para un informe no técnico.

**Estructura general (ejemplo orientativo)**
```json
{
  "source": "k6|jmeter",
  "aggregate": {
    "total_requests": 12345,
    "total_errors": 12,
    "error_rate_pct": 0.10,
    "approx_duration_ms": 60000,
    "notes": "Campos opcionales y solo si existen en el insumo"
  },
  "by_operation": [
    {
      "name": "Servicio/Operacion o label",
      "count": 3263,
      "errors": 0,
      "error_rate_pct": 0.0,
      "p95_ms": 800,
      "p90_ms": 600,
      "avg_ms": 350
    }
  ],
  "meta": {
    "from_file": "nombre.json|csv",
    "generated_at": "ISO8601",
    "version": "1.0"
  }
}

    Nota: Solo incluir campos disponibles. Si no existe el dato, no inventarlo. El cálculo de p95_ms y agregados se hace en los parsers con cuidado (evitar promediar percentiles; preferir percentiles por operación si se dispone de distribución).

4. Variables de Entorno (archivo .env)

Regla de seguridad: .env real no se versiona. Se versiona .env.example con placeholders.

Plantilla recomendada para .env

# ===== Azure OpenAI =====
AZURE_OPENAI_ENDPOINT=https://<tu-endpoint>.openai.azure.com/
AZURE_OPENAI_API_KEY=<TU-CLAVE-REAL>
AZURE_OPENAI_DEPLOYMENT_LIST=o4-mini,gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# ===== IA (control de salida y reintentos) =====
AI_ENFORCE_JSON=false              # con o4-mini dejar en false
AI_REASONING_EFFORT=low            # razonamiento moderado → menos respuestas vacías
AI_MAX_TOKENS=1024                 # presupuesto inicial
AI_RETRY_BOOST=768                 # incremento 2º intento si quedó corto
AI_MAX_TOKENS_CAP=3072             # tope absoluto 3º intento
AI_PROMPT_MODE=standard            # standard | resilient (si faltan datos, diga “no disponible”)

# ===== API (visibilidad y pruebas) =====
API_INCLUDE_SUMMARY=true           # en dev: ver el summary (trazabilidad)
AI_BYPASS=false                    # true: no llama IA; responde solo con summary (pruebas de parsers)

Ajustes prácticos

    Respuestas vacías o cortadas: subir AI_MAX_TOKENS a 1536 y AI_RETRY_BOOST a 1024.

    Entradas incompletas: AI_PROMPT_MODE=resilient.

    Producción: considerar API_INCLUDE_SUMMARY=false para no exponer el summary al front.

5. Instalación y Ejecución Local (Windows / PowerShell)

Requisitos: Python 3.11+, conexión a internet para dependencias, clave Azure OpenAI válida.

Pasos

    Abrir la carpeta del proyecto en VS Code.

    Crear y activar entorno virtual:

        python -m venv .venv

        . .\.venv\Scripts\Activate.ps1

    Actualizar pip e instalar dependencias:

        python -m pip install --upgrade pip

        pip install -r requirements.txt

    Crear .env desde el ejemplo:

        Copy-Item .env.example .env

        Editar .env con endpoint, key y deployments reales.

    Ejecutar la API:

        python -m uvicorn src.api.app:app --reload

    Probar con k6 (JSON):

        curl -X POST "http://127.0.0.1:8000/summary" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@samples/k6_sample.json"

    Probar sin IA (solo summary):

        Cerrar servidor, setear AI_BYPASS=true, relanzar uvicorn y repetir el curl.

6. Flujo del Endpoint /summary (E2E)

    Recepción del archivo por multipart/form-data, guardado por chunks (memoria controlada).

    Detección de tipo (k6/JMeter) en summary_service.

    Construcción de summary (parsers):

        k6: agregación por operación (por ejemplo, Servicio/Operación), errores y tiempos típicos.

        JMeter: agregación por label, errores y tiempos típicos.

    Llamada a IA (si AI_BYPASS=false): se envía solo el summary. Prompts en español no técnico.

    Respuesta JSON:

        provider: metadatos del modelo.

        ai_report: veredicto, puntos clave, riesgos, recomendaciones, próximos pasos (en español).

        usage: consumo de tokens reportado.

        debug: tiempos, bytes del archivo y del summary, estimación de tokens de prompt, etc.

        summary: incluido si API_INCLUDE_SUMMARY=true (útil en DEV).

Contrato de salida (200)

{
  "provider": { "name": "azure-openai", "model": "o4-mini", "api_version": "2024-12-01-preview" },
  "ai_report": {
    "summary_title": "string",
    "summary_text": "string (empieza con “Veredicto: Bueno/Regular/Malo.”, sin jerga)",
    "highlights": ["..."],
    "risks": ["..."],
    "recommendations": ["..."],
    "next_steps": ["..."]
  },
  "usage": { "model": "o4-mini", "prompt_tokens": 123, "completion_tokens": 456, "total_tokens": 579 },
  "debug": {
    "elapsed_ms": 842,
    "raw_input_bytes": 5123456,
    "summary_json_bytes": 7432,
    "summary_prompt_tokens_estimated": 1858,
    "filename": "k6_sample.json",
    "content_type": "application/json",
    "ai_bypass": false
  },
  "summary": { "...summary compacto..." }  # presente si API_INCLUDE_SUMMARY=true
}

Errores esperables

    400 Error leyendo archivo: archivo corrupto o mal subida multipart.

    400 Error construyendo summary: formato no reconocido o faltan columnas/claves base.

    502 Fallo consultando AI: revisar endpoint, deployment, versión y presupuestos de tokens.

    502 Contenido IA vacío: subir AI_MAX_TOKENS/AI_RETRY_BOOST o usar modo concise/resilient.