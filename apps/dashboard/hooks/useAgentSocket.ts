'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { logger } from '@/lib/utils/logger'
import { resolveEngineWsUrl } from '@/lib/demo-guard'

interface AgentStatus {
  id: string
  name: string
  status: 'online' | 'offline' | 'busy' | 'idle'
  lastActive: Date
  xp: number
  tasks: number
}

interface WebSocketMessage {
  type: 'agent_update' | 'task_complete' | 'alert' | 'heartbeat'
  payload: unknown
}

interface UseAgentSocketOptions {
  url?: string
  reconnectInterval?: number
  maxRetries?: number
}

const INITIAL_DEMO_AGENTS: Omit<AgentStatus, 'lastActive'>[] = [
  { id: '1', name: 'Scout Agent', status: 'online', xp: 15420, tasks: 234 },
  { id: '2', name: 'Guardian Agent', status: 'busy', xp: 12850, tasks: 189 },
  { id: '3', name: 'Portfolio Agent', status: 'online', xp: 11200, tasks: 156 },
  { id: '4', name: 'Revenue Agent', status: 'idle', xp: 9800, tasks: 123 },
]

export function useAgentSocket(options: UseAgentSocketOptions = {}) {
  const {
    url = resolveEngineWsUrl('/ws/agents'),
    reconnectInterval = 3000,
    maxRetries = 5,
  } = options

  const [agents, setAgents] = useState<AgentStatus[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [connectionState, setConnectionState] = useState<
    'connecting' | 'connected' | 'disconnected' | 'error'
  >('disconnected')
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const retriesRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>(undefined)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    setConnectionState('connecting')

    try {
      wsRef.current = new WebSocket(url)
      wsRef.current.onopen = () => {
        setIsConnected(true)
        setConnectionState('connected')
        retriesRef.current = 0
      }

      wsRef.current.onmessage = event => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          setLastMessage(message)
          if (message.type === 'agent_update') {
            setAgents(message.payload as AgentStatus[])
          }
        } catch {
          logger.error('Failed to parse WebSocket message')
        }
      }

      wsRef.current.onclose = () => {
        setIsConnected(false)
        setConnectionState('disconnected')
        if (retriesRef.current < maxRetries) {
          retriesRef.current++
          reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval)
        }
      }

      wsRef.current.onerror = () => setConnectionState('error')
    } catch {
      setConnectionState('error')
    }
  }, [url, reconnectInterval, maxRetries])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
    wsRef.current?.close()
    setIsConnected(false)
    setConnectionState('disconnected')
  }, [])

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  useEffect(() => {
    const now = new Date()
    setAgents(INITIAL_DEMO_AGENTS.map(a => ({ ...a, lastActive: now })))
    const mockInterval = setInterval(() => {
      setAgents(prev =>
        prev.map(agent => ({
          ...agent,
          xp: agent.xp + Math.floor(Math.random() * 10),
          lastActive: new Date(),
        }))
      )
    }, 5000)
    return () => clearInterval(mockInterval)
  }, [])

  useEffect(() => {
    return () => disconnect()
  }, [connect, disconnect])

  return { agents, isConnected, connectionState, lastMessage, connect, disconnect, sendMessage }
}
