import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../services/api'
import ExecutiveCard from '../components/ExecutiveCard'
import InsightCard from '../components/InsightCard'
import { TrendingUp, AlertTriangle, Users, Activity } from 'lucide-react'

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [executives, setExecutives] = useState([])
  const [insights, setInsights] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/api/v1/executives'),
      api.get('/api/v1/briefing/insights'),
    ])
      .then(([execRes, insRes]) => {
        setExecutives(execRes.data)
        setInsights(insRes.data)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const criticalCount = insights.filter(i => i.priority === 'critical').length
  const highCount = insights.filter(i => i.priority === 'high').length
  const totalInsights = insights.length

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div>
        <h1 className="text-2xl font-bold text-white">
          Good {getGreeting()}, {user?.full_name?.split(' ')[0]}
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          Here's what your AI executive team has flagged today.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={Activity} label="Active Executives" value={executives.length} color="prism" />
        <StatCard icon={AlertTriangle} label="Critical Alerts" value={criticalCount} color="red" />
        <StatCard icon={TrendingUp} label="High Priority" value={highCount} color="orange" />
        <StatCard icon={Users} label="Total Insights" value={totalInsights} color="blue" />
      </div>

      {/* Top Insights */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-white">Top Insights</h2>
          <button
            onClick={() => navigate('/briefing')}
            className="text-xs text-prism-400 hover:text-prism-300 transition-colors"
          >
            View full briefing →
          </button>
        </div>
        {loading ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="card animate-pulse h-48 bg-gray-900" />
            ))}
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {insights.slice(0, 3).map(insight => (
              <InsightCard key={insight.id} insight={insight} />
            ))}
          </div>
        )}
      </section>

      {/* AI Executives */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-white">AI Executive Team</h2>
          <button
            onClick={() => navigate('/executives')}
            className="text-xs text-prism-400 hover:text-prism-300 transition-colors"
          >
            View all →
          </button>
        </div>
        {loading ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="card animate-pulse h-48 bg-gray-900" />
            ))}
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {executives.slice(0, 3).map(exec => (
              <ExecutiveCard
                key={exec.id}
                executive={exec}
                onClick={() => navigate('/executives')}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

function StatCard({ icon: Icon, label, value, color }) {
  const colorMap = {
    prism: 'text-prism-400 bg-prism-950/60',
    red: 'text-red-400 bg-red-950/60',
    orange: 'text-orange-400 bg-orange-950/60',
    blue: 'text-blue-400 bg-blue-950/60',
  }
  return (
    <div className="card border border-gray-800">
      <div className={`inline-flex p-2 rounded-lg mb-3 ${colorMap[color]}`}>
        <Icon size={18} className={colorMap[color].split(' ')[0]} />
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{label}</p>
    </div>
  )
}

function getGreeting() {
  const h = new Date().getHours()
  if (h < 12) return 'morning'
  if (h < 17) return 'afternoon'
  return 'evening'
}
