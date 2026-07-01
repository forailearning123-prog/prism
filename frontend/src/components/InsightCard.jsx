import React from 'react'

export default function InsightCard({ insight }) {
  return (
    <article className="card border border-gray-800" role="article">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-400">{insight?.category || 'General'}</span>
        <span className="badge bg-gray-800 text-gray-200">{insight?.priority || 'normal'}</span>
      </div>
      <h3 className="font-semibold mb-1">{insight?.title || 'Insight'}</h3>
      <p className="text-sm text-gray-400">{insight?.summary || 'No summary available.'}</p>
    </article>
  )
}
