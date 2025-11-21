export interface User {
    id: number
    username: string
    email: string
    full_name: string | null
    role: 'admin' | 'operator' | 'viewer'
    is_active: boolean
    created_at: string
    updated_at?: string
}

export interface LoginCredentials {
    username: string
    password: string
}

export interface RegisterData {
    username: string
    email: string
    password: string
    full_name?: string
}

export interface TokenResponse {
    access_token: string
    refresh_token: string
    token_type: string
}

export type ScriptType = 'bash' | 'python' | 'ansible' | 'terraform'
export type ScriptStatus = 'draft' | 'active' | 'deprecated' | 'archived'

export interface Script {
    id: number
    name: string
    description: string | null
    script_type: ScriptType
    content: string
    parameters: Record<string, unknown> | null
    status: ScriptStatus
    version: string
    tags: string[] | null
    created_at: string
    updated_at: string
    created_by: string
    updated_by: string
}

export interface CreateScriptData {
    name: string
    description?: string
    script_type: ScriptType
    content: string
    parameters?: Record<string, unknown>
    tags?: string[]
    version?: string
}

export interface UpdateScriptData {
    name?: string
    description?: string
    content?: string
    parameters?: Record<string, unknown>
    status?: ScriptStatus
    tags?: string[]
    version?: string
}

export type ExecutionStatus = 'pending' | 'running' | 'success' | 'failed' | 'cancelled'

export interface Execution {
    id: number
    script_id: number
    status: ExecutionStatus
    parameters: Record<string, unknown> | null
    output: string | null
    error: string | null
    started_at: string
    completed_at: string | null
    executed_by: string
    created_at: string
}

export interface CreateExecutionData {
    script_id: number
    parameters?: Record<string, unknown>
}

export interface Secret {
    id: number
    name: string
    description: string | null
    category: string | null
    value?: string
    created_at: string
    updated_at: string
    created_by: string
    updated_by: string
    is_active: boolean
    last_accessed_at: string | null
}

export interface CreateSecretData {
    name: string
    description?: string
    value: string
    category?: string
}

export interface UpdateSecretData {
    name?: string
    description?: string
    value?: string
    category?: string
}

export interface AuditLog {
    id: number
    secret_id: number
    action: 'create' | 'read' | 'update' | 'delete' | 'access'
    user: string
    ip_address: string | null
    timestamp: string
    details: string | null
}

export interface ServiceStatus {
    status: string
    version?: string
}

export interface SystemStats {
    services: Record<string, ServiceStatus>
    summary: {
        total_users: number
        total_scripts: number
        total_executions: number
        total_secrets: number
    }
}

export interface ApiError {
    detail: string | Record<string, unknown>
}