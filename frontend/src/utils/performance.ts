export const performanceUtils = {
    // Lazy load images
    lazyLoadImage(imgElement: HTMLImageElement) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    const img = entry.target as HTMLImageElement
                    img.src = img.dataset.src || ''
                    observer.unobserve(img)
                }
            })
        })

        observer.observe(imgElement)
    },

    // Debounce scroll events
    debounceScroll(callback: Function, delay: number = 150) {
        let timeoutId: NodeJS.Timeout
        return () => {
            clearTimeout(timeoutId)
            timeoutId = setTimeout(callback, delay)
        }
    },

    // Throttle for continuous events
    throttle(callback: Function, limit: number = 100) {
        let waiting = false
        return (...args: any[]) => {
            if (!waiting) {
                callback(...args)
                waiting = true
                setTimeout(() => {
                    waiting = false
                }, limit)
            }
        }
    },

    // Preload critical resources
    preloadImage(src: string) {
        const img = new Image()
        img.src = src
    },

    // Check if in viewport
    isInViewport(element: HTMLElement) {
        const rect = element.getBoundingClientRect()
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        )
    },
}