import React from 'react'
import { AlertTriangle, AlertCircle, Info, TrendingUp } from 'lucide-react'

const priorityConfig = {
  critical: { badge: 'bg-red-900/60 text-red-300', icon: AlertTriangle, iconColor: 'text-red-400' },
  high: { badge: 'bg-orange-900/60 text-orange-300', icon: AlertCircle, iconColor: 'text-orange-400' },
  medium: { badge: 'bg-yellow-900/60 text-yellow-300', icon: AlertCircle, iconColor: 'text-yellow-400' },
  low: { badge: 'bg-green-900/60 text-green-300', icon: Info, iconColor: 'text-green-400' },
}

export default function InsightCard({ insight }) {
  const {
    executive_title,
    category,
    priority,
    title,
    summary,
    impact,
    recommendation,
    confidence,
  } = insight

  const config = priorityConfig[priority] || priorityConfig.low
  const Icon = config.icon

  return (
    <div className="card border border-gray-800 hover:border-gray-700 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <Icon size={15} className={config.iconColor} />
          <span className="text-xs text-gray-500">{executive_title} · {category}</span>
        </div>
        <span className={`badge ${config.badge}`}>{priority}</span>
      </div>

      <h4 className="font-medium text-white text-sm mb-2">{title}</h4>
      <p className="text-xs text-gray-400 mb-3">{summary}</p>

      {impact && (
        <div className="flex items-start gap-2 mb-2 text-xs">
          <span className="text-gray-600 shrink-0">Impact:</span>
          <span className="text-gray-300">{impact}</span>
        </div>
      )}

      {recommendation && (
        <div className="flex items-start gap-2 mb-3 text-xs">
          <span className="text-gray-600 shrink-0">Action:</span>
          <span className="text-prism-300">{recommendation}</span>
        </div>
      )}

      <div className="flex items-center gap-2 pt-3 border-t border-gray-800">
        <div className="flex-1 bg-gray-800 rounded-full h-1.5">
          <div
            className="bg-prism-500 h-1.5 rounded-full"
            style={{ width: `${confidence}%` }}
          />
        </div>
        <span className="text-xs text-gray-500 shrink-0 flex items-center gap-1">
          <TrendingUp size={11} />
          {confidence}% confidence
        </span>
      </div>
    </div>
  )
}
