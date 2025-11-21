export const touchUtils = {
    // Check if device supports touch
    isTouchDevice(): boolean {
        return (
            'ontouchstart' in window ||
            navigator.maxTouchPoints > 0 ||
            // @ts-ignore
            navigator.msMaxTouchPoints > 0
        )
    },

    // Get touch coordinates
    getTouchCoordinates(event: TouchEvent | React.TouchEvent) {
        if ('touches' in event && event.touches.length > 0) {
            return {
                x: event.touches[0].clientX,
                y: event.touches[0].clientY,
            }
        }
        return null
    },

    // Prevent default touch behavior
    preventZoom(element: HTMLElement) {
        element.addEventListener('touchstart', (e) => {
            if (e.touches.length > 1) {
                e.preventDefault()
            }
        }, { passive: false })
    },

    // Debounce touch events
    debouncedTouch(callback: Function, delay: number = 300) {
        let timeoutId: NodeJS.Timeout
        return (...args: any[]) => {
            clearTimeout(timeoutId)
            timeoutId = setTimeout(() => callback(...args), delay)
        }
    },
}