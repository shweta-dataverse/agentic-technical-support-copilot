.PHONY: install lint test run migrate check-azure up down build

install:
	pip install -e ".[dev]"
	python -m spacy download en_core_web_sm

lint:
	ruff check src tests
	mypy

test:
	pytest -q

run:
	uvicorn copilot.api.main:app --reload --port 8000

migrate:
	alembic upgrade head

check-azure:
	python scripts/check_azure_openai.py

search-indexes:
	python scripts/create_search_indexes.py

ingest:
	python -m copilot.ingestion.cli data/raw/manuals

up:
	docker compose up --build

down:
	docker compose down

build:
	docker build -t copilot-api:local .
