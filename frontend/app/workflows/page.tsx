'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { GitBranch, Plus, Trash2, Play } from 'lucide-react'
import { api } from '@/lib/api'
import type { Workflow } from '@/types'

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<Workflow[]>('/api/workflows/').then(setWorkflows).finally(() => setLoading(false))
  }, [])

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this workflow?')) return
    await api.delete(`/api/workflows/${id}`)
    setWorkflows(prev => prev.filter(w => w.id !== id))
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: '#f1f5f9', marginBottom: 6 }}>Workflows</h1>
          <p style={{ color: '#64748b', fontSize: 15 }}>Multi-agent pipelines and their configurations</p>
        </div>
        <Link href="/templates"><button className="btn-primary"><Plus size={15} /> New from Template</button></Link>
      </div>

      {loading ? (
        <div style={{ color: '#64748b' }}>Loading...</div>
      ) : workflows.length === 0 ? (
        <div className="card" style={{ padding: 48, textAlign: 'center' }}>
          <GitBranch size={40} style={{ color: '#334155', margin: '0 auto 16px' }} />
          <div style={{ color: '#64748b', marginBottom: 16 }}>No workflows yet</div>
          <Link href="/templates"><button className="btn-primary"><Plus size={15} /> Create from template</button></Link>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {workflows.map(wf => (
            <div key={wf.id} className="card" style={{ padding: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{ width: 40, height: 40, borderRadius: 10, background: '#1e2d4a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <GitBranch size={18} style={{ color: '#6366f1' }} />
                </div>
                <div>
                  <div style={{ fontWeight: 600, color: '#f1f5f9', fontSize: 15, marginBottom: 2 }}>{wf.name}</div>
                  <div style={{ fontSize: 13, color: '#64748b' }}>{wf.description || 'No description'}</div>
                  <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
                    {wf.trigger_channel && <span className="badge badge-blue">{wf.trigger_channel}</span>}
                    <span className={`badge ${wf.is_active ? 'badge-green' : 'badge-slate'}`}>{wf.is_active ? 'active' : 'inactive'}</span>
                    <span className="badge badge-slate">{wf.graph?.nodes?.length || 0} agents</span>
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <Link href={`/workflows/${wf.id}`}>
                  <button className="btn-ghost"><Play size={13} /> View</button>
                </Link>
                <button className="btn-danger" onClick={() => handleDelete(wf.id)}><Trash2 size={13} /></button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
