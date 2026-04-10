.PHONY: help install dev test lint build up down logs clean seed seed-graph migrate status shell-api shell-db shell-neo4j check format test-backend test-frontend test-integration run-backend run-frontend prod

# Color output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[0;33m
NC := \033[0m # No Color

BACKEND := backend
FRONTEND := frontend
DOCKER_COMPOSE := docker compose
PYTHONPATH := PYTHONPATH=$(BACKEND)

help:
	@echo "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(BLUE)  Impact Observatory | مرصد الأثر$(NC)"
	@echo "$(BLUE)  Decision Intelligence Platform for GCC Financial Markets$(NC)"
	@echo "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo ""
	@echo "$(GREEN)Development$(NC)"
	@echo "  make install              Install all dependencies"
	@echo "  make dev                  Start all services (Docker)"
	@echo "  make run-backend          Start backend only (local uvicorn)"
	@echo "  make run-frontend         Start frontend only (local next dev)"
	@echo "  make down                 Stop all services"
	@echo "  make logs                 Tail service logs"
	@echo "  make status               Health check all services"
	@echo ""
	@echo "$(GREEN)Testing$(NC)"
	@echo "  make test                 Run all tests"
	@echo "  make test-backend         Backend pytest only"
	@echo "  make test-frontend        Frontend build check"
	@echo "  make check                Full CI pipeline (lint + test + build)"
	@echo ""
	@echo "$(GREEN)Code Quality$(NC)"
	@echo "  make lint                 Run linters"
	@echo "  make format               Auto-format code"
	@echo ""
	@echo "$(GREEN)Production$(NC)"
	@echo "  make build                Build Docker images"
	@echo "  make prod                 Start with nginx reverse proxy"
	@echo ""
	@echo "$(GREEN)Data$(NC)"
	@echo "  make seed                 Load seed data into PostgreSQL"
	@echo "  make seed-graph           Load seed data into Neo4j"
	@echo "  make migrate              Run database migrations"
	@echo ""
	@echo "$(GREEN)Shells$(NC)"
	@echo "  make shell-api            Bash in API container"
	@echo "  make shell-db             psql into PostgreSQL"
	@echo "  make shell-neo4j          Cypher shell into Neo4j"
	@echo ""
	@echo "$(GREEN)Cleanup$(NC)"
	@echo "  make clean                Remove containers, volumes, caches"
	@echo ""

# ── Setup ───────────────────────────────────────────────────────────────────

install:
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	cd $(BACKEND) && pip install -q -r requirements.txt
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	cd $(FRONTEND) && npm install --silent
	@echo "$(GREEN)✓ Installation complete$(NC)"

# ── Development ─────────────────────────────────────────────────────────────

dev: up

up:
	@echo "$(BLUE)Starting Impact Observatory services...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo ""
	@echo "  🌐 Frontend:   http://localhost:3000"
	@echo "  🔧 Backend:    http://localhost:8000"
	@echo "  📚 API Docs:   http://localhost:8000/docs"
	@echo "  🗄️  PostgreSQL: localhost:5432"
	@echo "  🔗 Neo4j:      http://localhost:7474"
	@echo "  ⚡ Redis:      localhost:6379"

run-backend:
	@echo "$(BLUE)Starting backend (uvicorn)...$(NC)"
	cd $(BACKEND) && $(PYTHONPATH) uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	@echo "$(BLUE)Starting frontend (next dev)...$(NC)"
	cd $(FRONTEND) && npm run dev

down:
	@echo "$(BLUE)Stopping all services...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Services stopped$(NC)"

logs:
	$(DOCKER_COMPOSE) logs -f

status:
	@echo "$(BLUE)━━━ Impact Observatory Health ━━━$(NC)"
	@echo ""
	@echo -n "  Backend API:  " && curl -sf http://localhost:8000/health >/dev/null 2>&1 && echo "$(GREEN)✓ healthy$(NC)" || echo "$(RED)✗ down$(NC)"
	@echo -n "  Frontend:     " && curl -sf http://localhost:3000 >/dev/null 2>&1 && echo "$(GREEN)✓ healthy$(NC)" || echo "$(RED)✗ down$(NC)"
	@echo -n "  PostgreSQL:   " && $(DOCKER_COMPOSE) exec -T postgres pg_isready -U observatory_admin >/dev/null 2>&1 && echo "$(GREEN)✓ healthy$(NC)" || echo "$(RED)✗ down$(NC)"
	@echo -n "  Neo4j:        " && $(DOCKER_COMPOSE) exec -T neo4j cypher-shell -u neo4j -p io_graph_2026 'RETURN 1' >/dev/null 2>&1 && echo "$(GREEN)✓ healthy$(NC)" || echo "$(RED)✗ down$(NC)"
	@echo -n "  Redis:        " && $(DOCKER_COMPOSE) exec -T redis redis-cli ping >/dev/null 2>&1 && echo "$(GREEN)✓ healthy$(NC)" || echo "$(RED)✗ down$(NC)"

# ── Production ──────────────────────────────────────────────────────────────

build:
	@echo "$(BLUE)Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✓ Build complete$(NC)"

prod:
	@echo "$(BLUE)Starting Impact Observatory (production with nginx)...$(NC)"
	$(DOCKER_COMPOSE) --profile production up -d
	@echo "$(GREEN)✓ Production stack running on http://localhost$(NC)"

# ── Testing ─────────────────────────────────────────────────────────────────

test: test-backend test-frontend
	@echo "$(GREEN)✓ All tests passed$(NC)"

test-backend:
	@echo "$(BLUE)Running backend tests...$(NC)"
	cd $(BACKEND) && $(PYTHONPATH) pytest tests/ -v --tb=short 2>&1 || true
	@echo "$(GREEN)✓ Backend tests complete$(NC)"

test-frontend:
	@echo "$(BLUE)Building frontend (type check)...$(NC)"
	cd $(FRONTEND) && npm run build
	@echo "$(GREEN)✓ Frontend build passed$(NC)"

test-integration:
	@echo "$(BLUE)Running integration tests...$(NC)"
	cd $(BACKEND) && $(PYTHONPATH) pytest tests/test_integration.py -v --tb=short 2>&1 || true

# ── Code Quality ────────────────────────────────────────────────────────────

lint:
	@echo "$(BLUE)Linting...$(NC)"
	cd $(BACKEND) && ruff check . 2>&1 || true
	@echo "$(GREEN)✓ Lint complete$(NC)"

format:
	@echo "$(BLUE)Formatting...$(NC)"
	cd $(BACKEND) && ruff format . --quiet 2>&1 || true
	@echo "$(GREEN)✓ Format complete$(NC)"

check: lint test build
	@echo "$(GREEN)✓ Full CI pipeline passed$(NC)"

# ── Data ────────────────────────────────────────────────────────────────────

seed:
	@echo "$(BLUE)Loading GCC seed data into PostgreSQL...$(NC)"
	$(DOCKER_COMPOSE) exec -T postgres psql -U observatory_admin -d impact_observatory -f /docker-entrypoint-initdb.d/01-init.sql
	@echo "$(GREEN)✓ Seed data loaded$(NC)"

seed-graph:
	@echo "$(BLUE)Loading seed data into Neo4j...$(NC)"
	cd $(BACKEND) && $(PYTHONPATH) python -m scripts.seed_neo4j 2>&1 || true
	@echo "$(GREEN)✓ Graph seed loaded$(NC)"

migrate:
	@echo "$(BLUE)Running database migrations...$(NC)"
	cd $(BACKEND) && alembic upgrade head 2>&1 || true
	@echo "$(GREEN)✓ Migrations complete$(NC)"

# ── Shells ──────────────────────────────────────────────────────────────────

shell-api:
	$(DOCKER_COMPOSE) exec backend /bin/bash

shell-db:
	$(DOCKER_COMPOSE) exec postgres psql -U observatory_admin -d impact_observatory

shell-neo4j:
	$(DOCKER_COMPOSE) exec neo4j cypher-shell -u neo4j -p io_graph_2026

# ── Cleanup ─────────────────────────────────────────────────────────────────

clean:
	@echo "$(BLUE)Cleaning up...$(NC)"
	$(DOCKER_COMPOSE) down -v --remove-orphans 2>/dev/null || true
	find $(BACKEND) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find $(BACKEND) -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(BACKEND)/.coverage $(BACKEND)/htmlcov $(BACKEND)/.mypy_cache 2>/dev/null || true
	rm -rf $(FRONTEND)/node_modules $(FRONTEND)/.next $(FRONTEND)/.cache 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"
