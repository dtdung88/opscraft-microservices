import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'react-hot-toast'
import { UserPlus, Loader2 } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import type { RegisterData } from '@/types'

const registerSchema = z.object({
    username: z.string().min(3, 'Username must be at least 3 characters'),
    email: z.string().email('Invalid email address'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    full_name: z.string().optional(),
})

export default function RegisterPage() {
    const navigate = useNavigate()
    const register = useAuthStore((state) => state.register)
    const [isLoading, setIsLoading] = useState(false)

    const {
        register: registerField,
        handleSubmit,
        formState: { errors },
    } = useForm<RegisterData>({
        resolver: zodResolver(registerSchema),
    })

    const onSubmit = async (data: RegisterData) => {
        setIsLoading(true)
        try {
            await register(data)
            toast.success('Account created successfully!')
            navigate('/')
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Registration failed')
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                <div className="bg-white rounded-2xl shadow-xl p-8">
                    <div className="text-center mb-8">
                        <h1 className="text-3xl font-bold text-gray-900 mb-2">Create Account</h1>
                        <p className="text-gray-600">Join OpsCraft Platform</p>
                    </div>

                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                        <div>
                            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                                Username
                            </label>
                            <input
                                {...registerField('username')}
                                type="text"
                                id="username"
                                className="input"
                                placeholder="Choose a username"
                            />
                            {errors.username && (
                                <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
                            )}
                        </div>

                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                                Email
                            </label>
                            <input
                                {...registerField('email')}
                                type="email"
                                id="email"
                                className="input"
                                placeholder="your.email@example.com"
                            />
                            {errors.email && (
                                <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
                            )}
                        </div>

                        <div>
                            <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-2">
                                Full Name (Optional)
                            </label>
                            <input
                                {...registerField('full_name')}
                                type="text"
                                id="full_name"
                                className="input"
                                placeholder="John Doe"
                            />
                        </div>

                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                                Password
                            </label>
                            <input
                                {...registerField('password')}
                                type="password"
                                id="password"
                                className="input"
                                placeholder="Create a strong password"
                            />
                            {errors.password && (
                                <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
                            )}
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full btn-primary flex items-center justify-center space-x-2"
                        >
                            {isLoading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <>
                                    <UserPlus className="w-5 h-5" />
                                    <span>Create Account</span>
                                </>
                            )}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-sm text-gray-600">
                            Already have an account?{' '}
                            <Link to="/login" className="text-primary-600 hover:text-primary-700 font-medium">
                                Sign in
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}