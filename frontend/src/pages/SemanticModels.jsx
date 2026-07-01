import React, { useCallback, useEffect, useMemo, useState } from 'react'
import api from '../services/api'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'

const initialWizard = {
  name: '',
  description: '',
  data_source_ids: [],
  selected_tables: '',
}

export default function SemanticModels() {
  const [items, setItems] = useState([])
  const [dataSources, setDataSources] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [sortBy, setSortBy] = useState('updated_at')
  const [sortOrder, setSortOrder] = useState('desc')
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [total, setTotal] = useState(0)

  const [showWizard, setShowWizard] = useState(false)
  const [wizardStep, setWizardStep] = useState(1)
  const [wizard, setWizard] = useState(initialWizard)
  const [draftModelId, setDraftModelId] = useState(null)
  const [relationshipCandidates, setRelationshipCandidates] = useState([])
  const [validationIssues, setValidationIssues] = useState([])
  const [wizardLoading, setWizardLoading] = useState(false)

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / pageSize)), [total, pageSize])

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [modelsRes, sourcesRes] = await Promise.all([
        api.get('/api/v1/semantic-models', {
          params: {
            search: search || undefined,
            status: statusFilter || undefined,
            sort_by: sortBy,
            sort_order: sortOrder,
            page,
            page_size: pageSize,
          },
        }),
        api.get('/api/v1/connections', { params: { page: 1, page_size: 200 } }),
      ])
      setItems(modelsRes.data.items || [])
      setTotal(modelsRes.data.total || 0)
      setDataSources(sourcesRes.data.items || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [search, statusFilter, sortBy, sortOrder, page, pageSize])

  useEffect(() => {
    load()
  }, [load])

  const openWizard = () => {
    setWizard(initialWizard)
    setDraftModelId(null)
    setRelationshipCandidates([])
    setValidationIssues([])
    setWizardStep(1)
    setShowWizard(true)
  }

  const closeWizard = () => {
    setShowWizard(false)
    setWizardStep(1)
    setWizard(initialWizard)
    setDraftModelId(null)
    setRelationshipCandidates([])
    setValidationIssues([])
    setWizardLoading(false)
  }

  const toggleDataSource = (id) => {
    setWizard((prev) => {
      const exists = prev.data_source_ids.includes(id)
      return {
        ...prev,
        data_source_ids: exists ? prev.data_source_ids.filter((value) => value !== id) : [...prev.data_source_ids, id],
      }
    })
  }

  const detectRelationships = async () => {
    setWizardLoading(true)
    try {
      const tableList = wizard.selected_tables
        .split(',')
        .map((value) => value.trim())
        .filter(Boolean)
      const params = new URLSearchParams()
      wizard.data_source_ids.forEach((id) => params.append('data_source_ids', String(id)))
      tableList.forEach((table) => params.append('selected_tables', table))
      const { data } = await api.get(`/api/v1/semantic-models/relationship-candidates?${params.toString()}`)
      setRelationshipCandidates(data.candidates || [])
      setWizardStep(4)
    } catch (e) {
      setNotice(e.message)
    } finally {
      setWizardLoading(false)
    }
  }

  const createDraft = async () => {
    setWizardLoading(true)
    try {
      const payload = {
        name: wizard.name.trim(),
        description: wizard.description.trim(),
        data_source_ids: wizard.data_source_ids,
        selected_tables: wizard.selected_tables
          .split(',')
          .map((value) => value.trim())
          .filter(Boolean),
      }
      const { data } = await api.post('/api/v1/semantic-models', payload)
      setDraftModelId(data.id)
      setValidationIssues((data.validation_errors || []).concat(data.validation_warnings || []))
      setWizardStep(6)
      load()
    } catch (e) {
      setNotice(e.message)
    } finally {
      setWizardLoading(false)
    }
  }

  const runValidation = async () => {
    if (!draftModelId) return
    setWizardLoading(true)
    try {
      const { data } = await api.post(`/api/v1/semantic-models/${draftModelId}/validate`)
      setValidationIssues(data || [])
      setWizardStep(6)
    } catch (e) {
      setNotice(e.message)
    } finally {
      setWizardLoading(false)
    }
  }

  const publishModel = async () => {
    if (!draftModelId) return
    setWizardLoading(true)
    try {
      await api.post(`/api/v1/semantic-models/${draftModelId}/publish`)
      setNotice('Semantic model published successfully')
      closeWizard()
      load()
    } catch (e) {
      setNotice(e.message)
    } finally {
      setWizardLoading(false)
    }
  }

  const duplicateModel = async (id) => {
    try {
      await api.post(`/api/v1/semantic-models/${id}/duplicate`)
      setNotice('Semantic model duplicated')
      load()
    } catch (e) {
      setNotice(e.message)
    }
  }

  const archiveModel = async (item) => {
    const confirmed = window.confirm(`Archive "${item.name}"? You can still review and rollback versions later.`)
    if (!confirmed) return
    try {
      await api.post(`/api/v1/semantic-models/${item.id}/archive`)
      setNotice('Semantic model archived')
      load()
    } catch (e) {
      setNotice(e.message)
    }
  }

  if (loading) return <LoadingState count={5} height="h-36" />
  if (error) return <ErrorState message={error} />

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Semantic Models</h1>
          <p className="text-sm text-gray-400">Build governed business entities, metrics, relationships, and KPI definitions.</p>
        </div>
        <button className="btn-primary" onClick={openWizard}>Create Semantic Model</button>
      </div>

      {notice && (
        <div className="card border border-prism-800 text-sm text-prism-200 flex justify-between gap-3">
          <span>{notice}</span>
          <button className="text-gray-400 hover:text-gray-200" onClick={() => setNotice('')}>Dismiss</button>
        </div>
      )}

      <section className="card space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          <input
            className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm md:col-span-2"
            placeholder="Search models..."
            value={search}
            onChange={(event) => {
              setSearch(event.target.value)
              setPage(1)
            }}
          />
          <select
            className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm"
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(event.target.value)
              setPage(1)
            }}
          >
            <option value="">All statuses</option>
            <option value="draft">Draft</option>
            <option value="published">Published</option>
            <option value="archived">Archived</option>
          </select>
          <select className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
            <option value="updated_at">Last Updated</option>
            <option value="created_at">Created Date</option>
            <option value="name">Name</option>
            <option value="status">Status</option>
            <option value="version">Version</option>
          </select>
          <button className="btn-secondary" onClick={() => setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'))}>
            Order: {sortOrder.toUpperCase()}
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-gray-400 border-b border-gray-800">
              <tr>
                <th className="py-2 pr-4">Model</th>
                <th className="py-2 pr-4">Data Sources</th>
                <th className="py-2 pr-4">Owner</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2 pr-4">Version</th>
                <th className="py-2 pr-4">Updated</th>
                <th className="py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-b border-gray-900/70">
                  <td className="py-3 pr-4">
                    <p className="font-semibold">{item.name}</p>
                    <p className="text-xs text-gray-500">{item.description || 'No description'}</p>
                  </td>
                  <td className="py-3 pr-4">
                    <p className="text-gray-300">{(item.data_sources_used || []).join(', ') || '—'}</p>
                  </td>
                  <td className="py-3 pr-4">{item.owner}</td>
                  <td className="py-3 pr-4">
                    <span className={`badge ${
                      item.status === 'published'
                        ? 'bg-emerald-900/50 text-emerald-300'
                        : item.status === 'archived'
                          ? 'bg-gray-800 text-gray-300'
                          : 'bg-amber-900/50 text-amber-300'
                    }`}
                    >
                      {item.status}
                    </span>
                  </td>
                  <td className="py-3 pr-4">v{item.version}</td>
                  <td className="py-3 pr-4">{new Date(item.last_updated).toLocaleString()}</td>
                  <td className="py-3 text-right space-x-2">
                    <button className="btn-secondary text-xs" onClick={() => duplicateModel(item.id)}>Duplicate</button>
                    <button className="btn-secondary text-xs text-amber-300" onClick={() => archiveModel(item)}>Archive</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between">
          <p className="text-xs text-gray-500">Page {page} of {totalPages} · {total} total models</p>
          <div className="flex gap-2">
            <button className="btn-secondary" disabled={page <= 1} onClick={() => setPage((prev) => Math.max(1, prev - 1))}>Prev</button>
            <button className="btn-secondary" disabled={page >= totalPages} onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}>Next</button>
          </div>
        </div>
      </section>

      {showWizard && (
        <div className="fixed inset-0 bg-black/70 z-40 flex items-center justify-center p-4">
          <div className="w-full max-w-4xl card max-h-[90vh] overflow-y-auto space-y-5">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-xl font-semibold">Create Semantic Model</h2>
                <p className="text-xs text-gray-500">Step {wizardStep} of 6</p>
              </div>
              <button className="btn-secondary" onClick={closeWizard}>Close</button>
            </div>

            <div className="grid grid-cols-6 gap-2">
              {[1, 2, 3, 4, 5, 6].map((step) => (
                <div key={step} className={`h-2 rounded-full ${wizardStep >= step ? 'bg-prism-500' : 'bg-gray-800'}`} />
              ))}
            </div>

            {wizardStep === 1 && (
              <section className="space-y-3">
                <h3 className="font-medium">Step 1: Select Data Sources</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {dataSources.map((source) => (
                    <label key={source.id} className="card bg-gray-950 border border-gray-800 flex items-start gap-3 cursor-pointer">
                      <input type="checkbox" checked={wizard.data_source_ids.includes(source.id)} onChange={() => toggleDataSource(source.id)} />
                      <div>
                        <p className="font-medium">{source.name}</p>
                        <p className="text-xs text-gray-500">{source.source_type} · {source.status}</p>
                      </div>
                    </label>
                  ))}
                </div>
                <div className="flex justify-end">
                  <button className="btn-primary" disabled={!wizard.data_source_ids.length} onClick={() => setWizardStep(2)}>Next</button>
                </div>
              </section>
            )}

            {wizardStep === 2 && (
              <section className="space-y-3">
                <h3 className="font-medium">Step 2: Select Tables</h3>
                <textarea
                  className="w-full min-h-28 bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm"
                  value={wizard.selected_tables}
                  onChange={(event) => setWizard((prev) => ({ ...prev, selected_tables: event.target.value }))}
                  placeholder="orders, customers, invoices, employees"
                />
                <p className="text-xs text-gray-500">Enter comma-separated table names to include in this semantic model.</p>
                <div className="flex justify-between">
                  <button className="btn-secondary" onClick={() => setWizardStep(1)}>Back</button>
                  <button className="btn-primary" disabled={!wizard.selected_tables.trim()} onClick={() => setWizardStep(3)}>Next</button>
                </div>
              </section>
            )}

            {wizardStep === 3 && (
              <section className="space-y-3">
                <h3 className="font-medium">Step 3: Detect Relationships</h3>
                <p className="text-sm text-gray-400">Run automatic relationship detection from selected data sources and tables.</p>
                <div className="flex justify-between">
                  <button className="btn-secondary" onClick={() => setWizardStep(2)}>Back</button>
                  <button className="btn-primary" onClick={detectRelationships} disabled={wizardLoading}>
                    {wizardLoading ? 'Detecting...' : 'Detect Relationships'}
                  </button>
                </div>
              </section>
            )}

            {wizardStep === 4 && (
              <section className="space-y-3">
                <h3 className="font-medium">Detected Relationships</h3>
                <div className="card bg-gray-950 border border-gray-800">
                  {!relationshipCandidates.length ? (
                    <p className="text-sm text-gray-500">No candidate relationships detected from metadata.</p>
                  ) : (
                    <ul className="space-y-2 text-sm">
                      {relationshipCandidates.map((item, index) => (
                        <li key={index} className="border-b border-gray-900 pb-2">
                          <span className="font-medium">{item.left_table}.{item.left_column}</span>
                          <span className="text-gray-500"> → </span>
                          <span className="font-medium">{item.right_table}.{item.right_column}</span>
                          <span className="ml-2 text-xs text-gray-500">({item.relationship_type})</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <div className="flex justify-between">
                  <button className="btn-secondary" onClick={() => setWizardStep(3)}>Back</button>
                  <button className="btn-primary" onClick={() => setWizardStep(5)}>Next</button>
                </div>
              </section>
            )}

            {wizardStep === 5 && (
              <section className="space-y-3">
                <h3 className="font-medium">Step 4: Configure Business Model</h3>
                <input
                  className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm"
                  placeholder="Model Name"
                  value={wizard.name}
                  onChange={(event) => setWizard((prev) => ({ ...prev, name: event.target.value }))}
                />
                <textarea
                  className="w-full min-h-24 bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm"
                  placeholder="Business description and intent"
                  value={wizard.description}
                  onChange={(event) => setWizard((prev) => ({ ...prev, description: event.target.value }))}
                />
                <div className="flex justify-between">
                  <button className="btn-secondary" onClick={() => setWizardStep(4)}>Back</button>
                  <button className="btn-primary" disabled={!wizard.name.trim() || wizardLoading} onClick={createDraft}>
                    {wizardLoading ? 'Creating...' : 'Create Draft'}
                  </button>
                </div>
              </section>
            )}

            {wizardStep === 6 && (
              <section className="space-y-3">
                <h3 className="font-medium">Step 5 & 6: Validate and Publish</h3>
                <div className="card bg-gray-950 border border-gray-800">
                  {!validationIssues.length ? (
                    <p className="text-sm text-emerald-300">No validation issues found.</p>
                  ) : (
                    <ul className="space-y-2 text-sm">
                      {validationIssues.map((issue, index) => (
                        <li key={index} className={`${issue.severity === 'error' ? 'text-red-300' : 'text-amber-300'}`}>
                          [{issue.severity}] {issue.code}: {issue.message}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <div className="flex justify-between">
                  <button className="btn-secondary" onClick={() => setWizardStep(5)}>Back</button>
                  <div className="flex gap-2">
                    <button className="btn-secondary" onClick={runValidation} disabled={wizardLoading}>Re-Validate</button>
                    <button
                      className="btn-primary"
                      onClick={publishModel}
                      disabled={wizardLoading || validationIssues.some((issue) => issue.severity === 'error')}
                    >
                      {wizardLoading ? 'Publishing...' : 'Publish'}
                    </button>
                  </div>
                </div>
              </section>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
