.PHONY: install lint test run migrate check-azure search-indexes ingest search resolve worker ui eval eval-fast infra-plan infra-up infra-down up up-async down build

install:
	pip install -e ".[dev]"
	python -m spacy download en_core_web_md

lint:
	ruff check src tests ui
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

search:
	python -m copilot.retrieval.cli "$(q)" --index $(or $(index),manuals)

resolve:
	python -m copilot.agents.cli "$(title)" "$(desc)"

worker:
	python -m copilot.worker

eval:
	python scripts/run_eval.py

eval-fast:
	python scripts/run_eval.py --no-judge

ui:
	COPILOT_API_KEY=$${COPILOT_API_KEY:-dev-key-change-me} streamlit run ui/app.py

infra-plan:
	cd infra && terraform plan

infra-up:
	cd infra && terraform apply

infra-down:
	cd infra && terraform destroy

up:
	docker compose up --build

up-async:
	docker compose --profile async up --build

down:
	docker compose down

build:
	docker compose build
