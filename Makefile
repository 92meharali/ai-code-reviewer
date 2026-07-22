COMPOSE = docker compose
API_SERVICE = api

.PHONY: help up down restart logs ps build test shell health env

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

env: backend/.env ## Create backend .env from example if missing
backend/.env:
	cp backend/.env.example backend/.env

up: env ## Build and start services in the background
	$(COMPOSE) up --build -d

down: ## Stop and remove containers
	$(COMPOSE) down

restart: down up ## Restart all services

logs: ## Follow API service logs
	$(COMPOSE) logs -f $(API_SERVICE)

ps: ## Show running containers
	$(COMPOSE) ps

build: ## Build Docker images without starting
	$(COMPOSE) build

test: env ## Run backend tests inside a container
	$(COMPOSE) run --rm --no-deps $(API_SERVICE) pytest -v

shell: env ## Open a shell in the API container
	$(COMPOSE) run --rm --no-deps $(API_SERVICE) sh

health: ## Check API health endpoint
	@curl -sf http://localhost:$${API_PORT:-8000}/health | python3 -m json.tool
