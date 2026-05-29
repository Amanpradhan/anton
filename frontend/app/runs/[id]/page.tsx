'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { api } from '@/lib/api'
import { useRunEvents } from '@/lib/hooks/useWebSocket'
import type { Run, RunEvent } from '@/types'

const AGENT_COLORS: Record<string, string> = {
  orchestrator: '#6366f1',
  researcher:   '#06b6d4',
  analyst:      '#8b5cf6',
  critic:       '#f59e0b',
  reporter:     '#10b981',
  evaluator:    '#ec4899',
  system:       '#64748b',
}

function EventRow({ event }: { event: RunEvent }) {
  const color = AGENT_COLORS[event.agent] || '#64748b'
  const isError = event.event_type === 'error'

  return (
    <div style={{ display: 'flex', gap: 12, padding: '10px 0', borderBottom: '1px solid #1e2d4a' }}>
      <div style={{ width: 8, height: 8, borderRadius: '50%', background: isError ? '#f87171' : color, marginTop: 5, flexShrink: 0 }} />
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 2 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color }}>{event.agent}</span>
          <span style={{ fontSize: 11, color: '#334155', background: '#1e2d4a', padding: '1px 6px', borderRadius: 4 }}>{event.event_type}</span>
          {event.tokens_used > 0 && <span style={{ fontSize: 11, color: '#475569' }}>{event.tokens_used} tokens</span>}
        </div>
        <div style={{ fontSize: 13, color: isError ? '#f87171' : '#94a3b8', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>{event.content}</div>
      </div>
      <div style={{ fontSize: 11, color: '#334155', whiteSpace: 'nowrap', flexShrink: 0 }}>
        {new Date(event.timestamp).toLocaleTimeString()}
      </div>
    </div>
  )
}

function MessageRow({ msg }: { msg: any }) {
  const color = AGENT_COLORS[msg.sender] || '#64748b'
  return (
    <div style={{ display: 'flex', gap: 12, padding: '10px 0', borderBottom: '1px solid #1e2d4a' }}>
      <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, marginTop: 5, flexShrink: 0 }} />
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 2 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color }}>{msg.sender}</span>
          <span style={{ fontSize: 11, color: '#334155', background: '#1e2d4a', padding: '1px 6px', borderRadius: 4 }}>{msg.message_type}</span>
          {msg.tokens_used > 0 && <span style={{ fontSize: 11, color: '#475569' }}>{msg.tokens_used} tokens</span>}
        </div>
        <div style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>{msg.content}</div>
      </div>
    </div>
  )
}

function ScoreBar({ label, score }: { label: string; score: number }) {
  const pct = (score / 10) * 100
  const color = score >= 7 ? '#10b981' : score >= 5 ? '#f59e0b' : '#f87171'
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 12, color: '#94a3b8' }}>{label}</span>
        <span style={{ fontSize: 12, fontWeight: 600, color }}>{score}/10</span>
      </div>
      <div style={{ height: 4, background: '#1e2d4a', borderRadius: 2 }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 2, transition: 'width 0.5s' }} />
      </div>
    </div>
  )
}

