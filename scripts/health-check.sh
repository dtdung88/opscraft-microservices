#!/bin/bash

# ============================================================================
# OpsCraft Microservices - Health Check Script
# ============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}OpsCraft Health Check${NC}"
echo -e "${GREEN}================================${NC}\n"

check_service() {
    local name=$1
    local url=$2
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓${NC} $name is healthy"
        return 0
    else
        echo -e "${RED}✗${NC} $name is unhealthy (HTTP $response)"
        return 1
    fi
}

check_docker_service() {
    local service=$1
    
    if docker-compose ps | grep "$service" | grep -q "Up"; then
        echo -e "${GREEN}✓${NC} $service container is running"
        return 0
    else
        echo -e "${RED}✗${NC} $service container is not running"
        return 1
    fi
}

healthy=0
total=0

echo -e "${YELLOW}Checking Docker containers...${NC}"
check_docker_service "auth-service" && ((healthy++)); ((total++))
check_docker_service "script-service" && ((healthy++)); ((total++))
check_docker_service "execution-service" && ((healthy++)); ((total++))
check_docker_service "secret-service" && ((healthy++)); ((total++))
check_docker_service "notification-service" && ((healthy++)); ((total++))
check_docker_service "admin-service" && ((healthy++)); ((total++))

echo -e "\n${YELLOW}Checking service health endpoints...${NC}"
check_service "Auth Service" "http://localhost:8001/health" && ((healthy++)); ((total++))
check_service "Script Service" "http://localhost:8002/health" && ((healthy++)); ((total++))
check_service "Execution Service" "http://localhost:8003/health" && ((healthy++)); ((total++))
check_service "Secret Service" "http://localhost:8004/health" && ((healthy++)); ((total++))
check_service "Notification Service" "http://localhost:8005/health" && ((healthy++)); ((total++))
check_service "Admin Service" "http://localhost:8006/health" && ((healthy++)); ((total++))

echo -e "\n${YELLOW}Checking infrastructure services...${NC}"
check_docker_service "auth-db" && ((healthy++)); ((total++))
check_docker_service "redis" && ((healthy++)); ((total++))
check_docker_service "kafka" && ((healthy++)); ((total++))
check_docker_service "consul" && ((healthy++)); ((total++))

echo -e "\n${YELLOW}Checking monitoring services...${NC}"
check_docker_service "prometheus" && ((healthy++)); ((total++))
check_docker_service "grafana" && ((healthy++)); ((total++))
check_docker_service "jaeger" && ((healthy++)); ((total++))

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}Health Check Summary${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "Healthy services: ${GREEN}$healthy${NC}/$total"

if [ $healthy -eq $total ]; then
    echo -e "${GREEN}All services are healthy! ✓${NC}\n"
    exit 0
elif [ $healthy -gt $((total / 2)) ]; then
    echo -e "${YELLOW}Some services need attention${NC}\n"
    exit 1
else
    echo -e "${RED}System is unhealthy!${NC}\n"
    exit 2
fi