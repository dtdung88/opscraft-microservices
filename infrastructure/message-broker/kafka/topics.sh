#!/bin/bash
# Kafka Topics Creation Script for OpsCraft
set -euo pipefail

KAFKA_BOOTSTRAP_SERVER="${KAFKA_BOOTSTRAP_SERVER:-kafka:9092}"
PARTITIONS="${PARTITIONS:-3}"
REPLICATION_FACTOR="${REPLICATION_FACTOR:-1}"

echo "Creating Kafka topics for OpsCraft..."

# Function to create topic with error handling
create_topic() {
    local topic_name=$1
    local retention_ms=${2:-604800000}  # Default 7 days
    
    echo "Creating topic: $topic_name"
    kafka-topics --create \
        --bootstrap-server "$KAFKA_BOOTSTRAP_SERVER" \
        --topic "$topic_name" \
        --partitions "$PARTITIONS" \
        --replication-factor "$REPLICATION_FACTOR" \
        --config retention.ms="$retention_ms" \
        --config cleanup.policy=delete \
        --if-not-exists
}

# User events
create_topic "user-events" 2592000000  # 30 days retention

# Script events
create_topic "script-events" 2592000000

# Execution events
create_topic "execution-events" 604800000  # 7 days

# Secret events (longer retention for compliance)
create_topic "secret-events" 31536000000  # 365 days

# Approval events
create_topic "approval-events" 2592000000

# Notification events
create_topic "notification-events" 86400000  # 1 day

# Audit events (longest retention)
create_topic "audit-events" 31536000000

# System events
create_topic "system-events" 604800000

# Dead letter queue
create_topic "dlq-events" 2592000000

echo "All topics created successfully!"

# List all topics
echo "Current topics:"
kafka-topics --list --bootstrap-server "$KAFKA_BOOTSTRAP_SERVER"
