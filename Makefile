.PHONY: up down logs test lint seed migrate eval

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec api alembic upgrade head

seed:
	docker compose exec api python -m app.db.seed
	docker compose exec api python -m app.db.seed_documents

test:
	docker compose exec api pytest -q
	docker compose exec frontend npm test -- --run

lint:
	docker compose exec api ruff check app tests
	docker compose exec frontend npm run lint

eval:
	docker compose exec api python -m evaluation.run_evaluation
