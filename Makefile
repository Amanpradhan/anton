.PHONY: setup run stop logs migrate test lint

setup:
	@echo "Setting up Anton..."
	@cp -n .env.example .env || true
	@echo "→ .env created (fill in your API keys)"
	docker compose build
	@echo "✓ Anton is ready. Run 'make run' to start."

run:
	docker compose up

run-detached:
	docker compose up -d

stop:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec backend alembic upgrade head

test:
	docker compose exec backend pytest tests/ -v

lint:
	docker compose exec backend ruff check app/
	docker compose exec backend ruff format --check app/

# Local dev (without Docker) ───────────────────────────────────────────────────
dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev
