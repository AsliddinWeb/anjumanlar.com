.PHONY: help up down restart logs ps build pull clean migrate makemigration seed shell-backend shell-db shell-redis test lint format env prod-build prod-up prod-down prod-deploy prod-migrate prod-seed prod-create-admin prod-logs prod-ps

# Default target
help:
	@echo "Anjumanlar.com — development commands"
	@echo ""
	@echo "  make env              Copy .env.example -> .env (only if .env missing)"
	@echo "  make up               Start all dev services (detached)"
	@echo "  make down             Stop all services"
	@echo "  make restart          Restart all services"
	@echo "  make logs             Tail logs from all services"
	@echo "  make logs s=backend   Tail logs from one service"
	@echo "  make ps               List running containers"
	@echo "  make build            Rebuild all images"
	@echo "  make pull             Pull latest base images"
	@echo "  make clean            Stop and remove containers + volumes (DESTRUCTIVE)"
	@echo ""
	@echo "  make migrate          Run Alembic upgrade head"
	@echo "  make makemigration m=\"msg\"   Create new Alembic revision"
	@echo "  make seed             Run backend seed script"
	@echo ""
	@echo "  make shell-backend    Open shell in backend container"
	@echo "  make shell-db         Open psql in postgres container"
	@echo "  make shell-redis      Open redis-cli"
	@echo ""
	@echo "  make test             Run backend pytest"
	@echo "  make lint             Run linters (ruff + eslint)"
	@echo "  make format           Run formatters (ruff format + prettier)"
	@echo ""
	@echo "Ports (host machine):"
	@echo "  Postgres   localhost:8300"
	@echo "  Redis      localhost:8301"
	@echo "  MinIO API  localhost:8302   Console localhost:8303"
	@echo "  Meili      localhost:8304"
	@echo "  MailHog    SMTP localhost:8305   UI localhost:8306"
	@echo "  Backend    localhost:8307   (Swagger /docs)"
	@echo "  Frontend   localhost:8308"

env:
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example"; else echo ".env already exists"; fi

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f $(s)

ps:
	docker compose ps

build:
	docker compose build

pull:
	docker compose pull

clean:
	docker compose down -v --remove-orphans

migrate:
	docker compose exec backend alembic upgrade head

makemigration:
	docker compose exec backend alembic revision --autogenerate -m "$(m)"

seed:
	docker compose exec backend python -m app.scripts.seed_phase2

shell-backend:
	docker compose exec backend /bin/bash

shell-db:
	docker compose exec postgres psql -U $${POSTGRES_USER:-anjumanlar} -d $${POSTGRES_DB:-anjumanlar}

shell-redis:
	docker compose exec redis redis-cli

test:
	docker compose exec backend pytest

lint:
	docker compose exec backend ruff check .
	docker compose exec frontend pnpm lint

format:
	docker compose exec backend ruff format .
	docker compose exec frontend pnpm format

# ---------- production targets ----------

PROD := docker compose -f docker-compose.prod.yml

prod-build:
	$(PROD) build

prod-up:
	$(PROD) up -d

prod-down:
	$(PROD) down

prod-deploy:
	./scripts/deploy.sh

prod-migrate:
	$(PROD) exec backend alembic upgrade head

prod-seed:
	$(PROD) exec backend python -m app.scripts.seed_categories

# Create the first superadmin. Usage:
#   make prod-create-admin EMAIL=you@anjumanlar.com PASSWORD='Strong!2026' NAME='Site Admin'
prod-create-admin:
	$(PROD) exec backend python -m app.scripts.create_admin \
	    --email "$(EMAIL)" --password "$(PASSWORD)" --name "$(NAME)"

prod-logs:
	$(PROD) logs -f $(s)

prod-ps:
	$(PROD) ps
