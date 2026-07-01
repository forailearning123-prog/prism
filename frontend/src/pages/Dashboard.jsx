import React, { useCallback, useEffect, useMemo, useState } from 'react'
import api from '../services/api'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'

const initialCreateForm = {
  name: '',
  description: '',
  folder: 'General',
  tags: '',
  semantic_model_id: '',
  ai_prompt: '',
  mode: 'blank',
  theme_variant: 'corporate',
  kpis: '',
  dimensions: '',
}

const widgetTypeOptions = [
  'kpi_card',
  'line_chart',
  'bar_chart',
  'area_chart',
  'pie_chart',
  'donut_chart',
  'scatter_chart',
  'heat_map',
  'tree_map',
  'waterfall_chart',
  'funnel_chart',
  'gauge_chart',
  'table',
  'pivot_table',
  'map',
  'timeline',
  'text_panel',
  'image',
  'embedded_content',
]

const filterScopeOptions = [
  'global',
  'dashboard',
  'widget',
  'quick',
  'advanced',
  'relative_date',
  'saved',
  'cross',
]

const shareVisibilityOptions = ['private', 'team', 'department', 'organisation', 'public_link']
const shareRoleOptions = ['viewer', 'editor', 'owner']
const exportOptions = ['pdf', 'png', 'pptx', 'excel']

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const [items, setItems] = useState([])
  const [summary, setSummary] = useState({ total: 0, draft: 0, published: 0, archived: 0, favourites: 0 })
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const pageSize = 20
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [favouriteFilter, setFavouriteFilter] = useState('')
  const [sortBy, setSortBy] = useState('updated_at')
  const [sortOrder, setSortOrder] = useState('desc')

  const [showCreate, setShowCreate] = useState(false)
  const [createForm, setCreateForm] = useState(initialCreateForm)
  const [semanticModels, setSemanticModels] = useState([])

  const [activeDashboardId, setActiveDashboardId] = useState(null)
  const [activeDashboard, setActiveDashboard] = useState(null)
  const [widgets, setWidgets] = useState([])
  const [filters, setFilters] = useState([])
  const [permissions, setPermissions] = useState([])
  const [versions, setVersions] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [usage, setUsage] = useState(null)

  const [history, setHistory] = useState([])
  const [historyCursor, setHistoryCursor] = useState(-1)

  const [filterForm, setFilterForm] = useState({ scope: 'dashboard', widget_id: '', name: '', field: '', operator: 'equals', value: '' })
  const [shareForm, setShareForm] = useState({ visibility: 'private', principal: '', role: 'viewer' })

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / pageSize)), [total])

  const pushHistory = useCallback((nextWidgets) => {
    setHistory((prev) => {
      const trimmed = prev.slice(0, historyCursor + 1)
      return [...trimmed, JSON.stringify(nextWidgets)]
    })
    setHistoryCursor((prev) => prev + 1)
  }, [historyCursor])

  const fetchWorkspace = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [listRes, summaryRes, modelsRes] = await Promise.all([
        api.get('/api/v1/dashboards', {
          params: {
            search: search || undefined,
            status: statusFilter || undefined,
            favourite: favouriteFilter === '' ? undefined : favouriteFilter === 'true',
            sort_by: sortBy,
            sort_order: sortOrder,
            page,
            page_size: pageSize,
          },
        }),
        api.get('/api/v1/dashboards/workspace-summary'),
        api.get('/api/v1/semantic-models', { params: { page: 1, page_size: 200 } }),
      ])
      setItems(listRes.data.items || [])
      setTotal(listRes.data.total || 0)
      setSummary(summaryRes.data)
      setSemanticModels(modelsRes.data.items || [])

      if (!activeDashboardId && (listRes.data.items || []).length) {
        setActiveDashboardId(listRes.data.items[0].id)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [activeDashboardId, favouriteFilter, page, search, sortBy, sortOrder, statusFilter])

  const fetchDashboardDetails = useCallback(async (dashboardId) => {
    if (!dashboardId) {
      setActiveDashboard(null)
      setWidgets([])
      setFilters([])
      setPermissions([])
      setVersions([])
      setRecommendations([])
      setUsage(null)
      return
    }
    try {
      const [detailsRes, versionsRes, recommendationsRes, usageRes] = await Promise.all([
        api.get(`/api/v1/dashboards/${dashboardId}`),
        api.get(`/api/v1/dashboards/${dashboardId}/versions`),
        api.get(`/api/v1/dashboards/${dashboardId}/recommendations`).catch(() => ({ data: [] })),
        api.get(`/api/v1/dashboards/${dashboardId}/usage`).catch(() => ({ data: null })),
      ])
      setActiveDashboard(detailsRes.data)
      setWidgets(detailsRes.data.widgets || [])
      setFilters(detailsRes.data.filters || [])
      setPermissions(detailsRes.data.permissions || [])
      setVersions(versionsRes.data || [])
      setRecommendations(recommendationsRes.data || [])
      setUsage(usageRes.data)
      const snapshot = JSON.stringify(detailsRes.data.widgets || [])
      setHistory([snapshot])
      setHistoryCursor(0)
    } catch (e) {
      setNotice(e.message)
    }
  }, [])

  useEffect(() => {
    fetchWorkspace()
  }, [fetchWorkspace])

  useEffect(() => {
    fetchDashboardDetails(activeDashboardId)
  }, [activeDashboardId, fetchDashboardDetails])

  useEffect(() => {
    if (!activeDashboard || !activeDashboard.auto_save_enabled) return
    const handle = setTimeout(async () => {
      try {
        await api.post(`/api/v1/dashboards/${activeDashboard.id}/save-draft`, { note: 'Auto-saved by dashboard studio' })
      } catch {
      }
    }, 2500)
    return () => clearTimeout(handle)
  }, [widgets, filters, activeDashboard])

  const refreshActive = async () => {
    await fetchWorkspace()
    if (activeDashboardId) {
      await fetchDashboardDetails(activeDashboardId)
    }
  }

  const handleCreateDashboard = async () => {
    try {
      if (createForm.mode === 'ai') {
        const { data } = await api.post('/api/v1/dashboards/generate-ai', {
          prompt: createForm.ai_prompt.trim(),
          semantic_model_id: Number(createForm.semantic_model_id),
          theme_variant: createForm.theme_variant,
        })
        setActiveDashboardId(data.id)
        setNotice('AI dashboard generated successfully')
      } else {
        const { data } = await api.post('/api/v1/dashboards', {
          name: createForm.name.trim(),
          description: createForm.description.trim(),
          folder: createForm.folder.trim(),
          tags: splitCsv(createForm.tags),
          semantic_model_id: createForm.semantic_model_id ? Number(createForm.semantic_model_id) : null,
          creation_mode: createForm.mode,
          ai_prompt: createForm.ai_prompt.trim(),
          theme_variant: createForm.theme_variant,
          kpis: splitCsv(createForm.kpis),
          dimensions: splitCsv(createForm.dimensions),
        })
        setActiveDashboardId(data.id)
        setNotice('Dashboard created')
      }
      setShowCreate(false)
      setCreateForm(initialCreateForm)
      await refreshActive()
    } catch (e) {
      setNotice(e.message)
    }
  }

  const handleUpdateDashboardMeta = async (partial) => {
    if (!activeDashboardId) return
    try {
      await api.patch(`/api/v1/dashboards/${activeDashboardId}`, partial)
      await refreshActive()
    } catch (e) {
      setNotice(e.message)
    }
  }

  const handleDuplicate = async (item) => {
    try {
      const { data } = await api.post(`/api/v1/dashboards/${item.id}/duplicate`, {})
      setActiveDashboardId(data.id)
      setNotice('Dashboard duplicated')
      await refreshActive()
    } catch (e) {
      setNotice(e.message)
    }
  }

  const handleArchive = async (item) => {
    if (!window.confirm(`Archive "${item.name}"?`)) return
    try {
      await api.post(`/api/v1/dashboards/${item.id}/archive`)
      setNotice('Dashboard archived')
      await refreshActive()
    } catch (e) {
      setNotice(e.message)
    }
  }

  const handleDelete = async (item) => {
    if (!window.confirm(`Delete "${item.name}" permanently?`)) return
    try {
      await api.delete(`/api/v1/dashboards/${item.id}`)
      if (activeDashboardId === item.id) setActiveDashboardId(null)
      setNotice('Dashboard deleted')
      await refreshActive()
    } catch (e) {
      setNotice(e.message)
    }
  }

  const handleExport = async (format) => {
    if (!activeDashboardId) return
    try {
      const { data } = await api.post(`/api/v1/dashboards/${activeDashboardId}/export`, { format })
      setNotice(`Export prepared: ${data.name}.${format}`)
      await refreshActive()
    } catch (e) {
      setNotice(e.message)
    }
  }

  const addWidget = async (widgetType = 'kpi_card') => {
    if (!activeDashboardId) return
    const nextPositionX = ((widgets.length % 3) * 4)
    const nextPositionY = (Math.floor(widgets.length / 3) * 3)
    try {
      await api.post(`/api/v1/dashboards/${activeDashboardId}/widgets`, {
        widget_type: widgetType,
        title: `New ${humanize(widgetType)}`,
        description: 'Widget created from dashboard canvas',
        width: 4,
        height: 3,
        position_x: nextPositionX,
        position_y: nextPositionY,
        drill_behavior: { enabled: true, breadcrumb: true },
      })
      const nextWidgets = [...widgets, { widget_type: widgetType, position_x: nextPositionX, position_y: nextPositionY }]
      pushHistory(nextWidgets)
      await fetchDashboardDetails(activeDashboardId)
      setNotice('Widget added')
    } catch (e) {
      setNotice(e.message)
    }
  }

  const patchWidget = async (widgetId, updates, message = 'Widget updated') => {
    if (!activeDashboardId) return
    try {
      await api.patch(`/api/v1/dashboards/${activeDashboardId}/widgets/${widgetId}`, updates)
      const nextWidgets = widgets.map((widget) => (widget.id === widgetId ? { ...widget, ...updates } : widget))
      pushHistory(nextWidgets)
      await fetchDashboardDetails(activeDashboardId)
      setNotice(message)
    } catch (e) {
      setNotice(e.message)
    }
  }

  const copyWidget = async (widget) => {
    if (!activeDashboardId) return
    try {
      await api.post(`/api/v1/dashboards/${activeDashboardId}/widgets`, {
        widget_type: widget.widget_type,
        title: `${widget.title || humanize(widget.widget_type)} (Copy)`,
        subtitle: widget.subtitle,
        description: widget.description,
        data_source: widget.data_source,
        dimensions: widget.dimensions,
        measures: widget.measures,
        filters: widget.filters,
        colors: widget.colors,
        number_formatting: widget.number_formatting,
        conditional_formatting: widget.conditional_formatting,
        legends: widget.legends,
        labels: widget.labels,
        tooltips: widget.tooltips,
        drill_behavior: widget.drill_behavior,
        config: widget.config,
        width: widget.width,
        height: widget.height,
        position_x: widget.position_x + 1,
        position_y: widget.position_y + 1,
        z_index: widget.z_index,
        is_locked: widget.is_locked,
        group_key: widget.group_key,
        alignment: widget.alignment,
        snap_to_grid: widget.snap_to_grid,
      })
      const nextWidgets = [...widgets, { ...widget, id: undefined }]
      pushHistory(nextWidgets)
      await fetchDashboardDetails(activeDashboardId)
      setNotice('Widget copied')
    } catch (e) {
      setNotice(e.message)
    }
  }

  const removeWidget = async (widgetId) => {
    if (!activeDashboardId) return
    try {
      await api.delete(`/api/v1/dashboards/${activeDashboardId}/widgets/${widgetId}`)
      const nextWidgets = widgets.filter((widget) => widget.id !== widgetId)
      pushHistory(nextWidgets)
      await fetchDashboardDetails(activeDashboardId)
      setNotice('Widget deleted')
    } catch (e) {
      setNotice(e.message)
    }
  }

  const undoLayout = async () => {
    if (historyCursor <= 0 || !activeDashboardId) return
    const prevIndex = historyCursor - 1
    const snapshot = JSON.parse(history[prevIndex])
    setHistoryCursor(prevIndex)
    for (const widget of widgets) {
      const target = snapshot.find((item) => item.id === widget.id)
      if (!target) continue
      await api.patch(`/api/v1/dashboards/${activeDashboardId}/widgets/${widget.id}`, {
        position_x: target.position_x,
        position_y: target.position_y,
        width: target.width,
        height: target.height,
      })
    }
    await fetchDashboardDetails(activeDashboardId)
    setNotice('Undo applied')
  }

  const redoLayout = async () => {
    if (historyCursor >= history.length - 1 || !activeDashboardId) return
    const nextIndex = historyCursor + 1
    const snapshot = JSON.parse(history[nextIndex])
    setHistoryCursor(nextIndex)
    for (const widget of widgets) {
      const target = snapshot.find((item) => item.id === widget.id)
      if (!target) continue
      await api.patch(`/api/v1/dashboards/${activeDashboardId}/widgets/${widget.id}`, {
        position_x: target.position_x,
        position_y: target.position_y,
        width: target.width,
        height: target.height,
      })
    }
    await fetchDashboardDetails(activeDashboardId)
    setNotice('Redo applied')
  }

  const saveFilter = async () => {
    if (!activeDashboardId) return
    try {
      await api.post(`/api/v1/dashboards/${activeDashboardId}/filters`, {
        scope: filterForm.scope,
        widget_id: filterForm.widget_id ? Number(filterForm.widget_id) : null,
        name: filterForm.name.trim(),
        field: filterForm.field.trim(),
        operator: filterForm.operator.trim(),
        value: { expression: filterForm.value },
        is_saved: filterForm.scope === 'saved',
      })
      setFilterForm({ scope: 'dashboard', widget_id: '', name: '', field: '', operator: 'equals', value: '' })
      await fetchDashboardDetails(activeDashboardId)
      setNotice('Filter saved')
    } catch (e) {
      setNotice(e.message)
    }
  }

  const removeFilter = async (filterId) => {
    if (!activeDashboardId) return
    try {
      await api.delete(`/api/v1/dashboards/${activeDashboardId}/filters/${filterId}`)
      await fetchDashboardDetails(activeDashboardId)
      setNotice('Filter removed')
    } catch (e) {
      setNotice(e.message)
    }
  }

  const addSharePermission = async () => {
    if (!activeDashboardId) return
    try {
      await api.post(`/api/v1/dashboards/${activeDashboardId}/sharing`, {
        visibility: shareForm.visibility,
        principal: shareForm.principal.trim(),
        role: shareForm.role,
      })
      setShareForm({ visibility: 'private', principal: '', role: 'viewer' })
      await fetchDashboardDetails(activeDashboardId)
      setNotice('Sharing permission added')
    } catch (e) {
      setNotice(e.message)
    }
  }

  const removeSharePermission = async (permissionId) => {
    if (!activeDashboardId) return
    try {
      await api.delete(`/api/v1/dashboards/${activeDashboardId}/sharing/${permissionId}`)
      await fetchDashboardDetails(activeDashboardId)
      setNotice('Sharing permission removed')
    } catch (e) {
      setNotice(e.message)
    }
  }

  const publishDashboard = async () => {
    if (!activeDashboardId) return
    try {
      await api.post(`/api/v1/dashboards/${activeDashboardId}/publish`, { note: 'Published from Dashboard Studio' })
      await refreshActive()
      setNotice('Dashboard published')
    } catch (e) {
      setNotice(e.message)
    }
  }

  const saveDraft = async () => {
    if (!activeDashboardId) return
    try {
      await api.post(`/api/v1/dashboards/${activeDashboardId}/save-draft`, { note: 'Draft saved manually' })
      await refreshActive()
      setNotice('Draft saved')
    } catch (e) {
      setNotice(e.message)
    }
  }

  const restoreVersion = async (versionId) => {
    if (!activeDashboardId) return
    if (!window.confirm('Restore this version? Current unsaved changes may be replaced.')) return
    try {
      await api.post(`/api/v1/dashboards/${activeDashboardId}/restore/${versionId}`)
      await refreshActive()
      setNotice('Version restored')
    } catch (e) {
      setNotice(e.message)
    }
  }

  const compareVersions = async () => {
    if (!activeDashboardId || versions.length < 2) return
    const fromVersion = versions[1].version_number
    const toVersion = versions[0].version_number
    try {
      const { data } = await api.get(`/api/v1/dashboards/${activeDashboardId}/versions/compare`, {
        params: {
          from_version: fromVersion,
          to_version: toVersion,
        },
      })
      setNotice(`Comparison v${fromVersion}→v${toVersion}: +${data.widgets_added} widgets, -${data.widgets_removed} widgets, ${data.filters_changed} filter deltas`)
    } catch (e) {
      setNotice(e.message)
    }
  }

  const optimizeDashboard = async () => {
    if (!activeDashboardId) return
    try {
      await api.post(`/api/v1/dashboards/${activeDashboardId}/optimize`)
      await fetchDashboardDetails(activeDashboardId)
      setNotice('Optimization recommendations refreshed')
    } catch (e) {
      setNotice(e.message)
    }
  }

  const refreshAIRecommendations = async () => {
    if (!activeDashboardId) return
    try {
      const { data } = await api.get(`/api/v1/dashboards/${activeDashboardId}/ai-recommendations`)
      setRecommendations((data.recommendations || []).map((item, index) => ({
        id: `ai-${index}`,
        recommendation_type: 'better_chart',
        title: item.title,
        description: item.reason,
        reason: item.reason,
        confidence: item.confidence,
        metadata: { dimensions: item.dimensions, measures: item.measures },
      })))
      setNotice('AI recommendations generated')
    } catch (e) {
      setNotice(e.message)
    }
  }

  if (loading) return <LoadingState count={6} height="h-28" />
  if (error) return <ErrorState message={error} />

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <SummaryCard label="Total" value={summary.total} />
        <SummaryCard label="Draft" value={summary.draft} />
        <SummaryCard label="Published" value={summary.published} />
        <SummaryCard label="Archived" value={summary.archived} />
        <SummaryCard label="Favourites" value={summary.favourites} />
      </section>

      {notice && (
        <div className="card border border-prism-800 text-prism-100 text-sm flex items-center justify-between">
          <span>{notice}</span>
          <button className="text-xs text-gray-300 hover:text-white" onClick={() => setNotice('')}>Dismiss</button>
        </div>
      )}

      <div className="flex flex-wrap gap-3 items-end card">
        <div className="flex-1 min-w-[220px]">
          <label className="text-xs text-gray-400">Search</label>
          <input
            className="w-full mt-1 bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
            placeholder="Search dashboard name, description, or folder"
          />
        </div>
        <div>
          <label className="text-xs text-gray-400">Status</label>
          <select className="mt-1 bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All</option>
            <option value="draft">Draft</option>
            <option value="published">Published</option>
            <option value="archived">Archived</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-400">Favourite</label>
          <select className="mt-1 bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={favouriteFilter} onChange={(e) => setFavouriteFilter(e.target.value)}>
            <option value="">All</option>
            <option value="true">Favourites</option>
            <option value="false">Non-favourites</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-400">Sort</label>
          <select className="mt-1 bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="updated_at">Last Updated</option>
            <option value="created_at">Created Date</option>
            <option value="name">Name</option>
            <option value="status">Status</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-400">Order</label>
          <select className="mt-1 bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={sortOrder} onChange={(e) => setSortOrder(e.target.value)}>
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>
        <button className="btn-secondary" onClick={fetchWorkspace}>Apply</button>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>Create Dashboard</button>
      </div>

      {showCreate && (
        <div className="card space-y-4 border border-prism-800">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Create Dashboard</h2>
            <button className="btn-secondary" onClick={() => setShowCreate(false)}>Close</button>
          </div>

          <div className="grid md:grid-cols-3 gap-3">
            <div className="space-y-1">
              <label className="text-xs text-gray-400">Creation Mode</label>
              <select className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={createForm.mode} onChange={(e) => setCreateForm((prev) => ({ ...prev, mode: e.target.value }))}>
                <option value="ai">AI Generated</option>
                <option value="wizard">Guided Wizard</option>
                <option value="blank">Blank Canvas</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-xs text-gray-400">Dashboard Name</label>
              <input className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={createForm.name} onChange={(e) => setCreateForm((prev) => ({ ...prev, name: e.target.value }))} placeholder="Executive business overview" />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-gray-400">Semantic Model</label>
              <select className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={createForm.semantic_model_id} onChange={(e) => setCreateForm((prev) => ({ ...prev, semantic_model_id: e.target.value }))}>
                <option value="">Select model</option>
                {semanticModels.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
              </select>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs text-gray-400">Description</label>
              <input className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={createForm.description} onChange={(e) => setCreateForm((prev) => ({ ...prev, description: e.target.value }))} placeholder="Business purpose and audience" />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-gray-400">Folder</label>
              <input className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={createForm.folder} onChange={(e) => setCreateForm((prev) => ({ ...prev, folder: e.target.value }))} placeholder="Finance" />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-gray-400">Tags (comma-separated)</label>
              <input className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={createForm.tags} onChange={(e) => setCreateForm((prev) => ({ ...prev, tags: e.target.value }))} placeholder="executive, monthly, sales" />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-gray-400">Theme</label>
              <select className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={createForm.theme_variant} onChange={(e) => setCreateForm((prev) => ({ ...prev, theme_variant: e.target.value }))}>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="corporate">Corporate</option>
                <option value="custom">Custom</option>
              </select>
            </div>
          </div>

          {(createForm.mode === 'ai' || createForm.mode === 'wizard') && (
            <div className="grid md:grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs text-gray-400">AI Prompt</label>
                <textarea className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm h-24" value={createForm.ai_prompt} onChange={(e) => setCreateForm((prev) => ({ ...prev, ai_prompt: e.target.value }))} placeholder="Show monthly sales performance and compare by region" />
              </div>
              <div className="space-y-3">
                <div className="space-y-1">
                  <label className="text-xs text-gray-400">KPIs (comma-separated)</label>
                  <input className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={createForm.kpis} onChange={(e) => setCreateForm((prev) => ({ ...prev, kpis: e.target.value }))} placeholder="Revenue, Gross Margin, Attrition" />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-gray-400">Dimensions (comma-separated)</label>
                  <input className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={createForm.dimensions} onChange={(e) => setCreateForm((prev) => ({ ...prev, dimensions: e.target.value }))} placeholder="Region, Month, Department" />
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-end">
            <button className="btn-primary" onClick={handleCreateDashboard}>Generate Dashboard</button>
          </div>
        </div>
      )}

      <div className="grid lg:grid-cols-12 gap-4">
        <section className="lg:col-span-4 card space-y-3 max-h-[800px] overflow-y-auto">
          <h2 className="text-base font-semibold">Dashboard Workspace</h2>
          {items.map((item) => (
            <div key={item.id} className={`rounded-lg border p-3 transition-colors ${activeDashboardId === item.id ? 'border-prism-700 bg-prism-950/40' : 'border-gray-800 bg-gray-950/40'}`}>
              <div className="flex items-start justify-between gap-2">
                <button className="text-left" onClick={() => setActiveDashboardId(item.id)}>
                  <p className="font-medium text-sm text-white">{item.name}</p>
                  <p className="text-xs text-gray-400 mt-1">{item.description || 'No description'}</p>
                </button>
                <span className={`badge ${badgeColor(item.status)}`}>{item.status}</span>
              </div>
              <div className="text-xs text-gray-400 mt-2 flex flex-wrap gap-2">
                <span>Folder: {item.folder || 'General'}</span>
                <span>Widgets: {item.widgets_count}</span>
                <span>Updated: {formatDate(item.last_updated)}</span>
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                <button className="btn-secondary text-xs px-2 py-1" onClick={() => handleUpdateDashboardMeta({ is_favourite: !item.favourite })}>{item.favourite ? 'Unfavourite' : 'Favourite'}</button>
                <button className="btn-secondary text-xs px-2 py-1" onClick={() => handleDuplicate(item)}>Duplicate</button>
                <button className="btn-secondary text-xs px-2 py-1" onClick={() => handleArchive(item)}>Archive</button>
                <button className="btn-secondary text-xs px-2 py-1" onClick={() => handleDelete(item)}>Delete</button>
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                {exportOptions.map((format) => (
                  <button key={format} className="text-[11px] px-2 py-1 rounded-md border border-gray-700 hover:border-prism-600" onClick={() => {
                    setActiveDashboardId(item.id)
                    setTimeout(() => handleExport(format), 0)
                  }}>
                    Export {format.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
          ))}

          <div className="flex items-center justify-between text-xs">
            <button className="btn-secondary px-2 py-1" onClick={() => setPage((prev) => Math.max(1, prev - 1))} disabled={page <= 1}>Prev</button>
            <span className="text-gray-400">Page {page} / {totalPages}</span>
            <button className="btn-secondary px-2 py-1" onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))} disabled={page >= totalPages}>Next</button>
          </div>
        </section>

        <section className="lg:col-span-8 space-y-4">
          {!activeDashboard ? (
            <div className="card text-sm text-gray-400">Select a dashboard from the workspace to open the studio canvas.</div>
          ) : (
            <>
              <div className="card space-y-3">
                <div className="flex flex-wrap gap-3 items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-white">{activeDashboard.name}</h2>
                    <p className="text-xs text-gray-400">{activeDashboard.description || 'No description provided'} · Mode: {humanize(activeDashboard.creation_mode)}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button className="btn-secondary text-xs px-3 py-1.5" onClick={saveDraft}>Save Draft</button>
                    <button className="btn-primary text-xs px-3 py-1.5" onClick={publishDashboard}>Publish</button>
                    <button className="btn-secondary text-xs px-3 py-1.5" onClick={compareVersions}>Compare Versions</button>
                    <button className="btn-secondary text-xs px-3 py-1.5" onClick={undoLayout} disabled={historyCursor <= 0}>Undo</button>
                    <button className="btn-secondary text-xs px-3 py-1.5" onClick={redoLayout} disabled={historyCursor >= history.length - 1}>Redo</button>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-3 text-xs text-gray-400">
                  <div className="space-y-1">
                    <p>Status: <span className="text-gray-200">{activeDashboard.status}</span></p>
                    <p>Folder: <span className="text-gray-200">{activeDashboard.folder || 'General'}</span></p>
                    <p>Semantic Model: <span className="text-gray-200">{activeDashboard.semantic_model || 'Not linked'}</span></p>
                    <p>Auto Save: <span className="text-gray-200">{activeDashboard.auto_save_enabled ? 'Enabled' : 'Disabled'}</span></p>
                  </div>
                  <div className="space-y-1">
                    <p>Created: <span className="text-gray-200">{formatDate(activeDashboard.created_date)}</span></p>
                    <p>Updated: <span className="text-gray-200">{formatDate(activeDashboard.last_updated)}</span></p>
                    <p>Version: <span className="text-gray-200">v{activeDashboard.current_version}</span></p>
                    <p>Shared With: <span className="text-gray-200">{activeDashboard.shared_with?.join(', ') || 'None'}</span></p>
                  </div>
                </div>
              </div>

              <div className="card space-y-3">
                <div className="flex flex-wrap gap-2 items-center justify-between">
                  <h3 className="font-semibold text-sm">Canvas & Widget Engine</h3>
                  <div className="flex flex-wrap gap-2">
                    <select className="bg-gray-950 border border-gray-800 rounded-lg px-2 py-1 text-xs" onChange={(e) => addWidget(e.target.value)} defaultValue="kpi_card">
                      {widgetTypeOptions.map((type) => <option key={type} value={type}>Add {humanize(type)}</option>)}
                    </select>
                    <button className="btn-secondary text-xs px-3 py-1.5" onClick={refreshAIRecommendations}>AI Recommendations</button>
                    <button className="btn-secondary text-xs px-3 py-1.5" onClick={optimizeDashboard}>Optimize Layout</button>
                  </div>
                </div>

                {widgets.length === 0 ? (
                  <div className="border border-dashed border-gray-700 rounded-lg p-8 text-center text-sm text-gray-400">
                    Blank canvas ready. Add widgets using the selector to start composing this dashboard.
                  </div>
                ) : (
                  <div className="grid grid-cols-12 gap-3">
                    {widgets
                      .slice()
                      .sort((a, b) => a.position_y - b.position_y || a.position_x - b.position_x)
                      .map((widget) => (
                        <div key={widget.id} className="col-span-12 md:col-span-6 xl:col-span-4 border border-gray-800 rounded-lg bg-gray-950/60 p-3 space-y-2">
                          <div className="flex items-start justify-between">
                            <div>
                              <p className="text-sm font-medium text-white">{widget.title || humanize(widget.widget_type)}</p>
                              <p className="text-[11px] text-gray-400">{humanize(widget.widget_type)} · {widget.width}x{widget.height}</p>
                            </div>
                            <span className={`badge ${widget.is_locked ? 'bg-orange-900 text-orange-300' : 'bg-gray-800 text-gray-300'}`}>{widget.is_locked ? 'Locked' : 'Editable'}</span>
                          </div>
                          <p className="text-xs text-gray-400">{widget.description || 'No description'}</p>

                          <div className="grid grid-cols-2 gap-2 text-[11px]">
                            <button className="btn-secondary px-2 py-1" onClick={() => patchWidget(widget.id, { position_x: Math.max(0, widget.position_x - 1) }, 'Widget moved left')}>Move ←</button>
                            <button className="btn-secondary px-2 py-1" onClick={() => patchWidget(widget.id, { position_x: widget.position_x + 1 }, 'Widget moved right')}>Move →</button>
                            <button className="btn-secondary px-2 py-1" onClick={() => patchWidget(widget.id, { position_y: Math.max(0, widget.position_y - 1) }, 'Widget moved up')}>Move ↑</button>
                            <button className="btn-secondary px-2 py-1" onClick={() => patchWidget(widget.id, { position_y: widget.position_y + 1 }, 'Widget moved down')}>Move ↓</button>
                            <button className="btn-secondary px-2 py-1" onClick={() => patchWidget(widget.id, { width: Math.min(8, widget.width + 1) }, 'Widget resized wider')}>Resize +W</button>
                            <button className="btn-secondary px-2 py-1" onClick={() => patchWidget(widget.id, { height: Math.min(8, widget.height + 1) }, 'Widget resized taller')}>Resize +H</button>
                            <button className="btn-secondary px-2 py-1" onClick={() => patchWidget(widget.id, { is_locked: !widget.is_locked }, widget.is_locked ? 'Widget unlocked' : 'Widget locked')}>{widget.is_locked ? 'Unlock' : 'Lock'}</button>
                            <button className="btn-secondary px-2 py-1" onClick={() => patchWidget(widget.id, { snap_to_grid: !widget.snap_to_grid }, widget.snap_to_grid ? 'Snap disabled' : 'Snap enabled')}>{widget.snap_to_grid ? 'Unsnap' : 'Snap'}</button>
                            <button className="btn-secondary px-2 py-1" onClick={() => patchWidget(widget.id, { group_key: widget.group_key ? '' : `group-${widget.id}` }, widget.group_key ? 'Ungrouped' : 'Grouped')}>{widget.group_key ? 'Ungroup' : 'Group'}</button>
                            <button className="btn-secondary px-2 py-1" onClick={() => patchWidget(widget.id, { alignment: widget.alignment === 'center' ? 'start' : 'center' }, 'Alignment updated')}>Align</button>
                            <button className="btn-secondary px-2 py-1" onClick={() => copyWidget(widget)}>Copy</button>
                            <button className="btn-secondary px-2 py-1" onClick={() => removeWidget(widget.id)}>Delete</button>
                          </div>
                        </div>
                      ))}
                  </div>
                )}
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="card space-y-3">
                  <h3 className="font-semibold text-sm">Filters & Drill</h3>
                  <div className="grid grid-cols-2 gap-2">
                    <select className="bg-gray-950 border border-gray-800 rounded-lg px-2 py-1 text-xs" value={filterForm.scope} onChange={(e) => setFilterForm((prev) => ({ ...prev, scope: e.target.value }))}>
                      {filterScopeOptions.map((scope) => <option key={scope} value={scope}>{humanize(scope)}</option>)}
                    </select>
                    <select className="bg-gray-950 border border-gray-800 rounded-lg px-2 py-1 text-xs" value={filterForm.widget_id} onChange={(e) => setFilterForm((prev) => ({ ...prev, widget_id: e.target.value }))}>
                      <option value="">Widget (optional)</option>
                      {widgets.map((widget) => <option key={widget.id} value={widget.id}>{widget.title || `Widget ${widget.id}`}</option>)}
                    </select>
                    <input className="bg-gray-950 border border-gray-800 rounded-lg px-2 py-1 text-xs" value={filterForm.name} onChange={(e) => setFilterForm((prev) => ({ ...prev, name: e.target.value }))} placeholder="Filter name" />
                    <input className="bg-gray-950 border border-gray-800 rounded-lg px-2 py-1 text-xs" value={filterForm.field} onChange={(e) => setFilterForm((prev) => ({ ...prev, field: e.target.value }))} placeholder="Field" />
                    <input className="bg-gray-950 border border-gray-800 rounded-lg px-2 py-1 text-xs" value={filterForm.operator} onChange={(e) => setFilterForm((prev) => ({ ...prev, operator: e.target.value }))} placeholder="Operator" />
                    <input className="bg-gray-950 border border-gray-800 rounded-lg px-2 py-1 text-xs" value={filterForm.value} onChange={(e) => setFilterForm((prev) => ({ ...prev, value: e.target.value }))} placeholder="Value / expression" />
                  </div>
                  <button className="btn-primary text-xs px-3 py-1.5" onClick={saveFilter}>Save Filter</button>

                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {filters.map((item) => (
                      <div key={item.id} className="border border-gray-800 rounded-lg p-2 text-xs flex items-start justify-between gap-2">
                        <div>
                          <p className="text-gray-200">{item.name}</p>
                          <p className="text-gray-400">{humanize(item.scope)} · {item.field} {item.operator}</p>
                          <p className="text-gray-500">Drill path: Country → State → City → Branch, Year → Quarter → Month → Day</p>
                        </div>
                        <button className="text-red-300 hover:text-red-200" onClick={() => removeFilter(item.id)}>Remove</button>
                      </div>
                    ))}
                    {!filters.length && <p className="text-xs text-gray-500">No filters configured.</p>}
                  </div>
                </div>

                <div className="card space-y-3">
                  <h3 className="font-semibold text-sm">Sharing, Roles & Security</h3>
                  <div className="grid grid-cols-3 gap-2">
                    <select className="bg-gray-950 border border-gray-800 rounded-lg px-2 py-1 text-xs" value={shareForm.visibility} onChange={(e) => setShareForm((prev) => ({ ...prev, visibility: e.target.value }))}>
                      {shareVisibilityOptions.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}
                    </select>
                    <input className="bg-gray-950 border border-gray-800 rounded-lg px-2 py-1 text-xs" value={shareForm.principal} onChange={(e) => setShareForm((prev) => ({ ...prev, principal: e.target.value }))} placeholder="user@company.com / team" />
                    <select className="bg-gray-950 border border-gray-800 rounded-lg px-2 py-1 text-xs" value={shareForm.role} onChange={(e) => setShareForm((prev) => ({ ...prev, role: e.target.value }))}>
                      {shareRoleOptions.map((role) => <option key={role} value={role}>{humanize(role)}</option>)}
                    </select>
                  </div>
                  <button className="btn-primary text-xs px-3 py-1.5" onClick={addSharePermission}>Add Permission</button>

                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {permissions.map((item) => (
                      <div key={item.id} className="border border-gray-800 rounded-lg p-2 text-xs flex items-center justify-between">
                        <div>
                          <p className="text-gray-200">{item.principal}</p>
                          <p className="text-gray-400">{humanize(item.visibility)} · {humanize(item.role)}</p>
                        </div>
                        <button className="text-red-300 hover:text-red-200" onClick={() => removeSharePermission(item.id)}>Remove</button>
                      </div>
                    ))}
                    {!permissions.length && <p className="text-xs text-gray-500">No sharing permissions configured.</p>}
                  </div>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="card space-y-3">
                  <h3 className="font-semibold text-sm">Version History</h3>
                  <div className="space-y-2 max-h-56 overflow-y-auto">
                    {versions.map((version) => (
                      <div key={version.id} className="border border-gray-800 rounded-lg p-2 text-xs flex justify-between gap-2">
                        <div>
                          <p className="text-gray-200">v{version.version_number} · {version.title}</p>
                          <p className="text-gray-400">{version.description || 'No note'} · {formatDate(version.created_at)}</p>
                        </div>
                        <button className="btn-secondary text-xs px-2 py-1" onClick={() => restoreVersion(version.id)}>Restore</button>
                      </div>
                    ))}
                    {!versions.length && <p className="text-xs text-gray-500">No versions yet.</p>}
                  </div>
                </div>

                <div className="card space-y-3">
                  <h3 className="font-semibold text-sm">AI Optimization & Performance</h3>
                  <div className="text-xs text-gray-400 space-y-1">
                    <p>Views (7d): <span className="text-gray-200">{usage?.views_last_7_days ?? 0}</span></p>
                    <p>Avg render time: <span className="text-gray-200">{usage?.avg_render_time_ms ?? 0} ms</span></p>
                    <p>Avg widget count: <span className="text-gray-200">{usage?.avg_widget_count ?? 0}</span></p>
                    <p>Last viewed: <span className="text-gray-200">{usage?.last_viewed_at ? formatDate(usage.last_viewed_at) : 'Never'}</span></p>
                  </div>

                  <div className="space-y-2 max-h-56 overflow-y-auto">
                    {recommendations.map((item, index) => (
                      <div key={item.id ?? index} className="border border-gray-800 rounded-lg p-2 text-xs">
                        <p className="text-gray-200">{item.title}</p>
                        <p className="text-gray-400">{item.description || item.reason}</p>
                        <p className="text-gray-500">Type: {humanize(item.recommendation_type)} · Confidence: {(item.confidence * 100).toFixed(0)}%</p>
                      </div>
                    ))}
                    {!recommendations.length && <p className="text-xs text-gray-500">No recommendations available. Run optimization.</p>}
                  </div>
                </div>
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  )
}

function SummaryCard({ label, value }) {
  return (
    <div className="card border border-gray-800">
      <p className="text-xs text-gray-400">{label}</p>
      <p className="text-2xl font-bold text-white mt-1">{value}</p>
    </div>
  )
}

function splitCsv(value) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function humanize(value) {
  return String(value || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString()
}

function badgeColor(status) {
  if (status === 'published') return 'bg-green-900 text-green-300'
  if (status === 'archived') return 'bg-gray-800 text-gray-300'
  return 'bg-orange-900 text-orange-300'
}
