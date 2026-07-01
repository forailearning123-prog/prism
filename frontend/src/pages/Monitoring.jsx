import React, { useState, useEffect, useCallback } from 'react'
import { monitoringService } from '../services/monitoring'
import {
  Activity,
  Bell,
  BellOff,
  BrainCircuit,
  CheckCircle,
  ChevronDown,
  Clock,
  Copy,
  Download,
  Edit3,
  Eye,
  Filter,
  Plus,
  RefreshCw,
  Search,
  Shield,
  Sliders,
  Trash2,
  TrendingUp,
  XCircle,
  Zap,
  AlertTriangle,
  BarChart3,
  FileText,
  Gauge,
  Layers,
  Mail,
  MessageSquare,
  Play,
  Settings,
  Users,
  Webhook,
  Ban,
  AlertCircle,
  CheckCheck,
  MoreHorizontal,
} from 'lucide-react'

const tabs = [
  { id: 'overview', label: 'Overview', icon: Activity },
  { id: 'monitors', label: 'Monitors', icon: Eye },
  { id: 'alerts', label: 'Alerts', icon: Bell },
  { id: 'anomalies', label: 'Anomalies', icon: BrainCircuit },
  { id: 'workflows', label: 'Workflows', icon: Play },
  { id: 'notifications', label: 'Notifications', icon: MessageSquare },
  { id: 'escalations', label: 'Escalations', icon: Shield },
  { id: 'insights', label: 'Scheduled Insights', icon: FileText },
  { id: 'sla', label: 'SLA Metrics', icon: Gauge },
  { id: 'health', label: 'Health Score', icon: TrendingUp },
  { id: 'audit', label: 'Audit Log', icon: Layers },
]

const severityColors = {
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
  high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  low: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  informational: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
}

const statusColors = {
  active: 'bg-green-500/20 text-green-400',
  inactive: 'bg-gray-500/20 text-gray-400',
  archived: 'bg-red-500/20 text-red-400',
  open: 'bg-red-500/20 text-red-400',
  acknowledged: 'bg-yellow-500/20 text-yellow-400',
  resolved: 'bg-green-500/20 text-green-400',
  dismissed: 'bg-gray-500/20 text-gray-400',
  compliant: 'bg-green-500/20 text-green-400',
  breached: 'bg-red-500/20 text-red-400',
}

