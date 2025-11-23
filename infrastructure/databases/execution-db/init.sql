-- PostgreSQL initialization for Execution Database
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE SCHEMA IF NOT EXISTS executions;
SET search_path TO executions, public;

CREATE TABLE IF NOT EXISTS executions (
    id SERIAL PRIMARY KEY,
    script_id INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    parameters JSONB DEFAULT '{}',
    output TEXT,
    error TEXT,
    exit_code INTEGER,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    executed_by VARCHAR(255) NOT NULL,
    execution_time_ms INTEGER,
    container_id VARCHAR(255),
    resource_usage JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'success', 'failed', 'cancelled', 'timeout'))
);

CREATE INDEX IF NOT EXISTS idx_executions_script_id ON executions(script_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_executed_by ON executions(executed_by);
CREATE INDEX IF NOT EXISTS idx_executions_started_at ON executions(started_at DESC);

CREATE TABLE IF NOT EXISTS execution_logs (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    level VARCHAR(20) NOT NULL DEFAULT 'INFO',
    message TEXT NOT NULL,
    source VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_execution_logs_execution_id ON execution_logs(execution_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_timestamp ON execution_logs(timestamp);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA executions TO postgres;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA executions TO postgres;
