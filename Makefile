.PHONY: dev build up down logs clean deploy

dev:
	docker compose up -d db
	cd backend && uvicorn src.api:app --reload --port 8091

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	docker compose down -v
	docker system prune -f

deploy:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build