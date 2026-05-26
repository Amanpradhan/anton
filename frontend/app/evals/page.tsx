'use client'

import { useEffect, useState } from 'react'
import { ChartBar, Play } from 'lucide-react'
import { api } from '@/lib/api'
import type { EvalResult, EvalAggregate } from '@/types'

function ScoreBar({ score }: { score: number }) {
  const pct = (score / 10) * 100
  const color = score >= 7 ? '#10b981' : score >= 5 ? '#f59e0b' : '#f87171'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ flex: 1, height: 6, background: '#1e2d4a', borderRadius: 3 }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 3 }} />
      </div>
      <span style={{ fontSize: 12, color, fontWeight: 600, width: 32, textAlign: 'right' }}>{score.toFixed(1)}</span>
    </div>
  )
}

export default function EvalsPage() {
  const [results, setResults] = useState<EvalResult[]>([])
  const [aggregate, setAggregate] = useState<EvalAggregate | null>(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)

  const fetchResults = () => {
    api.get<{ results: EvalResult[]; aggregate: EvalAggregate | null }>('/api/evals/results')
      .then(data => { setResults(data.results); setAggregate(data.aggregate) })
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchResults() }, [])

  const handleRunBatch = async () => {
    setRunning(true)
    try {
      await api.post('/api/evals/run')
      setTimeout(fetchResults, 2000) // give pipeline a moment to start
    } catch {
      alert('Failed to start batch eval')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: '#f1f5f9', marginBottom: 6 }}>Evaluations</h1>
          <p style={{ color: '#64748b', fontSize: 15 }}>LLM-as-judge quality scores across pipeline runs</p>
        </div>
        <button className="btn-primary" onClick={handleRunBatch} disabled={running}>
          <Play size={14} /> {running ? 'Running 5 test cases...' : 'Run Batch Eval'}
        </button>
      </div>

      {/* Aggregate stats */}
      {aggregate && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 28 }}>
          {[
            { label: 'Avg Score', value: `${aggregate.avg_overall_score}/10`, color: aggregate.avg_overall_score >= 7 ? '#10b981' : '#f59e0b' },
            { label: 'Pass Rate', value: `${aggregate.pass_rate_pct}%`, color: '#6366f1' },
            { label: 'Passed', value: aggregate.passed, color: '#10b981' },
            { label: 'Failed', value: aggregate.failed, color: '#f87171' },
          ].map(({ label, value, color }) => (
            <div key={label} className="card" style={{ padding: 20 }}>
              <div style={{ fontSize: 12, color: '#64748b', marginBottom: 6 }}>{label}</div>
              <div style={{ fontSize: 28, fontWeight: 700, color }}>{value}</div>
            </div>
          ))}
        </div>
      )}

      {loading ? (
        <div style={{ color: '#64748b' }}>Loading...</div>
      ) : results.length === 0 ? (
        <div className="card" style={{ padding: 48, textAlign: 'center' }}>
          <ChartBar size={40} style={{ color: '#334155', margin: '0 auto 16px' }} />
          <div style={{ color: '#64748b', marginBottom: 16 }}>No eval results yet</div>
          <p style={{ fontSize: 13, color: '#475569', maxWidth: 400, margin: '0 auto 20px' }}>
            Evals run automatically after each pipeline completes, or trigger a batch of 5 test cases above.
          </p>
          <button className="btn-primary" onClick={handleRunBatch} disabled={running}>
            <Play size={14} /> Run Batch Eval
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {results.map((r, i) => (
            <div key={i} className="card" style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
                <div>
                  <div style={{ fontSize: 12, color: '#475569', marginBottom: 4 }}>Run {r.run_id.slice(0, 8)}...</div>
                  <span className={`badge ${r.passed ? 'badge-green' : 'badge-red'}`}>
                    {r.passed ? 'PASSED' : 'FAILED'}
                  </span>
                </div>
                <div style={{ fontSize: 28, fontWeight: 700, color: r.passed ? '#10b981' : '#f87171' }}>
                  {r.overall_score.toFixed(1)}<span style={{ fontSize: 14, color: '#475569' }}>/10</span>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
                <div><div style={{ fontSize: 11, color: '#475569', marginBottom: 4 }}>Specificity</div><ScoreBar score={r.specificity_score} /></div>
                <div><div style={{ fontSize: 11, color: '#475569', marginBottom: 4 }}>Completeness</div><ScoreBar score={r.completeness_score} /></div>
                <div><div style={{ fontSize: 11, color: '#475569', marginBottom: 4 }}>Accuracy Risk</div><ScoreBar score={r.accuracy_risk_score} /></div>
                <div><div style={{ fontSize: 11, color: '#475569', marginBottom: 4 }}>Usefulness</div><ScoreBar score={r.usefulness_score} /></div>
              </div>

              {r.feedback && (
                <div style={{ fontSize: 12, color: '#64748b', padding: '10px 12px', background: '#0a0f1e', borderRadius: 6, lineHeight: 1.5 }}>
                  {r.feedback}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
