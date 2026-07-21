.PHONY: install lint test run migrate up down build

install:
	pip install -e ".[dev]"

lint:
	ruff check src tests
	mypy

test:
	pytest -q

run:
	uvicorn copilot.api.main:app --reload --port 8000

migrate:
	alembic upgrade head

up:
	docker compose up --build

down:
	docker compose down

build:
	docker build -t copilot-api:local .
