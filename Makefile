.PHONY: help build up down logs test clean restart

ENV_FILE = .env
COMPOSE = docker-compose --env-file $(ENV_FILE)

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help:
	@echo "$(GREEN)OpsCraft Microservices - Available Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Development:$(NC)"
	@echo "  make build                - Build all services"
	@echo "  make up                   - Start all services"
	@echo "  make down                 - Stop all services"
	@echo "  make restart              - Restart all services"
	@echo "  make logs                 - View logs from all services"
	@echo "  make logs-service SVC=auth - View logs from specific service"
	@echo ""
	@echo "$(YELLOW)Testing:$(NC)"
	@echo "  make test                 - Run all tests"
	@echo "  make test-service SVC=auth - Test specific service"
	@echo "  make test-integration     - Run integration tests"
	@echo "  make test-e2e             - Run end-to-end tests"
	@echo ""
	@echo "$(YELLOW)Database:$(NC)"
	@echo "  make db-migrate           - Run database migrations"
	@echo "  make db-migrate-create MSG='message' - Create migration"
	@echo "  make db-seed              - Seed databases with test data"
	@echo "  make db-shell DB=auth     - Access database shell"
	@echo ""
	@echo "$(YELLOW)Kubernetes:$(NC)"
	@echo "  make k8s-deploy           - Deploy to Kubernetes"
	@echo "  make k8s-delete           - Delete from Kubernetes"
	@echo "  make k8s-status           - Check deployment status"
	@echo "  make k8s-logs SVC=auth    - View Kubernetes logs"
	@echo ""
	@echo "$(YELLOW)Monitoring:$(NC)"
	@echo "  make monitoring-up        - Start monitoring stack"
	@echo "  make monitoring-down      - Stop monitoring stack"
	@echo ""
	@echo "$(YELLOW)Cleanup:$(NC)"
	@echo "  make clean                - Clean up containers and volumes"
	@echo "  make clean-all            - Clean everything including images"
	@echo ""

# ============================================================================
# Development Commands
# ============================================================================

build:
	@echo "$(GREEN)Building all services...$(NC)"
	$(COMPOSE) build --parallel

up:
	@echo "$(GREEN)Starting all services...$(NC)"
	$(COMPOSE) up -d
	@echo ""
	@echo "$(GREEN)✓ Services started!$(NC)"
	@echo "  API Gateway:    http://localhost:8000"
	@echo "  Frontend:       http://localhost:3000"
	@echo "  Auth Service:   http://localhost:8001"
	@echo "  Script Service: http://localhost:8002"
	@echo "  Exec Service:   http://localhost:8003"
	@echo "  Secret Service: http://localhost:8004"
	@echo "  Notifications:  http://localhost:8005"
	@echo "  Admin Service:  http://localhost:8006"
	@echo ""
	@echo "  Prometheus:     http://localhost:9090"
	@echo "  Grafana:        http://localhost:3001"
	@echo "  Jaeger:         http://localhost:16686"
	@echo "  Kibana:         http://localhost:5601"
	@echo "  Consul:         http://localhost:8500"

down:
	@echo "$(YELLOW)Stopping all services...$(NC)"
	$(COMPOSE) down

restart:
	@echo "$(YELLOW)Restarting all services...$(NC)"
	$(COMPOSE) restart

logs:
	$(COMPOSE) logs -f

logs-service:
	@if [ -z "$(SVC)" ]; then \
		echo "$(RED)Error: Please specify service with SVC=service-name$(NC)"; \
		exit 1; \
	fi
	$(COMPOSE) logs -f $(SVC)-service

# ============================================================================
# Testing Commands
# ============================================================================

test:
	@echo "$(GREEN)Running all tests...$(NC)"
	$(COMPOSE) exec auth-service pytest tests/ -v
	$(COMPOSE) exec script-service pytest tests/ -v
	$(COMPOSE) exec execution-service pytest tests/ -v
	$(COMPOSE) exec secret-service pytest tests/ -v

test-service:
	@if [ -z "$(SVC)" ]; then \
		echo "$(RED)Error: Please specify service with SVC=service-name$(NC)"; \
		exit 1; \
	fi
	$(COMPOSE) exec $(SVC)-service pytest tests/ -v

test-integration:
	@echo "$(GREEN)Running integration tests...$(NC)"
	pytest tests/integration/ -v

test-e2e:
	@echo "$(GREEN)Running end-to-end tests...$(NC)"
	pytest tests/e2e/ -v

test-performance:
	@echo "$(GREEN)Running performance tests...$(NC)"
	locust -f tests/performance/locustfile.py --headless -u 100 -r 10 --run-time 5m

# ============================================================================
# Database Commands
# ============================================================================

db-migrate:
	@echo "$(GREEN)Running database migrations...$(NC)"
	$(COMPOSE) exec auth-service alembic upgrade head
	$(COMPOSE) exec script-service alembic upgrade head
	$(COMPOSE) exec execution-service alembic upgrade head
	$(COMPOSE) exec secret-service alembic upgrade head

