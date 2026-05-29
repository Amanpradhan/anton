'use client'

import { useEffect, useRef, useState } from 'react'
import { WS_BASE, api } from '@/lib/api'
import type { RunEvent } from '@/types'

export function useRunEvents(runId: string | null) {
  const [events, setEvents] = useState<RunEvent[]>([])
  const [connected, setConnected] = useState(false)
  const [done, setDone] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const doneRef = useRef(false)
  const seenRef = useRef<Set<string>>(new Set())
  const connectedRef = useRef(false)

  const addEvent = (event: RunEvent) => {
    if (event.event_type === 'ping') return
    const key = `${event.timestamp}-${event.agent}-${event.event_type}-${(event.content || '').slice(0, 40)}`
    if (seenRef.current.has(key)) return
    seenRef.current.add(key)
    setEvents((prev) => [...prev, event])
    if (event.event_type === 'complete' || event.event_type === 'error') {
      doneRef.current = true
      setDone(true)
    }
  }

  useEffect(() => {
    if (!runId) return

    // Reset state for this run
    doneRef.current = false
    connectedRef.current = false
    seenRef.current = new Set()

    // --- WebSocket for live events ---
    const ws = new WebSocket(`${WS_BASE}/ws/runs/${runId}`)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      connectedRef.current = true
    }
    ws.onmessage = (e) => {
      try { addEvent(JSON.parse(e.data)) } catch {}
    }
    ws.onclose = () => {
      setConnected(false)
      connectedRef.current = false
      wsRef.current = null
    }
    ws.onerror = () => {
      setConnected(false)
      connectedRef.current = false
      wsRef.current = null
    }

    // --- Polling fallback: read Redis buffer every 3s ---
    // Runs regardless of WebSocket state. Dedup ensures no duplicates.
    const pollInterval = setInterval(async () => {
      if (doneRef.current) return
      try {
        const buffered = await api.get<RunEvent[]>(`/api/runs/${runId}/events`)
        buffered.forEach(addEvent)
      } catch {}
    }, 3000)

    return () => {
      clearInterval(pollInterval)
      ws.onclose = null  // prevent onclose from firing after unmount
      ws.close()
      wsRef.current = null
    }
  }, [runId])

  const totalTokens = events.reduce((sum, e) => sum + (e.tokens_used || 0), 0)

  return { events, connected, done, totalTokens }
}
