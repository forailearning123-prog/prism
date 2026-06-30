import React from 'react'

export default function LoadingState({ count = 3, height = 'h-48' }) {
  return (
    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
      {[...Array(count)].map((_, i) => (
        <div key={i} className={`card animate-pulse ${height} bg-gray-900`} />
      ))}
    </div>
  )
}
