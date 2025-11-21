import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import {
    ArrowLeft,
    Play,
    XCircle,
    CheckCircle,
    Clock,
    AlertCircle,
    Terminal,
} from 'lucide-react'
import { executionsApi, scriptsApi } from '@/lib/api'
import { useWebSocket } from '@/hooks/useWebSocket'
import { formatDate, getStatusColor } from '@/lib/utils'
import type { Execution, ExecutionStatus } from '@/types'

interface WebSocketMessage {
    output?: string
    log?: string
}

export default function ExecutionDetailPage() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()
    const queryClient = useQueryClient()
    const logsEndRef = useRef<HTMLDivElement>(null)
    const [autoScroll, setAutoScroll] = useState(true)

    const { data: execution, isLoading } = useQuery({
        queryKey: ['execution', id],
        queryFn: () => executionsApi.get(Number(id)),
        enabled: !!id,
        refetchInterval: (query) => {
            const data = query.state.data as Execution | undefined
            return data?.status === 'running' || data?.status === 'pending' ? 2000 : false
        },
    })

    const { data: script } = useQuery({
        queryKey: ['script', execution?.script_id],
        queryFn: () => scriptsApi.get(execution!.script_id),
        enabled: !!execution?.script_id,
    })

    const { messages, isConnected } = useWebSocket(`executions/${id}`)

    const cancelMutation = useMutation({
        mutationFn: () => executionsApi.cancel(Number(id)),
        onSuccess: () => {
            toast.success('Execution cancelled')
            queryClient.invalidateQueries({ queryKey: ['execution', id] })
            queryClient.invalidateQueries({ queryKey: ['executions'] })
        },
        onError: (error: unknown) => {
            const err = error as { response?: { data?: { detail?: string } } }
            toast.error(err.response?.data?.detail || 'Failed to cancel execution')
        },
    })

    useEffect(() => {
        if (autoScroll && logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
        }
    }, [messages, execution?.output, autoScroll])

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
        )
    }

    if (!execution) {
        return (
            <div className="card text-center py-12">
                <p className="text-gray-600">Execution not found</p>
            </div>
        )
    }

    const statusIcons: Record<ExecutionStatus, typeof Clock> = {
        pending: Clock,
        running: Play,
        success: CheckCircle,
        failed: XCircle,
        cancelled: AlertCircle,
    }

    const StatusIcon = statusIcons[execution.status]

    const duration = execution.completed_at
        ? Math.round(
            (new Date(execution.completed_at).getTime() -
                new Date(execution.started_at).getTime()) /
            1000
        )
        : Math.round((Date.now() - new Date(execution.started_at).getTime()) / 1000)

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                    <button
                        onClick={() => navigate('/executions')}
                        className="p-2 hover:bg-gray-100 rounded-lg"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <div className="flex items-center space-x-3">
                            <h1 className="text-3xl font-bold text-gray-900">
                                Execution #{execution.id}
                            </h1>
                            <span
                                className={`px-3 py-1 text-sm rounded-full font-medium flex items-center space-x-2 ${getStatusColor(
                                    execution.status
                                )}`}
                            >
                                <StatusIcon
                                    className={`w-4 h-4 ${execution.status === 'running' ? 'animate-spin' : ''}`}
                                />
                                <span>{execution.status}</span>
                            </span>
                        </div>
                        <p className="mt-2 text-gray-600">
                            Started {formatDate(execution.started_at)} by {execution.executed_by}
                        </p>
                    </div>
                </div>

                {execution.status === 'running' && (
                    <button
                        onClick={() => cancelMutation.mutate()}
                        disabled={cancelMutation.isPending}
                        className="btn-danger flex items-center space-x-2"
                    >
                        <XCircle className="w-5 h-5" />
                        <span>Cancel</span>
                    </button>
                )}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="card">
                    <p className="text-sm text-gray-500 mb-1">Script</p>
                    <Link
                        to={`/scripts/${execution.script_id}`}
                        className="text-lg font-semibold text-primary-600 hover:text-primary-700"
                    >
                        {script?.name || `Script #${execution.script_id}`}
                    </Link>
                </div>

                <div className="card">
                    <p className="text-sm text-gray-500 mb-1">Duration</p>
                    <p className="text-lg font-semibold text-gray-900">{duration}s</p>
                </div>

                <div className="card">
                    <p className="text-sm text-gray-500 mb-1">Started</p>
                    <p className="text-lg font-semibold text-gray-900">
                        {formatDate(execution.started_at)}
                    </p>
                </div>

                <div className="card">
                    <p className="text-sm text-gray-500 mb-1">Completed</p>
                    <p className="text-lg font-semibold text-gray-900">
                        {execution.completed_at ? formatDate(execution.completed_at) : 'In progress...'}
                    </p>
                </div>
            </div>

            {/* Parameters */}
            {execution.parameters && Object.keys(execution.parameters).length > 0 && (
                <div className="card">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Parameters</h2>
                    <div className="bg-gray-50 rounded-lg p-4">
                        <pre className="text-sm text-gray-800 overflow-x-auto">
                            {JSON.stringify(execution.parameters, null, 2)}
                        </pre>
                    </div>
                </div>
            )}

            {/* Logs */}
            <div className="card">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                        <Terminal className="w-5 h-5 text-gray-500" />
                        <h2 className="text-lg font-semibold text-gray-900">Execution Logs</h2>
                        {isConnected && execution.status === 'running' && (
                            <span className="flex items-center space-x-2 text-sm text-green-600">
                                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                                <span>Live</span>
                            </span>
                        )}
                    </div>

                    <div className="flex items-center space-x-2">
                        <label className="flex items-center space-x-2 text-sm text-gray-600">
                            <input
                                type="checkbox"
                                checked={autoScroll}
                                onChange={(e) => setAutoScroll(e.target.checked)}
                                className="rounded border-gray-300"
                            />
                            <span>Auto-scroll</span>
                        </label>
                    </div>
                </div>

                <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm text-gray-100 h-96 overflow-y-auto">
                    {execution.output && (
                        <div className="whitespace-pre-wrap">{execution.output}</div>
                    )}

                    {(messages as WebSocketMessage[]).map((msg, idx) => (
                        <div key={idx} className="whitespace-pre-wrap">
                            {msg.output || msg.log || JSON.stringify(msg)}
                        </div>
                    ))}

                    {execution.status === 'running' && !messages.length && !execution.output && (
                        <div className="text-gray-400">Waiting for output...</div>
                    )}

                    {execution.status === 'pending' && (
                        <div className="text-gray-400">Execution pending...</div>
                    )}

                    <div ref={logsEndRef} />
                </div>
            </div>

            {/* Error */}
            {execution.error && (
                <div className="card border-l-4 border-red-500 bg-red-50">
                    <div className="flex items-start space-x-3">
                        <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
                        <div className="flex-1">
                            <h3 className="text-lg font-semibold text-red-900 mb-2">Error</h3>
                            <pre className="text-sm text-red-800 whitespace-pre-wrap overflow-x-auto">
                                {execution.error}
                            </pre>
                        </div>
                    </div>
                </div>
            )}

            {/* Success Message */}
            {execution.status === 'success' && (
                <div className="card border-l-4 border-green-500 bg-green-50">
                    <div className="flex items-center space-x-3">
                        <CheckCircle className="w-5 h-5 text-green-600" />
                        <div>
                            <h3 className="text-lg font-semibold text-green-900">
                                Execution Completed Successfully
                            </h3>
                            <p className="text-sm text-green-800 mt-1">
                                Completed in {duration} seconds
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}