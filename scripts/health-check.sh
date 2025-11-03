#!/bin/bash

echo "🏥 Checking service health..."
echo ""

services=(
    "http://localhost:8000/health:API Gateway"
    "http://localhost:8001/health:Auth Service"
    "http://localhost:8002/health:Script Service"
    "http://localhost:8003/health:Execution Service"
    "http://localhost:8004/health:Secret Service"
    "http://localhost:8005/health:Notification Service"
    "http://localhost:8006/health:Admin Service"
)

all_healthy=true

for service in "${services[@]}"; do
    IFS=':' read -r url name <<< "$service"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        echo "✅ $name - Healthy"
    else
        echo "❌ $name - Unhealthy (HTTP $response)"
        all_healthy=false
    fi
done

echo ""

if [ "$all_healthy" = true ]; then
    echo "✅ All services are healthy!"
    exit 0
else
    echo "⚠️  Some services are unhealthy. Check logs with: make logs"
    exit 1
fi