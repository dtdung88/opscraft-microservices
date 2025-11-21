import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Play, Filter, RefreshCw, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { executionsApi } from '@/lib/api'
import { formatDate, formatRelativeTime, getStatusColor } from '@/lib/utils'
import type { ExecutionStatus } from '@/types'

const statusIcons = {
    pending: Clock,
    running: Loader2,
    success: CheckCircle,
    failed: XCircle,
    cancelled: XCircle,
}

export default function ResponsiveExecutionsPage() {
    const [filterStatus, setFilterStatus] = useState<ExecutionStatus | ''>('')
    const [showFilters, setShowFilters] = useState(false)

    const { data: executions = [], isLoading, refetch } = useQuery({
        queryKey: ['executions', filterStatus],
        queryFn: () =>
            executionsApi.list({
                status: filterStatus || undefined,
            }),
        refetchInterval: 5000,
    })

    const stats = {
        total: executions.length,
        running: executions.filter((e) => e.status === 'running').length,
        success: executions.filter((e) => e.status === 'success').length,
        failed: executions.filter((e) => e.status === 'failed').length,
    }

    return (
        <div className="space-y-4 sm:space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Executions</h1>
                    <p className="mt-2 text-sm text-gray-600">Monitor script execution history</p>
                </div>
                <button
                    onClick={() => refetch()}
                    className="btn-secondary flex items-center justify-center space-x-2"
                >
                    <RefreshCw className="w-5 h-5" />
                    <span>Refresh</span>
                </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
                <div className="card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-xs sm:text-sm text-gray-500">Total</p>
                            <p className="text-xl sm:text-2xl font-bold text-gray-900">{stats.total}</p>
                        </div>
                        <Play className="w-6 h-6 sm:w-8 sm:h-8 text-gray-400" />
                    </div>
                </div>

                <div className="card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-xs sm:text-sm text-gray-500">Running</p>
                            <p className="text-xl sm:text-2xl font-bold text-blue-600">{stats.running}</p>
                        </div>
                        <Loader2 className="w-6 h-6 sm:w-8 sm:h-8 text-blue-400 animate-spin" />
                    </div>
                </div>

                <div className="card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-xs sm:text-sm text-gray-500">Success</p>
                            <p className="text-xl sm:text-2xl font-bold text-green-600">{stats.success}</p>
                        </div>
                        <CheckCircle className="w-6 h-6 sm:w-8 sm:h-8 text-green-400" />
                    </div>
                </div>

                <div className="card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-xs sm:text-sm text-gray-500">Failed</p>
                            <p className="text-xl sm:text-2xl font-bold text-red-600">{stats.failed}</p>
                        </div>
                        <XCircle className="w-6 h-6 sm:w-8 sm:h-8 text-red-400" />
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="card">
                <div className="flex items-center justify-between mb-4">
                    <button
                        onClick={() => setShowFilters(!showFilters)}
                        className="flex items-center space-x-2 text-sm"
                    >
                        <Filter className="w-4 h-4" />
                        <span>{showFilters ? 'Hide' : 'Show'} Filters</span>
                    </button>
                </div>

                {showFilters && (
                    <select
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value as ExecutionStatus | '')}
                        className="input w-full sm:w-auto"
                    >
                        <option value="">All Status</option>
                        <option value="pending">Pending</option>
                        <option value="running">Running</option>
                        <option value="success">Success</option>
                        <option value="failed">Failed</option>
                        <option value="cancelled">Cancelled</option>
                    </select>
                )}
            </div>

            {/* Executions List */}
            {isLoading ? (
                <div className="card text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading executions...</p>
                </div>
            ) : executions.length === 0 ? (
                <div className="card text-center py-12">
                    <Play className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">No executions found</p>
                    <Link to="/scripts" className="mt-4 inline-block text-primary-600 hover:text-primary-700">
                        Go to Scripts →
                    </Link>
                </div>
            ) : (
                <>
                    {/* Mobile Card View */}
                    <div className="space-y-4 sm:hidden">
                        {executions.map((execution) => {
                            const StatusIcon = statusIcons[execution.status]
                            const duration = execution.completed_at
                                ? Math.round(
                                    (new Date(execution.completed_at).getTime() -
                                        new Date(execution.started_at).getTime()) /
                                    1000
                                )
                                : null

                            return (
                                <Link
                                    key={execution.id}
                                    to={`/executions/${execution.id}`}
                                    className="card hover:shadow-lg transition-shadow"
                                >
                                    <div className="flex items-start justify-between mb-3">
                                        <div className="flex items-center space-x-2">
                                            <StatusIcon
                                                className={`w-5 h-5 ${execution.status === 'running' ? 'animate-spin' : ''}`}
                                            />
                                            <span className="font-medium">Execution #{execution.id}</span>
                                        </div>
                                        <span
                                            className={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor(
                                                execution.status
                                            )}`}
                                        >
                                            {execution.status}
                                        </span>
                                    </div>
                                    <div className="space-y-2 text-sm text-gray-600">
                                        <div className="flex justify-between">
                                            <span>Script:</span>
                                            <span className="font-medium">#{execution.script_id}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>User:</span>
                                            <span className="font-medium">{execution.executed_by}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Started:</span>
                                            <span className="font-medium">{formatRelativeTime(execution.started_at)}</span>
                                        </div>
                                        {duration && (
                                            <div className="flex justify-between">
                                                <span>Duration:</span>
                                                <span className="font-medium">{duration}s</span>
                                            </div>
                                        )}
                                    </div>
                                </Link>
                            )
                        })}
                    </div>

                    {/* Desktop Table View */}
                    <div className="hidden sm:block card overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                            ID
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                            Script
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                            Status
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                            Executed By
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                            Started
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                            Duration
                                        </th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                                            Actions
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {executions.map((execution) => {
                                        const StatusIcon = statusIcons[execution.status]
                                        const duration = execution.completed_at
                                            ? Math.round(
                                                (new Date(execution.completed_at).getTime() -
                                                    new Date(execution.started_at).getTime()) /
                                                1000
                                            )
                                            : null

                                        return (
                                            <tr key={execution.id} className="hover:bg-gray-50">
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <span className="text-sm font-medium text-gray-900">
                                                        #{execution.id}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <Link
                                                        to={`/scripts/${execution.script_id}`}
                                                        className="text-sm text-primary-600 hover:text-primary-700"
                                                    >
                                                        Script #{execution.script_id}
                                                    </Link>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="flex items-center space-x-2">
                                                        <StatusIcon
                                                            className={`w-5 h-5 ${execution.status === 'running' ? 'animate-spin' : ''
                                                                }`}
                                                        />
                                                        <span
                                                            className={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor(
                                                                execution.status
                                                            )}`}
                                                        >
                                                            {execution.status}
                                                        </span>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                    {execution.executed_by}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    <div>
                                                        <div>{formatRelativeTime(execution.started_at)}</div>
                                                        <div className="text-xs">{formatDate(execution.started_at)}</div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    {duration ? `${duration}s` : '-'}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                    <Link
                                                        to={`/executions/${execution.id}`}
                                                        className="text-primary-600 hover:text-primary-700"
                                                    >
                                                        View Details →
                                                    </Link>
                                                </td>
                                            </tr>
                                        )
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}