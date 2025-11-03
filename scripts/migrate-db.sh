#!/bin/bash
set -e

echo "📊 Running database migrations..."

services=("auth" "script" "execution" "secret")

for service in "${services[@]}"; do
    echo ""
    echo "Migrating ${service}-service database..."
    docker-compose exec -T ${service}-service alembic upgrade head
    echo "✅ ${service}-service migrations complete"
done

echo ""
echo "✅ All database migrations complete!"