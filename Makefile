.DEFAULT_GOAL := help

# Looks at comments using ## on targets and uses them to produce a help output.
.PHONY: help
help: ALIGN=14
help: ## Print this message
	@awk -F ': .*## ' -- "/^[^':]+: .*## /"' { printf "'$$(tput bold)'%-$(ALIGN)s'$$(tput sgr0)' %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

.PHONY: fmt
fmt: ## Autoformat code with Rye/Ruff
	rye fmt

.PHONY: generate
generate: ## Produce all generated artifacts
generate: generate/sqlc

.PHONY: generate/sqlc
generate/sqlc: ## Generate sqlc code
	cd src/riverqueue/driver/riversqlalchemy/dbsqlc && sqlc generate

.PHONY: lint
lint: ## Run linter with Rye/Ruff
	rye lint

.PHONY: test
test: ## Run test suite with Rye/pytest
	rye test

.PHONY: type-check
type-check: ## Run type check with MyPy
	rye run mypy -p riverqueue -p examples -p tests

.PHONY: verify
verify: ## Verify all generated artifacts
verify: verify/sqlc

.PHONY: verify/sqlc
verify/sqlc: # Verify sqlc code
	cd src/riverqueue/driver/riversqlalchemy/dbsqlc && sqlc verify

.PHONY: setup-db
setup-db:
	@if [ $$(docker ps -aq -f name=local-postgres-no-password) ]; then \
	  echo "Stopping and removing existing Docker container..."; \
	  docker stop local-postgres-no-password >/dev/null; \
	  docker rm local-postgres-no-password >/dev/null; \
	fi

	@echo "Starting PostgreSQL container..."
	docker run --name local-postgres-no-password -d \
	  -e POSTGRES_HOST_AUTH_METHOD=trust \
	  -p 5432:5432 \
	  postgres:latest

	@echo "Waiting for PostgreSQL to start..."
	sleep 5
	
	@echo "Creating PostgreSQL role for user $(USER)..."
	docker exec -i local-postgres-no-password psql -U postgres -c "CREATE ROLE $(USER) WITH LOGIN SUPERUSER;"

	@echo "Creating the river_test database..."
	docker exec -i local-postgres-no-password psql -U postgres -c "CREATE DATABASE river_test OWNER $(USER);"

	@echo "Installing the River CLI..."
	go install github.com/riverqueue/river/cmd/river@latest

	@echo "Running migrations..."
	river migrate-up --database-url "postgres://$(USER)@127.0.0.1:5432/river_test"

	@echo "Database setup complete!"
