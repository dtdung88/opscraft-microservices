#!/bin/bash

# ============================================================================
# OpsCraft Microservices - Development Setup Script
# ============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}OpsCraft Development Setup${NC}"
echo -e "${GREEN}================================${NC}\n"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker found${NC}"
echo -e "${GREEN}✓ Docker Compose found${NC}\n"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.template .env
    
    # Generate random keys
    SECRET_KEY=$(openssl rand -base64 32)
    ENCRYPTION_KEY=$(openssl rand -base64 32)
    
    # Update .env with generated keys
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env
    sed -i "s|ENCRYPTION_KEY=.*|ENCRYPTION_KEY=$ENCRYPTION_KEY|g" .env
    
    echo -e "${GREEN}✓ .env file created with generated keys${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Create necessary directories
echo -e "\n${YELLOW}Creating project directories...${NC}"

DIRS=(
    "infrastructure/databases/auth-db"
    "infrastructure/databases/script-db"
    "infrastructure/databases/execution-db"
    "infrastructure/databases/secret-db"
    "infrastructure/monitoring/prometheus"
    "infrastructure/monitoring/grafana/dashboards"
    "infrastructure/monitoring/elk"
    "logs"
    "data"
)

for dir in "${DIRS[@]}"; do
    mkdir -p "$dir"
    echo -e "${GREEN}✓ Created $dir${NC}"
done

# Create Prometheus configuration if not exists
if [ ! -f infrastructure/monitoring/prometheus/prometheus.yml ]; then
    echo -e "\n${YELLOW}Creating Prometheus configuration...${NC}"
    cat > infrastructure/monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'auth-service'
    static_configs:
      - targets: ['auth-service:8001']
  
  - job_name: 'script-service'
    static_configs:
      - targets: ['script-service:8002']
  
  - job_name: 'execution-service'
    static_configs:
      - targets: ['execution-service:8003']
  
  - job_name: 'secret-service'
    static_configs:
      - targets: ['secret-service:8004']
  
  - job_name: 'admin-service'
    static_configs:
      - targets: ['admin-service:8006']
EOF
    echo -e "${GREEN}✓ Prometheus configuration created${NC}"
fi

# Create Grafana datasource configuration
if [ ! -f infrastructure/monitoring/grafana/datasources.yml ]; then
    echo -e "${YELLOW}Creating Grafana datasource configuration...${NC}"
    cat > infrastructure/monitoring/grafana/datasources.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF
    echo -e "${GREEN}✓ Grafana datasource configuration created${NC}"
fi

# Create Logstash configuration
if [ ! -f infrastructure/monitoring/elk/logstash.conf ]; then
    echo -e "${YELLOW}Creating Logstash configuration...${NC}"
    cat > infrastructure/monitoring/elk/logstash.conf << 'EOF'
input {
  tcp {
    port => 5000
    codec => json
  }
}

filter {
  json {
    source => "message"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "opscraft-logs-%{+YYYY.MM.dd}"
  }
  stdout { codec => rubydebug }
}
EOF
    echo -e "${GREEN}✓ Logstash configuration created${NC}"
fi

# Create auth-db init script
if [ ! -f infrastructure/databases/auth-db/init.sql ]; then
    echo -e "${YELLOW}Creating auth-db init script...${NC}"
    cat > infrastructure/databases/auth-db/init.sql << 'EOF'
-- Initialize auth database
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE auth_db TO postgres;
EOF
    echo -e "${GREEN}✓ Auth DB init script created${NC}"
fi

# Pull Docker images
echo -e "\n${YELLOW}Pulling Docker images (this may take a while)...${NC}"
docker-compose pull

echo -e "\n${GREEN}Building services...${NC}"
docker-compose build --parallel

# Start infrastructure services first
echo -e "\n${YELLOW}Starting infrastructure services...${NC}"
docker-compose up -d postgres-auth postgres-script postgres-execution postgres-secret redis kafka zookeeper consul

echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Check service health
echo -e "\n${YELLOW}Checking service health...${NC}"

check_service() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps | grep $service | grep -q "Up"; then
            echo -e "${GREEN}✓ $service is up${NC}"
            return 0
        fi
        echo -e "${YELLOW}Waiting for $service... (attempt $attempt/$max_attempts)${NC}"
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED}✗ $service failed to start${NC}"
    return 1
}

check_service "auth-db" "5432"
check_service "redis" "6379"
check_service "kafka" "9092"

# Start application services
echo -e "\n${YELLOW}Starting application services...${NC}"
docker-compose up -d

echo -e "\n${YELLOW}Waiting for application services...${NC}"
sleep 15

# Run database migrations
echo -e "\n${YELLOW}Running database migrations...${NC}"
docker-compose exec -T auth-service alembic upgrade head || echo "Auth migrations not ready yet"
docker-compose exec -T script-service alembic upgrade head || echo "Script migrations not ready yet"
docker-compose exec -T execution-service alembic upgrade head || echo "Execution migrations not ready yet"
docker-compose exec -T secret-service alembic upgrade head || echo "Secret migrations not ready yet"

# Create first admin user
echo -e "\n${YELLOW}Creating admin user...${NC}"
cat > /tmp/create_admin.py << 'EOF'
import httpx
import asyncio

async def create_admin():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/v1/auth/register",
                json={
                    "username": "admin",
                    "email": "admin@opscraft.io",
                    "password": "Admin123!",
                    "full_name": "System Administrator"
                },
                timeout=10.0
            )
            if response.status_code == 201:
                print("✓ Admin user created successfully")
                print("  Username: admin")
                print("  Password: Admin123!")
            else:
                print(f"Admin user may already exist or service not ready")
        except Exception as e:
            print(f"Could not create admin user: {e}")

asyncio.run(create_admin())
EOF

python3 /tmp/create_admin.py || echo "Admin creation skipped"
rm /tmp/create_admin.py

# Show status
echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}================================${NC}\n"

echo -e "${YELLOW}Services are running at:${NC}"
echo -e "  API Gateway:    ${GREEN}http://localhost:8000${NC}"
echo -e "  Auth Service:   ${GREEN}http://localhost:8001${NC}"
echo -e "  Script Service: ${GREEN}http://localhost:8002${NC}"
echo -e "  Execution:      ${GREEN}http://localhost:8003${NC}"
echo -e "  Secret Service: ${GREEN}http://localhost:8004${NC}"
echo -e "  Notifications:  ${GREEN}http://localhost:8005${NC}"
echo -e "  Admin Service:  ${GREEN}http://localhost:8006${NC}"
echo -e ""
echo -e "  Prometheus:     ${GREEN}http://localhost:9090${NC}"
echo -e "  Grafana:        ${GREEN}http://localhost:3001${NC} (admin/admin)"
echo -e "  Jaeger:         ${GREEN}http://localhost:16686${NC}"
echo -e "  Kibana:         ${GREEN}http://localhost:5601${NC}"
echo -e "  Consul:         ${GREEN}http://localhost:8500${NC}"

echo -e "\n${YELLOW}Default admin credentials:${NC}"
echo -e "  Username: ${GREEN}admin${NC}"
echo -e "  Password: ${GREEN}Admin123!${NC}"

echo -e "\n${YELLOW}Useful commands:${NC}"
echo -e "  View logs:    ${GREEN}make logs${NC}"
echo -e "  Stop all:     ${GREEN}make down${NC}"
echo -e "  Restart:      ${GREEN}make restart${NC}"
echo -e "  Run tests:    ${GREEN}make test${NC}"

echo -e "\n${GREEN}Happy coding! 🚀${NC}\n"