#!/bin/bash
set -e

echo "🌱 Seeding test data..."

# Create test admin user
echo "Creating test admin user..."
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@opscraft.local",
    "password": "Admin123!",
    "full_name": "System Administrator"
  }'

# Login and get token
echo ""
echo "Logging in as admin..."
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin123!"
  }')

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ "$ACCESS_TOKEN" = "null" ]; then
    echo "❌ Failed to get access token"
    exit 1
fi

echo "✅ Got access token"

# Create sample scripts
echo ""
echo "Creating sample scripts..."

# Bash script
curl -X POST http://localhost:8000/api/v1/scripts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "name": "System Info",
    "description": "Display system information",
    "script_type": "bash",
    "content": "#!/bin/bash\necho \"System Information:\"\nuname -a\ndate\ndf -h",
    "tags": ["system", "info"]
  }'

# Python script
curl -X POST http://localhost:8000/api/v1/scripts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "name": "Python Hello World",
    "description": "Simple Python script",
    "script_type": "python",
    "content": "#!/usr/bin/env python3\nimport sys\nimport platform\n\nprint(f\"Hello from Python {sys.version}\")\nprint(f\"Platform: {platform.system()}\")",
    "tags": ["python", "demo"]
  }'

# Create sample secret
echo ""
echo "Creating sample secret..."
curl -X POST http://localhost:8000/api/v1/secrets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "name": "api_key",
    "description": "Sample API key",
    "value": "sk-1234567890abcdef",
    "category": "api_key"
  }'

echo ""
echo "✅ Seed data creation complete!"
echo ""
echo "Test credentials:"
echo "  Username: admin"
echo "  Password: Admin123!"