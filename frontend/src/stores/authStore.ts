import { create } from 'zustand'
import { authApi } from '@/lib/api'
import type { User, LoginCredentials, RegisterData } from '@/types'

interface AuthState {
    user: User | null
    isAuthenticated: boolean
    isLoading: boolean
    login: (credentials: LoginCredentials) => Promise<void>
    register: (userData: RegisterData) => Promise<void>
    logout: () => void
    loadUser: () => Promise<void>
    setUser: (user: User | null) => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
    user: null,
    isAuthenticated: !!localStorage.getItem('access_token'),
    isLoading: false,

    login: async (credentials: LoginCredentials) => {
        set({ isLoading: true })
        try {
            const tokens = await authApi.login(credentials)
            localStorage.setItem('access_token', tokens.access_token)
            localStorage.setItem('refresh_token', tokens.refresh_token)

            const user = await authApi.getCurrentUser()
            set({ user, isAuthenticated: true, isLoading: false })
        } catch (error) {
            set({ isLoading: false })
            throw error
        }
    },

    register: async (userData: RegisterData) => {
        set({ isLoading: true })
        try {
            await authApi.register(userData)
            // After registration, automatically log in
            await get().login({
                username: userData.username,
                password: userData.password,
            })
        } catch (error) {
            set({ isLoading: false })
            throw error
        }
    },

    logout: () => {
        authApi.logout()
        set({ user: null, isAuthenticated: false })
    },

    loadUser: async () => {
        const token = localStorage.getItem('access_token')
        if (!token) {
            set({ isAuthenticated: false, user: null })
            return
        }

        try {
            const user = await authApi.getCurrentUser()
            set({ user, isAuthenticated: true })
        } catch {
            set({ isAuthenticated: false, user: null })
            authApi.logout()
        }
    },

    setUser: (user: User | null) => {
        set({ user })
    },
}))