import React, { useEffect, useState } from 'react'
import api from '../services/api'
import { Calendar, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'

const healthColors = {
  Healthy: { bar: 'bg-green-500', text: 'text-green-400', bg: 'bg-green-950/30 border-green-800' },
  Caution: { bar: 'bg-yellow-500', text: 'text-yellow-400', bg: 'bg-yellow-950/30 border-yellow-800' },
  Critical: { bar: 'bg-red-500', text: 'text-red-400', bg: 'bg-red-950/30 border-red-800' },
}

const categoryColors = {
  Revenue: 'bg-blue-900/50 text-blue-300',
  Inventory: 'bg-orange-900/50 text-orange-300',
  'Cash Flow': 'bg-red-900/50 text-red-300',
  Customers: 'bg-purple-900/50 text-purple-300',
  Marketing: 'bg-pink-900/50 text-pink-300',
  HR: 'bg-green-900/50 text-green-300',
}

export default function Briefing() {
  const [briefing, setBriefing] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/api/v1/briefing/daily')
      .then(res => setBriefing(res.data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <LoadingState count={4} height="h-32" />
  }

  if (error) {
    return <ErrorState message={`Failed to load briefing: ${error}`} />
  }

  const health = healthColors[briefing.overall_health] || healthColors.Caution

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
          <Calendar size={14} />
          <span>{briefing.date}</span>
        </div>
        <h1 className="text-2xl font-bold text-white">Daily Intelligence Briefing</h1>
        <p className="text-gray-500 text-sm mt-1">{briefing.company}</p>
      </div>

      {/* Health Score */}
      <div className={`card border ${health.bg}`}>
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-xs text-gray-500 mb-0.5">Business Health Score</p>
            <p className={`text-3xl font-bold ${health.text}`}>{briefing.health_score}</p>
          </div>
          <div className="text-right">
            <span className={`badge ${health.bg} ${health.text} text-sm px-3 py-1`}>
              {briefing.overall_health}
            </span>
          </div>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-2">
          <div
            className={`${health.bar} h-2 rounded-full transition-all`}
            style={{ width: `${briefing.health_score}%` }}
          />
        </div>
        <p className="text-sm text-gray-400 mt-3 font-medium">{briefing.top_priority}</p>
      </div>

      {/* Items */}
      <div className="space-y-4">
        {briefing.items.map((item, idx) => (
          <BriefingItemCard key={idx} item={item} />
        ))}
      </div>
    </div>
  )
}

function BriefingItemCard({ item }) {
  const categoryColor = categoryColors[item.category] || 'bg-gray-800 text-gray-400'

  return (
    <div className="card border border-gray-800 hover:border-gray-700 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <span className={`badge ${categoryColor}`}>{item.category}</span>
        {item.probability && (
          <span className="text-xs text-gray-500 flex items-center gap-1">
            <TrendingUp size={11} />
            {item.probability}% probability
          </span>
        )}
      </div>

      <h3 className="font-semibold text-white mb-2">{item.title}</h3>
      <p className="text-sm text-gray-400 mb-3">{item.detail}</p>

      {item.impact && (
        <div className="flex items-start gap-2 mb-2">
          <AlertTriangle size={13} className="text-orange-400 mt-0.5 shrink-0" />
          <p className="text-sm text-orange-300">{item.impact}</p>
        </div>
      )}

      {item.recommendation && (
        <div className="flex items-start gap-2 pt-3 border-t border-gray-800">
          <CheckCircle size={13} className="text-prism-400 mt-0.5 shrink-0" />
          <p className="text-sm text-prism-300">{item.recommendation}</p>
        </div>
      )}
    </div>
  )
}
