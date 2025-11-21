import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import {
    Plus,
    Lock,
    Eye,
    EyeOff,
    Trash2,
    History,
    Copy,
    CheckCircle,
} from 'lucide-react'
import { secretsApi } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import type { CreateSecretData, Secret, AuditLog } from '@/types'

export default function SecretsPage() {
    const queryClient = useQueryClient()
    const [showCreateModal, setShowCreateModal] = useState(false)
    const [selectedSecret, setSelectedSecret] = useState<Secret | null>(null)
    const [showAuditModal, setShowAuditModal] = useState(false)
    const [revealedSecrets, setRevealedSecrets] = useState<Set<number>>(new Set())
    const [copiedId, setCopiedId] = useState<number | null>(null)

    const { data: secrets = [], isLoading } = useQuery({
        queryKey: ['secrets'],
        queryFn: () => secretsApi.list(),
    })

    const createMutation = useMutation({
        mutationFn: (data: CreateSecretData) => secretsApi.create(data),
        onSuccess: () => {
            toast.success('Secret created successfully!')
            queryClient.invalidateQueries({ queryKey: ['secrets'] })
            setShowCreateModal(false)
        },
        onError: (error: unknown) => {
            const err = error as { response?: { data?: { detail?: string } } }
            toast.error(err.response?.data?.detail || 'Failed to create secret')
        },
    })

    const deleteMutation = useMutation({
        mutationFn: (id: number) => secretsApi.delete(id),
        onSuccess: () => {
            toast.success('Secret deleted successfully!')
            queryClient.invalidateQueries({ queryKey: ['secrets'] })
        },
        onError: (error: unknown) => {
            const err = error as { response?: { data?: { detail?: string } } }
            toast.error(err.response?.data?.detail || 'Failed to delete secret')
        },
    })

    const { data: revealedData } = useQuery({
        queryKey: ['secret-reveal', selectedSecret?.id],
        queryFn: () => secretsApi.get(selectedSecret!.id, true),
        enabled: !!selectedSecret && revealedSecrets.has(selectedSecret.id),
    })

    const { data: auditLogs } = useQuery({
        queryKey: ['secret-audit', selectedSecret?.id],
        queryFn: () => secretsApi.getAuditLogs(selectedSecret!.id),
        enabled: !!selectedSecret && showAuditModal,
    })

    const handleRevealToggle = (secret: Secret) => {
        const newRevealed = new Set(revealedSecrets)
        if (newRevealed.has(secret.id)) {
            newRevealed.delete(secret.id)
        } else {
            newRevealed.add(secret.id)
        }
        setRevealedSecrets(newRevealed)
        setSelectedSecret(secret)
    }

    const handleCopy = async (text: string, id: number) => {
        try {
            await navigator.clipboard.writeText(text)
            setCopiedId(id)
            toast.success('Copied to clipboard!')
            setTimeout(() => setCopiedId(null), 2000)
        } catch {
            toast.error('Failed to copy')
        }
    }

    const handleDelete = (id: number, name: string) => {
        if (window.confirm(`Are you sure you want to delete secret "${name}"?`)) {
            deleteMutation.mutate(id)
        }
    }

    const handleShowAudit = (secret: Secret) => {
        setSelectedSecret(secret)
        setShowAuditModal(true)
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Secrets</h1>
                    <p className="mt-2 text-gray-600">Manage encrypted secrets and credentials</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="btn-primary flex items-center space-x-2"
                >
                    <Plus className="w-5 h-5" />
                    <span>New Secret</span>
                </button>
            </div>

            {/* Secrets List */}
            {isLoading ? (
                <div className="card text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading secrets...</p>
                </div>
            ) : secrets.length === 0 ? (
                <div className="card text-center py-12">
                    <Lock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600 mb-4">No secrets yet</p>
                    <button
                        onClick={() => setShowCreateModal(true)}
                        className="btn-primary inline-flex items-center space-x-2"
                    >
                        <Plus className="w-5 h-5" />
                        <span>Create your first secret</span>
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-4">
                    {secrets.map((secret) => {
                        const isRevealed = revealedSecrets.has(secret.id)
                        const secretValue = isRevealed && revealedData?.id === secret.id
                            ? revealedData.value
                            : null

                        return (
                            <div key={secret.id} className="card hover:shadow-lg transition-shadow">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center space-x-3 mb-2">
                                            <Lock className="w-5 h-5 text-gray-400" />
                                            <h3 className="text-lg font-semibold text-gray-900">{secret.name}</h3>
                                            {secret.category && (
                                                <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                                                    {secret.category}
                                                </span>
                                            )}
                                        </div>

                                        {secret.description && (
                                            <p className="text-gray-600 text-sm mb-3">{secret.description}</p>
                                        )}

                                        {isRevealed && secretValue ? (
                                            <div className="bg-gray-50 rounded-lg p-3 mb-3">
                                                <div className="flex items-center justify-between">
                                                    <code className="text-sm font-mono text-gray-900 break-all">
                                                        {secretValue}
                                                    </code>
                                                    <button
                                                        onClick={() => handleCopy(secretValue, secret.id)}
                                                        className="ml-3 p-2 hover:bg-gray-200 rounded transition-colors"
                                                        title="Copy to clipboard"
                                                    >
                                                        {copiedId === secret.id ? (
                                                            <CheckCircle className="w-4 h-4 text-green-600" />
                                                        ) : (
                                                            <Copy className="w-4 h-4 text-gray-600" />
                                                        )}
                                                    </button>
                                                </div>
                                            </div>
                                        ) : (
                                            <div className="bg-gray-100 rounded-lg p-3 mb-3">
                                                <span className="text-gray-400 text-sm">••••••••••••••••</span>
                                            </div>
                                        )}

                                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                                            <span>Created by {secret.created_by}</span>
                                            <span>•</span>
                                            <span>{formatDate(secret.created_at)}</span>
                                            {secret.last_accessed_at && (
                                                <>
                                                    <span>•</span>
                                                    <span>Last accessed {formatDate(secret.last_accessed_at)}</span>
                                                </>
                                            )}
                                        </div>
                                    </div>

                                    <div className="flex items-center space-x-2 ml-4">
                                        <button
                                            onClick={() => handleRevealToggle(secret)}
                                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                                            title={isRevealed ? 'Hide value' : 'Reveal value'}
                                        >
                                            {isRevealed ? (
                                                <EyeOff className="w-5 h-5 text-gray-600" />
                                            ) : (
                                                <Eye className="w-5 h-5 text-gray-600" />
                                            )}
                                        </button>

                                        <button
                                            onClick={() => handleShowAudit(secret)}
                                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                                            title="View audit logs"
                                        >
                                            <History className="w-5 h-5 text-gray-600" />
                                        </button>

                                        <button
                                            onClick={() => handleDelete(secret.id, secret.name)}
                                            className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                                            title="Delete secret"
                                        >
                                            <Trash2 className="w-5 h-5 text-red-600" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )
                    })}
                </div>
            )}

            {/* Create Secret Modal */}
            {showCreateModal && (
                <CreateSecretModal
                    onClose={() => setShowCreateModal(false)}
                    onSubmit={(data) => createMutation.mutate(data)}
                    isLoading={createMutation.isPending}
                />
            )}

            {/* Audit Log Modal */}
            {showAuditModal && selectedSecret && (
                <AuditLogModal
                    secret={selectedSecret}
                    logs={auditLogs || []}
                    onClose={() => {
                        setShowAuditModal(false)
                        setSelectedSecret(null)
                    }}
                />
            )}
        </div>
    )
}

