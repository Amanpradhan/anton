'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Bot, Plus, Trash2, Pencil } from 'lucide-react'
import { api } from '@/lib/api'
import type { Agent } from '@/types'

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<Agent[]>('/api/agents/').then(setAgents).finally(() => setLoading(false))
  }, [])

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this agent?')) return
    await api.delete(`/api/agents/${id}`)
    setAgents(prev => prev.filter(a => a.id !== id))
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: '#f1f5f9', marginBottom: 6 }}>Agents</h1>
          <p style={{ color: '#64748b', fontSize: 15 }}>Configure and manage your AI agents</p>
        </div>
        <Link href="/agents/new"><button className="btn-primary"><Plus size={15} /> New Agent</button></Link>
      </div>

      {loading ? (
        <div style={{ color: '#64748b' }}>Loading...</div>
      ) : agents.length === 0 ? (
        <div className="card" style={{ padding: 48, textAlign: 'center' }}>
          <Bot size={40} style={{ color: '#334155', margin: '0 auto 16px' }} />
          <div style={{ color: '#64748b', marginBottom: 16 }}>No agents yet</div>
          <Link href="/agents/new"><button className="btn-primary"><Plus size={15} /> Create your first agent</button></Link>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
          {agents.map(agent => (
            <div key={agent.id} className="card" style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{ width: 36, height: 36, borderRadius: 8, background: '#1e2d4a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Bot size={16} style={{ color: '#6366f1' }} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, color: '#f1f5f9', fontSize: 15 }}>{agent.name}</div>
                    <div style={{ fontSize: 12, color: '#64748b' }}>{agent.role}</div>
                  </div>
                </div>
                <span className={`badge ${agent.is_active ? 'badge-green' : 'badge-slate'}`}>
                  {agent.is_active ? 'active' : 'inactive'}
                </span>
              </div>

              <div style={{ fontSize: 13, color: '#64748b', marginBottom: 16, lineHeight: 1.5, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                {agent.system_prompt}
              </div>

              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
                <span className="badge badge-slate">{agent.model}</span>
                {agent.channels.map(c => <span key={c} className="badge badge-blue">{c}</span>)}
                {agent.tools.slice(0, 2).map(t => <span key={t} className="badge badge-slate">{t}</span>)}
              </div>

              <div style={{ display: 'flex', gap: 8, borderTop: '1px solid #1e2d4a', paddingTop: 14 }}>
                <Link href={`/agents/${agent.id}`} style={{ flex: 1 }}>
                  <button className="btn-ghost" style={{ width: '100%', justifyContent: 'center' }}>
                    <Pencil size={13} /> Edit
                  </button>
                </Link>
                <button className="btn-danger" onClick={() => handleDelete(agent.id)}>
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
