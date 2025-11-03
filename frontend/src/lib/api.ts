import axios, { AxiosError } from 'axios'
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
api.interceptors.request.use((config) => {
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
            // Token expired, try to refresh
            const refreshToken = localStorage.getItem('refresh_token')
            if (refreshToken) {
                try {
                    const { data } = await axios.post<TokenResponse>(
                        `${API_URL}/api/v1/auth/refresh`,
                        { refresh_token: refreshToken }
                    )
                    localStorage.setItem('access_token', data.access_token)
                    localStorage.setItem('refresh_token', data.refresh_token)

                    // Retry original request
                    if (error.config) {
                        error.config.headers.Authorization = `Bearer ${data.access_token}`
                        return axios.request(error.config)
                    }
                } catch {
                    // Refresh failed, logout
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
    login: async (credentials: LoginCredentials) => {
        const { data } = await api.post<TokenResponse>('/auth/login', credentials)
        return data
    },

    register: async (userData: RegisterData) => {
        const { data } = await api.post<User>('/auth/register', userData)
        return data
    },

    getCurrentUser: async () => {
        const { data } = await api.get<User>('/auth/me')
        return data
    },

    logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
    },
}

// Scripts API
export const scriptsApi = {
    list: async (params?: { skip?: number; limit?: number; search?: string; script_type?: string; status?: string }) => {
        const { data } = await api.get<Script[]>('/scripts', { params })
        return data
    },

    get: async (id: number) => {
        const { data } = await api.get<Script>(`/scripts/${id}`)
        return data
    },

    create: async (scriptData: CreateScriptData) => {
        const { data } = await api.post<Script>('/scripts', scriptData)
        return data
    },

    update: async (id: number, scriptData: UpdateScriptData) => {
        const { data } = await api.put<Script>(`/scripts/${id}`, scriptData)
        return data
    },

    delete: async (id: number) => {
        await api.delete(`/scripts/${id}`)
    },
}

// Executions API
export const executionsApi = {
    list: async (params?: { skip?: number; limit?: number; status?: string }) => {
        const { data } = await api.get<Execution[]>('/executions', { params })
        return data
    },

    get: async (id: number) => {
        const { data } = await api.get<Execution>(`/executions/${id}`)
        return data
    },

    create: async (executionData: CreateExecutionData) => {
        const { data } = await api.post<Execution>('/executions', executionData)
        return data
    },

    cancel: async (id: number) => {
        await api.post(`/executions/${id}/cancel`)
    },
}

// Secrets API
export const secretsApi = {
    list: async (params?: { skip?: number; limit?: number }) => {
        const { data } = await api.get<Secret[]>('/secrets', { params })
        return data
    },

    get: async (id: number, reveal: boolean = false) => {
        const { data } = await api.get<Secret>(`/secrets/${id}`, {
            params: { reveal },
        })
        return data
    },

    create: async (secretData: CreateSecretData) => {
        const { data } = await api.post<Secret>('/secrets', secretData)
        return data
    },

    update: async (id: number, secretData: UpdateSecretData) => {
        const { data } = await api.put<Secret>(`/secrets/${id}`, secretData)
        return data
    },

    delete: async (id: number) => {
        await api.delete(`/secrets/${id}`)
    },

    getAuditLogs: async (id: number) => {
        const { data } = await api.get<AuditLog[]>(`/secrets/${id}/audit`)
        return data
    },
}

// Admin API
export const adminApi = {
    getStats: async () => {
        const { data } = await api.get<SystemStats>('/admin/stats')
        return data
    },

    getUsers: async () => {
        const { data } = await api.get<User[]>('/admin/users')
        return data
    },

    updateUserRole: async (userId: number, role: string) => {
        const { data } = await api.post(`/admin/users/${userId}/role`, { role })
        return data
    },
}

export default api