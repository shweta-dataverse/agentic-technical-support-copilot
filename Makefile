.PHONY: install lint test run up down build

install:
	pip install -e ".[dev]"

lint:
	ruff check src tests

test:
	pytest -q

run:
	uvicorn copilot.api.main:app --reload --port 8000

up:
	docker compose up --build

down:
	docker compose down

build:
	docker build -t copilot-api:local .
