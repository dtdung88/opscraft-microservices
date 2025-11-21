import { NavLink } from 'react-router-dom'
import {
    LayoutDashboard,
    FileCode,
    Play,
    Lock,
    Shield,
    Activity,
    Clock,
    CheckSquare,
    FileText,
    X
} from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { cn } from '@/lib/utils'

interface ResponsiveSidebarProps {
    isOpen: boolean
    onClose: () => void
    isMobile: boolean
}

const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Scripts', href: '/scripts', icon: FileCode },
    { name: 'Executions', href: '/executions', icon: Play },
    { name: 'Schedules', href: '/schedules', icon: Clock },
    { name: 'Secrets', href: '/secrets', icon: Lock },
    { name: 'Approvals', href: '/approvals', icon: CheckSquare },
    { name: 'Audit Logs', href: '/audit', icon: FileText },
]

const adminNavigation = [
    { name: 'Admin', href: '/admin', icon: Shield },
]

export default function ResponsiveSidebar({ isOpen, onClose, isMobile }: ResponsiveSidebarProps) {
    const { user } = useAuthStore()
    const isAdmin = user?.role === 'admin'

    return (
        <aside className={cn(
            "fixed left-0 top-16 h-[calc(100vh-4rem)] bg-white border-r border-gray-200 overflow-y-auto transition-transform duration-300 z-20",
            "w-64",
            isMobile ? (
                isOpen ? "translate-x-0" : "-translate-x-full"
            ) : "translate-x-0"
        )}>
            {/* Close button for mobile */}
            {isMobile && (
                <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex justify-between items-center md:hidden">
                    <span className="font-semibold">Menu</span>
                    <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
                        <X className="w-5 h-5" />
                    </button>
                </div>
            )}

            <nav className="p-4 space-y-1">
                {navigation.map((item) => (
                    <NavLink
                        key={item.name}
                        to={item.href}
                        end={item.href === '/'}
                        onClick={() => isMobile && onClose()}
                        className={({ isActive }) =>
                            cn(
                                'flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors',
                                isActive
                                    ? 'bg-primary-50 text-primary-700 font-medium'
                                    : 'text-gray-700 hover:bg-gray-100'
                            )
                        }
                    >
                        <item.icon className="w-5 h-5 flex-shrink-0" />
                        <span className="truncate">{item.name}</span>
                    </NavLink>
                ))}

                {isAdmin && (
                    <>
                        <div className="pt-4 pb-2">
                            <div className="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                Administration
                            </div>
                        </div>
                        {adminNavigation.map((item) => (
                            <NavLink
                                key={item.name}
                                to={item.href}
                                onClick={() => isMobile && onClose()}
                                className={({ isActive }) =>
                                    cn(
                                        'flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors',
                                        isActive
                                            ? 'bg-primary-50 text-primary-700 font-medium'
                                            : 'text-gray-700 hover:bg-gray-100'
                                    )
                                }
                            >
                                <item.icon className="w-5 h-5 flex-shrink-0" />
                                <span className="truncate">{item.name}</span>
                            </NavLink>
                        ))}
                    </>
                )}

                <div className="pt-4">
                    <div className="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                        Monitoring
                    </div>
                    <a
                        href="http://localhost:9090"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors mt-1"
                    >
                        <Activity className="w-5 h-5 flex-shrink-0" />
                        <span className="truncate">Prometheus</span>
                    </a>
                    <a
                        href="http://localhost:3001"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                        <Activity className="w-5 h-5 flex-shrink-0" />
                        <span className="truncate">Grafana</span>
                    </a>
                </div>
            </nav>
        </aside>
    )
}