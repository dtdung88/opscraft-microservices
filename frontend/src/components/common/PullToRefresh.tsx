import { useState, useRef, useEffect } from 'react'
import { RefreshCw } from 'lucide-react'

interface PullToRefreshProps {
    onRefresh: () => Promise<void>
    children: React.ReactNode
}

export default function PullToRefresh({ onRefresh, children }: PullToRefreshProps) {
    const [startY, setStartY] = useState(0)
    const [pullDistance, setPullDistance] = useState(0)
    const [isRefreshing, setIsRefreshing] = useState(false)
    const containerRef = useRef<HTMLDivElement>(null)

    const threshold = 80

    const handleTouchStart = (e: TouchEvent) => {
        if (window.scrollY === 0) {
            setStartY(e.touches[0].clientY)
        }
    }

    const handleTouchMove = (e: TouchEvent) => {
        if (startY === 0 || window.scrollY > 0) return

        const currentY = e.touches[0].clientY
        const distance = currentY - startY

        if (distance > 0 && distance < 150) {
            setPullDistance(distance)
        }
    }

    const handleTouchEnd = async () => {
        if (pullDistance > threshold && !isRefreshing) {
            setIsRefreshing(true)
            try {
                await onRefresh()
            } finally {
                setIsRefreshing(false)
            }
        }
        setPullDistance(0)
        setStartY(0)
    }

    useEffect(() => {
        const container = containerRef.current
        if (!container) return

        container.addEventListener('touchstart', handleTouchStart, { passive: true })
        container.addEventListener('touchmove', handleTouchMove, { passive: true })
        container.addEventListener('touchend', handleTouchEnd)

        return () => {
            container.removeEventListener('touchstart', handleTouchStart)
            container.removeEventListener('touchmove', handleTouchMove)
            container.removeEventListener('touchend', handleTouchEnd)
        }
    }, [startY, pullDistance, isRefreshing])

    return (
        <div ref={containerRef} className="relative">
            {/* Pull indicator */}
            {(pullDistance > 0 || isRefreshing) && (
                <div
                    className="absolute top-0 left-0 right-0 flex items-center justify-center transition-all"
                    style={{
                        height: isRefreshing ? '60px' : `${Math.min(pullDistance, 60)}px`,
                    }}
                >
                    <RefreshCw
                        className={cn(
                            'text-primary-600',
                            isRefreshing && 'animate-spin'
                        )}
                        size={24}
                    />
                </div>
            )}

            {/* Content */}
            <div
                style={{
                    transform: isRefreshing
                        ? 'translateY(60px)'
                        : `translateY(${Math.min(pullDistance, 60)}px)`,
                    transition: isRefreshing || pullDistance === 0 ? 'transform 0.3s' : 'none',
                }}
            >
                {children}
            </div>
        </div>
    )
}