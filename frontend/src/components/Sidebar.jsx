import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Newspaper,
  Users,
  Settings,
  Zap,
  Database,
  Layers,
  BrainCircuit,
  TrendingUp,
  Activity,
  MessageSquare,
} from 'lucide-react'

const nav = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/briefing', icon: Newspaper, label: 'Daily Briefing' },
  { to: '/analyst', icon: BrainCircuit, label: 'AI Analyst' },
  { to: '/executives', icon: Users, label: 'AI Executives' },
  { to: '/monitoring', icon: Activity, label: 'Monitoring' },
  { to: '/collaboration', icon: MessageSquare, label: 'Collaboration' },
  { to: '/connections', icon: Database, label: 'Data Sources' },
  { to: '/semantic-models', icon: Layers, label: 'Semantic Models' },
  { to: '/forecasting', icon: TrendingUp, label: 'Forecasting' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  return (
    <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
      {/* Logo */}
      <div className="flex items-center gap-2 px-5 py-4 border-b border-gray-800">
        <div className="w-8 h-8 bg-prism-600 rounded-lg flex items-center justify-center">
          <Zap size={18} className="text-white" />
        </div>
        <span className="text-lg font-bold text-white tracking-tight">Prism</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-prism-900/60 text-prism-300 border border-prism-800'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-gray-800">
        <p className="text-xs text-gray-600">Prism v0.1.0 · Community Edition</p>
      </div>
    </aside>
  )
}
