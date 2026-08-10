.DEFAULT_GOAL := help

# Read the current version from VERSION file to tag the Docker image
export APP_VERSION := $(shell cat VERSION)

.PHONY: help build up down logs restart sh run-all run-orders run-carts db-query db-find db-del db-search-orders db-search-carts

help: ## Show this help message
	@echo "Usage: make [command]"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- [ DOCKER & INFRASTRUCTURE ] ---

build: ## Build the application Docker image using VERSION file
	@echo "Building image version $${APP_VERSION}..."
	docker compose build

up: ## Start containers in the background
	@echo "Starting containers version $${APP_VERSION}..."
	docker compose up -d

down: ## Stop and remove containers and networks
	docker compose down

logs: ## Tail the logs of all project services in real-time
	docker compose logs -f

restart: down up ## Restart the containers (down followed by up)

sh: ## Open an interactive shell inside the application container
	docker compose exec -it app /bin/bash

# --- [ APPLICATION & WORKERS ] ---

run-all: ## Run the main email orchestrator
	./scripts/run_local.sh all

run-orders: ## Run the Orders worker (STG) in isolation
	./scripts/run_stg.sh

run-carts: ## Run the Abandoned Carts worker (STC) in isolation
	./scripts/run_stc.sh

# --- [ DATABASE ] ---

db-query: ## Run the default SELECT query in the database via psql
	./scripts/query_all.sh

db-find: ## Prompt for an ID and search in the email control table
	@read -p "Enter '<field> <value>' (e.g., cpf 123) or just <ID>: " id; \
	./scripts/find_by_id.sh $$id

db-del: ## Prompt for an ID and physically delete it from the database
	@read -p "Enter '<field> <value>' (e.g., cpf 123) or just <ID> to delete: " id; \
	./scripts/delete_by_id.sh $$id

db-search-orders: ## Search for records with Orders status (STG)
	./scripts/search_stg.sh

db-search-carts: ## Search for records with Abandoned Cart status (STC)
	./scripts/search_stc.sh
