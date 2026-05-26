'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { WS_BASE } from '@/lib/api'
import type { RunEvent } from '@/types'

export function useRunEvents(runId: string | null) {
  const [events, setEvents] = useState<RunEvent[]>([])
  const [connected, setConnected] = useState(false)
  const [done, setDone] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  const connect = useCallback(() => {
    if (!runId || wsRef.current) return

    const ws = new WebSocket(`${WS_BASE}/ws/runs/${runId}`)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)

    ws.onmessage = (e) => {
      try {
        const event: RunEvent = JSON.parse(e.data)
        setEvents((prev) => [...prev, event])
        if (event.event_type === 'complete' || event.event_type === 'error') {
          setDone(true)
        }
      } catch {}
    }

    ws.onclose = () => {
      setConnected(false)
      wsRef.current = null
    }

    ws.onerror = () => {
      setConnected(false)
      wsRef.current = null
    }
  }, [runId])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [connect])

  const totalTokens = events.reduce((sum, e) => sum + (e.tokens_used || 0), 0)

  return { events, connected, done, totalTokens }
}
