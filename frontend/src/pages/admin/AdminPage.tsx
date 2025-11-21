import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import {
    Users,
    Activity,
    Database,
    Server,
    TrendingUp,
    Shield,
    AlertCircle,
    CheckCircle,
    Settings,
} from 'lucide-react'
import { adminApi } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import type { User, ServiceStatus } from '@/types'

export default function AdminPage() {
    const queryClient = useQueryClient()
    const [selectedUser, setSelectedUser] = useState<User | null>(null)
    const [showRoleModal, setShowRoleModal] = useState(false)

    const { data: stats } = useQuery({
        queryKey: ['admin-stats'],
        queryFn: () => adminApi.getStats(),
    })

    const { data: users = [] } = useQuery({
        queryKey: ['admin-users'],
        queryFn: () => adminApi.getUsers(),
    })

    const updateRoleMutation = useMutation({
        mutationFn: ({ userId, role }: { userId: number; role: string }) =>
            adminApi.updateUserRole(userId, role),
        onSuccess: () => {
            toast.success('User role updated successfully!')
            queryClient.invalidateQueries({ queryKey: ['admin-users'] })
            setShowRoleModal(false)
            setSelectedUser(null)
        },
        onError: (error: unknown) => {
            const err = error as { response?: { data?: { detail?: string } } }
            toast.error(err.response?.data?.detail || 'Failed to update user role')
        },
    })

    const handleChangeRole = (user: User) => {
        setSelectedUser(user)
        setShowRoleModal(true)
    }

    const serviceStatus = stats?.services || {}
    const summary = stats?.summary || {
        total_users: 0,
        total_scripts: 0,
        total_executions: 0,
        total_secrets: 0,
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
                <p className="mt-2 text-gray-600">System administration and monitoring</p>
            </div>

            {/* System Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-500">Total Users</p>
                            <p className="text-3xl font-bold text-gray-900">{summary.total_users}</p>
                        </div>
                        <Users className="w-10 h-10 text-primary-400" />
                    </div>
                </div>

                <div className="card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-500">Total Scripts</p>
                            <p className="text-3xl font-bold text-gray-900">{summary.total_scripts}</p>
                        </div>
                        <Database className="w-10 h-10 text-blue-400" />
                    </div>
                </div>

                <div className="card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-500">Total Executions</p>
                            <p className="text-3xl font-bold text-gray-900">{summary.total_executions}</p>
                        </div>
                        <Activity className="w-10 h-10 text-green-400" />
                    </div>
                </div>

                <div className="card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-500">Total Secrets</p>
                            <p className="text-3xl font-bold text-gray-900">{summary.total_secrets}</p>
                        </div>
                        <Shield className="w-10 h-10 text-purple-400" />
                    </div>
                </div>
            </div>

            {/* Service Health */}
            <div className="card">
                <div className="flex items-center space-x-3 mb-6">
                    <Server className="w-6 h-6 text-gray-600" />
                    <h2 className="text-xl font-bold text-gray-900">Service Health</h2>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(serviceStatus).map(([service, data]) => {
                        const serviceData = data as ServiceStatus
                        const isHealthy = serviceData.status === 'healthy' || serviceData.status !== 'unavailable'

                        return (
                            <div
                                key={service}
                                className={`p-4 rounded-lg border-2 ${isHealthy
                                    ? 'border-green-200 bg-green-50'
                                    : 'border-red-200 bg-red-50'
                                    }`}
                            >
                                <div className="flex items-center justify-between mb-2">
                                    <h3 className="font-semibold text-gray-900 capitalize">{service}</h3>
                                    {isHealthy ? (
                                        <CheckCircle className="w-5 h-5 text-green-600" />
                                    ) : (
                                        <AlertCircle className="w-5 h-5 text-red-600" />
                                    )}
                                </div>
                                <p
                                    className={`text-sm ${isHealthy ? 'text-green-700' : 'text-red-700'
                                        }`}
                                >
                                    {serviceData.status || 'Unknown'}
                                </p>
                                {serviceData.version && (
                                    <p className="text-xs text-gray-600 mt-1">Version: {serviceData.version}</p>
                                )}
                            </div>
                        )
                    })}
                </div>
            </div>

            {/* User Management */}
            <div className="card">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center space-x-3">
                        <Users className="w-6 h-6 text-gray-600" />
                        <h2 className="text-xl font-bold text-gray-900">User Management</h2>
                    </div>
                    <span className="text-sm text-gray-500">{users.length} total users</span>
                </div>

                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                    User
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                    Email
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                    Role
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                    Status
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                    Created
                                </th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {users.map((user) => (
                                <tr key={user.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center">
                                            <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                                                <span className="text-primary-700 font-semibold">
                                                    {user.username.charAt(0).toUpperCase()}
                                                </span>
                                            </div>
                                            <div className="ml-4">
                                                <div className="text-sm font-medium text-gray-900">
                                                    {user.full_name || user.username}
                                                </div>
                                                <div className="text-sm text-gray-500">@{user.username}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        {user.email}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span
                                            className={`px-2 py-1 text-xs rounded-full font-medium capitalize ${user.role === 'admin'
                                                ? 'bg-purple-100 text-purple-800'
                                                : user.role === 'operator'
                                                    ? 'bg-blue-100 text-blue-800'
                                                    : 'bg-gray-100 text-gray-800'
                                                }`}
                                        >
                                            {user.role}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span
                                            className={`px-2 py-1 text-xs rounded-full font-medium ${user.is_active
                                                ? 'bg-green-100 text-green-800'
                                                : 'bg-red-100 text-red-800'
                                                }`}
                                        >
                                            {user.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {formatDate(user.created_at)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button
                                            onClick={() => handleChangeRole(user)}
                                            className="text-primary-600 hover:text-primary-700"
                                        >
                                            Change Role
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* External Links */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <a
                    href="http://localhost:9090"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="card hover:shadow-lg transition-shadow cursor-pointer"
                >
                    <div className="flex items-center space-x-4">
                        <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                            <TrendingUp className="w-6 h-6 text-orange-600" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-gray-900">Prometheus</h3>
                            <p className="text-sm text-gray-500">Metrics & Monitoring</p>
                        </div>
                    </div>
                </a>

                <a
                    href="http://localhost:3001"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="card hover:shadow-lg transition-shadow cursor-pointer"
                >
                    <div className="flex items-center space-x-4">
                        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                            <Activity className="w-6 h-6 text-blue-600" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-gray-900">Grafana</h3>
                            <p className="text-sm text-gray-500">Dashboards & Analytics</p>
                        </div>
                    </div>
                </a>

                <a
                    href="http://localhost:16686"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="card hover:shadow-lg transition-shadow cursor-pointer"
                >
                    <div className="flex items-center space-x-4">
                        <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                            <Settings className="w-6 h-6 text-purple-600" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-gray-900">Jaeger</h3>
                            <p className="text-sm text-gray-500">Distributed Tracing</p>
                        </div>
                    </div>
                </a>
            </div>

            {/* Role Change Modal */}
            {showRoleModal && selectedUser && (
                <RoleChangeModal
                    user={selectedUser}
                    onClose={() => {
                        setShowRoleModal(false)
                        setSelectedUser(null)
                    }}
                    onSubmit={(role) =>
                        updateRoleMutation.mutate({ userId: selectedUser.id, role })
                    }
                    isLoading={updateRoleMutation.isPending}
                />
            )}
        </div>
    )
}

function RoleChangeModal({
    user,
    onClose,
    onSubmit,
    isLoading,
}: {
    user: User
    onClose: () => void
    onSubmit: (role: string) => void
    isLoading: boolean
}) {
    const [selectedRole, setSelectedRole] = useState(user.role)

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        onSubmit(selectedRole)
    }

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
                <div className="p-6 border-b border-gray-200">
                    <h2 className="text-2xl font-bold text-gray-900">Change User Role</h2>
                    <p className="mt-2 text-gray-600">
                        Change role for <span className="font-semibold">{user.username}</span>
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-3">
                            Select Role
                        </label>
                        <div className="space-y-3">
                            <label className="flex items-center p-3 border-2 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
                                <input
                                    type="radio"
                                    name="role"
                                    value="viewer"
                                    checked={selectedRole === 'viewer'}
                                    onChange={(e) => setSelectedRole(e.target.value as User['role'])}
                                    className="mr-3"
                                />
                                <div>
                                    <p className="font-medium text-gray-900">Viewer</p>
                                    <p className="text-sm text-gray-500">Read-only access</p>
                                </div>
                            </label>

                            <label className="flex items-center p-3 border-2 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
                                <input
                                    type="radio"
                                    name="role"
                                    value="operator"
                                    checked={selectedRole === 'operator'}
                                    onChange={(e) => setSelectedRole(e.target.value as User['role'])}
                                    className="mr-3"
                                />
                                <div>
                                    <p className="font-medium text-gray-900">Operator</p>
                                    <p className="text-sm text-gray-500">
                                        Can create and execute scripts
                                    </p>
                                </div>
                            </label>

                            <label className="flex items-center p-3 border-2 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
                                <input
                                    type="radio"
                                    name="role"
                                    value="admin"
                                    checked={selectedRole === 'admin'}
                                    onChange={(e) => setSelectedRole(e.target.value as User['role'])}
                                    className="mr-3"
                                />
                                <div>
                                    <p className="font-medium text-gray-900">Admin</p>
                                    <p className="text-sm text-gray-500">Full system access</p>
                                </div>
                            </label>
                        </div>
                    </div>

                    <div className="flex justify-end space-x-3 pt-4">
                        <button type="button" onClick={onClose} className="btn-secondary">
                            Cancel
                        </button>
                        <button type="submit" disabled={isLoading} className="btn-primary">
                            {isLoading ? 'Updating...' : 'Update Role'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}