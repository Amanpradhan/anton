'use client'

import { useCallback } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
  addEdge,
  type Node,
  type Edge,
  type Connection,
  MarkerType,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import type { WorkflowNode, WorkflowEdge } from '@/types'

const AGENT_COLORS: Record<string, string> = {
  orchestrator: '#6366f1',
  researcher:   '#06b6d4',
  analyst:      '#8b5cf6',
  critic:       '#f59e0b',
  reporter:     '#10b981',
  evaluator:    '#ec4899',
}

function AgentNode({ data }: { data: { label: string; role: string; color: string } }) {
  return (
    <div style={{
      background: '#0f1629',
      border: `2px solid ${data.color}`,
      borderRadius: 12,
      padding: '12px 18px',
      minWidth: 160,
      boxShadow: `0 0 20px ${data.color}33`,
    }}>
      <Handle type="target" position={Position.Top} style={{ background: data.color, border: 'none', width: 8, height: 8 }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: data.color }} />
        <div style={{ fontWeight: 600, fontSize: 14, color: '#f1f5f9' }}>{data.label}</div>
      </div>
      <div style={{ fontSize: 11, color: '#64748b', lineHeight: 1.4 }}>{data.role}</div>
      <Handle type="source" position={Position.Bottom} style={{ background: data.color, border: 'none', width: 8, height: 8 }} />
    </div>
  )
}

const nodeTypes = { agentNode: AgentNode }

function toFlowNodes(nodes: WorkflowNode[]): Node[] {
  const positions: Record<string, { x: number; y: number }> = {
    orchestrator: { x: 300, y: 0 },
    researcher:   { x: 300, y: 140 },
    analyst:      { x: 300, y: 280 },
    critic:       { x: 300, y: 420 },
    reporter:     { x: 300, y: 560 },
    evaluator:    { x: 580, y: 560 },
  }

  return nodes.map((n, i) => ({
    id: n.id,
    type: 'agentNode',
    position: positions[n.id.toLowerCase()] || { x: 100 + i * 200, y: i * 140 },
    data: {
      label: n.label,
      role: n.role,
      color: AGENT_COLORS[n.id.toLowerCase()] || '#6366f1',
    },
  }))
}

function toFlowEdges(edges: WorkflowEdge[]): Edge[] {
  return edges.map((e, i) => ({
    id: `e-${i}`,
    source: e.source,
    target: e.target,
    label: e.label || undefined,
    labelStyle: { fill: '#94a3b8', fontSize: 11 },
    labelBgStyle: { fill: '#0f1629', fillOpacity: 0.9 },
    style: {
      stroke: e.label?.includes('reject') || e.label?.includes('if') ? '#f59e0b' : '#334155',
      strokeWidth: 1.5,
    },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#334155' },
    animated: e.label?.includes('reject') || e.label?.includes('if'),
  }))
}

interface Props {
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  readonly?: boolean
}

export default function FlowCanvas({ nodes: wfNodes, edges: wfEdges, readonly = false }: Props) {
  const [nodes, , onNodesChange] = useNodesState(toFlowNodes(wfNodes))
  const [edges, setEdges, onEdgesChange] = useEdgesState(toFlowEdges(wfEdges))

  const onConnect = useCallback(
    (connection: Connection) => setEdges(eds => addEdge(connection, eds)),
    [setEdges]
  )

  return (
    <div style={{ width: '100%', height: '100%', borderRadius: 12, overflow: 'hidden', background: '#080b14' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={readonly ? undefined : onNodesChange}
        onEdgesChange={readonly ? undefined : onEdgesChange}
        onConnect={readonly ? undefined : onConnect}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        nodesDraggable={!readonly}
        nodesConnectable={!readonly}
        elementsSelectable={!readonly}
      >
        <Background color="#1e2d4a" gap={24} />
        <Controls style={{ background: '#0f1629', border: '1px solid #1e2d4a' }} />
        <MiniMap
          style={{ background: '#0f1629', border: '1px solid #1e2d4a' }}
          nodeColor={n => AGENT_COLORS[(n.id as string).toLowerCase()] || '#334155'}
        />
      </ReactFlow>
    </div>
  )
}
