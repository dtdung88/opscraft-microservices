import { NavLink } from 'react-router-dom'
import {
    LayoutDashboard,
    FileCode,
    Play,
    Lock,
    Shield,
    Activity,
} from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { cn } from '@/lib/utils'

const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Scripts', href: '/scripts', icon: FileCode },
    { name: 'Executions', href: '/executions', icon: Play },
    { name: 'Secrets', href: '/secrets', icon: Lock },
]

const adminNavigation = [
    { name: 'Admin', href: '/admin', icon: Shield },
]

export default function Sidebar() {
    const { user } = useAuthStore()
    const isAdmin = user?.role === 'admin'

    return (
        <aside className="fixed left-0 top-16 h-[calc(100vh-4rem)] w-64 bg-white border-r border-gray-200 overflow-y-auto">
            <nav className="p-4 space-y-1">
                {navigation.map((item) => (
                    <NavLink
                        key={item.name}
                        to={item.href}
                        end={item.href === '/'}
                        className={({ isActive }) =>
                            cn(
                                'flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors',
                                isActive
                                    ? 'bg-primary-50 text-primary-700 font-medium'
                                    : 'text-gray-700 hover:bg-gray-100'
                            )
                        }
                    >
                        <item.icon className="w-5 h-5" />
                        <span>{item.name}</span>
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
                                className={({ isActive }) =>
                                    cn(
                                        'flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors',
                                        isActive
                                            ? 'bg-primary-50 text-primary-700 font-medium'
                                            : 'text-gray-700 hover:bg-gray-100'
                                    )
                                }
                            >
                                <item.icon className="w-5 h-5" />
                                <span>{item.name}</span>
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
                        <Activity className="w-5 h-5" />
                        <span>Prometheus</span>
                    </a>
                    <a
                        href="http://localhost:3001"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                        <Activity className="w-5 h-5" />
                        <span>Grafana</span>
                    </a>
                </div>
            </nav>
        </aside>
    )
}