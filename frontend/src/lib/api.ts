import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import type {
    User,
    LoginCredentials,
    RegisterData,
    TokenResponse,
    Script,
    CreateScriptData,
    UpdateScriptData,
    Execution,
    CreateExecutionData,
    Secret,
    CreateSecretData,
    UpdateSecretData,
    AuditLog,
    SystemStats,
} from '@/types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
    baseURL: `${API_URL}/api/v1`,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Request interceptor to add auth token
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// Response interceptor to handle errors
api.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        if (error.response?.status === 401) {
            const refreshToken = localStorage.getItem('refresh_token')
            if (refreshToken) {
                try {
                    const { data } = await axios.post<TokenResponse>(
                        `${API_URL}/api/v1/auth/refresh`,
                        { refresh_token: refreshToken }
                    )
                    localStorage.setItem('access_token', data.access_token)
                    localStorage.setItem('refresh_token', data.refresh_token)

                    if (error.config) {
                        error.config.headers.Authorization = `Bearer ${data.access_token}`
                        return axios.request(error.config)
                    }
                } catch {
                    localStorage.removeItem('access_token')
                    localStorage.removeItem('refresh_token')
                    window.location.href = '/login'
                }
            }
        }
        return Promise.reject(error)
    }
)

// Auth API
export const authApi = {
    login: async (credentials: LoginCredentials): Promise<TokenResponse> => {
        const { data } = await api.post<TokenResponse>('/auth/login', credentials)
        return data
    },

    register: async (userData: RegisterData): Promise<User> => {
        const { data } = await api.post<User>('/auth/register', userData)
        return data
    },

    getCurrentUser: async (): Promise<User> => {
        const { data } = await api.get<User>('/auth/me')
        return data
    },

    logout: (): void => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
    },
}

// Scripts API
interface ScriptListParams {
    skip?: number
    limit?: number
    search?: string
    script_type?: string
    status?: string
}

export const scriptsApi = {
    list: async (params?: ScriptListParams): Promise<Script[]> => {
        const { data } = await api.get<Script[]>('/scripts', { params })
        return data
    },

    get: async (id: number): Promise<Script> => {
        const { data } = await api.get<Script>(`/scripts/${id}`)
        return data
    },

    create: async (scriptData: CreateScriptData): Promise<Script> => {
        const { data } = await api.post<Script>('/scripts', scriptData)
        return data
    },

    update: async (id: number, scriptData: UpdateScriptData): Promise<Script> => {
        const { data } = await api.put<Script>(`/scripts/${id}`, scriptData)
        return data
    },

    delete: async (id: number): Promise<void> => {
        await api.delete(`/scripts/${id}`)
    },
}

// Executions API
interface ExecutionListParams {
    skip?: number
    limit?: number
    status?: string
}

export const executionsApi = {
    list: async (params?: ExecutionListParams): Promise<Execution[]> => {
        const { data } = await api.get<Execution[]>('/executions', { params })
        return data
    },

    get: async (id: number): Promise<Execution> => {
        const { data } = await api.get<Execution>(`/executions/${id}`)
        return data
    },

    create: async (executionData: CreateExecutionData): Promise<Execution> => {
        const { data } = await api.post<Execution>('/executions', executionData)
        return data
    },

    cancel: async (id: number): Promise<void> => {
        await api.post(`/executions/${id}/cancel`)
    },
}

// Secrets API
interface SecretListParams {
    skip?: number
    limit?: number
}

export const secretsApi = {
    list: async (params?: SecretListParams): Promise<Secret[]> => {
        const { data } = await api.get<Secret[]>('/secrets', { params })
        return data
    },

    get: async (id: number, reveal: boolean = false): Promise<Secret> => {
        const { data } = await api.get<Secret>(`/secrets/${id}`, {
            params: { reveal },
        })
        return data
    },

    create: async (secretData: CreateSecretData): Promise<Secret> => {
        const { data } = await api.post<Secret>('/secrets', secretData)
        return data
    },

    update: async (id: number, secretData: UpdateSecretData): Promise<Secret> => {
        const { data } = await api.put<Secret>(`/secrets/${id}`, secretData)
        return data
    },

    delete: async (id: number): Promise<void> => {
        await api.delete(`/secrets/${id}`)
    },

    getAuditLogs: async (id: number): Promise<AuditLog[]> => {
        const { data } = await api.get<AuditLog[]>(`/secrets/${id}/audit`)
        return data
    },
}

// Admin API
interface UpdateRoleResponse {
    message: string
    user: User
}

export const adminApi = {
    getStats: async (): Promise<SystemStats> => {
        const { data } = await api.get<SystemStats>('/admin/stats')
        return data
    },

    getUsers: async (): Promise<User[]> => {
        const { data } = await api.get<User[]>('/admin/users')
        return data
    },

    updateUserRole: async (userId: number, role: string): Promise<UpdateRoleResponse> => {
        const { data } = await api.post<UpdateRoleResponse>(`/admin/users/${userId}/role`, { role })
        return data
    },
}

export default api