export default function Monitoring() {
  const [activeTab, setActiveTab] = useState('overview')
  const [stats, setStats] = useState(null)
  const [monitors, setMonitors] = useState([])
  const [alerts, setAlerts] = useState([])
  const [anomalies, setAnomalies] = useState([])
  const [workflows, setWorkflows] = useState([])
  const [healthScore, setHealthScore] = useState(null)
  const [slaMetrics, setSlaMetrics] = useState([])
  const [scheduledInsights, setScheduledInsights] = useState([])
  const [notifications, setNotifications] = useState([])
  const [escalationPolicies, setEscalationPolicies] = useState([])
  const [auditRecords, setAuditRecords] = useState([])
  const [notificationConfigs, setNotificationConfigs] = useState([])
  const [templates, setTemplates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [unreadCount, setUnreadCount] = useState(0)

  // Modal states
  const [showCreateMonitor, setShowCreateMonitor] = useState(false)
  const [showCreateWorkflow, setShowCreateWorkflow] = useState(false)
  const [showCreateInsight, setShowCreateInsight] = useState(false)
  const [showCreateSLA, setShowCreateSLA] = useState(false)
  const [showCreateEscalation, setShowCreateEscalation] = useState(false)
  const [showAlertDetail, setShowAlertDetail] = useState(null)
  const [showTemplateSelector, setShowTemplateSelector] = useState(false)

  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const [statsRes, unreadRes] = await Promise.all([
        monitoringService.getStats(),
        monitoringService.getUnreadCount(),
      ])
      setStats(statsRes.data)
      setUnreadCount(unreadRes.data.count)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load monitoring data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  useEffect(() => {
    loadTabData(activeTab)
  }, [activeTab, page])

  const loadTabData = async (tab) => {
    try {
      switch (tab) {
        case 'monitors': {
          const res = await monitoringService.getMonitors({ search, page, page_size: 20 })
          setMonitors(res.data.items || [])
          break
        }
        case 'alerts': {
          const res = await monitoringService.getAlerts({ page, page_size: 20 })
          setAlerts(res.data.items || [])
          break
        }
        case 'anomalies': {
          const res = await monitoringService.getAnomalies({ page, page_size: 20 })
          setAnomalies(res.data.items || [])
          break
        }
        case 'workflows': {
          const res = await monitoringService.getWorkflows({ page, page_size: 20 })
          setWorkflows(res.data.items || [])
          break
        }
        case 'notifications': {
          const [configRes, notifRes] = await Promise.all([
            monitoringService.getNotificationConfigs(),
            monitoringService.getNotifications({ page, page_size: 20 }),
          ])
          setNotificationConfigs(configRes.data || [])
          setNotifications(notifRes.data || [])
          break
        }
        case 'escalations': {
          const res = await monitoringService.getEscalationPolicies()
          setEscalationPolicies(res.data || [])
          break
        }
        case 'insights': {
          const res = await monitoringService.getScheduledInsights({ page, page_size: 20 })
          setScheduledInsights(res.data.items || [])
          break
        }
        case 'sla': {
          const res = await monitoringService.getSLAMetrics({ page, page_size: 20 })
          setSlaMetrics(res.data.items || [])
          break
        }
        case 'health': {
          const res = await monitoringService.getHealthScore()
          setHealthScore(res.data)
          break
        }
        case 'audit': {
          const res = await monitoringService.getAuditRecords({ page, page_size: 50 })
          setAuditRecords(res.data.items || [])
          break
        }
        case 'overview': {
          const [tmplRes] = await Promise.all([
            monitoringService.getTemplates(),
          ])
          setTemplates(tmplRes.data || [])
          break
        }
      }
    } catch (err) {
      console.error(`Error loading ${tab}:`, err)
    }
  }

  const handleCreateMonitor = async (data) => {
    try {
      await monitoringService.createMonitor(data)
      setShowCreateMonitor(false)
      loadTabData('monitors')
    } catch (err) {
      alert(err?.response?.data?.detail || 'Failed to create monitor')
    }
  }

  const handleAcknowledge = async (id) => {
    await monitoringService.acknowledgeAlert(id)
    loadTabData('alerts')
  }

  const handleResolve = async (id, notes = '') => {
    await monitoringService.resolveAlert(id, { resolution_notes: notes })
    loadTabData('alerts')
  }

  const handleToggle = async (id) => {
    await monitoringService.toggleMonitor(id)
    loadTabData('monitors')
  }

  const handleDuplicate = async (id) => {
    await monitoringService.duplicateMonitor(id)
    loadTabData('monitors')
  }

  const handleEvaluate = async () => {
    await monitoringService.evaluateAll()
    loadData()
  }

  const handleDetectAnomalies = async () => {
    await monitoringService.detectAnomalies()
    loadTabData('anomalies')
  }

  const handleRefreshHealth = async () => {
    const res = await monitoringService.refreshHealthScore()
    setHealthScore(res.data)
  }

  const handleApplyTemplate = async (id) => {
    await monitoringService.applyTemplate(id)
    setShowTemplateSelector(false)
    loadTabData('monitors')
  }

  const NotificationBell = () => (
    <div className="relative">
      <Bell size={20} />
      {unreadCount > 0 && (
        <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
          {unreadCount > 9 ? '9+' : unreadCount}
        </span>
      )}
    </div>
  )

  // ── Render Main ──
  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="animate-spin text-prism-500" size={32} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Real-Time Monitoring</h1>
          <p className="text-gray-400 mt-1">Intelligence, monitoring & automation</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleEvaluate}
            className="btn btn-ghost btn-sm"
          >
            <RefreshCw size={14} /> Evaluate All
          </button>
          <button
            onClick={handleDetectAnomalies}
            className="btn btn-ghost btn-sm"
          >
            <BrainCircuit size={14} /> Detect Anomalies
          </button>
          <NotificationBell />
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => { setActiveTab(tab.id); setPage(1) }}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? 'bg-prism-900/60 text-prism-300 border border-prism-800'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
            }`}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── OVERVIEW ── */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Stats Cards */}
          {stats && (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
              <StatCard icon={Eye} label="Total Monitors" value={stats.total_monitors} color="blue" />
              <StatCard icon={Activity} label="Active" value={stats.active_monitors} color="green" />
              <StatCard icon={Bell} label="Total Alerts" value={stats.total_alerts} color="yellow" />
              <StatCard icon={AlertTriangle} label="Open Alerts" value={stats.open_alerts} color="red" />
              <StatCard icon={XCircle} label="Critical" value={stats.critical_alerts} color="red" />
              <StatCard icon={BrainCircuit} label="Anomalies" value={stats.recent_anomalies} color="purple" />
              <StatCard icon={TrendingUp} label="Health Score" value={stats.health_score ? `${Math.round(stats.health_score)}%` : 'N/A'} color="green" />
            </div>
          )}

          {/* Templates */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Quick Start Templates</h2>
              <button
                onClick={() => setShowTemplateSelector(true)}
                className="btn btn-primary btn-sm"
              >
                <Plus size={14} /> Apply Template
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {templates.map((tmpl) => (
                <div key={tmpl.id} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                  <h3 className="text-white font-medium">{tmpl.name}</h3>
                  <p className="text-gray-400 text-sm mt-1">{tmpl.description}</p>
                  <div className="flex gap-2 mt-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${severityColors[tmpl.severity] || 'bg-gray-500/20 text-gray-400'}`}>
                      {tmpl.severity}
                    </span>
                    <span className="text-xs text-gray-500 bg-gray-700/50 px-2 py-0.5 rounded">{tmpl.frequency}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── MONITORS ── */}
      {activeTab === 'monitors' && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search monitors..."
                  className="bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-500 w-64"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <button onClick={() => setShowTemplateSelector(true)} className="btn btn-ghost btn-sm">
                <Copy size={14} /> From Template
              </button>
              <button onClick={() => setShowCreateMonitor(true)} className="btn btn-primary btn-sm">
                <Plus size={14} /> Create Monitor
              </button>
            </div>
          </div>

          <div className="space-y-3">
            {monitors.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Eye size={48} className="mx-auto mb-3 opacity-30" />
                <p>No monitors yet</p>
                <button onClick={() => setShowCreateMonitor(true)} className="btn btn-primary btn-sm mt-3">
                  Create your first monitor
                </button>
              </div>
            ) : (
              monitors.map((m) => (
                <div key={m.id} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${m.status === 'active' ? 'bg-green-500' : 'bg-gray-500'}`} />
                      <div>
                        <h3 className="text-white font-medium">{m.name}</h3>
                        <p className="text-gray-400 text-sm">{m.description || 'No description'}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${severityColors[m.severity]}`}>
                        {m.severity}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusColors[m.status]}`}>
                        {m.status}
                      </span>
                      <button onClick={() => handleToggle(m.id)} className="btn btn-ghost btn-xs">
                        {m.status === 'active' ? <Ban size={14} /> : <Play size={14} />}
                      </button>
                      <button onClick={() => handleDuplicate(m.id)} className="btn btn-ghost btn-xs">
                        <Copy size={14} />
                      </button>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                    <span>Frequency: {m.frequency}</span>
                    <span>Rules: {m.rules?.length || 0}</span>
                    <span>Alerts: {m.alert_count}</span>
                    <span>Evaluations: {m.evaluation_count}</span>
                    {m.last_evaluated_at && <span>Last: {new Date(m.last_evaluated_at).toLocaleString()}</span>}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* ── ALERTS ── */}
      {activeTab === 'alerts' && (
        <div className="space-y-3">
          {alerts.length === 0 ? (
            <div className="card text-center py-12 text-gray-500">
              <Bell size={48} className="mx-auto mb-3 opacity-30" />
              <p>No alerts</p>
            </div>
          ) : (
            alerts.map((alert) => (
              <div key={alert.id} className="card">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className={`mt-1 w-2 h-2 rounded-full ${alert.severity === 'critical' ? 'bg-red-500' : alert.severity === 'high' ? 'bg-orange-500' : 'bg-yellow-500'}`} />
                    <div>
                      <h3 className="text-white font-medium">{alert.title}</h3>
                      <p className="text-gray-400 text-sm mt-1">{alert.message}</p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                        <span>{new Date(alert.created_at).toLocaleString()}</span>
                        <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${statusColors[alert.status]}`}>
                          {alert.status}
                        </span>
                        <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${severityColors[alert.severity]}`}>
                          {alert.severity}
                        </span>
                        <span>Source: {alert.source}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {alert.status === 'open' && (
                      <>
                        <button onClick={() => handleAcknowledge(alert.id)} className="btn btn-ghost btn-xs">
                          <CheckCircle size={14} /> Acknowledge
                        </button>
                        <button onClick={() => handleResolve(alert.id)} className="btn btn-ghost btn-xs">
                          <CheckCheck size={14} /> Resolve
                        </button>
                      </>
                    )}
                  </div>
                </div>
                {alert.possible_causes?.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-700">
                    <p className="text-xs text-gray-500 mb-1">Possible causes:</p>
                    <ul className="text-xs text-gray-400 space-y-0.5">
                      {alert.possible_causes.slice(0, 3).map((c, i) => (
                        <li key={i}>• {c}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* ── ANOMALIES ── */}
      {activeTab === 'anomalies' && (
        <div className="space-y-3">
          {anomalies.length === 0 ? (
            <div className="card text-center py-12 text-gray-500">
              <BrainCircuit size={48} className="mx-auto mb-3 opacity-30" />
              <p>No anomalies detected</p>
            </div>
          ) : (
            anomalies.map((a) => (
              <div key={a.id} className="card">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-white font-medium">{a.metric_name}</h3>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${severityColors[a.severity]}`}>
                        {a.severity}
                      </span>
                    </div>
                    <p className="text-gray-400 text-sm mt-1">{a.ai_explanation}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                      <span>Category: {a.category}</span>
                      <span>Score: {a.anomaly_score?.toFixed(2)}</span>
                      <span>Confidence: {(a.confidence * 100).toFixed(0)}%</span>
                      <span>Value: {a.metric_value?.toFixed(2)}</span>
                      <span>Expected: {a.expected_value?.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
                {a.possible_causes?.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-700">
                    <p className="text-xs text-gray-500 mb-1">Suggested actions:</p>
                    <ul className="text-xs text-gray-400 space-y-0.5">
                      {a.suggested_actions?.slice(0, 3).map((s, i) => (
                        <li key={i}>• {s}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* ── WORKFLOWS ── */}
      {activeTab === 'workflows' && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Automation Workflows</h2>
            <button onClick={() => setShowCreateWorkflow(true)} className="btn btn-primary btn-sm">
              <Plus size={14} /> Create Workflow
            </button>
          </div>
          {workflows.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Play size={48} className="mx-auto mb-3 opacity-30" />
              <p>No workflows yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {workflows.map((w) => (
                <div key={w.id} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-white font-medium">{w.name}</h3>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${w.is_active ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                          {w.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                      <p className="text-gray-400 text-sm">{w.description}</p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                        <span>Trigger: {w.trigger_type}</span>
                        <span>Steps: {w.steps?.length || 0}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => monitoringService.executeWorkflow(w.id).then(() => loadTabData('workflows'))}
                      className="btn btn-ghost btn-sm"
                    >
                      <Play size={14} /> Run
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── NOTIFICATIONS ── */}
      {activeTab === 'notifications' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 card">
            <h2 className="text-lg font-semibold text-white mb-4">Recent Notifications</h2>
            {notifications.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <MessageSquare size={48} className="mx-auto mb-3 opacity-30" />
                <p>No notifications</p>
              </div>
            ) : (
              <div className="space-y-2">
                {notifications.map((n) => (
                  <div key={n.id} className="flex items-center justify-between bg-gray-800/50 rounded-lg p-3 border border-gray-700">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${n.read_at ? 'bg-gray-600' : 'bg-prism-500'}`} />
                      <div>
                        <p className="text-sm text-white">{n.channel}</p>
                        <p className="text-xs text-gray-500">{n.status} · {new Date(n.created_at).toLocaleString()}</p>
                      </div>
                    </div>
                    {!n.read_at && (
                      <button onClick={() => monitoringService.markNotificationRead(n.id).then(loadData)} className="btn btn-ghost btn-xs">
                        Mark Read
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Notification Settings</h2>
            {notificationConfigs.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Settings size={32} className="mx-auto mb-2 opacity-30" />
                <p className="text-sm">No channels configured</p>
              </div>
            ) : (
              <div className="space-y-2">
                {notificationConfigs.map((c) => (
                  <div key={c.id} className="flex items-center justify-between bg-gray-800/50 rounded-lg p-3">
                    <span className="text-sm text-white">{c.channel}</span>
                    <span className={`text-xs ${c.enabled ? 'text-green-400' : 'text-gray-500'}`}>
                      {c.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── HEALTH SCORE ── */}
      {activeTab === 'health' && (
        <div className="space-y-6">
          {healthScore && (
            <div className="card">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-white">Business Health Score</h2>
                <button onClick={handleRefreshHealth} className="btn btn-ghost btn-sm">
                  <RefreshCw size={14} /> Refresh
                </button>
              </div>
              <div className="flex items-center gap-8 mb-6">
                <div className="relative w-32 h-32">
                  <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 36 36">
                    <circle cx="18" cy="18" r="15.5" fill="none" stroke="#1f2937" strokeWidth="3" />
                    <circle
                      cx="18" cy="18" r="15.5" fill="none"
                      stroke={healthScore.overall_score >= 70 ? '#22c55e' : healthScore.overall_score >= 40 ? '#eab308' : '#ef4444'}
                      strokeWidth="3"
                      strokeDasharray={`${healthScore.overall_score}, 100`}
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl font-bold text-white">{Math.round(healthScore.overall_score)}%</span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 flex-1">
                  <HealthDimension label="KPI Performance" value={healthScore.kpi_performance} />
                  <HealthDimension label="Forecast Confidence" value={healthScore.forecast_confidence} />
                  <HealthDimension label="Active Risks" value={healthScore.active_risks} />
                  <HealthDimension label="Open Alerts" value={healthScore.open_alerts} />
                  <HealthDimension label="Data Quality" value={healthScore.data_quality} />
                  <HealthDimension label="Operational Efficiency" value={healthScore.operational_efficiency} />
                </div>
              </div>
              <p className="text-xs text-gray-500">Last updated: {new Date(healthScore.created_at).toLocaleString()}</p>
            </div>
          )}
        </div>
      )}

      {/* ── SLA ── */}
      {activeTab === 'sla' && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">SLA Metrics</h2>
            <button onClick={() => setShowCreateSLA(true)} className="btn btn-primary btn-sm">
              <Plus size={14} /> Add SLA Metric
            </button>
          </div>
          {slaMetrics.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Gauge size={48} className="mx-auto mb-3 opacity-30" />
              <p>No SLA metrics configured</p>
            </div>
          ) : (
            <div className="space-y-3">
              {slaMetrics.map((s) => (
                <div key={s.id} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-white font-medium">{s.name}</h3>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusColors[s.status]}`}>
                          {s.status}
                        </span>
                      </div>
                      <p className="text-gray-400 text-sm mt-1">{s.description}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span>Target: {s.target_value} {s.target_unit}</span>
                        <span>Current: {s.current_value ?? 'N/A'}</span>
                        <span>Breaches: {s.breaches}</span>
                        <span>Trend: {s.trend}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── AUDIT ── */}
      {activeTab === 'audit' && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Audit Log</h2>
          {auditRecords.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Layers size={48} className="mx-auto mb-3 opacity-30" />
              <p>No audit records yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              {auditRecords.map((r) => (
                <div key={r.id} className="flex items-center gap-3 bg-gray-800/50 rounded-lg p-3 border border-gray-700 text-sm">
                  <Clock size={14} className="text-gray-500 shrink-0" />
                  <span className="text-gray-400 w-32">{new Date(r.created_at).toLocaleString()}</span>
                  <span className="text-prism-300 font-medium">{r.action}</span>
                  <span className="text-gray-500">{r.entity_type}#{r.entity_id}</span>
                  {r.user_id && <span className="text-gray-500">by user #{r.user_id}</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── ESCALATIONS ── */}
      {activeTab === 'escalations' && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Escalation Policies</h2>
            <button onClick={() => setShowCreateEscalation(true)} className="btn btn-primary btn-sm">
              <Plus size={14} /> Add Policy
            </button>
          </div>
          {escalationPolicies.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Shield size={48} className="mx-auto mb-3 opacity-30" />
              <p>No escalation policies</p>
            </div>
          ) : (
            <div className="space-y-3">
              {escalationPolicies.map((p) => (
                <div key={p.id} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                  <h3 className="text-white font-medium">{p.name}</h3>
                  <p className="text-xs text-gray-500 mt-1">
                    {p.steps?.length || 0} escalation step(s)
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── INSIGHTS ── */}
      {activeTab === 'insights' && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Scheduled Insights</h2>
            <button onClick={() => setShowCreateInsight(true)} className="btn btn-primary btn-sm">
              <Plus size={14} /> Schedule Insight
            </button>
          </div>
          {scheduledInsights.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <FileText size={48} className="mx-auto mb-3 opacity-30" />
              <p>No scheduled insights</p>
            </div>
          ) : (
            <div className="space-y-3">
              {scheduledInsights.map((s) => (
                <div key={s.id} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-white font-medium">{s.name}</h3>
                      <p className="text-gray-400 text-sm">{s.description}</p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                        <span>Schedule: {s.schedule_cron}</span>
                        <span>Format: {s.format}</span>
                        <span>KPIs: {s.included_kpis?.length || 0}</span>
                        <span>Recipients: {s.recipients?.length || 0}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Sub-components ──

function StatCard({ icon: Icon, label, value, color }) {
  const colors = {
    blue: 'bg-blue-500/10 text-blue-400',
    green: 'bg-green-500/10 text-green-400',
    yellow: 'bg-yellow-500/10 text-yellow-400',
    red: 'bg-red-500/10 text-red-400',
    purple: 'bg-purple-500/10 text-purple-400',
  }
  return (
    <div className={`card flex items-center gap-3 ${colors[color] || colors.blue}`}>
      <Icon size={24} />
      <div>
        <p className="text-2xl font-bold">{value ?? '—'}</p>
        <p className="text-xs opacity-80">{label}</p>
      </div>
    </div>
  )
}

function HealthDimension({ label, value }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <div className="flex items-center gap-2 mt-1">
        <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all"
            style={{
              width: `${Math.min(value, 100)}%`,
              backgroundColor: value >= 70 ? '#22c55e' : value >= 40 ? '#eab308' : '#ef4444',
            }}
          />
        </div>
        <span className="text-sm font-medium text-white w-10 text-right">{Math.round(value)}%</span>
      </div>
    </div>
  )
}