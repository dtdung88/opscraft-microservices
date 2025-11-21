import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import {
    Plus,
    Lock,
    Eye,
    EyeOff,
    Trash2,
    Copy,
    CheckCircle,
    Shield,
    Key
} from 'lucide-react'
import { secretsApi } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import type { Secret } from '@/types'

export default function ResponsiveSecretsPage() {
    const queryClient = useQueryClient()
    const [showCreateModal, setShowCreateModal] = useState(false)
    const [revealedSecrets, setRevealedSecrets] = useState<Set<number>>(new Set())
    const [copiedId, setCopiedId] = useState<number | null>(null)

    const { data: secrets = [], isLoading } = useQuery({
        queryKey: ['secrets'],
        queryFn: () => secretsApi.list(),
    })

    const deleteMutation = useMutation({
        mutationFn: (id: number) => secretsApi.delete(id),
        onSuccess: () => {
            toast.success('Secret deleted successfully!')
            queryClient.invalidateQueries({ queryKey: ['secrets'] })
        },
    })

    const handleRevealToggle = async (secret: Secret) => {
        const newRevealed = new Set(revealedSecrets)
        if (newRevealed.has(secret.id)) {
            newRevealed.delete(secret.id)
        } else {
            newRevealed.add(secret.id)
        }
        setRevealedSecrets(newRevealed)
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

    return (
        <div className="space-y-4 sm:space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Secrets</h1>
                    <p className="mt-2 text-sm text-gray-600">Manage encrypted secrets and credentials</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="btn-primary flex items-center justify-center space-x-2"
                >
                    <Plus className="w-5 h-5" />
                    <span>New Secret</span>
                </button>
            </div>

            {/* Info Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="card bg-blue-50 border-blue-200">
                    <div className="flex items-center space-x-3">
                        <Shield className="w-10 h-10 text-blue-600" />
                        <div>
                            <p className="text-sm text-blue-600 font-medium">AES-256 Encrypted</p>
                            <p className="text-xs text-blue-500">Military-grade security</p>
                        </div>
                    </div>
                </div>
                <div className="card bg-green-50 border-green-200">
                    <div className="flex items-center space-x-3">
                        <Lock className="w-10 h-10 text-green-600" />
                        <div>
                            <p className="text-sm text-green-600 font-medium">{secrets.length} Secrets</p>
                            <p className="text-xs text-green-500">Securely stored</p>
                        </div>
                    </div>
                </div>
                <div className="card bg-purple-50 border-purple-200">
                    <div className="flex items-center space-x-3">
                        <Key className="w-10 h-10 text-purple-600" />
                        <div>
                            <p className="text-sm text-purple-600 font-medium">Audit Logged</p>
                            <p className="text-xs text-purple-500">Full access tracking</p>
                        </div>
                    </div>
                </div>
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

                        return (
                            <div key={secret.id} className="card hover:shadow-lg transition-shadow">
                                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center space-x-3 mb-2">
                                            <Lock className="w-5 h-5 text-gray-400 flex-shrink-0" />
                                            <h3 className="text-base sm:text-lg font-semibold text-gray-900 truncate">
                                                {secret.name}
                                            </h3>
                                            {secret.category && (
                                                <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded flex-shrink-0">
                                                    {secret.category}
                                                </span>
                                            )}
                                        </div>

                                        {secret.description && (
                                            <p className="text-sm text-gray-600 mb-3">{secret.description}</p>
                                        )}

                                        <div className="bg-gray-50 rounded-lg p-3 mb-3 break-all">
                                            {isRevealed ? (
                                                <code className="text-sm font-mono text-gray-900">
                                                    {secret.value || '••••••••••••••••'}
                                                </code>
                                            ) : (
                                                <span className="text-gray-400 text-sm">••••••••••••••••</span>
                                            )}
                                        </div>

                                        <div className="flex flex-wrap items-center gap-2 text-xs sm:text-sm text-gray-500">
                                            <span>Created by {secret.created_by}</span>
                                            <span className="hidden sm:inline">•</span>
                                            <span className="hidden sm:inline">{formatDate(secret.created_at)}</span>
                                        </div>
                                    </div>

                                    <div className="flex sm:flex-col items-center sm:items-end space-x-2 sm:space-x-0 sm:space-y-2">
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

                                        {isRevealed && secret.value && (
                                            <button
                                                onClick={() => handleCopy(secret.value!, secret.id)}
                                                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                                                title="Copy to clipboard"
                                            >
                                                {copiedId === secret.id ? (
                                                    <CheckCircle className="w-5 h-5 text-green-600" />
                                                ) : (
                                                    <Copy className="w-5 h-5 text-gray-600" />
                                                )}
                                            </button>
                                        )}

                                        <button
                                            onClick={() => {
                                                if (confirm(`Delete secret "${secret.name}"?`)) {
                                                    deleteMutation.mutate(secret.id)
                                                }
                                            }}
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
        </div>
    )
}