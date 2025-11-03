#!/bin/bash
set -e

ENVIRONMENT=${1:-production}

echo "🚀 Deploying OpsCraft to $ENVIRONMENT..."

# Check if kubectl is available
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl is required"; exit 1; }

# Create namespace
echo "Creating namespace..."
kubectl apply -f k8s/namespaces/opscraft.yaml

# Create secrets
echo "Creating secrets..."
if [ -f .env ]; then
    kubectl create secret generic opscraft-secrets \
        --from-env-file=.env \
        -n opscraft \
        --dry-run=client -o yaml | kubectl apply -f -
else
    echo "⚠️  .env file not found. Using example secrets."
fi

# Deploy infrastructure
echo "Deploying infrastructure..."
kubectl apply -f k8s/statefulsets/

# Wait for statefulsets
echo "Waiting for statefulsets to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n opscraft --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n opscraft --timeout=300s
kubectl wait --for=condition=ready pod -l app=kafka -n opscraft --timeout=300s

# Deploy ConfigMaps
echo "Deploying ConfigMaps..."
kubectl apply -f k8s/configmaps/

# Deploy services
echo "Deploying microservices..."
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/

# Wait for deployments
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available deployment --all -n opscraft --timeout=300s

# Deploy HPA
echo "Deploying autoscalers..."
kubectl apply -f k8s/hpa/

# Deploy Ingress
echo "Deploying ingress..."
kubectl apply -f k8s/ingress/

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Check status: kubectl get all -n opscraft"
echo "View logs: kubectl logs -f -l app=auth-service -n opscraft"