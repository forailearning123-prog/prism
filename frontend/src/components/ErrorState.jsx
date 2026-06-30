import React from 'react'
import { AlertTriangle } from 'lucide-react'

export default function ErrorState({ message }) {
  return (
    <div className="card border border-red-900 bg-red-950/20 p-6 flex flex-col items-center justify-center text-center">
      <AlertTriangle size={32} className="text-red-500 mb-3" />
      <h3 className="text-lg font-semibold text-red-400 mb-1">Failed to Load</h3>
      <p className="text-sm text-red-300/80">{message || "An unexpected error occurred while fetching data."}</p>
    </div>
  )
}
