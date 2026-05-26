export interface Agent {
  id: string
  name: string
  role: string
  system_prompt: string
  model: string
  temperature: number
  tools: string[]
  channels: string[]
  memory_enabled: boolean
  memory_window: number
  max_tokens: number
  max_iterations: number
  schedule: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface WorkflowNode {
  id: string
  label: string
  role: string
}

export interface WorkflowEdge {
  source: string
  target: string
  label: string
}

export interface Workflow {
  id: string
  name: string
  description: string | null
  graph: { nodes: WorkflowNode[]; edges: WorkflowEdge[] }
  trigger_channel: string | null
  is_template: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  run_id: string
  sender: string
  recipient: string
  content: string
  message_type: string
  tokens_used: number
  created_at: string
}

export interface Run {
  id: string
  workflow_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  input: string | null
  trigger_source: string
  trigger_id: string | null
  output: string | null
  error: string | null
  total_tokens: number
  estimated_cost_usd: number
  started_at: string | null
  completed_at: string | null
  created_at: string
  messages: Message[]
}

export interface RunEvent {
  run_id: string
  agent: string
  event_type: string
  content: string
  tokens_used: number
  timestamp: string
}

export interface EvalResult {
  run_id: string
  overall_score: number
  specificity_score: number
  completeness_score: number
  accuracy_risk_score: number
  usefulness_score: number
  passed: boolean
  feedback: string
  created_at: string
}

export interface EvalAggregate {
  total_runs: number
  avg_overall_score: number
  pass_rate_pct: number
  passed: number
  failed: number
}

export interface Template {
  id: string
  name: string
  description: string
  example_prompt: string
  graph: { nodes: WorkflowNode[]; edges: WorkflowEdge[] }
}