function CreateSecretModal({
    onClose,
    onSubmit,
    isLoading,
}: {
    onClose: () => void
    onSubmit: (data: CreateSecretData) => void
    isLoading: boolean
}) {
    const [formData, setFormData] = useState<CreateSecretData>({
        name: '',
        value: '',
        description: '',
        category: 'api_key',
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        onSubmit(formData)
    }

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
                <div className="p-6 border-b border-gray-200">
                    <h2 className="text-2xl font-bold text-gray-900">Create New Secret</h2>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Secret Name *
                        </label>
                        <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            className="input"
                            placeholder="e.g., AWS_ACCESS_KEY"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Secret Value *
                        </label>
                        <textarea
                            value={formData.value}
                            onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                            rows={3}
                            className="input font-mono"
                            placeholder="Enter secret value..."
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
                        <select
                            value={formData.category}
                            onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                            className="input"
                        >
                            <option value="api_key">API Key</option>
                            <option value="password">Password</option>
                            <option value="token">Token</option>
                            <option value="certificate">Certificate</option>
                            <option value="other">Other</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Description
                        </label>
                        <textarea
                            value={formData.description}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            rows={2}
                            className="input"
                            placeholder="Optional description..."
                        />
                    </div>

                    <div className="flex justify-end space-x-3 pt-4">
                        <button type="button" onClick={onClose} className="btn-secondary">
                            Cancel
                        </button>
                        <button type="submit" disabled={isLoading} className="btn-primary">
                            {isLoading ? 'Creating...' : 'Create Secret'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}

function AuditLogModal({
    secret,
    logs,
    onClose,
}: {
    secret: Secret
    logs: AuditLog[]
    onClose: () => void
}) {
    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[80vh] overflow-hidden flex flex-col">
                <div className="p-6 border-b border-gray-200">
                    <h2 className="text-2xl font-bold text-gray-900">Audit Logs - {secret.name}</h2>
                </div>

                <div className="flex-1 overflow-y-auto p-6">
                    {logs.length === 0 ? (
                        <p className="text-gray-500 text-center py-8">No audit logs yet</p>
                    ) : (
                        <div className="space-y-4">
                            {logs.map((log) => (
                                <div key={log.id} className="border border-gray-200 rounded-lg p-4">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded uppercase">
                                            {log.action}
                                        </span>
                                        <span className="text-sm text-gray-500">{formatDate(log.timestamp)}</span>
                                    </div>
                                    <div className="text-sm">
                                        <p className="text-gray-700">
                                            <span className="font-medium">User:</span> {log.user}
                                        </p>
                                        {log.ip_address && (
                                            <p className="text-gray-700">
                                                <span className="font-medium">IP:</span> {log.ip_address}
                                            </p>
                                        )}
                                        {log.details && (
                                            <p className="text-gray-700">
                                                <span className="font-medium">Details:</span> {log.details}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="p-6 border-t border-gray-200">
                    <button onClick={onClose} className="btn-secondary w-full">
                        Close
                    </button>
                </div>
            </div>
        </div>
    )
}