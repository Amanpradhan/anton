'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { Bot, GitBranch, Play, TrendingUp, Plus, ArrowRight } from 'lucide-react'
import { api } from '@/lib/api'
import type { Agent, Run, Workflow } from '@/types'

function StatCard({ label, value, icon: Icon, color }: { label: string; value: number | string; icon: any; color: string }) {
  return (
    <div className="card" style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 13, color: '#64748b', marginBottom: 8 }}>{label}</div>
          <div style={{ fontSize: 32, fontWeight: 700, color: '#f1f5f9' }}>{value}</div>
        </div>
        <div style={{ width: 44, height: 44, borderRadius: 10, background: `${color}22`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Icon size={20} style={{ color }} />
        </div>
      </div>
    </div>
  )
}

function statusBadge(status: string) {
  const map: Record<string, string> = { completed: 'badge-green', running: 'badge-blue', pending: 'badge-amber', failed: 'badge-red' }
  return <span className={`badge ${map[status] || 'badge-slate'}`}>{status}</span>
}

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [runs, setRuns] = useState<Run[]>([])
  const [loading, setLoading] = useState(true)

  const runsRef = useRef<Run[]>([])
  runsRef.current = runs

  useEffect(() => {
    const fetchAll = () => Promise.all([
      api.get<Agent[]>('/api/agents/'),
      api.get<Workflow[]>('/api/workflows/'),
      api.get<Run[]>('/api/runs/'),
    ]).then(([a, w, r]) => { setAgents(a); setWorkflows(w); setRuns(r); setLoading(false) })
      .catch(() => setLoading(false))

    fetchAll()

    // Adaptive polling: 2s when any run is active, 10s when all idle
    let timeoutId: ReturnType<typeof setTimeout>
    const poll = async () => {
      await fetchAll()
      const hasActive = runsRef.current.some(r => r.status === 'running' || r.status === 'pending')
      timeoutId = setTimeout(poll, hasActive ? 2000 : 10000)
    }
    timeoutId = setTimeout(poll, 2000)
    return () => clearTimeout(timeoutId)
  }, [])

  const totalCost = runs.reduce((s, r) => s + r.estimated_cost_usd, 0)

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: '#f1f5f9', marginBottom: 6 }}>Dashboard</h1>
        <p style={{ color: '#64748b', fontSize: 15 }}>Your autonomous agent command center</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 32 }}>
        <StatCard label="Agents" value={agents.length} icon={Bot} color="#6366f1" />
        <StatCard label="Workflows" value={workflows.length} icon={GitBranch} color="#8b5cf6" />
        <StatCard label="Total Runs" value={runs.length} icon={Play} color="#06b6d4" />
        <StatCard label="Total Cost" value={`$${totalCost.toFixed(4)}`} icon={TrendingUp} color="#10b981" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div className="card" style={{ padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h2 style={{ fontSize: 16, fontWeight: 600, color: '#f1f5f9' }}>Recent Runs</h2>
            <Link href="/runs" style={{ fontSize: 13, color: '#6366f1', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}>View all <ArrowRight size={13} /></Link>
          </div>
          {loading ? <div style={{ color: '#64748b', fontSize: 14 }}>Loading...</div> : runs.length === 0 ? (
            <div style={{ color: '#64748b', fontSize: 14 }}>No runs yet. Trigger a workflow to get started.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {runs.slice(0, 5).map(run => (
                <Link key={run.id} href={`/runs/${run.id}`} style={{ textDecoration: 'none' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', borderRadius: 8, background: '#0a0f1e' }}>
                    <div>
                      <div style={{ fontSize: 13, color: '#f1f5f9', marginBottom: 2, maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{run.input || 'No input'}</div>
                      <div style={{ fontSize: 12, color: '#475569' }}>{run.total_tokens.toLocaleString()} tokens · ${run.estimated_cost_usd.toFixed(4)}</div>
                    </div>
                    {statusBadge(run.status)}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        <div className="card" style={{ padding: 24 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: '#f1f5f9', marginBottom: 20 }}>Quick Actions</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[
              { href: '/agents/new', label: 'Create a new agent', icon: Bot, desc: 'Configure an AI agent with tools and memory' },
              { href: '/workflows', label: 'Build a workflow', icon: GitBranch, desc: 'Connect agents into a pipeline' },
              { href: '/templates', label: 'Browse templates', icon: Plus, desc: 'Start from a pre-built workflow' },
              { href: '/evals', label: 'Run evaluations', icon: TrendingUp, desc: 'Score pipeline output quality' },
            ].map(({ href, label, icon: Icon, desc }) => (
              <Link key={href} href={href} style={{ textDecoration: 'none' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 14px', borderRadius: 8, background: '#0a0f1e', border: '1px solid #1e2d4a', cursor: 'pointer' }}>
                  <div style={{ width: 36, height: 36, borderRadius: 8, background: '#1e2d4a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Icon size={16} style={{ color: '#6366f1' }} />
                  </div>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 500, color: '#f1f5f9' }}>{label}</div>
                    <div style={{ fontSize: 12, color: '#475569' }}>{desc}</div>
                  </div>
                  <ArrowRight size={14} style={{ marginLeft: 'auto', color: '#334155' }} />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
