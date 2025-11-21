import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { User, Mail, Calendar, Shield, Key, Save } from 'lucide-react'
import { authApi } from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'
import { formatDate } from '@/lib/utils'
import api from '@/lib/api'

export default function ProfilePage() {
    const { user } = useAuthStore()
    const [isChangingPassword, setIsChangingPassword] = useState(false)
    const [passwordData, setPasswordData] = useState({
        old_password: '',
        new_password: '',
        confirm_password: '',
    })

    const { data: currentUser } = useQuery({
        queryKey: ['current-user'],
        queryFn: () => authApi.getCurrentUser(),
        initialData: user || undefined,
    })

    const changePasswordMutation = useMutation({
        mutationFn: async (data: { old_password: string; new_password: string }) => {
            await api.post('/auth/change-password', data)
        },
        onSuccess: () => {
            toast.success('Password changed successfully!')
            setIsChangingPassword(false)
            setPasswordData({
                old_password: '',
                new_password: '',
                confirm_password: '',
            })
        },
        onError: (error: unknown) => {
            const err = error as { response?: { data?: { detail?: string } } }
            toast.error(err.response?.data?.detail || 'Failed to change password')
        },
    })

    const handlePasswordChange = (e: React.FormEvent) => {
        e.preventDefault()

        if (passwordData.new_password !== passwordData.confirm_password) {
            toast.error('New passwords do not match')
            return
        }

        if (passwordData.new_password.length < 8) {
            toast.error('Password must be at least 8 characters')
            return
        }

        changePasswordMutation.mutate({
            old_password: passwordData.old_password,
            new_password: passwordData.new_password,
        })
    }

    if (!currentUser) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
        )
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900">Profile Settings</h1>
                <p className="mt-2 text-gray-600">Manage your account information</p>
            </div>

            {/* Profile Info */}
            <div className="card">
                <div className="flex items-center space-x-6 mb-6">
                    <div className="w-20 h-20 rounded-full bg-primary-100 flex items-center justify-center">
                        <span className="text-3xl font-bold text-primary-700">
                            {currentUser.username.charAt(0).toUpperCase()}
                        </span>
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900">
                            {currentUser.full_name || currentUser.username}
                        </h2>
                        <p className="text-gray-600">@{currentUser.username}</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="flex items-start space-x-3">
                        <User className="w-5 h-5 text-gray-400 mt-1" />
                        <div>
                            <p className="text-sm text-gray-500">Username</p>
                            <p className="font-medium text-gray-900">{currentUser.username}</p>
                        </div>
                    </div>

                    <div className="flex items-start space-x-3">
                        <Mail className="w-5 h-5 text-gray-400 mt-1" />
                        <div>
                            <p className="text-sm text-gray-500">Email</p>
                            <p className="font-medium text-gray-900">{currentUser.email}</p>
                        </div>
                    </div>

                    <div className="flex items-start space-x-3">
                        <Shield className="w-5 h-5 text-gray-400 mt-1" />
                        <div>
                            <p className="text-sm text-gray-500">Role</p>
                            <span
                                className={`inline-block px-3 py-1 text-sm rounded-full font-medium capitalize ${currentUser.role === 'admin'
                                    ? 'bg-purple-100 text-purple-800'
                                    : currentUser.role === 'operator'
                                        ? 'bg-blue-100 text-blue-800'
                                        : 'bg-gray-100 text-gray-800'
                                    }`}
                            >
                                {currentUser.role}
                            </span>
                        </div>
                    </div>

                    <div className="flex items-start space-x-3">
                        <Calendar className="w-5 h-5 text-gray-400 mt-1" />
                        <div>
                            <p className="text-sm text-gray-500">Member Since</p>
                            <p className="font-medium text-gray-900">
                                {formatDate(currentUser.created_at)}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Security Settings */}
            <div className="card">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center space-x-3">
                        <Key className="w-6 h-6 text-gray-600" />
                        <h2 className="text-xl font-bold text-gray-900">Security</h2>
                    </div>
                </div>

                {!isChangingPassword ? (
                    <div>
                        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                            <div>
                                <p className="font-medium text-gray-900">Password</p>
                                <p className="text-sm text-gray-500">
                                    Last changed: {currentUser.updated_at ? formatDate(currentUser.updated_at) : 'Never'}
                                </p>
                            </div>
                            <button
                                onClick={() => setIsChangingPassword(true)}
                                className="btn-secondary"
                            >
                                Change Password
                            </button>
                        </div>
                    </div>
                ) : (
                    <form onSubmit={handlePasswordChange} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Current Password
                            </label>
                            <input
                                type="password"
                                value={passwordData.old_password}
                                onChange={(e) =>
                                    setPasswordData({ ...passwordData, old_password: e.target.value })
                                }
                                className="input"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                New Password
                            </label>
                            <input
                                type="password"
                                value={passwordData.new_password}
                                onChange={(e) =>
                                    setPasswordData({ ...passwordData, new_password: e.target.value })
                                }
                                className="input"
                                minLength={8}
                                required
                            />
                            <p className="mt-1 text-sm text-gray-500">
                                Must be at least 8 characters long
                            </p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Confirm New Password
                            </label>
                            <input
                                type="password"
                                value={passwordData.confirm_password}
                                onChange={(e) =>
                                    setPasswordData({ ...passwordData, confirm_password: e.target.value })
                                }
                                className="input"
                                required
                            />
                        </div>

                        <div className="flex justify-end space-x-3 pt-4">
                            <button
                                type="button"
                                onClick={() => {
                                    setIsChangingPassword(false)
                                    setPasswordData({
                                        old_password: '',
                                        new_password: '',
                                        confirm_password: '',
                                    })
                                }}
                                className="btn-secondary"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={changePasswordMutation.isPending}
                                className="btn-primary flex items-center space-x-2"
                            >
                                <Save className="w-5 h-5" />
                                <span>
                                    {changePasswordMutation.isPending ? 'Saving...' : 'Save Password'}
                                </span>
                            </button>
                        </div>
                    </form>
                )}
            </div>

            {/* Role Permissions */}
            <div className="card">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Role Permissions</h2>
                <div className="space-y-3">
                    {currentUser.role === 'admin' && (
                        <>
                            <PermissionItem
                                title="Full System Access"
                                description="Complete control over all features and settings"
                                granted={true}
                            />
                            <PermissionItem
                                title="User Management"
                                description="Create, modify, and delete user accounts"
                                granted={true}
                            />
                        </>
                    )}

                    {(currentUser.role === 'admin' || currentUser.role === 'operator') && (
                        <>
                            <PermissionItem
                                title="Script Management"
                                description="Create, edit, and delete automation scripts"
                                granted={true}
                            />
                            <PermissionItem
                                title="Execute Scripts"
                                description="Run automation scripts and view execution logs"
                                granted={true}
                            />
                            <PermissionItem
                                title="Secret Management"
                                description="Create and manage encrypted secrets"
                                granted={true}
                            />
                        </>
                    )}

                    <PermissionItem
                        title="View Scripts"
                        description="View existing scripts and their details"
                        granted={true}
                    />
                    <PermissionItem
                        title="View Executions"
                        description="View execution history and logs"
                        granted={true}
                    />
                </div>
            </div>

            {/* Account Status */}
            <div className="card">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Account Status</h2>
                <div className="flex items-center justify-between p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center space-x-3">
                        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                        <div>
                            <p className="font-medium text-green-900">Account Active</p>
                            <p className="text-sm text-green-700">Your account is in good standing</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

function PermissionItem({
    title,
    description,
    granted,
}: {
    title: string
    description: string
    granted: boolean
}) {
    return (
        <div className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50">
            <div
                className={`w-5 h-5 rounded-full flex items-center justify-center mt-0.5 ${granted ? 'bg-green-100' : 'bg-gray-100'
                    }`}
            >
                {granted ? (
                    <svg
                        className="w-3 h-3 text-green-600"
                        fill="none"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path d="M5 13l4 4L19 7"></path>
                    </svg>
                ) : (
                    <svg
                        className="w-3 h-3 text-gray-400"
                        fill="none"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                )}
            </div>
            <div className="flex-1">
                <p className="font-medium text-gray-900">{title}</p>
                <p className="text-sm text-gray-500">{description}</p>
            </div>
        </div>
    )
}