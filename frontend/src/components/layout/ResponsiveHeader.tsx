import { useNavigate } from 'react-router-dom'
import { Menu, LogOut, User, Settings, Bell, Search } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { useState } from 'react'

interface ResponsiveHeaderProps {
    onMenuClick: () => void
    isMobile: boolean
}

export default function ResponsiveHeader({ onMenuClick, isMobile }: ResponsiveHeaderProps) {
    const navigate = useNavigate()
    const { user, logout } = useAuthStore()
    const [showUserMenu, setShowUserMenu] = useState(false)
    const [showNotifications, setShowNotifications] = useState(false)

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    return (
        <header className="fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-200 z-30">
            <div className="h-full px-4 sm:px-6 flex items-center justify-between">
                <div className="flex items-center space-x-2 sm:space-x-4">
                    {isMobile && (
                        <button
                            onClick={onMenuClick}
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors lg:hidden"
                        >
                            <Menu className="w-6 h-6 text-gray-600" />
                        </button>
                    )}

                    <div className="flex items-center space-x-2 sm:space-x-3">
                        <h1 className="text-xl sm:text-2xl font-bold text-primary-600">
                            OpsCraft
                        </h1>
                        <span className="hidden sm:inline text-sm text-gray-500">
                            Infrastructure Automation
                        </span>
                    </div>
                </div>

                {/* Search Bar - Hidden on mobile */}
                <div className="hidden md:flex flex-1 max-w-md mx-4">
                    <div className="relative w-full">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search scripts, executions..."
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                    </div>
                </div>

                <div className="flex items-center space-x-2 sm:space-x-4">
                    {/* Notifications */}
                    <div className="relative">
                        <button
                            onClick={() => setShowNotifications(!showNotifications)}
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors relative"
                        >
                            <Bell className="w-5 h-5 text-gray-600" />
                            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                        </button>

                        {showNotifications && (
                            <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
                                <div className="p-4 border-b">
                                    <h3 className="font-semibold">Notifications</h3>
                                </div>
                                <div className="max-h-96 overflow-y-auto">
                                    <div className="p-4 hover:bg-gray-50 cursor-pointer border-b">
                                        <p className="text-sm font-medium">Script execution completed</p>
                                        <p className="text-xs text-gray-500 mt-1">2 minutes ago</p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* User Menu */}
                    <div className="relative">
                        <button
                            onClick={() => setShowUserMenu(!showUserMenu)}
                            className="flex items-center space-x-2 p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                                <span className="text-primary-700 font-semibold text-sm">
                                    {user?.username.charAt(0).toUpperCase()}
                                </span>
                            </div>
                            <div className="hidden sm:block text-left">
                                <div className="text-sm font-medium">{user?.full_name || user?.username}</div>
                                <div className="text-xs text-gray-500 capitalize">{user?.role}</div>
                            </div>
                        </button>

                        {showUserMenu && (
                            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
                                <button
                                    onClick={() => {
                                        navigate('/profile')
                                        setShowUserMenu(false)
                                    }}
                                    className="w-full flex items-center space-x-2 px-4 py-3 hover:bg-gray-50 transition-colors"
                                >
                                    <User className="w-5 h-5 text-gray-600" />
                                    <span>Profile</span>
                                </button>
                                <button
                                    onClick={() => {
                                        navigate('/settings')
                                        setShowUserMenu(false)
                                    }}
                                    className="w-full flex items-center space-x-2 px-4 py-3 hover:bg-gray-50 transition-colors"
                                >
                                    <Settings className="w-5 h-5 text-gray-600" />
                                    <span>Settings</span>
                                </button>
                                <hr />
                                <button
                                    onClick={handleLogout}
                                    className="w-full flex items-center space-x-2 px-4 py-3 hover:bg-gray-50 text-red-600 transition-colors"
                                >
                                    <LogOut className="w-5 h-5" />
                                    <span>Logout</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </header>
    )
}