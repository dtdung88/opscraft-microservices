import { useNavigate } from 'react-router-dom'
import { LogOut, User, Settings } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'

export default function Header() {
    const navigate = useNavigate()
    const { user, logout } = useAuthStore()

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    return (
        <header className="fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-200 z-10">
            <div className="h-full px-6 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                    <h1 className="text-2xl font-bold text-primary-600">OpsCraft</h1>
                    <span className="text-sm text-gray-500">Infrastructure Automation</span>
                </div>

                <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                        <User className="w-5 h-5 text-gray-600" />
                        <div className="text-sm">
                            <div className="font-medium">{user?.full_name || user?.username}</div>
                            <div className="text-gray-500 text-xs capitalize">{user?.role}</div>
                        </div>
                    </div>

                    <button
                        onClick={() => navigate('/profile')}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        title="Profile Settings"
                    >
                        <Settings className="w-5 h-5 text-gray-600" />
                    </button>

                    <button
                        onClick={handleLogout}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        title="Logout"
                    >
                        <LogOut className="w-5 h-5 text-gray-600" />
                    </button>
                </div>
            </div>
        </header>
    )
}