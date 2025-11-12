FROM python:3.11-slim

WORKDIR /app

# Poetry
RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* /app/
RUN poetry install --no-interaction --no-ansi

COPY src /app/src
COPY README.md /app/README.md

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
