import React, { useEffect, useState } from 'react'
import api from '../services/api'
import ExecutiveCard from '../components/ExecutiveCard'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'

export default function Executives() {
  const [executives, setExecutives] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/api/v1/executives')
      .then(res => setExecutives(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">AI Executive Team</h1>
        <p className="text-gray-500 text-sm mt-1">
          Your 24×7 AI counterparts monitoring every area of your business.
        </p>
      </div>

      {loading ? (
        <LoadingState count={6} height="h-52" />
      ) : error ? (
        <ErrorState message={error} />
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {executives.map(exec => (
            <ExecutiveCard key={exec.id} executive={exec} />
          ))}
        </div>
      )}
    </div>
  )
}
