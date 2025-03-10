SHELL := bash

UV := uv
UVICORN := uvicorn
ALEMBIC := alembic

test: ## Run tests
	$(UV) run pytest

lint: ## Lint code
	$(UV) run ruff app tests

install: ## Install dependencies
	$(UV) install

run: ## Run the application
	$(UV) run $(UVICORN) app.main:app --reload --workers 1 --host 0.0.0.0 --port 8000 --env-file .env

migrate: ## Create a new alembic migration with a message
	@read -p "Enter migration message: " msg; \
	$(UV) run $(ALEMBIC) revision --autogenerate -m "$$msg"

upgrade: ## Upgrade the database to the latest revision
	$(UV) run $(ALEMBIC) upgrade head

populate: ## generate data
	$(UV) run -m scripts.populate_database