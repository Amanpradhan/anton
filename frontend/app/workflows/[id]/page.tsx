'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import dynamic from 'next/dynamic'
import { Play, ArrowLeft } from 'lucide-react'
import { api } from '@/lib/api'
import type { Workflow, Run } from '@/types'

// React Flow must be client-only (no SSR)
const FlowCanvas = dynamic(() => import('@/components/workflow/FlowCanvas'), { ssr: false })

export default function WorkflowDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [workflow, setWorkflow] = useState<Workflow | null>(null)
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState(false)
  const [prompt, setPrompt] = useState('')

  useEffect(() => {
    api.get<Workflow>(`/api/workflows/${id}`).then(setWorkflow).finally(() => setLoading(false))
  }, [id])

  const handleTrigger = async () => {
    if (!prompt.trim()) return
    setTriggering(true)
    try {
      const run = await api.post<Run>('/api/runs/', { workflow_id: id, input: prompt })
      router.push(`/runs/${run.id}`)
    } catch {
      alert('Failed to trigger workflow')
      setTriggering(false)
    }
  }

  if (loading) return <div style={{ color: '#64748b' }}>Loading...</div>
  if (!workflow) return <div style={{ color: '#64748b' }}>Workflow not found</div>

  const hasGraph = workflow.graph?.nodes?.length > 0

  return (
    <div style={{ height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button className="btn-ghost" onClick={() => router.push('/workflows')} style={{ padding: '6px 10px' }}>
            <ArrowLeft size={15} />
          </button>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 700, color: '#f1f5f9' }}>{workflow.name}</h1>
            <p style={{ fontSize: 13, color: '#64748b' }}>{workflow.description}</p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span className={`badge ${workflow.is_active ? 'badge-green' : 'badge-slate'}`}>
            {workflow.is_active ? 'active' : 'inactive'}
          </span>
          {workflow.trigger_channel && <span className="badge badge-blue">{workflow.trigger_channel}</span>}
        </div>
      </div>

      {/* Trigger panel */}
      <div className="card" style={{ padding: 16, marginBottom: 16, display: 'flex', gap: 10 }}>
        <input
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          placeholder="Enter your research request to trigger this workflow..."
          onKeyDown={e => e.key === 'Enter' && handleTrigger()}
          style={{ flex: 1 }}
        />
        <button className="btn-primary" onClick={handleTrigger} disabled={triggering || !prompt.trim()}>
          <Play size={14} /> {triggering ? 'Starting...' : 'Run'}
        </button>
      </div>

      {/* React Flow canvas */}
      <div className="card" style={{ flex: 1, padding: 0, overflow: 'hidden' }}>
        {hasGraph ? (
          <FlowCanvas nodes={workflow.graph.nodes} edges={workflow.graph.edges} readonly />
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b' }}>
            No graph configured for this workflow
          </div>
        )}
      </div>
    </div>
  )
}
