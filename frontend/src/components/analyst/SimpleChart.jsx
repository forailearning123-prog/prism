import React from 'react'

function formatValue(v) {
  const value = Number(v) || 0
  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`
  if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`
  return value % 1 === 0 ? String(value) : value.toFixed(1)
}

function gradientId(title) {
  return `grad-${String(title || 'chart').replace(/[^a-zA-Z0-9_-]/g, '-')}`
}

function LineChart({ data, xKey, yKey, title, color = '#818cf8' }) {
  if (!data || data.length === 0) return null

  const width = 400
  const height = 160
  const padding = { top: 20, right: 20, bottom: 30, left: 45 }
  const values = data.map((d) => Number(d[yKey]) || 0)
  const minVal = Math.min(...values)
  const maxVal = Math.max(...values)
  const range = maxVal - minVal || 1
  const plotW = width - padding.left - padding.right
  const plotH = height - padding.top - padding.bottom
  const lastIndex = Math.max(data.length - 1, 1)
  const fillId = gradientId(title)

  const toX = (i) => padding.left + (i / lastIndex) * plotW
  const toY = (v) => padding.top + plotH - ((v - minVal) / range) * plotH

  const points = data.map((d, i) => `${toX(i)},${toY(Number(d[yKey]) || 0)}`).join(' ')
  const areaPoints = [
    `${padding.left},${padding.top + plotH}`,
    ...data.map((d, i) => `${toX(i)},${toY(Number(d[yKey]) || 0)}`),
    `${padding.left + plotW},${padding.top + plotH}`,
  ].join(' ')

  return (
    <div className="w-full">
      {title && <p className="text-xs text-gray-400 mb-2">{title}</p>}
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: '160px' }}>
        <defs>
          <linearGradient id={fillId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.3" />
            <stop offset="100%" stopColor={color} stopOpacity="0.02" />
          </linearGradient>
        </defs>
        <polygon points={areaPoints} fill={`url(#${fillId})`} />
        <polyline points={points} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        {data.map((d, i) => (
          <circle key={`${String(d[xKey])}-${i}`} cx={toX(i)} cy={toY(Number(d[yKey]) || 0)} r="3" fill={color} />
        ))}
        {data.map((d, i) => (
          <text
            key={`label-${String(d[xKey])}-${i}`}
            x={toX(i)}
            y={height - 5}
            textAnchor="middle"
            style={{ fontSize: '9px', fill: '#6b7280' }}
          >
            {String(d[xKey] ?? '').slice(0, 6)}
          </text>
        ))}
        <text x={padding.left - 5} y={padding.top + 4} textAnchor="end" style={{ fontSize: '9px', fill: '#6b7280' }}>{formatValue(maxVal)}</text>
        <text x={padding.left - 5} y={padding.top + plotH + 4} textAnchor="end" style={{ fontSize: '9px', fill: '#6b7280' }}>{formatValue(minVal)}</text>
      </svg>
    </div>
  )
}

function BarChart({ data, xKey, yKey, title, color = '#818cf8' }) {
  if (!data || data.length === 0) return null

  const width = 400
  const height = 160
  const padding = { top: 20, right: 20, bottom: 30, left: 45 }
  const plotW = width - padding.left - padding.right
  const plotH = height - padding.top - padding.bottom
  const values = data.map((d) => Number(d[yKey]) || 0)
  const maxVal = Math.max(...values) || 1
  const barW = Math.max(4, (plotW / data.length) * 0.7)
  const gap = plotW / data.length

  return (
    <div className="w-full">
      {title && <p className="text-xs text-gray-400 mb-2">{title}</p>}
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: '160px' }}>
        {data.map((d, i) => {
          const val = Number(d[yKey]) || 0
          const barH = (val / maxVal) * plotH
          const x = padding.left + i * gap + (gap - barW) / 2
          const y = padding.top + plotH - barH

          return (
            <g key={`${String(d[xKey])}-${i}`}>
              <rect x={x} y={y} width={barW} height={barH} rx="2" fill={color} fillOpacity="0.8" />
              <text x={x + barW / 2} y={height - 5} textAnchor="middle" style={{ fontSize: '9px', fill: '#6b7280' }}>
                {String(d[xKey] ?? '').slice(0, 5)}
              </text>
            </g>
          )
        })}
        <text x={padding.left - 5} y={padding.top + 4} textAnchor="end" style={{ fontSize: '9px', fill: '#6b7280' }}>{formatValue(maxVal)}</text>
      </svg>
    </div>
  )
}

function KpiCard({ title, value, trend }) {
  const trendIcon = trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'
  const trendColor = trend === 'up' ? 'text-emerald-400' : trend === 'down' ? 'text-red-400' : 'text-gray-400'

  return (
    <div className="bg-gray-800/60 rounded-lg p-4 border border-gray-700">
      <p className="text-xs text-gray-400 mb-1">{title}</p>
      <div className="flex items-end gap-2">
        <span className="text-2xl font-bold text-white">{value}</span>
        <span className={`text-sm font-medium mb-0.5 ${trendColor}`}>{trendIcon}</span>
      </div>
    </div>
  )
}

export default function SimpleChart({ visualization }) {
  if (!visualization) return null

  const { type, title, data, x_key, y_key, value, trend } = visualization

  if (type === 'kpi_card') {
    return <KpiCard title={title} value={value} trend={trend} />
  }

  if (type === 'bar_chart') {
    return <BarChart data={data} xKey={x_key || 'period'} yKey={y_key || 'value'} title={title} />
  }

  return <LineChart data={data} xKey={x_key || 'period'} yKey={y_key || 'value'} title={title} />
}
