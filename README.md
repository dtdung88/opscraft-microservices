# 🔧 OpsCraft - Microservices Architecture

> Enterprise-grade microservices platform for managing and executing infrastructure automation scripts with real-time monitoring, secret management, and role-based access control.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-ready-blue.svg)](https://kubernetes.io/)

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Microservices](#microservices)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development](#development)
- [Deployment](#deployment)
- [Monitoring & Observability](#monitoring--observability)
- [Testing](#testing)
- [CI/CD](#cicd)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## 🏗️ Architecture Overview

OpsCraft follows a microservices architecture with the following key components:

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (NGINX)                       │
│                         Port: 8000                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────────────┐
        │              │                      │
┌───────▼──────┐ ┌────▼─────┐ ┌────────────▼──────────┐
│ Auth Service │ │  Script  │ │  Execution Service    │
│  Port: 8001  │ │  Service │ │     Port: 8003        │
│              │ │Port: 8002│ │                       │
└──────┬───────┘ └────┬─────┘ └───────────┬───────────┘
       │              │                   │
┌──────▼──────┐ ┌────▼──────┐ ┌─────────▼──────────┐
│  Secret     │ │Notification│ │   Admin Service    │
│  Service    │ │  Service   │ │    Port: 8006      │
│ Port: 8004  │ │Port: 8005  │ │                    │
└─────────────┘ └────────────┘ └────────────────────┘
       │              │                   │
       └──────────────┼───────────────────┘
                      │
        ┌─────────────┴──────────────┐
        │                            │
┌───────▼────────┐        ┌─────────▼────────┐
│    Kafka       │        │    PostgreSQL    │
│  Event Broker  │        │   (per service)  │
└────────────────┘        └──────────────────┘
        │
┌───────▼────────┐        ┌──────────────────┐
│     Redis      │        │    Monitoring    │
│  Cache/Pub-Sub │        │ Prometheus/Jaeger│
└────────────────┘        └──────────────────┘
```

### Key Design Principles

1. **Service Independence**: Each service has its own database
2. **Event-Driven**: Services communicate via Kafka events
3. **API Gateway**: Single entry point for all client requests
4. **Observability**: Distributed tracing, metrics, and centralized logging
5. **Resilience**: Circuit breakers, retries, and graceful degradation
6. **Scalability**: Horizontal scaling with Kubernetes HPA

## 🎯 Microservices

### 1. Auth Service (Port 8001)
- User authentication and authorization
- JWT token management
- Role-based access control (RBAC)
- User management

**Database**: auth_db (PostgreSQL)
**Events Published**: user.created, user.logged_in
**Dependencies**: Redis (cache), Kafka (events)

### 2. Script Service (Port 8002)
- Script CRUD operations
- Script versioning
- Tag management
- Script validation

**Database**: script_db (PostgreSQL)
**Events Published**: script.created, script.updated, script.deleted
**Events Consumed**: user.created
**Dependencies**: Auth Service, Redis, Kafka

### 3. Execution Service (Port 8003)
- Script execution in Docker containers
- Execution queue management (Celery)
- Real-time log streaming
- Execution history

**Database**: execution_db (PostgreSQL)
**Events Published**: execution.started, execution.completed
**Events Consumed**: script.created, script.updated
**Dependencies**: Script Service, Secret Service, Redis, Kafka, Docker

### 4. Secret Service (Port 8004)
- AES-256 encrypted secret storage
- Secret audit logging
- Secret injection for executions
- Secret lifecycle management

**Database**: secret_db (PostgreSQL)
**Events Published**: secret.created, secret.accessed
**Events Consumed**: execution.started
**Dependencies**: Redis, Kafka

### 5. Notification Service (Port 8005)
- WebSocket connections
- Real-time log streaming
- Notification broadcasting
- Connection management

**Events Consumed**: execution.started, execution.completed, *.* (all events)
**Dependencies**: Redis (Pub/Sub), Kafka

### 6. Admin Service (Port 8006)
- Admin operations aggregation
- User management
- System statistics
- Cross-service reporting

**Dependencies**: All other services (via REST APIs)

## 📦 Prerequisites

### Required Software

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Make** (optional, for convenience)
- **kubectl** 1.24+ (for Kubernetes deployment)
- **Helm** 3.0+ (optional, for advanced K8s deployments)

### System Requirements

- **RAM**: Minimum 8GB, recommended 16GB+
- **CPU**: 4+ cores recommended
- **Disk**: 20GB+ free space
- **OS**: Linux, macOS, or Windows with WSL2

## 🚀 Quick Start

### 1. Clone and Configure

```bash
# Clone repository
git clone https://github.com/yourusername/opscraft-microservices.git
cd opscraft-microservices

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Start Services

```bash
# Build and start all services
make build
make up

# Or without Make
docker-compose build
docker-compose up -d
```

### 3. Verify Deployment

```bash
# Check service health
make health-check

# View service status
docker-compose ps

# View logs
make logs
```

### 4. Access Services

- **API Gateway**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)
- **Jaeger**: http://localhost:16686
- **Kibana**: http://localhost:5601
- **Consul**: http://localhost:8500

### 5. Initialize Database

```bash
# Run migrations
make db-migrate

# Seed test data (optional)
make db-seed
```

### 6. Create First User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "SecurePass123",
    "full_name": "System Administrator"
  }'
```

## 💻 Development

### Running Individual Services

```bash
# Start specific service
docker-compose up -d auth-service

# View service logs
make logs-service SVC=auth

# Restart service
docker-compose restart auth-service
```

### Making Changes

```bash
# 1. Make code changes
nano services/auth-service/app/api/routes.py

# 2. Rebuild service
docker-compose build auth-service

# 3. Restart service
docker-compose restart auth-service

# 4. Run tests
make test-service SVC=auth
```

### Adding a New Migration

```bash
# Create migration
make db-migrate-create SVC=auth MSG="add user preferences"

# Run migration
make db-migrate
```

### Local Development Without Docker

```bash
# Auth Service
cd services/auth-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/auth_db"
export REDIS_URL="redis://localhost:6379/0"
uvicorn main:app --reload --port 8001
```

## 🚢 Deployment

### Docker Compose (Development/Staging)

```bash
# Production compose file
docker-compose -f docker-compose.prod.yml up -d

# Scale specific service
docker-compose up -d --scale execution-service=3
```

### Kubernetes (Production)

```bash
# Deploy to Kubernetes
make k8s-deploy

# Check deployment status
make k8s-status

# View logs
make k8s-logs SVC=auth

# Scale deployment
kubectl scale deployment auth-service --replicas=5 -n opscraft
```

### ArgoCD (GitOps)

```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Apply OpsCraft application
kubectl apply -f ci-cd/argocd/application.yaml

# Access ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

## 📊 Monitoring & Observability

### Metrics (Prometheus + Grafana)

```bash
# Start monitoring stack
make monitoring-up

# Access Grafana
open http://localhost:3001
# Login: admin/admin

# Import dashboards
# Dashboard IDs: 315 (Kubernetes), 1860 (Node Exporter)
```

### Distributed Tracing (Jaeger)

```bash
# View traces
open http://localhost:16686

# Search for traces by service
# Service: auth-service, script-service, etc.
```

### Logging (ELK Stack)

```bash
# Access Kibana
open http://localhost:5601

# Create index pattern: logstash-*
# Explore logs with correlation IDs
```

### Service Discovery (Consul)

```bash
# View service registry
open http://localhost:8500

# Check service health
curl http://localhost:8500/v1/health/service/auth-service
```

## 🧪 Testing

### Unit Tests

```bash
# All services
make test

# Specific service
make test-service SVC=auth

# With coverage
docker-compose exec auth-service pytest tests/ --cov=app --cov-report=html
```

### Integration Tests

```bash
# Run integration tests
make test-integration

# Tests complete workflows across services
pytest tests/integration/ -v
```

### End-to-End Tests

```bash
# Run E2E tests
make test-e2e

# Tests complete user journeys
pytest tests/e2e/ -v
```

### Performance Tests

```bash
# Run Locust tests
make test-performance

# Or manually
locust -f tests/performance/locustfile.py
# Access UI: http://localhost:8089
```

## 🔄 CI/CD

### GitHub Actions

Automated pipelines for each service:

- Lint & type checking
- Unit tests
- Build Docker images
- Push to container registry
- Deploy to Kubernetes
- Run integration tests

### Jenkins

Multi-service pipeline with:

- Change detection
- Parallel testing
- Conditional builds
- Kubernetes deployment
- Smoke tests

### Setting Up CI/CD

```bash
# 1. Configure secrets in GitHub
GITHUB_TOKEN, KUBE_CONFIG, SLACK_WEBHOOK

# 2. Push to trigger pipeline
git add .
git commit -m "Update auth service"
git push origin main

# 3. Monitor pipeline
# GitHub: Actions tab
# Jenkins: http://jenkins-url/job/opscraft
```

## ⚙️ Configuration

### Environment Variables

Each service has its own `.env` file with:

```bash
# Service Configuration
SERVICE_NAME=auth-service
SERVICE_PORT=8001

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis
REDIS_URL=redis://host:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Security
SECRET_KEY=your-secret-key-min-32-chars
JWT_EXPIRATION=30m

# Tracing
JAEGER_HOST=jaeger
JAEGER_PORT=6831
```

### Service Discovery

Services discover each other via:

1. **DNS** (in Docker Compose): `http://auth-service:8001`
2. **Consul** (optional): Service registry with health checks
3. **Kubernetes Services**: `http://auth-service.opscraft.svc.cluster.local:8001`

## 🔍 Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check Docker
docker ps
docker-compose ps

# Check logs
make logs-service SVC=auth

# Restart services
make restart
```

#### Database Connection Errors

```bash
# Check database
docker-compose exec auth-db psql -U postgres -d auth_db

# Run migrations
make db-migrate

# Check connection string
echo $DATABASE_URL
```

#### Kafka Not Working

```bash
# Check Kafka
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Create topics manually
docker-compose exec kafka kafka-topics --create \
  --topic user-events \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1
```

#### Service Communication Failures

```bash
# Test service-to-service communication
docker-compose exec auth-service curl http://script-service:8002/health

# Check API Gateway
curl http://localhost:8000/health

# Verify service discovery
curl http://localhost:8500/v1/catalog/services
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Restart services
make restart

# View detailed logs
make logs
```

## 📚 Additional Resources

- [Architecture Documentation](docs/architecture/)
- [API Documentation](docs/api/)
- [Deployment Guide](docs/deployment/)
- [Monitoring Guide](docs/monitoring/)
- [Contributing Guide](CONTRIBUTING.md)

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/opscraft-microservices/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/opscraft-microservices/discussions)
- **Slack**: [Join our Slack](https://slack.opscraft.io)

---

**Made with ❤️ by the OpsCraft team**