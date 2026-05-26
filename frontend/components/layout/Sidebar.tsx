'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Bot,
  ChartBar,
  GitBranch,
  LayoutDashboard,
  Play,
  Shapes,
} from 'lucide-react'

const nav = [
  { href: '/',          label: 'Dashboard',  icon: LayoutDashboard },
  { href: '/agents',    label: 'Agents',     icon: Bot },
  { href: '/workflows', label: 'Workflows',  icon: GitBranch },
  { href: '/runs',      label: 'Runs',       icon: Play },
  { href: '/templates', label: 'Templates',  icon: Shapes },
  { href: '/evals',     label: 'Evals',      icon: ChartBar },
]

export default function Sidebar() {
  const path = usePathname()

  return (
    <aside style={{ width: 220, minHeight: '100vh', background: '#090d1a', borderRight: '1px solid #1e2d4a', display: 'flex', flexDirection: 'column', padding: '24px 0' }}>
      {/* Logo */}
      <div style={{ padding: '0 20px 32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, fontWeight: 700 }}>A</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 16, color: '#f1f5f9' }}>Anton</div>
            <div style={{ fontSize: 11, color: '#475569' }}>AI Orchestration</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '0 12px', display: 'flex', flexDirection: 'column', gap: 2 }}>
        {nav.map(({ href, label, icon: Icon }) => {
          const active = href === '/' ? path === '/' : path.startsWith(href)
          return (
            <Link
              key={href}
              href={href}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '9px 12px',
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 500,
                textDecoration: 'none',
                color: active ? '#f1f5f9' : '#64748b',
                background: active ? '#1e2d4a' : 'transparent',
                transition: 'all 0.15s',
              }}
            >
              <Icon size={16} style={{ color: active ? '#6366f1' : '#64748b' }} />
              {label}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div style={{ padding: '16px 20px', borderTop: '1px solid #1e2d4a', marginTop: 'auto' }}>
        <div style={{ fontSize: 12, color: '#334155' }}>v0.1.0 · Built with LangGraph</div>
      </div>
    </aside>
  )
}