db-migrate-create:
	@if [ -z "$(MSG)" ]; then \
		echo "$(RED)Error: Please specify message with MSG='message'$(NC)"; \
		exit 1; \
	fi
	@if [ -z "$(SVC)" ]; then \
		echo "$(RED)Error: Please specify service with SVC=service-name$(NC)"; \
		exit 1; \
	fi
	$(COMPOSE) exec $(SVC)-service alembic revision --autogenerate -m "$(MSG)"

db-seed:
	@echo "$(GREEN)Seeding databases...$(NC)"
	./scripts/seed-data.sh

db-shell:
	@if [ -z "$(DB)" ]; then \
		echo "$(RED)Error: Please specify database with DB=db-name$(NC)"; \
		exit 1; \
	fi
	$(COMPOSE) exec $(DB)-db psql -U postgres -d $(DB)_db

# ============================================================================
# Kubernetes Commands
# ============================================================================

k8s-deploy:
	@echo "$(GREEN)Deploying to Kubernetes...$(NC)"
	kubectl apply -f k8s/namespaces/
	kubectl apply -f k8s/configmaps/
	kubectl apply -f k8s/secrets/
	kubectl apply -f k8s/statefulsets/
	kubectl apply -f k8s/deployments/
	kubectl apply -f k8s/services/
	kubectl apply -f k8s/hpa/
	kubectl apply -f k8s/ingress/
	@echo "$(GREEN)✓ Deployment complete!$(NC)"

k8s-delete:
	@echo "$(YELLOW)Deleting from Kubernetes...$(NC)"
	kubectl delete -f k8s/ingress/
	kubectl delete -f k8s/hpa/
	kubectl delete -f k8s/services/
	kubectl delete -f k8s/deployments/
	kubectl delete -f k8s/statefulsets/
	kubectl delete -f k8s/configmaps/
	kubectl delete -f k8s/namespaces/

k8s-status:
	@echo "$(GREEN)Kubernetes Status:$(NC)"
	kubectl get all -n opscraft

k8s-logs:
	@if [ -z "$(SVC)" ]; then \
		echo "$(RED)Error: Please specify service with SVC=service-name$(NC)"; \
		exit 1; \
	fi
	kubectl logs -f -l app=$(SVC)-service -n opscraft

# ============================================================================
# Monitoring Commands
# ============================================================================

monitoring-up:
	@echo "$(GREEN)Starting monitoring stack...$(NC)"
	$(COMPOSE) up -d prometheus grafana jaeger elasticsearch logstash kibana
	@echo "$(GREEN)✓ Monitoring stack started!$(NC)"

monitoring-down:
	@echo "$(YELLOW)Stopping monitoring stack...$(NC)"
	$(COMPOSE) stop prometheus grafana jaeger elasticsearch logstash kibana

# ============================================================================
# Cleanup Commands
# ============================================================================

clean:
	@echo "$(YELLOW)Cleaning up...$(NC)"
	$(COMPOSE) down -v
	docker system prune -f

clean-all:
	@echo "$(RED)Cleaning everything...$(NC)"
	$(COMPOSE) down -v --rmi all
	docker system prune -af --volumes

# ============================================================================
# Setup & Utility Commands
# ============================================================================

setup-dev:
	@echo "$(GREEN)Setting up development environment...$(NC)"
	./scripts/setup-dev.sh

health-check:
	@echo "$(GREEN)Checking service health...$(NC)"
	./scripts/health-check.sh

create-secrets:
	@echo "$(GREEN)Creating Kubernetes secrets...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found$(NC)"; \
		exit 1; \
	fi
	kubectl create secret generic opscraft-secrets \
		--from-env-file=.env \
		-n opscraft \
		--dry-run=client -o yaml | kubectl apply -f -

# ============================================================================
# Docker Build & Push (for CI/CD)
# ============================================================================

docker-build-all:
	@echo "$(GREEN)Building all service images...$(NC)"
	docker build -t opscraft/auth-service:latest ./services/auth-service
	docker build -t opscraft/script-service:latest ./services/script-service
	docker build -t opscraft/execution-service:latest ./services/execution-service
	docker build -t opscraft/secret-service:latest ./services/secret-service
	docker build -t opscraft/notification-service:latest ./services/notification-service
	docker build -t opscraft/admin-service:latest ./services/admin-service
	docker build -t opscraft/frontend:latest ./frontend

docker-push-all:
	@echo "$(GREEN)Pushing all service images...$(NC)"
	docker push opscraft/auth-service:latest
	docker push opscraft/script-service:latest
	docker push opscraft/execution-service:latest
	docker push opscraft/secret-service:latest
	docker push opscraft/notification-service:latest
	docker push opscraft/admin-service:latest
	docker push opscraft/frontend:latest