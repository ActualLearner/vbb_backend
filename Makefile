# Makefile for the TeamFlow project
# ----------------------------------
# This file provides commands for managing the development environment and running tasks.

# Use a variable for the compose file to avoid repetition
COMPOSE_FILE = -f compose.yaml

# Phony targets tell Make that these are not files. This is a best practice.
.PHONY: help up up-build down down-vol setup migrate test shell logs format lint

# --- High-Level Commands ---

help: ## ✨ Show this help message
	@echo "Usage: make [command]"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## 🛠️  Run the full setup: build, start services, and migrate
	make up-build
	make migrate
	@echo "✅ Project setup complete! Server is running in the background."

# --- Development Environment ---

up: ## 🚀 Start services in the background
	docker compose $(COMPOSE_FILE) up -d web db

up-build: ## 🔨 Rebuild images and start services
	docker compose $(COMPOSE_FILE) up --build -d web db

down: ## 🛑 Stop the services
	docker compose $(COMPOSE_FILE) down

down-vol: ## 💥 Stop services and remove database volumes (destructive!)
	docker compose $(COMPOSE_FILE) down -v

logs: ## 📜 Follow logs for the web service
	docker compose $(COMPOSE_FILE) logs -f web

# --- Code Quality ---

format: ## 🎨 Auto-formats all Python code
	@echo "Formatting code with black and isort..."
	docker compose $(COMPOSE_FILE) run --rm lint "./scripts/format.sh"

lint: ## 🔎 Check for linting errors and formatting issues
	@echo "Running lint and format checks..."
	docker compose $(COMPOSE_FILE) run --rm lint

qa: lint test ## ✅ Run all quality checks (linting and testing)
	@echo "\n✅ All quality checks passed!"

# --- One-off Task Commands ---

migrate: ## 🏃 Run database migrations
	@echo "Running database migrations..."
	docker compose $(COMPOSE_FILE) exec web python manage.py migrate

test: ## 🧪 Run the pytest test suite
	@echo "Running tests..."
	docker compose $(COMPOSE_FILE) run --rm test

shell: ## 💻 Open a shell inside the web container
	@echo "Starting a new shell..."
	docker compose $(COMPOSE_FILE) exec web sh

superuser: ## 👑 Create a new Django superuser
	docker compose $(COMPOSE_FILE) exec web python manage.py createsuperuser
