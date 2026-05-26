'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import dynamic from 'next/dynamic'
import { Shapes, Plus } from 'lucide-react'
import { api } from '@/lib/api'
import type { Template, Workflow } from '@/types'

const FlowCanvas = dynamic(() => import('@/components/workflow/FlowCanvas'), { ssr: false })

export default function TemplatesPage() {
  const router = useRouter()
  const [templates, setTemplates] = useState<Template[]>([])
  const [selected, setSelected] = useState<Template | null>(null)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState<string | null>(null)

  useEffect(() => {
    api.get<Template[]>('/api/workflows/templates').then(setTemplates).finally(() => setLoading(false))
  }, [])

  const handleCreate = async (templateId: string) => {
    setCreating(templateId)
    try {
      const wf = await api.post<Workflow>(`/api/workflows/from-template/${templateId}`)
      router.push(`/workflows/${wf.id}`)
    } catch {
      alert('Failed to create workflow from template')
      setCreating(null)
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: '#f1f5f9', marginBottom: 6 }}>Templates</h1>
        <p style={{ color: '#64748b', fontSize: 15 }}>Pre-built multi-agent workflows ready to use</p>
      </div>

      {loading ? <div style={{ color: '#64748b' }}>Loading...</div> : (
        <div style={{ display: 'grid', gridTemplateColumns: selected ? '320px 1fr' : 'repeat(auto-fill, minmax(340px, 1fr))', gap: 20, transition: 'all 0.3s' }}>
          {/* Template cards */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {templates.map(t => (
              <div key={t.id} className="card" onClick={() => setSelected(t === selected ? null : t)}
                style={{ padding: 20, cursor: 'pointer', borderColor: selected?.id === t.id ? '#6366f1' : '#1e2d4a', transition: 'border-color 0.15s' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                  <div style={{ width: 36, height: 36, borderRadius: 8, background: '#1e2d4a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Shapes size={16} style={{ color: '#6366f1' }} />
                  </div>
                  <div style={{ fontWeight: 600, color: '#f1f5f9', fontSize: 15 }}>{t.name}</div>
                </div>
                <div style={{ fontSize: 13, color: '#64748b', marginBottom: 14, lineHeight: 1.5 }}>{t.description}</div>
                <div style={{ fontSize: 12, color: '#475569', marginBottom: 14, fontStyle: 'italic' }}>
                  Example: "{t.example_prompt}"
                </div>
                <div style={{ display: 'flex', gap: 6, marginBottom: 14 }}>
                  {t.graph?.nodes?.map(n => (
                    <span key={n.id} className="badge badge-slate">{n.label}</span>
                  ))}
                </div>
                <button className="btn-primary" style={{ width: '100%', justifyContent: 'center' }}
                  onClick={e => { e.stopPropagation(); handleCreate(t.id) }}
                  disabled={creating === t.id}>
                  <Plus size={14} /> {creating === t.id ? 'Creating...' : 'Use this template'}
                </button>
              </div>
            ))}
          </div>

          {/* Graph preview */}
          {selected && (
            <div className="card" style={{ padding: 0, overflow: 'hidden', minHeight: 500 }}>
              <div style={{ padding: '14px 18px', borderBottom: '1px solid #1e2d4a' }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: '#f1f5f9' }}>Pipeline Preview — {selected.name}</div>
              </div>
              <div style={{ height: 'calc(100% - 50px)' }}>
                <FlowCanvas nodes={selected.graph.nodes} edges={selected.graph.edges} readonly />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
