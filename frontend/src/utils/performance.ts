type AnyFunction = (...args: unknown[]) => unknown

export const performanceUtils = {
    // Lazy load images
    lazyLoadImage(imgElement: HTMLImageElement): void {
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
    debounceScroll(callback: AnyFunction, delay: number = 150): () => void {
        let timeoutId: ReturnType<typeof setTimeout>
        return () => {
            clearTimeout(timeoutId)
            timeoutId = setTimeout(() => callback(), delay)
        }
    },

    // Throttle for continuous events
    throttle<T extends unknown[]>(callback: (...args: T) => void, limit: number = 100): (...args: T) => void {
        let waiting = false
        return (...args: T) => {
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
    preloadImage(src: string): void {
        const img = new Image()
        img.src = src
    },

    // Check if in viewport
    isInViewport(element: HTMLElement): boolean {
        const rect = element.getBoundingClientRect()
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        )
    },
}