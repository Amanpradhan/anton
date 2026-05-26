'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Play, ArrowRight } from 'lucide-react'
import { api } from '@/lib/api'
import type { Run } from '@/types'
import { formatDistanceToNow } from 'date-fns'

function statusBadge(status: string) {
  const map: Record<string, string> = { completed: 'badge-green', running: 'badge-blue', pending: 'badge-amber', failed: 'badge-red' }
  return <span className={`badge ${map[status] || 'badge-slate'}`}>{status}</span>
}

export default function RunsPage() {
  const [runs, setRuns] = useState<Run[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<Run[]>('/api/runs/').then(setRuns).finally(() => setLoading(false))
    // Poll every 5s for running pipelines
    const interval = setInterval(() => api.get<Run[]>('/api/runs/').then(setRuns), 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: '#f1f5f9', marginBottom: 6 }}>Runs</h1>
        <p style={{ color: '#64748b', fontSize: 15 }}>All pipeline executions and their results</p>
      </div>

      {loading ? (
        <div style={{ color: '#64748b' }}>Loading...</div>
      ) : runs.length === 0 ? (
        <div className="card" style={{ padding: 48, textAlign: 'center' }}>
          <Play size={40} style={{ color: '#334155', margin: '0 auto 16px' }} />
          <div style={{ color: '#64748b' }}>No runs yet. Open a workflow and trigger it.</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {runs.map(run => (
            <Link key={run.id} href={`/runs/${run.id}`} style={{ textDecoration: 'none' }}>
              <div className="card" style={{ padding: 18, display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', transition: 'border-color 0.15s' }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 14, fontWeight: 500, color: '#f1f5f9', marginBottom: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 500 }}>
                    {run.input || 'No input'}
                  </div>
                  <div style={{ display: 'flex', gap: 12, fontSize: 12, color: '#475569' }}>
                    <span>{run.trigger_source}</span>
                    <span>{run.total_tokens.toLocaleString()} tokens</span>
                    <span>${run.estimated_cost_usd.toFixed(4)}</span>
                    <span>{formatDistanceToNow(new Date(run.created_at), { addSuffix: true })}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  {statusBadge(run.status)}
                  <ArrowRight size={14} style={{ color: '#334155' }} />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
