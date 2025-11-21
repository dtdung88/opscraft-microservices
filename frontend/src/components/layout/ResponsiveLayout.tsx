import { Outlet } from 'react-router-dom'
import { useState, useEffect } from 'react'
import ResponsiveSidebar from './ResponsiveSidebar'
import ResponsiveHeader from './ResponsiveHeader'

export default function ResponsiveLayout() {
    const [sidebarOpen, setSidebarOpen] = useState(false)
    const [isMobile, setIsMobile] = useState(false)

    useEffect(() => {
        const checkMobile = () => {
            setIsMobile(window.innerWidth < 768)
            if (window.innerWidth >= 768) {
                setSidebarOpen(false)
            }
        }

        checkMobile()
        window.addEventListener('resize', checkMobile)
        return () => window.removeEventListener('resize', checkMobile)
    }, [])

    return (
        <div className="min-h-screen bg-gray-50">
            <ResponsiveHeader
                onMenuClick={() => setSidebarOpen(!sidebarOpen)}
                isMobile={isMobile}
            />

            {/* Overlay for mobile */}
            {isMobile && sidebarOpen && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 z-20 md:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            <div className="flex">
                <ResponsiveSidebar
                    isOpen={sidebarOpen}
                    onClose={() => setSidebarOpen(false)}
                    isMobile={isMobile}
                />

                <main className={`
                    flex-1 p-4 sm:p-6 lg:p-8 
                    transition-all duration-300
                    ${isMobile ? 'ml-0' : 'md:ml-64'}
                    mt-16
                `}>
                    <div className="max-w-7xl mx-auto">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    )
}