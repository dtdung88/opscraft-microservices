import { useState, useEffect } from 'react'

interface ResponsiveState {
    isMobile: boolean
    isTablet: boolean
    isDesktop: boolean
    isLargeDesktop: boolean
    width: number
    height: number
}

export function useResponsive(): ResponsiveState {
    const [state, setState] = useState<ResponsiveState>({
        isMobile: false,
        isTablet: false,
        isDesktop: false,
        isLargeDesktop: false,
        width: 0,
        height: 0,
    })

    useEffect(() => {
        const updateSize = () => {
            const width = window.innerWidth
            const height = window.innerHeight

            setState({
                isMobile: width < 768,
                isTablet: width >= 768 && width < 1024,
                isDesktop: width >= 1024 && width < 1280,
                isLargeDesktop: width >= 1280,
                width,
                height,
            })
        }

        updateSize()
        window.addEventListener('resize', updateSize)

        return () => window.removeEventListener('resize', updateSize)
    }, [])

    return state
}