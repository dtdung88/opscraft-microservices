#!/bin/bash
set -e

echo "🚀 Setting up OpsCraft Development Environment..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed."; exit 1; }

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.template .env
    
    # Generate random keys
    SECRET_KEY=$(openssl rand -base64 32)
    ENCRYPTION_KEY=$(openssl rand -base64 32)
    
    # Update .env with generated keys
    sed -i "s/your_super_secret_key_minimum_32_characters_long/$SECRET_KEY/" .env
    sed -i "s/your-encryption-key-32-chars/$ENCRYPTION_KEY/" .env
    
    echo "✅ .env file created with secure random keys"
else
    echo "✅ .env file already exists"
fi

# Create required directories
echo "📁 Creating directories..."
mkdir -p logs/{auth,script,execution,secret,notification,admin}
mkdir -p data/{postgres,redis,kafka}

# Pull Docker images
echo "🐳 Pulling Docker images..."
docker-compose pull

# Build services
echo "🔨 Building services..."
docker-compose build

# Start infrastructure services first
echo "🎯 Starting infrastructure services..."
docker-compose up -d auth-db script-db execution-db secret-db redis kafka zookeeper

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 15

# Run database migrations
echo "📊 Running database migrations..."
docker-compose exec -T auth-service alembic upgrade head || echo "Auth DB migrations pending..."
docker-compose exec -T script-service alembic upgrade head || echo "Script DB migrations pending..."
docker-compose exec -T execution-service alembic upgrade head || echo "Execution DB migrations pending..."
docker-compose exec -T secret-service alembic upgrade head || echo "Secret DB migrations pending..."

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

# Wait for services to start
sleep 10

# Health check
echo "🏥 Performing health checks..."
./scripts/health-check.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "📍 Service URLs:"
echo "   - API Gateway: http://localhost:8000"
echo "   - Frontend: http://localhost:3000"
echo "   - Grafana: http://localhost:3001 (admin/admin)"
echo "   - Prometheus: http://localhost:9090"
echo "   - Jaeger: http://localhost:16686"
echo "   - Kibana: http://localhost:5601"
echo ""
echo "📚 Next steps:"
echo "   1. Access the frontend at http://localhost:3000"
echo "   2. Create your first user account"
echo "   3. View logs: make logs"
echo "   4. Stop services: make down"
echo ""