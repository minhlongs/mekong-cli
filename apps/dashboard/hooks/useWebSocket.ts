'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { logger } from '@/lib/utils/logger'
import { resolveEngineWsUrl } from '@/lib/demo-guard'

export type WSEventType =
  | 'connected' | 'disconnected' | 'lead_added' | 'lead_qualified' | 'client_converted'
  | 'invoice_created' | 'invoice_paid' | 'content_created' | 'franchise_added'
  | 'vc_score_updated' | 'moat_updated' | 'data_refresh' | 'heartbeat' | 'pong'

export interface WSMessage {
  type: WSEventType
  data?: Record<string, unknown>
  client_id?: string
  timestamp?: string
  connections?: number
}

export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error'

interface UseWebSocketOptions {
  autoReconnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onConnect?: (clientId: string) => void
  onDisconnect?: () => void
  onMessage?: (message: WSMessage) => void
  onEvent?: (type: WSEventType, data: Record<string, unknown> | undefined) => void
}

export function useWebSocket(url: string, options: UseWebSocketOptions = {}) {
  const {
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onConnect,
    onDisconnect,
    onMessage,
    onEvent,
  } = options

  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null)
  const [clientId, setClientId] = useState<string | null>(null)
  const [connectionCount, setConnectionCount] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    setConnectionState('connecting')
    setError(null)

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setConnectionState('connected')
        reconnectAttemptsRef.current = 0
      }

      ws.onclose = () => {
        setConnectionState('disconnected')
        setClientId(null)
        onDisconnect?.()

        if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          reconnectTimeoutRef.current = setTimeout(() => connect(), reconnectInterval)
        }
      }

      ws.onerror = () => {
        setConnectionState('error')
        setError('WebSocket connection error')
      }

      ws.onmessage = event => {
        try {
          const message: WSMessage = JSON.parse(event.data)
          setLastMessage(message)

          if (message.type === 'connected') {
            setClientId(message.client_id || null)
            onConnect?.(message.client_id || '')
          }
          if (message.connections !== undefined) {
            setConnectionCount(message.connections)
          }

          onMessage?.(message)
          onEvent?.(message.type, message.data)
        } catch (e) {
          logger.error('Failed to parse WebSocket message', e)
        }
      }
    } catch {
      setConnectionState('error')
      setError('Failed to create WebSocket connection')
    }
  }, [url, autoReconnect, reconnectInterval, maxReconnectAttempts, onConnect, onDisconnect, onMessage, onEvent])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
    reconnectAttemptsRef.current = maxReconnectAttempts
    wsRef.current?.close()
    setConnectionState('disconnected')
  }, [maxReconnectAttempts])

  const send = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  const ping = useCallback(() => send({ type: 'ping' }), [send])
  const requestRefresh = useCallback(() => send({ type: 'request_refresh' }), [send])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  return {
    connectionState,
    isConnected: connectionState === 'connected',
    isConnecting: connectionState === 'connecting',
    clientId,
    connectionCount,
    lastMessage,
    error,
    connect,
    disconnect,
    send,
    ping,
    requestRefresh,
  }
}

export function useAntigravityRealtime(options?: {
  onLeadAdded?: (data: Record<string, unknown> | undefined) => void
  onInvoicePaid?: (data: Record<string, unknown> | undefined) => void
  onVCScoreUpdated?: (data: Record<string, unknown> | undefined) => void
  onDataRefresh?: () => void
}) {
  const wsUrl = resolveEngineWsUrl('/ws')

  return useWebSocket(wsUrl, {
    autoReconnect: true,
    onEvent: (type, data) => {
      if (type === 'lead_added') options?.onLeadAdded?.(data)
      else if (type === 'invoice_paid') options?.onInvoicePaid?.(data)
      else if (type === 'vc_score_updated') options?.onVCScoreUpdated?.(data)
      else if (type === 'data_refresh') options?.onDataRefresh?.()
    },
  })
}

export default useWebSocket
