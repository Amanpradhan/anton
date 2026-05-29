'use client'

import { useEffect, useRef, useState } from 'react'
import { api } from '@/lib/api'
import type { RunEvent } from '@/types'

export function useRunEvents(runId: string | null) {
  const [events, setEvents] = useState<RunEvent[]>([])
  const [done, setDone] = useState(false)

  // Keep seenRef and doneRef inside the effect via a ref-to-object so closures
  // always access the same mutable container — avoids the stale-closure trap.
  const stateRef = useRef({ seen: new Set<string>(), done: false })

  useEffect(() => {
    if (!runId) return

    // Fresh state for this run
    stateRef.current = { seen: new Set(), done: false }
    setEvents([])
    setDone(false)

    const poll = async () => {
      if (stateRef.current.done) return
      try {
        const buffered = await api.get<RunEvent[]>(`/api/runs/${runId}/events`)
        const newEvents: RunEvent[] = []

        for (const event of buffered) {
          if (event.event_type === 'ping') continue
          const key = `${event.timestamp}|${event.agent}|${event.event_type}|${(event.content ?? '').slice(0, 60)}`
          if (stateRef.current.seen.has(key)) continue
          stateRef.current.seen.add(key)
          newEvents.push(event)
          // Only the system agent signals pipeline termination.
          // Individual agents also emit event_type="complete" for their own step.
          if (event.agent === 'system' && (event.event_type === 'complete' || event.event_type === 'error')) {
            stateRef.current.done = true
            setDone(true)
          }
        }

        if (newEvents.length > 0) {
          setEvents(prev => [...prev, ...newEvents])
        }
      } catch {}
    }

    poll() // immediate on mount
    const id = setInterval(poll, 2000)
    return () => clearInterval(id)
  }, [runId])

  const totalTokens = events.reduce((sum, e) => sum + (e.tokens_used || 0), 0)

  // connected: true while run is active (polling is always running)
  return { events, connected: !done, done, totalTokens }
}
