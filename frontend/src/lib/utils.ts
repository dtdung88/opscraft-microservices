import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    })
}

export function formatRelativeTime(date: string | Date): string {
    const now = new Date()
    const then = new Date(date)
    const seconds = Math.floor((now.getTime() - then.getTime()) / 1000)

    if (seconds < 60) return 'just now'
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`
    return formatDate(date)
}

export function getStatusColor(status: string): string {
    const colors: Record<string, string> = {
        pending: 'bg-yellow-100 text-yellow-800',
        running: 'bg-blue-100 text-blue-800',
        success: 'bg-green-100 text-green-800',
        failed: 'bg-red-100 text-red-800',
        cancelled: 'bg-gray-100 text-gray-800',
        active: 'bg-green-100 text-green-800',
        draft: 'bg-gray-100 text-gray-800',
        deprecated: 'bg-orange-100 text-orange-800',
        archived: 'bg-gray-100 text-gray-800',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
}

export function truncate(str: string, length: number): string {
    if (str.length <= length) return str
    return str.substring(0, length) + '...'
}

export function getScriptIcon(type: string): string {
    const icons: Record<string, string> = {
        bash: '🐚',
        python: '🐍',
        ansible: '⚙️',
        terraform: '🏗️',
    }
    return icons[type] || '📄'
}