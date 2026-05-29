'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { WS_BASE } from '@/lib/api'
import type { RunEvent } from '@/types'

export function useRunEvents(runId: string | null) {
  const [events, setEvents] = useState<RunEvent[]>([])
  const [connected, setConnected] = useState(false)
  const [done, setDone] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const doneRef = useRef(false)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const connect = useCallback(() => {
    if (!runId || wsRef.current || doneRef.current) return

    const ws = new WebSocket(`${WS_BASE}/ws/runs/${runId}`)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)

    ws.onmessage = (e) => {
      try {
        const event: RunEvent = JSON.parse(e.data)
        // Ignore heartbeat pings
        if (event.event_type === 'ping') return
        setEvents((prev) => [...prev, event])
        if (event.event_type === 'complete' || event.event_type === 'error') {
          doneRef.current = true
          setDone(true)
        }
      } catch {}
    }

    ws.onclose = () => {
      setConnected(false)
      wsRef.current = null
      // Auto-reconnect if the run isn't finished yet
      if (!doneRef.current) {
        reconnectTimer.current = setTimeout(connect, 2000)
      }
    }

    ws.onerror = () => {
      setConnected(false)
      wsRef.current = null
    }
  }, [runId])

  useEffect(() => {
    connect()
    return () => {
      doneRef.current = false
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [connect])

  const totalTokens = events.reduce((sum, e) => sum + (e.tokens_used || 0), 0)

  return { events, connected, done, totalTokens }
}
