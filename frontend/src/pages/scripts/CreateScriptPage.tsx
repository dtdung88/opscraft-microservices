import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { Save, X, Plus } from 'lucide-react'
import Editor from '@monaco-editor/react'
import { scriptsApi } from '@/lib/api'
import type { CreateScriptData, ScriptType } from '@/types'

const scriptSchema = z.object({
    name: z.string().min(1, 'Name is required').max(255),
    description: z.string().optional(),
    script_type: z.enum(['bash', 'python', 'ansible', 'terraform']),
    content: z.string().min(1, 'Script content is required'),
    version: z.string().default('1.0.0'),
})

type ScriptFormData = z.infer<typeof scriptSchema>

const scriptTemplates: Record<ScriptType, string> = {
    bash: `#!/bin/bash
# Script description

echo "Starting script execution..."

# Your code here

echo "Script completed successfully"`,
    python: `#!/usr/bin/env python3
"""
Script description
"""

def main():
    print("Starting script execution...")
    
    # Your code here
    
    print("Script completed successfully")

if __name__ == "__main__":
    main()`,
    ansible: `---
- name: Ansible Playbook
  hosts: all
  become: yes
  
  tasks:
    - name: Example task
      debug:
        msg: "Hello from Ansible"`,
    terraform: `# Terraform configuration

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Your resources here
`,
}

export default function CreateScriptPage() {
    const navigate = useNavigate()
    const [content, setContent] = useState('')
    const [tags, setTags] = useState<string[]>([])
    const [tagInput, setTagInput] = useState('')

    const {
        register,
        handleSubmit,
        watch,
        setValue,
        formState: { errors },
    } = useForm<ScriptFormData>({
        resolver: zodResolver(scriptSchema),
        defaultValues: {
            script_type: 'bash',
            version: '1.0.0',
            content: scriptTemplates.bash,
        },
    })

    const scriptType = watch('script_type')

    const createMutation = useMutation({
        mutationFn: (data: CreateScriptData) => scriptsApi.create(data),
        onSuccess: (data) => {
            toast.success('Script created successfully!')
            navigate(`/scripts/${data.id}`)
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to create script')
        },
    })

    const handleScriptTypeChange = (type: ScriptType) => {
        setValue('script_type', type)
        if (!content || content === scriptTemplates[scriptType]) {
            setContent(scriptTemplates[type])
            setValue('content', scriptTemplates[type])
        }
    }

    const handleAddTag = () => {
        if (tagInput.trim() && !tags.includes(tagInput.trim())) {
            setTags([...tags, tagInput.trim()])
            setTagInput('')
        }
    }

    const handleRemoveTag = (tag: string) => {
        setTags(tags.filter((t) => t !== tag))
    }

    const onSubmit = (data: ScriptFormData) => {
        createMutation.mutate({
            ...data,
            content,
            tags: tags.length > 0 ? tags : undefined,
        })
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Create Script</h1>
                    <p className="mt-2 text-gray-600">Create a new automation script</p>
                </div>
                <button
                    onClick={() => navigate('/scripts')}
                    className="btn-secondary flex items-center space-x-2"
                >
                    <X className="w-5 h-5" />
                    <span>Cancel</span>
                </button>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                {/* Basic Info */}
                <div className="card space-y-4">
                    <h2 className="text-lg font-semibold text-gray-900">Basic Information</h2>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Script Name *
                            </label>
                            <input
                                {...register('name')}
                                type="text"
                                className="input"
                                placeholder="e.g., Deploy Application"
                            />
                            {errors.name && (
                                <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                            )}
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Script Type *
                            </label>
                            <select
                                {...register('script_type')}
                                onChange={(e) => handleScriptTypeChange(e.target.value as ScriptType)}
                                className="input"
                            >
                                <option value="bash">Bash</option>
                                <option value="python">Python</option>
                                <option value="ansible">Ansible</option>
                                <option value="terraform">Terraform</option>
                            </select>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Description
                        </label>
                        <textarea
                            {...register('description')}
                            rows={3}
                            className="input"
                            placeholder="Brief description of what this script does..."
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Version</label>
                        <input
                            {...register('version')}
                            type="text"
                            className="input"
                            placeholder="1.0.0"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
                        <div className="flex space-x-2">
                            <input
                                type="text"
                                value={tagInput}
                                onChange={(e) => setTagInput(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                                className="input flex-1"
                                placeholder="Add tags (press Enter)"
                            />
                            <button
                                type="button"
                                onClick={handleAddTag}
                                className="btn-secondary flex items-center space-x-2"
                            >
                                <Plus className="w-4 h-4" />
                                <span>Add</span>
                            </button>
                        </div>
                        {tags.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-2">
                                {tags.map((tag) => (
                                    <span
                                        key={tag}
                                        className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm flex items-center space-x-2"
                                    >
                                        <span>{tag}</span>
                                        <button
                                            type="button"
                                            onClick={() => handleRemoveTag(tag)}
                                            className="hover:text-primary-900"
                                        >
                                            <X className="w-3 h-3" />
                                        </button>
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Script Editor */}
                <div className="card">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-semibold text-gray-900">Script Content *</h2>
                        <span className="text-sm text-gray-500 capitalize">{scriptType}</span>
                    </div>

                    <div className="border border-gray-300 rounded-lg overflow-hidden">
                        <Editor
                            height="500px"
                            language={scriptType === 'bash' ? 'shell' : scriptType}
                            value={content}
                            onChange={(value) => {
                                setContent(value || '')
                                setValue('content', value || '')
                            }}
                            theme="vs-dark"
                            options={{
                                minimap: { enabled: false },
                                fontSize: 14,
                                lineNumbers: 'on',
                                scrollBeyondLastLine: false,
                                automaticLayout: true,
                                tabSize: 2,
                            }}
                        />
                    </div>
                    {errors.content && (
                        <p className="mt-2 text-sm text-red-600">{errors.content.message}</p>
                    )}
                </div>

                {/* Actions */}
                <div className="flex justify-end space-x-4">
                    <button
                        type="button"
                        onClick={() => navigate('/scripts')}
                        className="btn-secondary"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={createMutation.isPending}
                        className="btn-primary flex items-center space-x-2"
                    >
                        <Save className="w-5 h-5" />
                        <span>{createMutation.isPending ? 'Creating...' : 'Create Script'}</span>
                    </button>
                </div>
            </form>
        </div>
    )
}