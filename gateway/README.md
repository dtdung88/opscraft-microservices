# API Gateway

Routes requests to appropriate microservices.

## Port: 8000 (External)

## Routing:
- /api/v1/auth/* -> auth-service:8001
- /api/v1/scripts/* -> script-service:8002
- /api/v1/executions/* -> execution-service:8003
- /api/v1/secrets/* -> secret-service:8004
- /api/v1/admin/* -> admin-service:8005
- /ws/* -> execution-service:8003
