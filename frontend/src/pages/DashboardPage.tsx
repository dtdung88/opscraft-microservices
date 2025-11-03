import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { FileCode, Play, Lock, TrendingUp, Activity } from 'lucide-react'
import { scriptsApi, executionsApi, secretsApi, adminApi } from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'
import { formatRelativeTime, getStatusColor } from '@/lib/utils'

export default function DashboardPage() {
    const { user } = useAuthStore()

    const { data: scripts = [] } = useQuery({
        queryKey: ['scripts'],
        queryFn: () => scriptsApi.list({ limit: 5 }),
    })

    const { data: executions = [] } = useQuery({
        queryKey: ['executions'],
        queryFn: () => executionsApi.list({ limit: 5 }),
    })

    const { data: secrets = [] } = useQuery({
        queryKey: ['secrets'],
        queryFn: () => secretsApi.list({ limit: 5 }),
    })

    const { data: stats } = useQuery({
        queryKey: ['stats'],
        queryFn: () => adminApi.getStats(),
        enabled: user?.role === 'admin',
    })

    const statCards = [
        {
            name: 'Total Scripts',
            value: stats?.summary.total_scripts || scripts.length,
            icon: FileCode,
            color: 'bg-blue-500',
            href: '/scripts',
        },
        {
            name: 'Executions',
            value: stats?.summary.total_executions || executions.length,
            icon: Play,
            color: 'bg-green-500',
            href: '/executions',
        },
        {
            name: 'Secrets',
            value: stats?.summary.total_secrets || secrets.length,
            icon: Lock,
            color: 'bg-purple-500',
            href: '/secrets',
        },
        {
            name: 'Active Users',
            value: stats?.summary.total_users || 0,
            icon: Activity,
            color: 'bg-orange-500',
            href: '/admin',
        },
    ]

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
                <p className="mt-2 text-gray-600">
                    Welcome back, {user?.full_name || user?.username}!
                </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {statCards.map((stat) => (
                    <Link
                        key={stat.name}
                        to={stat.href}
                        className="card hover:shadow-lg transition-shadow"
                    >
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                                <p className="mt-2 text-3xl font-bold text-gray-900">{stat.value}</p>
                            </div>
                            <div className={`${stat.color} p-3 rounded-lg`}>
                                <stat.icon className="w-6 h-6 text-white" />
                            </div>
                        </div>
                    </Link>
                ))}
            </div>

            {/* Recent Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Recent Scripts */}
                <div className="card">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-bold text-gray-900">Recent Scripts</h2>
                        <Link to="/scripts" className="text-sm text-primary-600 hover:text-primary-700">
                            View all →
                        </Link>
                    </div>
                    <div className="space-y-3">
                        {scripts.length === 0 ? (
                            <p className="text-gray-500 text-center py-8">No scripts yet</p>
                        ) : (
                            scripts.map((script) => (
                                <Link
                                    key={script.id}
                                    to={`/scripts/${script.id}`}
                                    className="block p-3 rounded-lg hover:bg-gray-50 transition-colors"
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex-1">
                                            <p className="font-medium text-gray-900">{script.name}</p>
                                            <p className="text-sm text-gray-500 capitalize">{script.script_type}</p>
                                        </div>
                                        <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(script.status)}`}>
                                            {script.status}
                                        </span>
                                    </div>
                                </Link>
                            ))
                        )}
                    </div>
                </div>

                {/* Recent Executions */}
                <div className="card">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-bold text-gray-900">Recent Executions</h2>
                        <Link to="/executions" className="text-sm text-primary-600 hover:text-primary-700">
                            View all →
                        </Link>
                    </div>
                    <div className="space-y-3">
                        {executions.length === 0 ? (
                            <p className="text-gray-500 text-center py-8">No executions yet</p>
                        ) : (
                            executions.map((execution) => (
                                <Link
                                    key={execution.id}
                                    to={`/executions/${execution.id}`}
                                    className="block p-3 rounded-lg hover:bg-gray-50 transition-colors"
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex-1">
                                            <p className="font-medium text-gray-900">Execution #{execution.id}</p>
                                            <p className="text-sm text-gray-500">
                                                {formatRelativeTime(execution.started_at)}
                                            </p>
                                        </div>
                                        <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(execution.status)}`}>
                                            {execution.status}
                                        </span>
                                    </div>
                                </Link>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}