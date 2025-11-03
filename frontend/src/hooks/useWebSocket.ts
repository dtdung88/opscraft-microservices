import { useEffect, useRef, useState } from 'react'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export function useWebSocket(channel: string) {
    const [messages, setMessages] = useState<any[]>([])
    const [isConnected, setIsConnected] = useState(false)
    const wsRef = useRef<WebSocket | null>(null)

    useEffect(() => {
        const ws = new WebSocket(`${WS_URL}/ws/${channel}`)

        ws.onopen = () => {
            console.log(`WebSocket connected to ${channel}`)
            setIsConnected(true)
        }

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data)
            setMessages((prev) => [...prev, data])
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

    const sendMessage = (message: any) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message))
        }
    }

    const clearMessages = () => {
        setMessages([])
    }

    return { messages, isConnected, sendMessage, clearMessages }
}