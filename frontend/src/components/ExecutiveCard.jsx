import React from 'react'
import { AlertTriangle, AlertCircle, Info, TrendingDown } from 'lucide-react'

const riskColors = {
  high: 'border-red-800 bg-red-950/30',
  medium: 'border-yellow-800 bg-yellow-950/20',
  low: 'border-green-800 bg-green-950/20',
}

const riskBadge = {
  high: 'bg-red-900/60 text-red-300',
  medium: 'bg-yellow-900/60 text-yellow-300',
  low: 'bg-green-900/60 text-green-300',
}

const RiskIcon = ({ level }) => {
  if (level === 'high') return <AlertTriangle size={14} className="text-red-400" />
  if (level === 'medium') return <AlertCircle size={14} className="text-yellow-400" />
  return <Info size={14} className="text-green-400" />
}

export default function ExecutiveCard({ executive, onClick }) {
  const { title, role, description, focus_areas, status, insights_count, risk_level } = executive

  return (
    <div
      onClick={onClick}
      className={`card border cursor-pointer hover:border-prism-700 transition-all hover:shadow-lg hover:shadow-prism-950/50 ${riskColors[risk_level] || riskColors.low}`}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-white text-base">{title}</h3>
          <p className="text-xs text-gray-500 mt-0.5">{role}</p>
        </div>
        <span className={`badge ${riskBadge[risk_level] || riskBadge.low} flex items-center gap-1`}>
          <RiskIcon level={risk_level} />
          {risk_level} risk
        </span>
      </div>

      <p className="text-sm text-gray-400 mb-4 line-clamp-2">{description}</p>

      <div className="flex flex-wrap gap-1.5 mb-4">
        {focus_areas.map(area => (
          <span key={area} className="badge bg-gray-800 text-gray-400">
            {area}
          </span>
        ))}
      </div>

      <div className="flex items-center justify-between pt-3 border-t border-gray-800">
        <span className="text-xs text-gray-500 flex items-center gap-1.5">
          <TrendingDown size={12} className="text-prism-400" />
          <span className="text-prism-400 font-medium">{insights_count}</span> active insights
        </span>
        <span className={`text-xs font-medium ${status === 'active' ? 'text-green-400' : 'text-gray-500'}`}>
          ● {status}
        </span>
      </div>
    </div>
  )
}
