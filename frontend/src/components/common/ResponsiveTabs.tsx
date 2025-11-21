import { useState } from 'react'
import { cn } from '@/lib/utils'

interface Tab {
    id: string
    label: string
    icon?: React.ReactNode
    content: React.ReactNode
}

interface ResponsiveTabsProps {
    tabs: Tab[]
    defaultTab?: string
}

export default function ResponsiveTabs({ tabs, defaultTab }: ResponsiveTabsProps) {
    const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id)

    return (
        <div className="w-full">
            {/* Mobile: Dropdown */}
            <div className="sm:hidden mb-4">
                <select
                    value={activeTab}
                    onChange={(e) => setActiveTab(e.target.value)}
                    className="input w-full"
                >
                    {tabs.map((tab) => (
                        <option key={tab.id} value={tab.id}>
                            {tab.label}
                        </option>
                    ))}
                </select>
            </div>

            {/* Desktop: Tabs */}
            <div className="hidden sm:block border-b border-gray-200 mb-6">
                <nav className="flex space-x-8 overflow-x-auto">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={cn(
                                'flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap',
                                activeTab === tab.id
                                    ? 'border-primary-500 text-primary-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            )}
                        >
                            {tab.icon}
                            <span>{tab.label}</span>
                        </button>
                    ))}
                </nav>
            </div>

            {/* Content */}
            <div>
                {tabs.map(
                    (tab) =>
                        tab.id === activeTab && (
                            <div key={tab.id} className="animate-fadeIn">
                                {tab.content}
                            </div>
                        )
                )}
            </div>
        </div>
    )
}