# One multi-stage Dockerfile, four runtime targets (api, worker, ingest, ui).
# The base stage installs the package and its runtime deps once, so all four
# images share that cached layer. Every image runs as a non-root user.

FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

# install runtime deps only (no dev, no eval), then the spaCy model Presidio needs
COPY pyproject.toml README.md alembic.ini ./
COPY src ./src
RUN pip install . && python -m spacy download en_core_web_sm

# prompt files are data, copied after the dependency layer so the cache holds
COPY prompts ./prompts

RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

# api: FastAPI service
FROM base AS api
EXPOSE 8000
CMD ["uvicorn", "copilot.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# worker: Service Bus consumer
FROM base AS worker
CMD ["python", "-m", "copilot.worker"]

# ingest: one-off vectorization job (reads mounted data/)
FROM base AS ingest
ENTRYPOINT ["python", "-m", "copilot.ingestion.cli"]
CMD ["data/raw/manuals"]

# ui: Streamlit console
FROM base AS ui
COPY ui ./ui
EXPOSE 8501
CMD ["streamlit", "run", "ui/app.py", \
     "--server.port", "8501", "--server.address", "0.0.0.0"]
