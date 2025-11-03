import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, Search, Filter } from 'lucide-react'
import { scriptsApi } from '@/lib/api'
import { getStatusColor, getScriptIcon, formatDate } from '@/lib/utils'
import type { ScriptType, ScriptStatus } from '@/types'

export default function ScriptsPage() {
    const [search, setSearch] = useState('')
    const [filterType, setFilterType] = useState<ScriptType | ''>('')
    const [filterStatus, setFilterStatus] = useState<ScriptStatus | ''>('')

    const { data: scripts = [], isLoading } = useQuery({
        queryKey: ['scripts', search, filterType, filterStatus],
        queryFn: () =>
            scriptsApi.list({
                search: search || undefined,
                script_type: filterType || undefined,
                status: filterStatus || undefined,
            }),
    })

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Scripts</h1>
                    <p className="mt-2 text-gray-600">Manage your automation scripts</p>
                </div>
                <Link to="/scripts/new" className="btn-primary flex items-center space-x-2">
                    <Plus className="w-5 h-5" />
                    <span>New Script</span>
                </Link>
            </div>

            {/* Filters */}
            <div className="card">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search scripts..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="input pl-10"
                        />
                    </div>

                    <select
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value as ScriptType | '')}
                        className="input"
                    >
                        <option value="">All Types</option>
                        <option value="bash">Bash</option>
                        <option value="python">Python</option>
                        <option value="ansible">Ansible</option>
                        <option value="terraform">Terraform</option>
                    </select>

                    <select
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value as ScriptStatus | '')}
                        className="input"
                    >
                        <option value="">All Status</option>
                        <option value="draft">Draft</option>
                        <option value="active">Active</option>
                        <option value="deprecated">Deprecated</option>
                        <option value="archived">Archived</option>
                    </select>
                </div>
            </div>

            {/* Scripts List */}
            {isLoading ? (
                <div className="card text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading scripts...</p>
                </div>
            ) : scripts.length === 0 ? (
                <div className="card text-center py-12">
                    <p className="text-gray-600 mb-4">No scripts found</p>
                    <Link to="/scripts/new" className="btn-primary inline-flex items-center space-x-2">
                        <Plus className="w-5 h-5" />
                        <span>Create your first script</span>
                    </Link>
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {scripts.map((script) => (
                        <Link
                            key={script.id}
                            to={`/scripts/${script.id}`}
                            className="card hover:shadow-lg transition-shadow"
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center space-x-2 mb-2">
                                        <span className="text-2xl">{getScriptIcon(script.script_type)}</span>
                                        <h3 className="text-lg font-semibold text-gray-900">{script.name}</h3>
                                    </div>
                                    {script.description && (
                                        <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                                            {script.description}
                                        </p>
                                    )}
                                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                                        <span className="capitalize">{script.script_type}</span>
                                        <span>•</span>
                                        <span>v{script.version}</span>
                                        <span>•</span>
                                        <span>{formatDate(script.updated_at)}</span>
                                    </div>
                                </div>
                                <span
                                    className={`px-3 py-1 text-xs rounded-full font-medium ${getStatusColor(
                                        script.status
                                    )}`}
                                >
                                    {script.status}
                                </span>
                            </div>
                            {script.tags && script.tags.length > 0 && (
                                <div className="mt-3 flex flex-wrap gap-2">
                                    {script.tags.map((tag) => (
                                        <span
                                            key={tag}
                                            className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
                                        >
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </Link>
                    ))}
                </div>
            )}
        </div>
    )
}