import React from 'react'

export default function ExecutiveCard({ executive, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={executive?.title || 'Executive'}
      className="card text-left w-full hover:border-prism-700 transition-colors"
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold">{executive?.title || 'Executive'}</h3>
        <span className="badge bg-gray-800 text-gray-200">{executive?.status || 'active'}</span>
      </div>
      <p className="text-sm text-gray-400 mb-2">{executive?.role || '-'}</p>
      <p className="text-xs text-gray-500">{executive?.description || 'No description available.'}</p>
    </button>
  )
}
