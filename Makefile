.PHONY: help dev test docker-build docker-up docker-down docker-logs clean gpu-check

help:
	@echo "LocalllmOcrMK2 - Makefile Commands"
	@echo "===================================="
	@echo ""
	@echo "Development:"
	@echo "  make dev              - Start all services locally (Redis, vLLM, Celery, FastAPI, Frontend)"
	@echo "  make gpu-check        - Check GPU environment"
	@echo "  make clean            - Stop services and clean up"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run all tests (unit, integration, performance)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     - Build Docker images"
	@echo "  make docker-up        - Start services with docker-compose"
	@echo "  make docker-down      - Stop and remove services"
	@echo "  make docker-logs      - Show docker-compose logs"
	@echo ""

dev:
	@echo "🚀 Starting LocalllmOcrMK2 development environment..."
	@bash backend/start_dev.sh

gpu-check:
	@echo "🔍 Checking GPU environment..."
	@cd backend && python check_gpu.py

test:
	@echo "🧪 Running all tests..."
	@bash tests/run_tests.sh

docker-build:
	@echo "🔨 Building Docker images..."
	docker-compose build

docker-up:
	@echo "🚀 Starting services with docker-compose..."
	docker-compose up -d
	@echo ""
	@echo "✅ Services starting..."
	@echo "Waiting for containers to be healthy (30-60 seconds)..."
	@sleep 10
	@docker-compose ps
	@echo ""
	@echo "📍 Access points:"
	@echo "   Frontend:  http://localhost"
	@echo "   API Docs:  http://localhost:8080/docs"
	@echo "   Redis:     localhost:6379"

docker-down:
	@echo "⛔ Stopping docker-compose services..."
	docker-compose down

docker-logs:
	@echo "📋 Docker-compose logs:"
	docker-compose logs -f

clean:
	@echo "🧹 Cleaning up..."
	@bash backend/cleanup.sh
