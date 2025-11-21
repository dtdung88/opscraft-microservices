import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import {
    Edit,
    Trash2,
    Play,
    ArrowLeft,
    Save,
    X,
    Calendar,
    User,
    Tag,
    FileCode,
} from 'lucide-react'
import Editor from '@monaco-editor/react'
import { scriptsApi, executionsApi } from '@/lib/api'
import { formatDate, getStatusColor, getScriptIcon } from '@/lib/utils'
import type { UpdateScriptData } from '@/types'

export default function ScriptDetailPage() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()
    const queryClient = useQueryClient()
    const [isEditing, setIsEditing] = useState(false)
    const [editContent, setEditContent] = useState('')
    const [editName, setEditName] = useState('')
    const [editDescription, setEditDescription] = useState('')

    const { data: script, isLoading } = useQuery({
        queryKey: ['script', id],
        queryFn: () => scriptsApi.get(Number(id)),
        enabled: !!id,
    })

    const updateMutation = useMutation({
        mutationFn: (data: UpdateScriptData) => scriptsApi.update(Number(id), data),
        onSuccess: () => {
            toast.success('Script updated successfully!')
            queryClient.invalidateQueries({ queryKey: ['script', id] })
            queryClient.invalidateQueries({ queryKey: ['scripts'] })
            setIsEditing(false)
        },
        onError: (error: unknown) => {
            const err = error as { response?: { data?: { detail?: string } } }
            toast.error(err.response?.data?.detail || 'Failed to update script')
        },
    })

    const deleteMutation = useMutation({
        mutationFn: () => scriptsApi.delete(Number(id)),
        onSuccess: () => {
            toast.success('Script deleted successfully!')
            navigate('/scripts')
        },
        onError: (error: unknown) => {
            const err = error as { response?: { data?: { detail?: string } } }
            toast.error(err.response?.data?.detail || 'Failed to delete script')
        },
    })

    const executeMutation = useMutation({
        mutationFn: () => executionsApi.create({ script_id: Number(id) }),
        onSuccess: (data) => {
            toast.success('Execution started!')
            navigate(`/executions/${data.id}`)
        },
        onError: (error: unknown) => {
            const err = error as { response?: { data?: { detail?: string } } }
            toast.error(err.response?.data?.detail || 'Failed to start execution')
        },
    })

    const handleEdit = () => {
        if (script) {
            setEditName(script.name)
            setEditDescription(script.description || '')
            setEditContent(script.content)
            setIsEditing(true)
        }
    }

    const handleSave = () => {
        updateMutation.mutate({
            name: editName,
            description: editDescription,
            content: editContent,
        })
    }

    const handleDelete = () => {
        if (window.confirm('Are you sure you want to delete this script?')) {
            deleteMutation.mutate()
        }
    }

    const handleExecute = () => {
        if (window.confirm('Execute this script now?')) {
            executeMutation.mutate()
        }
    }

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
        )
    }

    if (!script) {
        return (
            <div className="card text-center py-12">
                <p className="text-gray-600">Script not found</p>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                    <button
                        onClick={() => navigate('/scripts')}
                        className="p-2 hover:bg-gray-100 rounded-lg"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <div className="flex items-center space-x-3">
                            <span className="text-3xl">{getScriptIcon(script.script_type)}</span>
                            {isEditing ? (
                                <input
                                    type="text"
                                    value={editName}
                                    onChange={(e) => setEditName(e.target.value)}
                                    className="text-3xl font-bold text-gray-900 border-b-2 border-primary-500 focus:outline-none"
                                />
                            ) : (
                                <h1 className="text-3xl font-bold text-gray-900">{script.name}</h1>
                            )}
                            <span
                                className={`px-3 py-1 text-sm rounded-full font-medium ${getStatusColor(
                                    script.status
                                )}`}
                            >
                                {script.status}
                            </span>
                        </div>
                        {isEditing ? (
                            <textarea
                                value={editDescription}
                                onChange={(e) => setEditDescription(e.target.value)}
                                rows={2}
                                className="mt-2 w-full input"
                                placeholder="Description..."
                            />
                        ) : (
                            script.description && (
                                <p className="mt-2 text-gray-600">{script.description}</p>
                            )
                        )}
                    </div>
                </div>

                <div className="flex items-center space-x-2">
                    {isEditing ? (
                        <>
                            <button
                                onClick={() => setIsEditing(false)}
                                className="btn-secondary flex items-center space-x-2"
                            >
                                <X className="w-5 h-5" />
                                <span>Cancel</span>
                            </button>
                            <button
                                onClick={handleSave}
                                disabled={updateMutation.isPending}
                                className="btn-primary flex items-center space-x-2"
                            >
                                <Save className="w-5 h-5" />
                                <span>{updateMutation.isPending ? 'Saving...' : 'Save'}</span>
                            </button>
                        </>
                    ) : (
                        <>
                            <button
                                onClick={handleExecute}
                                disabled={executeMutation.isPending || script.status !== 'active'}
                                className="btn-primary flex items-center space-x-2"
                            >
                                <Play className="w-5 h-5" />
                                <span>{executeMutation.isPending ? 'Starting...' : 'Execute'}</span>
                            </button>
                            <button
                                onClick={handleEdit}
                                className="btn-secondary flex items-center space-x-2"
                            >
                                <Edit className="w-5 h-5" />
                                <span>Edit</span>
                            </button>
                            <button
                                onClick={handleDelete}
                                disabled={deleteMutation.isPending}
                                className="btn-danger flex items-center space-x-2"
                            >
                                <Trash2 className="w-5 h-5" />
                                <span>Delete</span>
                            </button>
                        </>
                    )}
                </div>
            </div>

            {/* Metadata */}
            <div className="card">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="flex items-center space-x-3">
                        <FileCode className="w-5 h-5 text-gray-400" />
                        <div>
                            <p className="text-sm text-gray-500">Type</p>
                            <p className="font-medium capitalize">{script.script_type}</p>
                        </div>
                    </div>

                    <div className="flex items-center space-x-3">
                        <Tag className="w-5 h-5 text-gray-400" />
                        <div>
                            <p className="text-sm text-gray-500">Version</p>
                            <p className="font-medium">v{script.version}</p>
                        </div>
                    </div>

                    <div className="flex items-center space-x-3">
                        <User className="w-5 h-5 text-gray-400" />
                        <div>
                            <p className="text-sm text-gray-500">Created By</p>
                            <p className="font-medium">{script.created_by}</p>
                        </div>
                    </div>

                    <div className="flex items-center space-x-3">
                        <Calendar className="w-5 h-5 text-gray-400" />
                        <div>
                            <p className="text-sm text-gray-500">Last Updated</p>
                            <p className="font-medium">{formatDate(script.updated_at)}</p>
                        </div>
                    </div>
                </div>

                {script.tags && script.tags.length > 0 && (
                    <div className="mt-6">
                        <p className="text-sm text-gray-500 mb-2">Tags</p>
                        <div className="flex flex-wrap gap-2">
                            {script.tags.map((tag) => (
                                <span
                                    key={tag}
                                    className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                                >
                                    {tag}
                                </span>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Script Content */}
            <div className="card">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Script Content</h2>
                <div className="border border-gray-300 rounded-lg overflow-hidden">
                    <Editor
                        height="600px"
                        language={script.script_type === 'bash' ? 'shell' : script.script_type}
                        value={isEditing ? editContent : script.content}
                        onChange={(value) => isEditing && setEditContent(value || '')}
                        theme="vs-dark"
                        options={{
                            readOnly: !isEditing,
                            minimap: { enabled: true },
                            fontSize: 14,
                            lineNumbers: 'on',
                            scrollBeyondLastLine: false,
                            automaticLayout: true,
                        }}
                    />
                </div>
            </div>
        </div>
    )
}