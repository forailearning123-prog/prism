import React, { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api from '../services/api'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'

export default function DataSourceDetails() {
  const navigate = useNavigate()
  const { sourceId } = useParams()
  const [data, setData] = useState(null)
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [detailsRes, healthRes] = await Promise.all([
        api.get(`/api/v1/connections/${sourceId}`),
        api.get(`/api/v1/connections/${sourceId}/health`),
      ])
      setData(detailsRes.data)
      setHealth(healthRes.data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [sourceId])

  useEffect(() => {
    load()
  }, [load])

  if (loading) return <LoadingState count={4} height="h-40" />
  if (error) return <ErrorState message={error} />
  if (!data) return null

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <button className="btn-secondary" onClick={() => navigate('/connections')}>
          Back
        </button>
        <h1 className="text-2xl font-bold">{data.name}</h1>
        <span className="badge bg-gray-800 text-gray-200">{data.status}</span>
      </div>

      <section className="card">
        <h2 className="text-lg font-semibold mb-3">Overview</h2>
        <div className="grid md:grid-cols-3 gap-3 text-sm">
          <div>Type: {data.source_type}</div>
          <div>Owner: {data.owner}</div>
          <div>Created: {new Date(data.created_at).toLocaleString()}</div>
          <div>Last Sync: {data.last_sync_at ? new Date(data.last_sync_at).toLocaleString() : '-'}</div>
          <div>Last Successful Refresh: {data.last_successful_refresh_at ? new Date(data.last_successful_refresh_at).toLocaleString() : '-'}</div>
          <div>Usage Count: {data.usage_count}</div>
        </div>
      </section>

      <section className="card">
        <h2 className="text-lg font-semibold mb-3">Connection Information</h2>
        <div className="grid md:grid-cols-2 gap-3 text-sm">
          <div>Host: {data.host || '-'}</div>
          <div>Port: {data.port || '-'}</div>
          <div>Database: {data.database_name || '-'}</div>
          <div>Base URL: {data.base_url || '-'}</div>
          <div>Authentication: {data.authentication_type || '-'}</div>
          <div>Schedule: {data.schedule || '-'}</div>
        </div>
        <p className="text-xs text-gray-400 mt-3">Credentials are encrypted and hidden for security.</p>
      </section>

      <section className="card">
        <h2 className="text-lg font-semibold mb-3">Health Status</h2>
        <div className="text-sm">
          <div>Status: {health?.status || data.status}</div>
          <div className="text-gray-400 mt-1">{health?.reason || 'Health status available.'}</div>
        </div>
      </section>

      <section className="card">
        <h2 className="text-lg font-semibold mb-3">Tables & Columns</h2>
        {data.metadata?.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left border-b border-gray-800 text-gray-400">
                  <th className="py-2 pr-3">Object</th>
                  <th className="py-2 pr-3">Column</th>
                  <th className="py-2 pr-3">Type</th>
                  <th className="py-2 pr-3">Sample</th>
                </tr>
              </thead>
              <tbody>
                {data.metadata.map((col, idx) => (
                  <tr key={`${col.object_name}-${col.column_name}-${idx}`} className="border-b border-gray-900">
                    <td className="py-2 pr-3">{col.object_name}</td>
                    <td className="py-2 pr-3">{col.column_name}</td>
                    <td className="py-2 pr-3">{col.data_type}</td>
                    <td className="py-2 pr-3">{col.sample_value || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-gray-400">No metadata available.</p>
        )}
      </section>

      <section className="card">
        <h2 className="text-lg font-semibold mb-3">Recent Syncs</h2>
        {(data.recent_syncs || []).length ? (
          <div className="space-y-2 text-sm">
            {data.recent_syncs.map((sync) => (
              <div key={sync.id} className="border border-gray-800 rounded-lg px-3 py-2 flex justify-between">
                <span>{sync.result}</span>
                <span>{sync.message}</span>
                <span>{sync.duration_ms}ms</span>
                <span>{new Date(sync.created_at).toLocaleString()}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">No sync history found.</p>
        )}
      </section>

      <section className="card">
        <h2 className="text-lg font-semibold mb-3">Connection Logs</h2>
        {(data.logs || []).length ? (
          <div className="space-y-2 text-sm">
            {data.logs.map((log) => (
              <div key={log.id} className="border border-gray-800 rounded-lg px-3 py-2">
                <div className="flex justify-between">
                  <span>{log.action}</span>
                  <span>{log.result}</span>
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  Duration: {log.duration_ms}ms · User: {log.user_id || '-'} · {new Date(log.created_at).toLocaleString()}
                </div>
                {log.error_message && <div className="text-xs text-red-300 mt-1">{log.error_message}</div>}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">No logs found.</p>
        )}
      </section>

      <section className="card">
        <h2 className="text-lg font-semibold mb-2">Future AI Recommendations</h2>
        <p className="text-sm text-gray-400">No recommendations yet.</p>
      </section>
    </div>
  )
}
