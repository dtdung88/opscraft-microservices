import { useEffect, useRef, useState, useCallback } from 'react'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

interface UseWebSocketReturn<T> {
    messages: T[]
    isConnected: boolean
    sendMessage: (message: T) => void
    clearMessages: () => void
}

export function useWebSocket<T = unknown>(channel: string): UseWebSocketReturn<T> {
    const [messages, setMessages] = useState<T[]>([])
    const [isConnected, setIsConnected] = useState(false)
    const wsRef = useRef<WebSocket | null>(null)

    useEffect(() => {
        const ws = new WebSocket(`${WS_URL}/ws/${channel}`)

        ws.onopen = () => {
            console.log(`WebSocket connected to ${channel}`)
            setIsConnected(true)
        }

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data) as T
                setMessages((prev) => [...prev, data])
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error)
            }
        }

        ws.onerror = (error) => {
            console.error('WebSocket error:', error)
        }

        ws.onclose = () => {
            console.log(`WebSocket disconnected from ${channel}`)
            setIsConnected(false)
        }

        wsRef.current = ws

        return () => {
            ws.close()
        }
    }, [channel])

    const sendMessage = useCallback((message: T) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message))
        }
    }, [])

    const clearMessages = useCallback(() => {
        setMessages([])
    }, [])

    return { messages, isConnected, sendMessage, clearMessages }
}