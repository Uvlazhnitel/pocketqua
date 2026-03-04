PYTHON ?= python3.12

.PHONY: run-api run-bot test lint

run-api:
	$(PYTHON) -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

run-bot:
	$(PYTHON) -m bot.main

test:
	$(PYTHON) -m pytest -q

lint:
	@echo "lint target is optional for MVP"
