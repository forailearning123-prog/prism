import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'

const initialForm = {
  name: '',
  source_type: 'postgresql',
  description: '',
  schedule: '',
  tags: '',
  host: '',
  port: '',
  username: '',
  password: '',
  database_name: '',
  base_url: '',
  authentication_type: 'none',
  headers: '{}',
  file_name: '',
  file_content_base64: '',
}

function encodeFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = String(reader.result || '')
      const payload = result.includes(',') ? result.split(',')[1] : result
      resolve(payload)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

export default function Connections() {
  const navigate = useNavigate()
  const [sources, setSources] = useState([])
  const [connectors, setConnectors] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState('desc')
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [total, setTotal] = useState(0)
  const [showWizard, setShowWizard] = useState(false)
  const [wizardStep, setWizardStep] = useState(1)
  const [wizardMode, setWizardMode] = useState('create')
  const [editingSource, setEditingSource] = useState(null)
  const [form, setForm] = useState(initialForm)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState(null)
  const [previewData, setPreviewData] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / pageSize)), [total, pageSize])

  const loadData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [sourcesRes, connectorsRes] = await Promise.all([
        api.get('/api/v1/connections', {
          params: {
            search: search || undefined,
            status: statusFilter || undefined,
            source_type: typeFilter || undefined,
            sort_by: sortBy,
            sort_order: sortOrder,
            page,
            page_size: pageSize,
          },
        }),
        api.get('/api/v1/connections/connectors'),
      ])
      setSources(sourcesRes.data.items || [])
      setTotal(sourcesRes.data.total || 0)
      setConnectors(connectorsRes.data || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [search, statusFilter, typeFilter, sortBy, sortOrder, page, pageSize])

  useEffect(() => {
    loadData()
  }, [loadData])

  const openCreateWizard = () => {
    setWizardMode('create')
    setEditingSource(null)
    setWizardStep(1)
    setForm(initialForm)
    setTestResult(null)
    setPreviewData(null)
    setShowWizard(true)
  }

  const openEditWizard = async (source) => {
    try {
      const { data } = await api.get(`/api/v1/connections/${source.id}`)
      setWizardMode('edit')
      setEditingSource(source)
      setWizardStep(2)
      setForm({
        ...initialForm,
        name: data.name,
        source_type: data.source_type,
        description: data.description || '',
        schedule: data.schedule || '',
        tags: (data.tags || []).join(', '),
        host: data.host || '',
        port: data.port || '',
        database_name: data.database_name || '',
        base_url: data.base_url || '',
        authentication_type: data.authentication_type || 'none',
      })
      setTestResult(null)
      setPreviewData(null)
      setShowWizard(true)
    } catch (e) {
      setNotice(e.message)
    }
  }

  const parsePayload = useCallback(() => {
    const tags = form.tags
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean)
    let headers = {}
    if (form.headers.trim()) {
      try {
        headers = JSON.parse(form.headers)
      } catch {
        throw new Error('Headers must be valid JSON')
      }
    }
    return {
      ...form,
      port: form.port ? Number(form.port) : null,
      tags,
      headers,
    }
  }, [form])

  const runTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const payload = parsePayload()
      const { data } = await api.post('/api/v1/connections/test', payload)
      setTestResult(data)
      if (data.success) setWizardStep(4)
    } catch (e) {
      setTestResult({ success: false, message: e.message })
    } finally {
      setTesting(false)
    }
  }

  const loadPreview = useCallback(async () => {
    try {
      const payload = parsePayload()
      const { data } = await api.post('/api/v1/connections/preview', payload)
      setPreviewData(data)
    } catch (e) {
      setPreviewData({ error: e.message })
    }
  }, [parsePayload])

  useEffect(() => {
    if (showWizard && wizardStep === 4) {
      loadPreview()
    }
  }, [wizardStep, showWizard, loadPreview])

  const saveConnection = async () => {
    setSubmitting(true)
    try {
      const payload = parsePayload()
      if (wizardMode === 'create') {
        await api.post('/api/v1/connections', payload)
        setNotice('Connection saved successfully')
      } else {
        await api.patch(`/api/v1/connections/${editingSource.id}`, payload)
        setNotice('Connection updated successfully')
      }
      setShowWizard(false)
      loadData()
    } catch (e) {
      setNotice(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  const testSaved = async (sourceId) => {
    try {
      const { data } = await api.post(`/api/v1/connections/${sourceId}/test`)
      setNotice(data.message)
      loadData()
    } catch (e) {
      setNotice(e.message)
    }
  }

  const refreshMetadata = async (sourceId) => {
    try {
      const { data } = await api.post(`/api/v1/connections/${sourceId}/refresh-metadata`)
      setNotice(data.message)
      loadData()
    } catch (e) {
      setNotice(e.message)
    }
  }

  const deleteSource = async (source) => {
    const confirmed = window.confirm(
      `Delete "${source.name}"?\nThis can impact downstream dashboards, automations, and AI recommendations.`
    )
    if (!confirmed) return
    try {
      await api.delete(`/api/v1/connections/${source.id}`)
      setNotice('Source deleted successfully')
      loadData()
    } catch (e) {
      setNotice(e.message)
    }
  }

  const onFileChange = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    const content = await encodeFile(file)
    setForm((prev) => ({ ...prev, file_name: file.name, file_content_base64: content }))
  }

  if (loading) return <LoadingState count={6} height="h-36" />
  if (error) return <ErrorState message={error} />

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Data Sources</h1>
          <p className="text-sm text-gray-400">Manage enterprise connectors, sync health, and metadata.</p>
        </div>
        <button className="btn-primary" onClick={openCreateWizard}>
          Connect New Data Source
        </button>
      </div>

      {notice && (
        <div className="card border border-prism-800 text-prism-200 text-sm flex justify-between items-center">
          <span>{notice}</span>
          <button className="text-xs text-prism-400" onClick={() => setNotice('')}>
            Dismiss
          </button>
        </div>
      )}

      <div className="card space-y-4">
        <div className="grid md:grid-cols-5 gap-3">
          <input
            aria-label="Search data source"
            className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm md:col-span-2"
            placeholder="Search by source name"
            value={search}
            onChange={(e) => {
              setPage(1)
              setSearch(e.target.value)
            }}
          />
          <select
            aria-label="Filter by type"
            className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm"
            value={typeFilter}
            onChange={(e) => {
              setPage(1)
              setTypeFilter(e.target.value)
            }}
          >
            <option value="">All types</option>
            {connectors.map((connector) => (
              <option key={connector.type} value={connector.type}>
                {connector.title}
              </option>
            ))}
          </select>
          <select
            aria-label="Filter by status"
            className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm"
            value={statusFilter}
            onChange={(e) => {
              setPage(1)
              setStatusFilter(e.target.value)
            }}
          >
            <option value="">All status</option>
            <option value="healthy">Healthy</option>
            <option value="warning">Warning</option>
            <option value="failed">Failed</option>
            <option value="pending">Pending</option>
            <option value="disconnected">Disconnected</option>
          </select>
          <div className="flex gap-2">
            <select
              aria-label="Sort field"
              className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm w-full"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="created_at">Created</option>
              <option value="name">Name</option>
              <option value="status">Status</option>
              <option value="last_sync_at">Last Sync</option>
              <option value="last_successful_refresh_at">Last Refresh</option>
            </select>
            <button className="btn-secondary" onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}>
              {sortOrder === 'asc' ? '↑' : '↓'}
            </button>
          </div>
        </div>

        {sources.length === 0 ? (
          <div className="border border-dashed border-gray-800 rounded-lg p-10 text-center text-gray-400">
            No data sources found. Connect your first data source to begin.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-gray-400 border-b border-gray-800">
                  <th className="py-2 pr-4">Source Name</th>
                  <th className="py-2 pr-4">Type</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Owner</th>
                  <th className="py-2 pr-4">Last Sync</th>
                  <th className="py-2 pr-4">Last Refresh</th>
                  <th className="py-2 pr-4">Created</th>
                  <th className="py-2 pr-4">Actions</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((source) => (
                  <tr key={source.id} className="border-b border-gray-900">
                    <td className="py-3 pr-4">
                      <div className="font-medium">{source.name}</div>
                      <div className="text-xs text-gray-400">{(source.tags || []).join(', ') || 'No tags'}</div>
                    </td>
                    <td className="py-3 pr-4">{source.source_type}</td>
                    <td className="py-3 pr-4">
                      <span className="badge bg-gray-800 text-gray-200">{source.status}</span>
                    </td>
                    <td className="py-3 pr-4">{source.owner}</td>
                    <td className="py-3 pr-4">{source.last_sync_at ? new Date(source.last_sync_at).toLocaleString() : '-'}</td>
                    <td className="py-3 pr-4">
                      {source.last_successful_refresh_at ? new Date(source.last_successful_refresh_at).toLocaleString() : '-'}
                    </td>
                    <td className="py-3 pr-4">{new Date(source.created_at).toLocaleDateString()}</td>
                    <td className="py-3 pr-4">
                      <div className="flex flex-wrap gap-2">
                        <button className="btn-secondary text-xs" onClick={() => navigate(`/connections/${source.id}`)}>
                          View
                        </button>
                        <button className="btn-secondary text-xs" onClick={() => openEditWizard(source)}>
                          Edit
                        </button>
                        <button className="btn-secondary text-xs" onClick={() => testSaved(source.id)}>
                          Test
                        </button>
                        <button className="btn-secondary text-xs" onClick={() => refreshMetadata(source.id)}>
                          Refresh
                        </button>
                        <button className="btn-secondary text-xs text-red-300" onClick={() => deleteSource(source)}>
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">
            Showing page {page} of {totalPages} ({total} sources)
          </span>
          <div className="flex gap-2">
            <button className="btn-secondary" disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>
              Previous
            </button>
            <button className="btn-secondary" disabled={page >= totalPages} onClick={() => setPage((p) => Math.min(totalPages, p + 1))}>
              Next
            </button>
          </div>
        </div>
      </div>

      {showWizard && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true">
          <div className="w-full max-w-4xl card max-h-[90vh] overflow-y-auto space-y-5">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">{wizardMode === 'create' ? 'Connect New Data Source' : 'Edit Data Source'}</h2>
              <button className="btn-secondary" onClick={() => setShowWizard(false)}>
                Close
              </button>
            </div>
            <div className="text-sm text-gray-400">Step {wizardStep} of 5</div>

            {wizardStep === 1 && (
              <div className="grid md:grid-cols-3 gap-3">
                {connectors.map((connector) => (
                  <button
                    key={connector.type}
                    onClick={() => {
                      setForm((prev) => ({ ...prev, source_type: connector.type }))
                      setWizardStep(2)
                    }}
                    className={`text-left border rounded-lg p-4 ${
                      form.source_type === connector.type ? 'border-prism-500 bg-prism-950/30' : 'border-gray-800'
                    }`}
                  >
                    <div className="font-medium">{connector.title}</div>
                    <div className="text-xs text-gray-400 mt-1">{connector.description}</div>
                  </button>
                ))}
              </div>
            )}

            {wizardStep >= 2 && (
              <div className="grid md:grid-cols-2 gap-3">
                <input
                  className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm"
                  placeholder="Source Name"
                  value={form.name}
                  onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
                />
                <input
                  className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm"
                  placeholder="Tags (Finance, HR)"
                  value={form.tags}
                  onChange={(e) => setForm((p) => ({ ...p, tags: e.target.value }))}
                />
                <input
                  className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm"
                  placeholder="Description"
                  value={form.description}
                  onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
                />
                <input
                  className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm"
                  placeholder="Schedule (e.g. 0 * * * *)"
                  value={form.schedule}
                  onChange={(e) => setForm((p) => ({ ...p, schedule: e.target.value }))}
                />

                {['postgresql', 'mysql', 'sqlserver'].includes(form.source_type) && (
                  <>
                    <input className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" placeholder="Host" value={form.host} onChange={(e) => setForm((p) => ({ ...p, host: e.target.value }))} />
                    <input className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" placeholder="Port" value={form.port} onChange={(e) => setForm((p) => ({ ...p, port: e.target.value }))} />
                    <input className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" placeholder="Username" value={form.username} onChange={(e) => setForm((p) => ({ ...p, username: e.target.value }))} />
                    <input type="password" className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" placeholder="Password" value={form.password} onChange={(e) => setForm((p) => ({ ...p, password: e.target.value }))} />
                    <input className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm md:col-span-2" placeholder="Database Name" value={form.database_name} onChange={(e) => setForm((p) => ({ ...p, database_name: e.target.value }))} />
                  </>
                )}

                {form.source_type === 'rest_api' && (
                  <>
                    <input className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" placeholder="Base URL" value={form.base_url} onChange={(e) => setForm((p) => ({ ...p, base_url: e.target.value }))} />
                    <select className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={form.authentication_type} onChange={(e) => setForm((p) => ({ ...p, authentication_type: e.target.value }))}>
                      <option value="none">No Authentication</option>
                      <option value="api_key">API Key</option>
                      <option value="bearer">Bearer Auth</option>
                    </select>
                    <textarea className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm md:col-span-2" rows={4} placeholder='Headers JSON e.g. {"X-Api-Key":"value"}' value={form.headers} onChange={(e) => setForm((p) => ({ ...p, headers: e.target.value }))} />
                  </>
                )}

                {['csv', 'excel'].includes(form.source_type) && (
                  <div className="md:col-span-2 space-y-2">
                    <input type="file" accept={form.source_type === 'csv' ? '.csv' : '.xls,.xlsx'} onChange={onFileChange} />
                    {form.file_name && <p className="text-xs text-gray-400">Selected: {form.file_name}</p>}
                  </div>
                )}
              </div>
            )}

            {wizardStep === 3 && (
              <div className="card bg-gray-950 border border-gray-800">
                {testing ? (
                  <div>Connecting...</div>
                ) : testResult ? (
                  <div className={testResult.success ? 'text-green-300' : 'text-red-300'}>
                    {testResult.success ? 'Success: ' : 'Failed: '}
                    {testResult.message}
                  </div>
                ) : (
                  <div>Click test connection to validate network, authentication input, and endpoint availability.</div>
                )}
              </div>
            )}

            {wizardStep === 4 && (
              <div className="card bg-gray-950 border border-gray-800 space-y-3">
                <h3 className="font-medium">Preview</h3>
                {previewData?.error && <p className="text-red-300 text-sm">{previewData.error}</p>}
                <div>
                  <h4 className="text-sm text-gray-400 mb-1">Tables/Resources</h4>
                  <div className="text-sm">{(previewData?.tables || []).join(', ') || 'No preview metadata available'}</div>
                </div>
                <div>
                  <h4 className="text-sm text-gray-400 mb-1">Columns</h4>
                  <div className="text-xs max-h-48 overflow-auto border border-gray-800 rounded-lg p-2">
                    {(previewData?.columns || []).map((col, idx) => (
                      <div key={`${col.column_name}-${idx}`} className="py-1 border-b border-gray-900 last:border-0">
                        {col.object_name}.{col.column_name} ({col.data_type})
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {wizardStep === 5 && (
              <div className="card bg-gray-950 border border-gray-800 text-sm">
                Save connection securely. Credentials are encrypted and never returned by the API.
              </div>
            )}

            <div className="flex flex-wrap justify-between gap-2">
              <button className="btn-secondary" disabled={wizardStep <= 1} onClick={() => setWizardStep((s) => Math.max(1, s - 1))}>
                Back
              </button>
              <div className="flex gap-2">
                {wizardStep === 2 && (
                  <button className="btn-secondary" onClick={() => setWizardStep(3)}>
                    Continue
                  </button>
                )}
                {wizardStep === 3 && (
                  <button className="btn-secondary" onClick={runTest} disabled={testing}>
                    {testing ? 'Testing...' : 'Test Connection'}
                  </button>
                )}
                {wizardStep === 4 && (
                  <button className="btn-secondary" onClick={() => setWizardStep(5)}>
                    Continue
                  </button>
                )}
                {wizardStep === 5 && (
                  <button className="btn-primary" onClick={saveConnection} disabled={submitting}>
                    {submitting ? 'Saving...' : wizardMode === 'create' ? 'Save Connection' : 'Save Changes'}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
