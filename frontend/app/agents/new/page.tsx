'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'

const AVAILABLE_TOOLS = ['web_search', 'summarize', 'calculator', 'code_interpreter']
const AVAILABLE_CHANNELS = ['telegram', 'slack', 'whatsapp']
const MODELS = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash', 'gemini-1.5-flash']

export default function NewAgentPage() {
  const router = useRouter()
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    name: '',
    role: '',
    system_prompt: '',
    model: 'gemini-2.5-flash',
    temperature: 0.7,
    tools: [] as string[],
    channels: [] as string[],
    memory_enabled: true,
    memory_window: 10,
    max_tokens: 2048,
    max_iterations: 10,
    schedule: '',
  })

  const toggle = (field: 'tools' | 'channels', value: string) => {
    setForm(prev => ({
      ...prev,
      [field]: prev[field].includes(value)
        ? prev[field].filter(v => v !== value)
        : [...prev[field], value],
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.post('/api/agents/', { ...form, schedule: form.schedule || null })
      router.push('/agents')
    } catch (err) {
      alert('Failed to create agent')
      setSaving(false)
    }
  }

  return (
    <div style={{ maxWidth: 640 }}>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: '#f1f5f9', marginBottom: 6 }}>New Agent</h1>
        <p style={{ color: '#64748b', fontSize: 15 }}>Configure a new AI agent for your workflows</p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="card" style={{ padding: 28, display: 'flex', flexDirection: 'column', gap: 20 }}>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div>
              <label>Name *</label>
              <input value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} placeholder="e.g. Researcher" required />
            </div>
            <div>
              <label>Role *</label>
              <input value={form.role} onChange={e => setForm(p => ({ ...p, role: e.target.value }))} placeholder="e.g. Web Research Specialist" required />
            </div>
          </div>

          <div>
            <label>System Prompt *</label>
            <textarea
              value={form.system_prompt}
              onChange={e => setForm(p => ({ ...p, system_prompt: e.target.value }))}
              placeholder="Describe how this agent should behave, its personality, and its responsibilities..."
              rows={5}
              required
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div>
              <label>Model</label>
              <select value={form.model} onChange={e => setForm(p => ({ ...p, model: e.target.value }))}>
                {MODELS.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            <div>
              <label>Temperature ({form.temperature})</label>
              <input type="range" min={0} max={2} step={0.1} value={form.temperature}
                onChange={e => setForm(p => ({ ...p, temperature: parseFloat(e.target.value) }))}
                style={{ padding: 0, marginTop: 10 }}
              />
            </div>
          </div>

          <div>
            <label>Tools</label>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 4 }}>
              {AVAILABLE_TOOLS.map(t => (
                <button key={t} type="button" onClick={() => toggle('tools', t)}
                  style={{ padding: '6px 12px', borderRadius: 6, fontSize: 13, cursor: 'pointer', border: '1px solid', borderColor: form.tools.includes(t) ? '#6366f1' : '#1e2d4a', background: form.tools.includes(t) ? '#6366f122' : 'transparent', color: form.tools.includes(t) ? '#a5b4fc' : '#64748b', transition: 'all 0.15s' }}>
                  {t}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label>Channels</label>
            <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
              {AVAILABLE_CHANNELS.map(c => (
                <button key={c} type="button" onClick={() => toggle('channels', c)}
                  style={{ padding: '6px 12px', borderRadius: 6, fontSize: 13, cursor: 'pointer', border: '1px solid', borderColor: form.channels.includes(c) ? '#06b6d4' : '#1e2d4a', background: form.channels.includes(c) ? '#06b6d422' : 'transparent', color: form.channels.includes(c) ? '#67e8f9' : '#64748b', transition: 'all 0.15s' }}>
                  {c}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
            <div>
              <label>Max Tokens</label>
              <input type="number" value={form.max_tokens} onChange={e => setForm(p => ({ ...p, max_tokens: parseInt(e.target.value) }))} min={256} max={32768} />
            </div>
            <div>
              <label>Max Iterations</label>
              <input type="number" value={form.max_iterations} onChange={e => setForm(p => ({ ...p, max_iterations: parseInt(e.target.value) }))} min={1} max={50} />
            </div>
            <div>
              <label>Memory Window</label>
              <input type="number" value={form.memory_window} onChange={e => setForm(p => ({ ...p, memory_window: parseInt(e.target.value) }))} min={1} max={100} disabled={!form.memory_enabled} />
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button
              type="button"
              onClick={() => setForm(p => ({ ...p, memory_enabled: !p.memory_enabled }))}
              style={{
                width: 40, height: 22, borderRadius: 11, border: 'none', cursor: 'pointer',
                background: form.memory_enabled ? '#6366f1' : '#1e2d4a',
                position: 'relative', transition: 'background 0.2s', flexShrink: 0,
              }}
            >
              <span style={{
                position: 'absolute', top: 3, left: form.memory_enabled ? 21 : 3,
                width: 16, height: 16, borderRadius: '50%', background: '#fff',
                transition: 'left 0.2s',
              }} />
            </button>
            <div>
              <div style={{ fontSize: 14, color: '#f1f5f9', fontWeight: 500 }}>Memory</div>
              <div style={{ fontSize: 12, color: '#475569' }}>
                {form.memory_enabled ? `Retain last ${form.memory_window} messages across turns` : 'Disabled — agent has no context between turns'}
              </div>
            </div>
          </div>

          <div>
            <label>Schedule (cron, optional)</label>
            <input value={form.schedule} onChange={e => setForm(p => ({ ...p, schedule: e.target.value }))} placeholder="e.g. 0 9 * * 1 (every Monday at 9am)" />
          </div>

          <div style={{ display: 'flex', gap: 10, paddingTop: 8, borderTop: '1px solid #1e2d4a' }}>
            <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Creating...' : 'Create Agent'}</button>
            <button type="button" className="btn-ghost" onClick={() => router.push('/agents')}>Cancel</button>
          </div>
        </div>
      </form>
    </div>
  )
}
