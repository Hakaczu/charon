.PHONY: dev-up migrate job test

dev-up:
	docker compose up --build

migrate:
	docker compose run --rm backend alembic upgrade head

job:
	docker compose run --rm backend python -m app.jobs.runner

test:
	docker compose run --rm backend pytest