export default function RunDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [run, setRun] = useState<Run | null>(null)
  const [evalResult, setEvalResult] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<'monitor' | 'report' | 'eval'>('monitor')
  const { events, connected, done, totalTokens } = useRunEvents(id)

  useEffect(() => {
    api.get<Run>(`/api/runs/${id}`).then(setRun)
  }, [id])

  // Refresh run data when WebSocket signals completion
  useEffect(() => {
    if (done) api.get<Run>(`/api/runs/${id}`).then(setRun)
  }, [id, done])

  // Polling fallback: refresh every 4s until run is terminal (handles late navigation)
  useEffect(() => {
    if (run?.status === 'completed' || run?.status === 'failed') return
    const interval = setInterval(() => {
      api.get<Run>(`/api/runs/${id}`).then(setRun)
    }, 4000)
    return () => clearInterval(interval)
  }, [id, run?.status])

  // Fetch eval, retry until available (eval runs async after report)
  useEffect(() => {
    let cancelled = false
    const fetchEval = () => {
      api.get<any>(`/api/evals/results/${id}`)
        .then(data => {
          if (cancelled) return
          if (data && data.overall_score !== undefined) {
            setEvalResult(data)
          } else if (!evalResult) {
            setTimeout(fetchEval, 5000) // retry until eval is ready
          }
        })
        .catch(() => {})
    }
    fetchEval()
    return () => { cancelled = true }
  }, [id])

  const statusColor: Record<string, string> = { completed: '#10b981', running: '#6366f1', pending: '#f59e0b', failed: '#f87171' }
  const messages: any[] = (run as any)?.messages || []
  const isCompleted = run?.status === 'completed' || run?.status === 'failed'

  return (
    <div style={{ height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <button className="btn-ghost" onClick={() => router.push('/runs')} style={{ padding: '6px 10px' }}>
          <ArrowLeft size={15} />
        </button>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 14, color: '#f1f5f9', fontWeight: 500, maxWidth: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {run?.input || 'Loading...'}
          </div>
          <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>Run ID: {id}</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {connected && !done && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: '#10b981' }}>
              <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#10b981', animation: 'pulse 1s infinite' }} />
              Live
            </div>
          )}
          {run && <span style={{ fontSize: 12, fontWeight: 600, color: statusColor[run.status] || '#64748b' }}>{run.status}</span>}
        </div>
      </div>

      {/* Stats bar */}
      <div style={{ display: 'flex', gap: 20, marginBottom: 16, padding: '12px 16px', background: '#0f1629', borderRadius: 10, border: '1px solid #1e2d4a', fontSize: 13 }}>
        <span style={{ color: '#64748b' }}>Tokens: <strong style={{ color: '#f1f5f9' }}>{(run?.total_tokens || totalTokens).toLocaleString()}</strong></span>
        <span style={{ color: '#64748b' }}>Cost: <strong style={{ color: '#f1f5f9' }}>${(run?.estimated_cost_usd || ((run?.total_tokens || totalTokens) / 1000 * 0.00107)).toFixed(4)}</strong></span>
        <span style={{ color: '#64748b' }}>Events: <strong style={{ color: '#f1f5f9' }}>{events.length || messages.length}</strong></span>
        <span style={{ color: '#64748b' }}>Source: <strong style={{ color: '#f1f5f9' }}>{run?.trigger_source || '—'}</strong></span>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 16 }}>
        {(['monitor', 'report', 'eval'] as const).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            style={{ padding: '8px 16px', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer', border: 'none', background: activeTab === tab ? '#6366f1' : '#1e2d4a', color: activeTab === tab ? 'white' : '#64748b', transition: 'all 0.15s' }}>
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="card" style={{ flex: 1, overflow: 'auto', padding: 20 }}>
        {activeTab === 'monitor' && (
          <div>
            {/* Live events take priority; fall back to DB messages for completed runs */}
            {events.length > 0 ? (
              events.map((e, i) => <EventRow key={i} event={e} />)
            ) : messages.length > 0 ? (
              messages.map((m, i) => <MessageRow key={i} msg={m} />)
            ) : (
              <div style={{ color: '#64748b', fontSize: 14 }}>
                {isCompleted ? 'No agent events recorded for this run.' : 'Waiting for agent activity...'}
              </div>
            )}
          </div>
        )}

        {activeTab === 'report' && (
          <div>
            {run?.output ? (
              <div style={{ fontSize: 14, color: '#e2e8f0', lineHeight: 1.8 }} className="prose-dark">
                <ReactMarkdown
                  components={{
                    h1: ({ children }) => <h1 style={{ fontSize: 22, fontWeight: 700, color: '#f1f5f9', marginBottom: 12, marginTop: 24 }}>{children}</h1>,
                    h2: ({ children }) => <h2 style={{ fontSize: 18, fontWeight: 600, color: '#f1f5f9', marginBottom: 10, marginTop: 20 }}>{children}</h2>,
                    h3: ({ children }) => <h3 style={{ fontSize: 15, fontWeight: 600, color: '#cbd5e1', marginBottom: 8, marginTop: 16 }}>{children}</h3>,
                    p: ({ children }) => <p style={{ marginBottom: 12, color: '#94a3b8' }}>{children}</p>,
                    strong: ({ children }) => <strong style={{ color: '#e2e8f0', fontWeight: 600 }}>{children}</strong>,
                    li: ({ children }) => <li style={{ marginBottom: 4, color: '#94a3b8' }}>{children}</li>,
                    ul: ({ children }) => <ul style={{ paddingLeft: 20, marginBottom: 12 }}>{children}</ul>,
                    ol: ({ children }) => <ol style={{ paddingLeft: 20, marginBottom: 12 }}>{children}</ol>,
                    hr: () => <hr style={{ border: 'none', borderTop: '1px solid #1e2d4a', margin: '20px 0' }} />,
                    code: ({ children }) => <code style={{ background: '#1e2d4a', padding: '2px 6px', borderRadius: 4, fontSize: 12, color: '#06b6d4' }}>{children}</code>,
                  }}
                >
                  {run.output}
                </ReactMarkdown>
              </div>
            ) : (
              <div style={{ color: '#64748b', fontSize: 14 }}>
                {run?.status === 'running' || run?.status === 'pending' ? 'Report will appear here when the pipeline completes...' : 'No report generated.'}
              </div>
            )}
          </div>
        )}

        {activeTab === 'eval' && (
          <div style={{ maxWidth: 480 }}>
            <div style={{ fontSize: 14, color: '#64748b', marginBottom: 20 }}>
              LLM-as-judge quality scores for this run&apos;s report
            </div>
            {!evalResult ? (
              <div style={{ color: '#64748b', fontSize: 14 }}>
                {isCompleted ? 'No evaluation found for this run.' : 'Evaluation runs automatically after the report is generated. Check back shortly.'}
              </div>
            ) : (
              <>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24, padding: 16, background: '#0a0f1e', borderRadius: 10 }}>
                  <div style={{ fontSize: 36, fontWeight: 700, color: evalResult.passed ? '#10b981' : '#f87171' }}>
                    {evalResult.overall_score.toFixed(1)}
                  </div>
                  <div>
                    <div style={{ fontSize: 13, color: '#94a3b8' }}>Overall Score</div>
                    <span className={`badge ${evalResult.passed ? 'badge-green' : 'badge-red'}`}>
                      {evalResult.passed ? 'PASSED' : 'FAILED'} (threshold: 7.0)
                    </span>
                  </div>
                </div>
                <ScoreBar label="Specificity" score={evalResult.specificity_score} />
                <ScoreBar label="Completeness" score={evalResult.completeness_score} />
                <ScoreBar label="Accuracy Risk" score={evalResult.accuracy_risk_score} />
                <ScoreBar label="Usefulness" score={evalResult.usefulness_score} />
                {evalResult.feedback && (
                  <div style={{ marginTop: 20, padding: 14, background: '#0a0f1e', borderRadius: 8, fontSize: 13, color: '#94a3b8', lineHeight: 1.6 }}>
                    {evalResult.feedback}
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
