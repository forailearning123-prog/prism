import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Bell,
  Copy,
  Download,
  GitCompareArrows,
  Loader2,
  Play,
  Plus,
  RefreshCcw,
  Search,
  ShieldAlert,
  SlidersHorizontal,
  Sparkles,
  Target,
  Trash2,
  TrendingUp,
} from 'lucide-react'
import api from '../services/api'
import { forecastingService } from '../services/forecasting'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'

const KPI_OPTIONS = ['Revenue', 'Sales', 'Expenses', 'Profit', 'Employee Count', 'Customer Churn', 'Inventory', 'Cash Flow', 'Other']
const HORIZON_OPTIONS = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'yearly', label: 'Yearly' },
]
const DETAIL_TABS = ['overview', 'scenarios', 'what-if', 'drivers', 'risks', 'opportunities', 'versions', 'alerts']

const initialWizard = {
  name: '',
  description: '',
  business_domain: 'Finance',
  semantic_model_id: '',
  semantic_model_name: '',
  target_metric: 'Revenue',
  horizon: 'monthly',
  confidence_level: 0.95,
  variables: ['Demand', 'Pricing', 'Conversion'],
}

const initialScenarioForm = {
  name: '',
  description: '',
  variables: [{ name: 'Demand', base_value: 100, adjusted_value: 108, variable_type: 'percentage', unit: '%', impact_direction: 'positive' }],
}

const initialRiskForm = {
  name: '',
  risk_type: 'Market',
  risk_level: 'medium',
  probability: 0.35,
  business_impact: '',
  recommended_actions: 'Monitor drivers, define mitigation owner',
}

const initialCompareState = {
  primary_forecast_id: '',
  comparison_forecast_id: '',
}

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleString()
}

function formatShortDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString()
}

function formatMetric(value, metric = '') {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—'
  const lower = metric.toLowerCase()
  if (lower.includes('revenue') || lower.includes('sales') || lower.includes('expense') || lower.includes('profit') || lower.includes('cash')) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(Number(value))
  }
  if (lower.includes('churn')) {
    return `${Number(value).toFixed(2)}%`
  }
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: Number(value) >= 1000 ? 0 : 2 }).format(Number(value))
}

function statusBadgeClass(status) {
  if (status === 'ready') return 'bg-green-500/15 text-green-300 border border-green-500/30'
  if (status === 'generating') return 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/30'
  if (status === 'failed') return 'bg-red-500/15 text-red-300 border border-red-500/30'
  if (status === 'archived') return 'bg-gray-500/15 text-gray-300 border border-gray-500/30'
  return 'bg-gray-700/40 text-gray-300 border border-gray-600/50'
}

function riskBadgeClass(level) {
  if (level === 'critical') return 'bg-red-500/15 text-red-300 border border-red-500/30'
  if (level === 'high') return 'bg-orange-500/15 text-orange-300 border border-orange-500/30'
  if (level === 'medium') return 'bg-yellow-500/15 text-yellow-300 border border-yellow-500/30'
  return 'bg-green-500/15 text-green-300 border border-green-500/30'
}

function StatusBadge({ status }) {
  return (
    <span className={`badge gap-1 ${statusBadgeClass(status)}`}>
      {status === 'generating' && <Loader2 size={12} className="animate-spin" />}
      {status}
    </span>
  )
}

function RiskBadge({ level }) {
  return <span className={`badge ${riskBadgeClass(level)}`}>{level}</span>
}

function StatCard({ icon: Icon, label, value, accent = 'text-prism-300' }) {
  return (
    <div className="card">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm text-gray-400">{label}</p>
          <p className="text-3xl font-semibold text-white mt-2">{value}</p>
        </div>
        <div className={`w-12 h-12 rounded-xl bg-gray-800 flex items-center justify-center ${accent}`}>
          <Icon size={22} />
        </div>
      </div>
    </div>
  )
}

function ForecastTrendChart({ historical = [], forecast = [], upper = [], lower = [], metric = '' }) {
  const points = [...historical, ...forecast]
  const values = [...points, ...upper, ...lower].map((item) => Number(item.value))
  if (!points.length || !values.length) {
    return <div className="rounded-xl border border-dashed border-gray-700 p-8 text-sm text-gray-400">Generate a forecast to visualize projected trends.</div>
  }

  const width = 720
  const height = 320
  const padding = 34
  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)
  const span = Math.max(maxValue - minValue, 1)
  const pointX = (index) => padding + (index / Math.max(points.length - 1, 1)) * (width - padding * 2)
  const pointY = (value) => height - padding - ((Number(value) - minValue) / span) * (height - padding * 2)
  const historicalCoords = historical.map((item, index) => ({ ...item, x: pointX(index), y: pointY(item.value) }))
  const forecastCoords = forecast.map((item, index) => ({ ...item, x: pointX(historical.length + index), y: pointY(item.value) }))
  const upperCoords = upper.map((item, index) => ({ ...item, x: pointX(historical.length + index), y: pointY(item.value) }))
  const lowerCoords = lower.map((item, index) => ({ ...item, x: pointX(historical.length + index), y: pointY(item.value) }))
  const toPolyline = (coords) => coords.map((item) => `${item.x},${item.y}`).join(' ')
  const forecastLineCoords = historicalCoords.length ? [historicalCoords[historicalCoords.length - 1], ...forecastCoords] : forecastCoords
  const bandCoords = [...upperCoords, ...lowerCoords.slice().reverse()].map((item) => `${item.x},${item.y}`).join(' ')
  const bandLabel = forecastCoords[Math.max(0, forecastCoords.length - 1)]

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-4 text-xs text-gray-400">
        <span className="inline-flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-prism-500" />Historical</span>
        <span className="inline-flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-green-400" />Forecast</span>
        <span className="inline-flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-cyan-400/70" />Confidence range</span>
      </div>
      <div className="rounded-xl border border-gray-800 bg-gray-950/70 p-3 overflow-x-auto">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full min-w-[720px] h-[320px]">
          {[0, 1, 2, 3, 4].map((tick) => {
            const y = padding + ((height - padding * 2) / 4) * tick
            const tickValue = maxValue - (span / 4) * tick
            return (
              <g key={tick}>
                <line x1={padding} x2={width - padding} y1={y} y2={y} stroke="#1f2937" strokeDasharray="3 3" />
                <text x={8} y={y + 4} fill="#9ca3af" fontSize="11">{formatMetric(tickValue, metric)}</text>
              </g>
            )
          })}
          {bandCoords && <polygon points={bandCoords} fill="rgba(34, 211, 238, 0.12)" stroke="none" />}
          {historicalCoords.length > 1 && <polyline points={toPolyline(historicalCoords)} fill="none" stroke="#7c3aed" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />}
          {forecastLineCoords.length > 1 && <polyline points={toPolyline(forecastLineCoords)} fill="none" stroke="#22c55e" strokeWidth="3" strokeDasharray="8 6" strokeLinecap="round" strokeLinejoin="round" />}
          {historicalCoords.map((item) => <circle key={`h-${item.period}`} cx={item.x} cy={item.y} r="3" fill="#a78bfa" />)}
          {forecastCoords.map((item) => <circle key={`f-${item.period}`} cx={item.x} cy={item.y} r="3.5" fill="#22c55e" />)}
          {points.map((item, index) => {
            const x = pointX(index)
            return (
              <text key={`${item.period}-${index}`} x={x} y={height - 10} textAnchor="middle" fill="#9ca3af" fontSize="11">
                {index % 2 === 0 || points.length <= 8 ? item.period : ''}
              </text>
            )
          })}
          {bandLabel && <text x={bandLabel.x - 80} y={bandLabel.y - 18} fill="#67e8f9" fontSize="12">Confidence band</text>}
        </svg>
      </div>
    </div>
  )
}

function DriverBars({ drivers = [] }) {
  if (!drivers.length) {
    return <div className="rounded-xl border border-dashed border-gray-700 p-8 text-sm text-gray-400">Generate driver analysis to identify the strongest forecast inputs.</div>
  }

  return (
    <div className="space-y-4">
      {drivers.map((driver) => (
        <div key={driver.name} className="rounded-xl border border-gray-800 bg-gray-950/70 p-4">
          <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
            <div>
              <div className="flex items-center gap-2 text-white font-medium">
                <span>{driver.name}</span>
                {driver.direction === 'positive' ? <ArrowUpRight size={16} className="text-green-400" /> : <ArrowDownRight size={16} className="text-red-400" />}
              </div>
              <p className="text-sm text-gray-400 mt-1">{driver.description}</p>
            </div>
            <span className="text-sm text-prism-300 font-medium">{Math.round((driver.weight || 0) * 100)}%</span>
          </div>
          <div className="h-3 rounded-full bg-gray-800 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-prism-500 to-cyan-400" style={{ width: `${Math.max(6, (driver.weight || 0) * 100)}%` }} />
          </div>
        </div>
      ))}
    </div>
  )
}

function EmptyState({ title, description, actionLabel, onAction }) {
  return (
    <div className="card border-dashed border-gray-700 text-center py-12">
      <TrendingUp size={32} className="mx-auto text-prism-400 mb-3" />
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      <p className="text-sm text-gray-400 mt-2 max-w-xl mx-auto">{description}</p>
      {actionLabel && onAction && (
        <button className="btn-primary mt-5" onClick={onAction}>{actionLabel}</button>
      )}
    </div>
  )
}

export default function Forecasting() {
  const navigate = useNavigate()
  const { forecastId } = useParams()

  const [activeView, setActiveView] = useState(forecastId ? 'detail' : 'workspace')
  const [detailTab, setDetailTab] = useState('overview')
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState('')
  const [detailError, setDetailError] = useState('')
  const [notice, setNotice] = useState('')

  const [summary, setSummary] = useState(null)
  const [forecasts, setForecasts] = useState([])
  const [total, setTotal] = useState(0)
  const [semanticModels, setSemanticModels] = useState([])

  const [filters, setFilters] = useState({
    search: '',
    status: '',
    horizon: '',
    domain: '',
    sort_by: 'updated_at',
    sort_order: 'desc',
  })

  const [selectedForecast, setSelectedForecast] = useState(null)
  const [latestResult, setLatestResult] = useState(null)
  const [scenarios, setScenarios] = useState([])
  const [driverAnalysis, setDriverAnalysis] = useState(null)
  const [risks, setRisks] = useState([])
  const [opportunities, setOpportunities] = useState([])
  const [versions, setVersions] = useState([])
  const [alerts, setAlerts] = useState([])
  const [recommendations, setRecommendations] = useState([])

  const [wizardStep, setWizardStep] = useState(1)
  const [wizard, setWizard] = useState(initialWizard)
  const [wizardSubmitting, setWizardSubmitting] = useState(false)

  const [scenarioForm, setScenarioForm] = useState(initialScenarioForm)
  const [scenarioSubmitting, setScenarioSubmitting] = useState(false)

  const [riskForm, setRiskForm] = useState(initialRiskForm)
  const [riskSubmitting, setRiskSubmitting] = useState(false)

  const [whatIfVariables, setWhatIfVariables] = useState([])
  const [whatIfLoading, setWhatIfLoading] = useState(false)
  const [whatIfResult, setWhatIfResult] = useState(null)

  const [compareForm, setCompareForm] = useState(initialCompareState)
  const [compareResult, setCompareResult] = useState(null)
  const [compareLoading, setCompareLoading] = useState(false)

  const [selectedVersionIds, setSelectedVersionIds] = useState([])

  const domainOptions = useMemo(() => Array.from(new Set(forecasts.map((item) => item.business_domain).filter(Boolean))), [forecasts])
  const resolvedResult = latestResult || selectedForecast?.latest_result || null

  const loadWorkspace = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [summaryRes, forecastsRes, modelsRes] = await Promise.all([
        forecastingService.getWorkspaceSummary(),
        forecastingService.listForecasts({
          search: filters.search || undefined,
          status: filters.status || undefined,
          horizon: filters.horizon || undefined,
          domain: filters.domain || undefined,
          sort_by: filters.sort_by,
          sort_order: filters.sort_order,
          skip: 0,
          limit: 100,
        }),
        api.get('/api/v1/semantic-models', { params: { page: 1, page_size: 200 } }),
      ])
      setSummary(summaryRes.data)
      setForecasts(forecastsRes.data.items || [])
      setTotal(forecastsRes.data.total || 0)
      setSemanticModels(modelsRes.data.items || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [filters])

  const loadForecastDetail = useCallback(async (id, nextTab = detailTab) => {
    if (!id) return
    setDetailLoading(true)
    setDetailError('')
    try {
      const [forecastRes, latestRes, scenariosRes, versionsRes, alertsRes, recsRes, risksRes, oppsRes, driversRes] = await Promise.allSettled([
        forecastingService.getForecast(id),
        forecastingService.getLatestResult(id),
        forecastingService.listScenarios(id),
        forecastingService.listVersions(id),
        forecastingService.listAlerts(id),
        forecastingService.getRecommendations(id),
        forecastingService.listRisks({ forecast_id: id }),
        forecastingService.listOpportunities({ is_active: true }),
        forecastingService.getDriverAnalysis(id),
      ])

      if (forecastRes.status !== 'fulfilled') throw forecastRes.reason
      setSelectedForecast(forecastRes.value.data)
      setLatestResult(latestRes.status === 'fulfilled' ? latestRes.value.data : forecastRes.value.data.latest_result || null)
      setScenarios(scenariosRes.status === 'fulfilled' ? scenariosRes.value.data : [])
      setVersions(versionsRes.status === 'fulfilled' ? versionsRes.value.data : [])
      setAlerts(alertsRes.status === 'fulfilled' ? alertsRes.value.data : [])
      setRecommendations(recsRes.status === 'fulfilled' ? recsRes.value.data : [])
      setRisks(risksRes.status === 'fulfilled' ? risksRes.value.data.items || [] : [])
      setOpportunities(oppsRes.status === 'fulfilled' ? oppsRes.value.data.items || [] : [])
      setDriverAnalysis(driversRes.status === 'fulfilled' ? driversRes.value.data : null)
      setActiveView('detail')
      setDetailTab(nextTab)
    } catch (err) {
      setDetailError(err.message)
    } finally {
      setDetailLoading(false)
    }
  }, [detailTab])

  useEffect(() => {
    loadWorkspace()
  }, [loadWorkspace])

  useEffect(() => {
    if (forecastId) {
      loadForecastDetail(forecastId)
    }
  }, [forecastId, loadForecastDetail])

  useEffect(() => {
    if (!selectedForecast) {
      setWhatIfVariables([])
      setWhatIfResult(null)
      return
    }
    const variables = (selectedForecast.variables || []).map((name) => ({ name, adjustment_percent: 0 }))
    setWhatIfVariables(variables)
    setWhatIfResult(null)
  }, [selectedForecast])

  useEffect(() => {
    if (!selectedForecast || !whatIfVariables.length || activeView !== 'detail' || detailTab !== 'what-if') return
    const timer = setTimeout(async () => {
      setWhatIfLoading(true)
      try {
        const { data } = await forecastingService.runWhatIf(selectedForecast.id, whatIfVariables)
        setWhatIfResult(data)
      } catch (err) {
        setWhatIfResult(null)
      } finally {
        setWhatIfLoading(false)
      }
    }, 350)
    return () => clearTimeout(timer)
  }, [selectedForecast, whatIfVariables, activeView, detailTab])

  const openCreateWizard = () => {
    setWizard(initialWizard)
    setWizardStep(1)
    setActiveView('create')
  }

  const handleViewForecast = async (forecast) => {
    navigate(`/forecasting/${forecast.id}`)
    await loadForecastDetail(forecast.id)
  }

  const handleGenerateForecast = async (forecast) => {
    setNotice('')
    try {
      await forecastingService.generateForecast(forecast.id)
      setNotice(`Generated new forecast version for ${forecast.name}`)
      await loadWorkspace()
      if (selectedForecast?.id === forecast.id || String(forecastId) === String(forecast.id)) {
        await loadForecastDetail(forecast.id)
      }
    } catch (err) {
      setNotice(err.message)
    }
  }

  const handleDuplicateForecast = async (forecast) => {
    setNotice('')
    try {
      const { data } = await forecastingService.duplicateForecast(forecast.id)
      setNotice(`Duplicated ${forecast.name}`)
      await loadWorkspace()
      navigate(`/forecasting/${data.id}`)
      await loadForecastDetail(data.id)
    } catch (err) {
      setNotice(err.message)
    }
  }

  const handleDeleteForecast = async (forecast) => {
    const confirmed = window.confirm(`Archive "${forecast.name}"?`)
    if (!confirmed) return
    setNotice('')
    try {
      await forecastingService.deleteForecast(forecast.id)
      setNotice(`${forecast.name} archived`)
      if (selectedForecast?.id === forecast.id) {
        setSelectedForecast(null)
        navigate('/forecasting')
        setActiveView('workspace')
      }
      await loadWorkspace()
    } catch (err) {
      setNotice(err.message)
    }
  }

  const updateWizardVariable = (index, value) => {
    setWizard((prev) => ({
      ...prev,
      variables: prev.variables.map((item, itemIndex) => (itemIndex === index ? value : item)),
    }))
  }

  const addWizardVariable = () => {
    setWizard((prev) => ({ ...prev, variables: [...prev.variables, ''] }))
  }

  const removeWizardVariable = (index) => {
    setWizard((prev) => ({ ...prev, variables: prev.variables.filter((_, itemIndex) => itemIndex !== index) }))
  }

  const handleCreateForecast = async () => {
    setWizardSubmitting(true)
    setNotice('')
    try {
      const name = wizard.name.trim() || `${wizard.target_metric} Forecast`
      const payload = {
        name,
        description: wizard.description,
        business_domain: wizard.business_domain,
        semantic_model_id: wizard.semantic_model_id ? Number(wizard.semantic_model_id) : null,
        target_metric: wizard.target_metric,
        horizon: wizard.horizon,
        confidence_level: Number(wizard.confidence_level),
        variables: wizard.variables.map((item) => item.trim()).filter(Boolean),
      }
      const { data } = await forecastingService.createForecast(payload)
      await forecastingService.generateForecast(data.id)
      setNotice(`Created and generated ${name}`)
      setActiveView('detail')
      navigate(`/forecasting/${data.id}`)
      await loadWorkspace()
      await loadForecastDetail(data.id)
    } catch (err) {
      setNotice(err.message)
    } finally {
      setWizardSubmitting(false)
    }
  }

  const addScenarioVariable = () => {
    setScenarioForm((prev) => ({
      ...prev,
      variables: [...prev.variables, { name: '', base_value: 100, adjusted_value: 105, variable_type: 'percentage', unit: '%', impact_direction: 'positive' }],
    }))
  }

  const updateScenarioVariable = (index, field, value) => {
    setScenarioForm((prev) => ({
      ...prev,
      variables: prev.variables.map((item, itemIndex) => (itemIndex === index ? { ...item, [field]: value } : item)),
    }))
  }

  const handleCreateScenario = async () => {
    if (!selectedForecast) return
    setScenarioSubmitting(true)
    try {
      await forecastingService.createScenario(selectedForecast.id, {
        name: scenarioForm.name || `${selectedForecast.target_metric} sensitivity scenario`,
        description: scenarioForm.description,
        variables: scenarioForm.variables
          .filter((item) => item.name.trim())
          .map((item) => ({
            ...item,
            base_value: Number(item.base_value),
            adjusted_value: Number(item.adjusted_value),
          })),
      })
      setScenarioForm(initialScenarioForm)
      setNotice('Scenario created')
      await loadForecastDetail(selectedForecast.id, 'scenarios')
    } catch (err) {
      setNotice(err.message)
    } finally {
      setScenarioSubmitting(false)
    }
  }

  const handleRunScenario = async (scenario) => {
    if (!selectedForecast) return
    try {
      await forecastingService.runScenario(selectedForecast.id, scenario.id)
      setNotice(`Scenario "${scenario.name}" completed`)
      await loadForecastDetail(selectedForecast.id, 'scenarios')
    } catch (err) {
      setNotice(err.message)
    }
  }

  const handleDeleteScenario = async (scenario) => {
    if (!selectedForecast) return
    try {
      await forecastingService.deleteScenario(selectedForecast.id, scenario.id)
      setNotice(`Scenario "${scenario.name}" deleted`)
      await loadForecastDetail(selectedForecast.id, 'scenarios')
    } catch (err) {
      setNotice(err.message)
    }
  }

  const handleGenerateDrivers = async () => {
    if (!selectedForecast) return
    try {
      await forecastingService.generateDriverAnalysis(selectedForecast.id)
      setNotice('Driver analysis refreshed')
      await loadForecastDetail(selectedForecast.id, 'drivers')
    } catch (err) {
      setNotice(err.message)
    }
  }

  const handleCreateRisk = async () => {
    if (!selectedForecast) return
    setRiskSubmitting(true)
    try {
      await forecastingService.createRisk({
        ...riskForm,
        forecast_id: selectedForecast.id,
        probability: Number(riskForm.probability),
        recommended_actions: riskForm.recommended_actions.split(',').map((item) => item.trim()).filter(Boolean),
      })
      setRiskForm(initialRiskForm)
      setNotice('Risk assessment added')
      await loadForecastDetail(selectedForecast.id, 'risks')
    } catch (err) {
      setNotice(err.message)
    } finally {
      setRiskSubmitting(false)
    }
  }

  const handleGenerateOpportunities = async () => {
    try {
      await forecastingService.generateOpportunities()
      setNotice('Opportunity insights refreshed')
      if (selectedForecast) {
        await loadForecastDetail(selectedForecast.id, 'opportunities')
      } else {
        const { data } = await forecastingService.listOpportunities({ is_active: true })
        setOpportunities(data.items || [])
      }
    } catch (err) {
      setNotice(err.message)
    }
  }

  const handleGenerateRecommendations = async () => {
    if (!selectedForecast) return
    try {
      await forecastingService.generateRecommendations(selectedForecast.id)
      setNotice('Recommendations generated')
      await loadForecastDetail(selectedForecast.id, 'overview')
    } catch (err) {
      setNotice(err.message)
    }
  }

  const handleMarkAlertRead = async (alertId) => {
    if (!selectedForecast) return
    try {
      await forecastingService.markAlertRead(selectedForecast.id, alertId)
      setAlerts((prev) => prev.map((item) => (item.id === alertId ? { ...item, is_read: true } : item)))
    } catch (err) {
      setNotice(err.message)
    }
  }

  const handleExport = async () => {
    if (!selectedForecast) return
    try {
      const { data } = await forecastingService.exportForecast(selectedForecast.id, 'json')
      setNotice(data.note || 'Forecast exported as JSON payload')
    } catch (err) {
      setNotice(err.message)
    }
  }

  const handleCompare = async () => {
    if (!compareForm.primary_forecast_id || !compareForm.comparison_forecast_id) return
    setCompareLoading(true)
    try {
      const { data } = await forecastingService.compareForecasts({
        primary_forecast_id: Number(compareForm.primary_forecast_id),
        comparison_forecast_id: Number(compareForm.comparison_forecast_id),
      })
      setCompareResult(data)
    } catch (err) {
      setNotice(err.message)
    } finally {
      setCompareLoading(false)
    }
  }

  const toggleVersionSelection = (versionId) => {
    setSelectedVersionIds((prev) => {
      if (prev.includes(versionId)) return prev.filter((item) => item !== versionId)
      if (prev.length >= 2) return [prev[1], versionId]
      return [...prev, versionId]
    })
  }

  const selectedVersions = useMemo(() => versions.filter((item) => selectedVersionIds.includes(item.id)), [versions, selectedVersionIds])

  if (loading) return <LoadingState count={6} height="h-44" />
  if (error) return <ErrorState message={error} />

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">Predictive Analytics & Forecasting</h1>
          <p className="text-sm text-gray-400 mt-1">Model business outcomes, compare scenarios, and turn forecast signals into action.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button className={`btn-secondary ${activeView === 'workspace' ? 'ring-1 ring-prism-600' : ''}`} onClick={() => { setActiveView('workspace'); navigate('/forecasting') }}>
            Workspace
          </button>
          <button className={`btn-secondary ${activeView === 'detail' ? 'ring-1 ring-prism-600' : ''}`} onClick={() => setActiveView('detail')} disabled={!selectedForecast}>
            Forecast Detail
          </button>
          <button className="btn-primary" onClick={openCreateWizard}>Create Forecast</button>
        </div>
      </div>

      {notice && (
        <div className="card border border-prism-800 text-sm text-prism-200 flex items-start justify-between gap-3">
          <span>{notice}</span>
          <button className="text-gray-400 hover:text-gray-200" onClick={() => setNotice('')}>Dismiss</button>
        </div>
      )}

      {activeView === 'workspace' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            <StatCard icon={TrendingUp} label="Total Forecasts" value={summary?.total_forecasts ?? total} />
            <StatCard icon={Sparkles} label="Ready" value={summary?.ready_forecasts ?? 0} accent="text-green-300" />
            <StatCard icon={Loader2} label="In Progress" value={summary?.in_progress_forecasts ?? 0} accent="text-indigo-300" />
            <StatCard icon={AlertTriangle} label="Failed" value={summary?.failed_forecasts ?? 0} accent="text-red-300" />
          </div>

          <section className="card space-y-4">
            <div className="grid grid-cols-1 xl:grid-cols-5 gap-3">
              <div className="xl:col-span-2 relative">
                <Search size={16} className="absolute left-3 top-3 text-gray-500" />
                <input
                  className="w-full bg-gray-950 border border-gray-800 rounded-lg pl-10 pr-3 py-2 text-sm"
                  placeholder="Search forecasts..."
                  value={filters.search}
                  onChange={(event) => setFilters((prev) => ({ ...prev, search: event.target.value }))}
                />
              </div>
              <select className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={filters.status} onChange={(event) => setFilters((prev) => ({ ...prev, status: event.target.value }))}>
                <option value="">All statuses</option>
                <option value="draft">Draft</option>
                <option value="generating">Generating</option>
                <option value="ready">Ready</option>
                <option value="failed">Failed</option>
                <option value="archived">Archived</option>
              </select>
              <select className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={filters.horizon} onChange={(event) => setFilters((prev) => ({ ...prev, horizon: event.target.value }))}>
                <option value="">All horizons</option>
                {HORIZON_OPTIONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
              </select>
              <select className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={filters.domain} onChange={(event) => setFilters((prev) => ({ ...prev, domain: event.target.value }))}>
                <option value="">All domains</option>
                {domainOptions.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap gap-2">
                <select className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={filters.sort_by} onChange={(event) => setFilters((prev) => ({ ...prev, sort_by: event.target.value }))}>
                  <option value="updated_at">Last Updated</option>
                  <option value="created_at">Created Date</option>
                  <option value="name">Name</option>
                  <option value="status">Status</option>
                  <option value="horizon">Horizon</option>
                  <option value="last_generated_at">Last Generated</option>
                </select>
                <button className="btn-secondary" onClick={() => setFilters((prev) => ({ ...prev, sort_order: prev.sort_order === 'asc' ? 'desc' : 'asc' }))}>
                  Order: {filters.sort_order.toUpperCase()}
                </button>
              </div>
              <button className="btn-secondary" onClick={loadWorkspace}>Refresh</button>
            </div>

            {!forecasts.length ? (
              <EmptyState
                title="No forecasts yet"
                description="Create your first forecasting definition to start modeling KPIs, scenarios, and predictive insights."
                actionLabel="Create Forecast"
                onAction={openCreateWizard}
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[980px] text-sm">
                  <thead className="text-left text-gray-400 border-b border-gray-800">
                    <tr>
                      <th className="py-3 pr-4">Name</th>
                      <th className="py-3 pr-4">Domain</th>
                      <th className="py-3 pr-4">Target Metric</th>
                      <th className="py-3 pr-4">Horizon</th>
                      <th className="py-3 pr-4">Confidence</th>
                      <th className="py-3 pr-4">Status</th>
                      <th className="py-3 pr-4">Last Generated</th>
                      <th className="py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {forecasts.map((forecast) => (
                      <tr key={forecast.id} className="border-b border-gray-800/80 text-gray-200">
                        <td className="py-4 pr-4">
                          <div className="font-medium text-white">{forecast.name}</div>
                          <div className="text-xs text-gray-500 mt-1">{forecast.description || 'No description provided'}</div>
                        </td>
                        <td className="py-4 pr-4">{forecast.business_domain || '—'}</td>
                        <td className="py-4 pr-4">{forecast.target_metric}</td>
                        <td className="py-4 pr-4 capitalize">{forecast.horizon}</td>
                        <td className="py-4 pr-4">{Math.round((forecast.confidence_level || 0) * 100)}%</td>
                        <td className="py-4 pr-4"><StatusBadge status={forecast.status} /></td>
                        <td className="py-4 pr-4 text-gray-400">{formatDate(forecast.last_generated_at)}</td>
                        <td className="py-4 text-right">
                          <div className="flex flex-wrap justify-end gap-2">
                            <button className="btn-secondary !px-3 !py-1.5" onClick={() => handleViewForecast(forecast)}>View</button>
                            <button className="btn-secondary !px-3 !py-1.5" onClick={() => handleGenerateForecast(forecast)}>Generate</button>
                            <button className="btn-secondary !px-3 !py-1.5" onClick={() => handleDuplicateForecast(forecast)}><Copy size={14} /></button>
                            <button className="btn-secondary !px-3 !py-1.5 text-red-300" onClick={() => handleDeleteForecast(forecast)}><Trash2 size={14} /></button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {forecasts.length >= 2 && (
            <section className="card space-y-4">
              <div className="flex items-center gap-2">
                <GitCompareArrows size={18} className="text-prism-300" />
                <h2 className="text-lg font-semibold text-white">Compare Forecasts</h2>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-3">
                <select className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={compareForm.primary_forecast_id} onChange={(event) => setCompareForm((prev) => ({ ...prev, primary_forecast_id: event.target.value }))}>
                  <option value="">Select primary forecast</option>
                  {forecasts.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
                <select className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={compareForm.comparison_forecast_id} onChange={(event) => setCompareForm((prev) => ({ ...prev, comparison_forecast_id: event.target.value }))}>
                  <option value="">Select comparison forecast</option>
                  {forecasts.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
                <button className="btn-primary" onClick={handleCompare} disabled={compareLoading}>
                  {compareLoading ? 'Comparing...' : 'Compare'}
                </button>
              </div>
              {compareResult && (
                <div className="rounded-xl border border-gray-800 bg-gray-950/70 p-4">
                  <p className="text-white font-medium">{compareResult.summary}</p>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4 text-sm">
                    <div>
                      <p className="text-gray-400">Primary Latest Value</p>
                      <p className="text-white mt-1">{formatMetric(compareResult.primary_latest_value, compareResult.primary_metric)}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Comparison Latest Value</p>
                      <p className="text-white mt-1">{formatMetric(compareResult.comparison_latest_value, compareResult.comparison_metric)}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Delta</p>
                      <p className={`mt-1 font-medium ${compareResult.delta_percentage >= 0 ? 'text-green-300' : 'text-red-300'}`}>{compareResult.delta_percentage}%</p>
                    </div>
                  </div>
                </div>
              )}
            </section>
          )}
        </div>
      )}

      {activeView === 'create' && (
        <section className="card space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-white">Create Forecast Wizard</h2>
              <p className="text-sm text-gray-400 mt-1">Build a planning-ready forecast in five guided steps.</p>
            </div>
            <button className="btn-secondary" onClick={() => setActiveView('workspace')}>Back to Workspace</button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {[1, 2, 3, 4, 5].map((step) => (
              <div key={step} className={`rounded-xl border px-4 py-3 text-sm ${wizardStep === step ? 'border-prism-500 bg-prism-500/10 text-prism-200' : step < wizardStep ? 'border-green-500/40 bg-green-500/10 text-green-200' : 'border-gray-800 bg-gray-950 text-gray-400'}`}>
                Step {step}
              </div>
            ))}
          </div>

          {wizardStep === 1 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-300 mb-2">Semantic Model</label>
                <select className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={wizard.semantic_model_id} onChange={(event) => {
                  const match = semanticModels.find((item) => String(item.id) === event.target.value)
                  setWizard((prev) => ({ ...prev, semantic_model_id: event.target.value, semantic_model_name: match?.name || '' }))
                }}>
                  <option value="">No semantic model selected</option>
                  {semanticModels.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
                <p className="text-xs text-gray-500 mt-2">Optional: link the forecast to an existing semantic model.</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-300 mb-2">Forecast Name</label>
                  <input className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={wizard.name} onChange={(event) => setWizard((prev) => ({ ...prev, name: event.target.value }))} placeholder="Revenue Plan FY25" />
                </div>
                <div>
                  <label className="block text-sm text-gray-300 mb-2">Business Domain</label>
                  <input className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={wizard.business_domain} onChange={(event) => setWizard((prev) => ({ ...prev, business_domain: event.target.value }))} placeholder="Finance" />
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-300 mb-2">Description</label>
                <textarea className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm min-h-[120px]" value={wizard.description} onChange={(event) => setWizard((prev) => ({ ...prev, description: event.target.value }))} placeholder="Describe the planning context, assumptions, or audience." />
              </div>
            </div>
          )}

          {wizardStep === 2 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-300 mb-2">Target KPI</label>
                <select className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={wizard.target_metric} onChange={(event) => setWizard((prev) => ({ ...prev, target_metric: event.target.value }))}>
                  {KPI_OPTIONS.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-300 mb-2">Confidence Level</label>
                <input type="range" min="0.5" max="0.99" step="0.01" value={wizard.confidence_level} onChange={(event) => setWizard((prev) => ({ ...prev, confidence_level: event.target.value }))} className="w-full accent-prism-500" />
                <p className="text-sm text-prism-200 mt-2">{Math.round(Number(wizard.confidence_level) * 100)}%</p>
              </div>
            </div>
          )}

          {wizardStep === 3 && (
            <div>
              <label className="block text-sm text-gray-300 mb-2">Forecast Horizon</label>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                {HORIZON_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    className={`rounded-xl border px-4 py-4 text-sm ${wizard.horizon === option.value ? 'border-prism-500 bg-prism-500/10 text-prism-200' : 'border-gray-800 bg-gray-950 text-gray-300'}`}
                    onClick={() => setWizard((prev) => ({ ...prev, horizon: option.value }))}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {wizardStep === 4 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h3 className="text-lg font-semibold text-white">Planning Variables</h3>
                  <p className="text-sm text-gray-400 mt-1">Add the main levers that influence this forecast.</p>
                </div>
                <button className="btn-secondary" onClick={addWizardVariable}><Plus size={16} /></button>
              </div>
              <div className="space-y-3">
                {wizard.variables.map((variable, index) => (
                  <div key={`${index}-${variable}`} className="flex gap-2">
                    <input className="flex-1 bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={variable} onChange={(event) => updateWizardVariable(index, event.target.value)} placeholder="e.g. Pipeline coverage" />
                    {wizard.variables.length > 1 && <button className="btn-secondary" onClick={() => removeWizardVariable(index)}><Trash2 size={14} /></button>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {wizardStep === 5 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="rounded-xl border border-gray-800 bg-gray-950/70 p-5 space-y-3 text-sm">
                <h3 className="text-lg font-semibold text-white">Review</h3>
                <div><span className="text-gray-400">Forecast:</span> <span className="text-white">{wizard.name || `${wizard.target_metric} Forecast`}</span></div>
                <div><span className="text-gray-400">Semantic Model:</span> <span className="text-white">{wizard.semantic_model_name || 'None selected'}</span></div>
                <div><span className="text-gray-400">Domain:</span> <span className="text-white">{wizard.business_domain}</span></div>
                <div><span className="text-gray-400">Target KPI:</span> <span className="text-white">{wizard.target_metric}</span></div>
                <div><span className="text-gray-400">Horizon:</span> <span className="text-white capitalize">{wizard.horizon}</span></div>
                <div><span className="text-gray-400">Confidence:</span> <span className="text-white">{Math.round(Number(wizard.confidence_level) * 100)}%</span></div>
                <div>
                  <span className="text-gray-400">Variables:</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {wizard.variables.filter(Boolean).map((item) => <span key={item} className="badge bg-gray-800 text-gray-200 border border-gray-700">{item}</span>)}
                  </div>
                </div>
              </div>
              <div className="rounded-xl border border-prism-800 bg-prism-900/10 p-5 text-sm text-prism-100">
                <h3 className="text-lg font-semibold text-white">What happens next?</h3>
                <ul className="mt-3 space-y-2 list-disc list-inside">
                  <li>The forecast definition will be saved.</li>
                  <li>A deterministic synthetic forecast will be generated automatically.</li>
                  <li>You can immediately review scenarios, drivers, alerts, and recommendations.</li>
                </ul>
              </div>
            </div>
          )}

          <div className="flex flex-wrap justify-between gap-3">
            <button className="btn-secondary" onClick={() => setWizardStep((prev) => Math.max(1, prev - 1))} disabled={wizardStep === 1 || wizardSubmitting}>Back</button>
            {wizardStep < 5 ? (
              <button className="btn-primary" onClick={() => setWizardStep((prev) => Math.min(5, prev + 1))}>Next</button>
            ) : (
              <button className="btn-primary" onClick={handleCreateForecast} disabled={wizardSubmitting}>
                {wizardSubmitting ? 'Creating…' : 'Create & Generate'}
              </button>
            )}
          </div>
        </section>
      )}

      {activeView === 'detail' && (
        <div className="space-y-6">
          {detailLoading ? (
            <LoadingState count={4} height="h-40" />
          ) : detailError ? (
            <ErrorState message={detailError} />
          ) : !selectedForecast ? (
            <EmptyState
              title="Select a forecast"
              description="Choose a forecast from the workspace to review its output, scenarios, risks, and opportunities."
              actionLabel="Open Workspace"
              onAction={() => setActiveView('workspace')}
            />
          ) : (
            <>
              <section className="card">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="text-2xl font-semibold text-white">{selectedForecast.name}</h2>
                      <StatusBadge status={selectedForecast.status} />
                    </div>
                    <p className="text-sm text-gray-400 mt-2 max-w-3xl">{selectedForecast.description || 'No description provided.'}</p>
                    <div className="flex flex-wrap gap-4 mt-4 text-sm text-gray-400">
                      <span>Domain: <span className="text-gray-200">{selectedForecast.business_domain || '—'}</span></span>
                      <span>Target Metric: <span className="text-gray-200">{selectedForecast.target_metric}</span></span>
                      <span>Horizon: <span className="text-gray-200 capitalize">{selectedForecast.horizon}</span></span>
                      <span>Last Generated: <span className="text-gray-200">{formatDate(selectedForecast.last_generated_at)}</span></span>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button className="btn-secondary" onClick={() => handleGenerateForecast(selectedForecast)}><RefreshCcw size={16} className="mr-2 inline" />Regenerate</button>
                    <button className="btn-secondary" onClick={() => handleDuplicateForecast(selectedForecast)}><Copy size={16} className="mr-2 inline" />Duplicate</button>
                    <button className="btn-secondary" onClick={handleExport}><Download size={16} className="mr-2 inline" />Export JSON</button>
                  </div>
                </div>
              </section>

              <div className="flex flex-wrap gap-2">
                {DETAIL_TABS.map((tab) => (
                  <button
                    key={tab}
                    className={`px-4 py-2 rounded-lg text-sm font-medium capitalize ${detailTab === tab ? 'bg-prism-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}
                    onClick={() => setDetailTab(tab)}
                  >
                    {tab.replace('-', ' ')}
                  </button>
                ))}
              </div>

              {detailTab === 'overview' && (
                <div className="space-y-6">
                  <section className="card space-y-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <h3 className="text-lg font-semibold text-white">Executive Summary</h3>
                        <p className="text-sm text-gray-400 mt-1">Narrative view of the latest forecast version.</p>
                      </div>
                      <button className="btn-secondary" onClick={handleGenerateRecommendations}><Sparkles size={16} className="mr-2 inline" />Generate Recommendations</button>
                    </div>
                    <div className="rounded-xl border border-gray-800 bg-gray-950/70 p-5 text-gray-200">
                      {resolvedResult?.executive_summary || 'Generate a forecast to populate the executive summary.'}
                    </div>
                    <ForecastTrendChart
                      historical={resolvedResult?.historical_data || []}
                      forecast={resolvedResult?.forecast_data || []}
                      upper={resolvedResult?.confidence_upper || []}
                      lower={resolvedResult?.confidence_lower || []}
                      metric={selectedForecast.target_metric}
                    />
                  </section>

                  <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                    <section className="card">
                      <h3 className="text-lg font-semibold text-white mb-4">Key Factors</h3>
                      <ul className="space-y-3 text-sm text-gray-300">
                        {(resolvedResult?.key_factors || []).map((item) => (
                          <li key={item} className="rounded-xl border border-gray-800 bg-gray-950/70 p-3">{item}</li>
                        ))}
                      </ul>
                    </section>
                    <section className="card">
                      <h3 className="text-lg font-semibold text-white mb-4">Assumptions</h3>
                      <ul className="space-y-3 text-sm text-gray-300">
                        {(resolvedResult?.assumptions || []).map((item) => (
                          <li key={item} className="rounded-xl border border-gray-800 bg-gray-950/70 p-3">{item}</li>
                        ))}
                      </ul>
                    </section>
                  </div>

                  <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                    <section className="card">
                      <h3 className="text-lg font-semibold text-white mb-4">Recommendations</h3>
                      <ul className="space-y-3 text-sm text-gray-300">
                        {(resolvedResult?.recommendations || []).map((item) => (
                          <li key={item} className="rounded-xl border border-gray-800 bg-gray-950/70 p-3">{item}</li>
                        ))}
                      </ul>
                    </section>
                    <section className="card">
                      <h3 className="text-lg font-semibold text-white mb-4">AI Recommendations</h3>
                      {!recommendations.length ? (
                        <p className="text-sm text-gray-400">No AI recommendations generated yet.</p>
                      ) : (
                        <div className="space-y-3">
                          {recommendations.map((item) => (
                            <div key={item.id} className="rounded-xl border border-gray-800 bg-gray-950/70 p-4">
                              <div className="flex items-center justify-between gap-3">
                                <h4 className="text-white font-medium">{item.business_objective}</h4>
                                <span className="badge bg-prism-500/15 text-prism-200 border border-prism-500/30">{Math.round((item.confidence || 0) * 100)}%</span>
                              </div>
                              <p className="text-sm text-gray-400 mt-2">{item.expected_impact}</p>
                              <div className="mt-3 text-sm text-gray-300">
                                <p className="text-gray-500 mb-2">Next steps</p>
                                <ul className="space-y-1 list-disc list-inside">
                                  {(item.next_steps || []).map((step) => <li key={step}>{step}</li>)}
                                </ul>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </section>
                  </div>
                </div>
              )}

              {detailTab === 'scenarios' && (
                <div className="grid grid-cols-1 xl:grid-cols-[1.1fr_0.9fr] gap-6">
                  <section className="card space-y-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <h3 className="text-lg font-semibold text-white">Scenario Plans</h3>
                        <p className="text-sm text-gray-400 mt-1">Model upside and downside outcomes for the latest forecast.</p>
                      </div>
                    </div>
                    {!scenarios.length ? (
                      <p className="text-sm text-gray-400">No scenarios created yet.</p>
                    ) : (
                      <div className="space-y-4">
                        {scenarios.map((scenario) => (
                          <div key={scenario.id} className="rounded-xl border border-gray-800 bg-gray-950/70 p-4 space-y-3">
                            <div className="flex flex-wrap items-start justify-between gap-3">
                              <div>
                                <div className="flex items-center gap-2">
                                  <h4 className="text-white font-medium">{scenario.name}</h4>
                                  <StatusBadge status={scenario.status} />
                                </div>
                                <p className="text-sm text-gray-400 mt-2">{scenario.description || 'No description provided.'}</p>
                              </div>
                              <div className="flex gap-2">
                                <button className="btn-secondary !px-3 !py-1.5" onClick={() => handleRunScenario(scenario)}><Play size={14} /></button>
                                <button className="btn-secondary !px-3 !py-1.5 text-red-300" onClick={() => handleDeleteScenario(scenario)}><Trash2 size={14} /></button>
                              </div>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {(scenario.variables || []).map((item) => (
                                <span key={`${scenario.id}-${item.id}`} className="badge bg-gray-800 text-gray-200 border border-gray-700">{item.name}: {item.base_value} <span aria-label="to">&rarr;</span> {item.adjusted_value}{item.unit}</span>
                              ))}
                            </div>
                            {scenario.estimated_impact?.projected_value && (
                              <div className="rounded-xl border border-prism-800 bg-prism-900/10 p-4 text-sm text-prism-100">
                                <div className="flex flex-wrap gap-4">
                                  <span>Projected Value: <span className="text-white">{formatMetric(scenario.estimated_impact.projected_value, selectedForecast.target_metric)}</span></span>
                                  <span>Change: <span className={scenario.estimated_impact.percentage_change >= 0 ? 'text-green-300' : 'text-red-300'}>{scenario.estimated_impact.percentage_change}%</span></span>
                                </div>
                                <p className="mt-2">{scenario.result_summary}</p>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </section>

                  <section className="card space-y-4">
                    <div>
                      <h3 className="text-lg font-semibold text-white">Create Scenario</h3>
                      <p className="text-sm text-gray-400 mt-1">Add variable adjustments and run impact analysis.</p>
                    </div>
                    <input className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={scenarioForm.name} onChange={(event) => setScenarioForm((prev) => ({ ...prev, name: event.target.value }))} placeholder="Best case expansion plan" />
                    <textarea className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm min-h-[96px]" value={scenarioForm.description} onChange={(event) => setScenarioForm((prev) => ({ ...prev, description: event.target.value }))} placeholder="Describe the conditions for this scenario." />
                    <div className="space-y-3">
                      {scenarioForm.variables.map((item, index) => (
                        <div key={index} className="rounded-xl border border-gray-800 bg-gray-950/70 p-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                          <input className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={item.name} onChange={(event) => updateScenarioVariable(index, 'name', event.target.value)} placeholder="Variable name" />
                          <input className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={item.impact_direction} onChange={(event) => updateScenarioVariable(index, 'impact_direction', event.target.value)} placeholder="Impact direction" />
                          <input type="number" className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={item.base_value} onChange={(event) => updateScenarioVariable(index, 'base_value', event.target.value)} placeholder="Base value" />
                          <input type="number" className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={item.adjusted_value} onChange={(event) => updateScenarioVariable(index, 'adjusted_value', event.target.value)} placeholder="Adjusted value" />
                        </div>
                      ))}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button className="btn-secondary" onClick={addScenarioVariable}><Plus size={16} className="mr-2 inline" />Add Variable</button>
                      <button className="btn-primary" onClick={handleCreateScenario} disabled={scenarioSubmitting}>{scenarioSubmitting ? 'Saving…' : 'Create Scenario'}</button>
                    </div>
                  </section>
                </div>
              )}

              {detailTab === 'what-if' && (
                <section className="card space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-white">What-If Analysis</h3>
                    <p className="text-sm text-gray-400 mt-1">Adjust planning variables and see the projected impact update automatically.</p>
                  </div>
                  {!whatIfVariables.length ? (
                    <p className="text-sm text-gray-400">No forecast variables are defined. Add variables to the forecast and regenerate to unlock what-if analysis.</p>
                  ) : (
                    <div className="grid grid-cols-1 xl:grid-cols-[1.1fr_0.9fr] gap-6">
                      <div className="space-y-4">
                        {whatIfVariables.map((item, index) => (
                          <div key={item.name} className="rounded-xl border border-gray-800 bg-gray-950/70 p-4">
                            <div className="flex items-center justify-between gap-3 mb-3">
                              <div>
                                <p className="text-white font-medium">{item.name}</p>
                                <p className="text-xs text-gray-500">Adjustment range: -25% to +25%</p>
                              </div>
                              <span className={`font-medium ${Number(item.adjustment_percent) >= 0 ? 'text-green-300' : 'text-red-300'}`}>{Number(item.adjustment_percent).toFixed(0)}%</span>
                            </div>
                            <input
                              type="range"
                              min="-25"
                              max="25"
                              step="1"
                              value={item.adjustment_percent}
                              onChange={(event) => setWhatIfVariables((prev) => prev.map((entry, entryIndex) => (entryIndex === index ? { ...entry, adjustment_percent: Number(event.target.value) } : entry)))}
                              className="w-full accent-prism-500"
                            />
                          </div>
                        ))}
                      </div>
                      <div className="rounded-xl border border-prism-800 bg-prism-900/10 p-5 space-y-4">
                        <div className="flex items-center justify-between gap-3">
                          <h4 className="text-lg font-semibold text-white">Projected Outcome</h4>
                          {whatIfLoading && <Loader2 size={18} className="animate-spin text-prism-300" />}
                        </div>
                        <div>
                          <p className="text-sm text-gray-400">Baseline</p>
                          <p className="text-2xl font-semibold text-white mt-1">{formatMetric(whatIfResult?.baseline_value ?? safeBaseline(resolvedResult), selectedForecast.target_metric)}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-400">Projected</p>
                          <p className="text-3xl font-semibold text-white mt-1">{formatMetric(whatIfResult?.projected_value, selectedForecast.target_metric)}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-400">Impact</p>
                          <p className={`text-xl font-semibold mt-1 ${(whatIfResult?.percentage_change || 0) >= 0 ? 'text-green-300' : 'text-red-300'}`}>{whatIfResult?.percentage_change ?? 0}%</p>
                        </div>
                        <p className="text-sm text-prism-100">{whatIfResult?.summary || 'Move a slider to evaluate a scenario.'}</p>
                        {!!whatIfResult?.impact_breakdown?.length && (
                          <div className="space-y-2 text-sm text-gray-200">
                            {whatIfResult.impact_breakdown.map((item) => (
                              <div key={item.name} className="flex justify-between gap-3">
                                <span>{item.name}</span>
                                <span className={item.contribution_percent >= 0 ? 'text-green-300' : 'text-red-300'}>{item.contribution_percent}%</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </section>
              )}

              {detailTab === 'drivers' && (
                <section className="card space-y-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <h3 className="text-lg font-semibold text-white">Driver Analysis</h3>
                      <p className="text-sm text-gray-400 mt-1">Understand which variables most strongly influence the selected KPI.</p>
                    </div>
                    <button className="btn-secondary" onClick={handleGenerateDrivers}><RefreshCcw size={16} className="mr-2 inline" />Regenerate</button>
                  </div>
                  {driverAnalysis?.analysis_summary && <div className="rounded-xl border border-gray-800 bg-gray-950/70 p-4 text-sm text-gray-300">{driverAnalysis.analysis_summary}</div>}
                  <DriverBars drivers={driverAnalysis?.drivers || []} />
                </section>
              )}

              {detailTab === 'risks' && (
                <div className="grid grid-cols-1 xl:grid-cols-[1.1fr_0.9fr] gap-6">
                  <section className="card space-y-4">
                    <div className="flex items-center gap-2">
                      <ShieldAlert size={18} className="text-yellow-300" />
                      <h3 className="text-lg font-semibold text-white">Risk Assessments</h3>
                    </div>
                    {!risks.length ? (
                      <p className="text-sm text-gray-400">No risks logged for this forecast yet.</p>
                    ) : (
                      <div className="space-y-4">
                        {risks.map((risk) => (
                          <div key={risk.id} className="rounded-xl border border-gray-800 bg-gray-950/70 p-4">
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <div className="flex items-center gap-2">
                                  <h4 className="text-white font-medium">{risk.name}</h4>
                                  <RiskBadge level={risk.risk_level} />
                                </div>
                                <p className="text-sm text-gray-500 mt-1">{risk.risk_type}</p>
                              </div>
                              <span className="text-sm text-gray-300">{Math.round((risk.probability || 0) * 100)}%</span>
                            </div>
                            <p className="text-sm text-gray-300 mt-3">{risk.business_impact}</p>
                            <ul className="mt-3 space-y-1 text-sm text-gray-400 list-disc list-inside">
                              {(risk.recommended_actions || []).map((action) => <li key={action}>{action}</li>)}
                            </ul>
                          </div>
                        ))}
                      </div>
                    )}
                  </section>
                  <section className="card space-y-4">
                    <div>
                      <h3 className="text-lg font-semibold text-white">Log Risk</h3>
                      <p className="text-sm text-gray-400 mt-1">Capture probability, impact, and mitigation steps.</p>
                    </div>
                    <input className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={riskForm.name} onChange={(event) => setRiskForm((prev) => ({ ...prev, name: event.target.value }))} placeholder="Supplier disruption" />
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <input className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={riskForm.risk_type} onChange={(event) => setRiskForm((prev) => ({ ...prev, risk_type: event.target.value }))} placeholder="Risk type" />
                      <select className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm" value={riskForm.risk_level} onChange={(event) => setRiskForm((prev) => ({ ...prev, risk_level: event.target.value }))}>
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                        <option value="critical">Critical</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm text-gray-300 mb-2">Probability</label>
                      <input type="range" min="0" max="1" step="0.05" value={riskForm.probability} onChange={(event) => setRiskForm((prev) => ({ ...prev, probability: event.target.value }))} className="w-full accent-prism-500" />
                      <p className="text-sm text-prism-200 mt-2">{Math.round(Number(riskForm.probability) * 100)}%</p>
                    </div>
                    <textarea className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm min-h-[100px]" value={riskForm.business_impact} onChange={(event) => setRiskForm((prev) => ({ ...prev, business_impact: event.target.value }))} placeholder="Describe business impact." />
                    <textarea className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm min-h-[80px]" value={riskForm.recommended_actions} onChange={(event) => setRiskForm((prev) => ({ ...prev, recommended_actions: event.target.value }))} placeholder="Comma separated recommended actions" />
                    <button className="btn-primary" onClick={handleCreateRisk} disabled={riskSubmitting}>{riskSubmitting ? 'Saving…' : 'Add Risk'}</button>
                  </section>
                </div>
              )}

              {detailTab === 'opportunities' && (
                <section className="card space-y-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <h3 className="text-lg font-semibold text-white">Opportunity Insights</h3>
                      <p className="text-sm text-gray-400 mt-1">Deterministic opportunities derived from forecast signals.</p>
                    </div>
                    <button className="btn-secondary" onClick={handleGenerateOpportunities}><Sparkles size={16} className="mr-2 inline" />Generate Opportunities</button>
                  </div>
                  {!opportunities.length ? (
                    <p className="text-sm text-gray-400">No opportunities available yet.</p>
                  ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      {opportunities.map((item) => (
                        <div key={item.id} className="rounded-xl border border-gray-800 bg-gray-950/70 p-5">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="badge bg-prism-500/15 text-prism-200 border border-prism-500/30">Priority #{item.priority_rank}</span>
                                <span className="badge bg-gray-800 text-gray-200 border border-gray-700">{item.opportunity_type}</span>
                              </div>
                              <h4 className="text-white font-medium mt-3">{item.name}</h4>
                            </div>
                            <span className="text-green-300 font-medium">{Math.round((item.confidence_score || 0) * 100)}%</span>
                          </div>
                          <p className="text-sm text-gray-300 mt-3">{item.description}</p>
                          <div className="mt-4 text-sm text-gray-400">Expected value: <span className="text-white">{formatMetric(item.expected_value, selectedForecast.target_metric)}</span></div>
                          <ul className="mt-3 space-y-1 text-sm text-gray-400 list-disc list-inside">
                            {(item.recommended_actions || []).map((action) => <li key={action}>{action}</li>)}
                          </ul>
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              )}

              {detailTab === 'versions' && (
                <section className="card space-y-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <h3 className="text-lg font-semibold text-white">Forecast Versions</h3>
                      <p className="text-sm text-gray-400 mt-1">Review previous forecast generations and compare two snapshots.</p>
                    </div>
                    <button className="btn-secondary" onClick={() => handleGenerateForecast(selectedForecast)}><RefreshCcw size={16} className="mr-2 inline" />New Version</button>
                  </div>
                  {!versions.length ? (
                    <p className="text-sm text-gray-400">No versions available yet.</p>
                  ) : (
                    <div className="space-y-4">
                      {versions.map((version) => (
                        <div key={version.id} className="rounded-xl border border-gray-800 bg-gray-950/70 p-4 flex flex-wrap items-center justify-between gap-3">
                          <div>
                            <div className="flex items-center gap-2 text-white font-medium">
                              <input type="checkbox" checked={selectedVersionIds.includes(version.id)} onChange={() => toggleVersionSelection(version.id)} className="accent-prism-500" />
                              Version {version.version_number}
                            </div>
                            <p className="text-sm text-gray-400 mt-2">{version.notes || 'No notes added.'}</p>
                          </div>
                          <div className="text-sm text-gray-400 text-right">
                            <div>Created {formatDate(version.created_at)}</div>
                            <div>Created by user #{version.created_by}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  {selectedVersions.length === 2 && (
                    <div className="rounded-xl border border-prism-800 bg-prism-900/10 p-4">
                      <div className="flex items-center gap-2 text-prism-100 font-medium">
                        <GitCompareArrows size={16} /> Local Version Comparison
                      </div>
                      <p className="text-sm text-prism-100 mt-2">Version {selectedVersions[0].version_number} and version {selectedVersions[1].version_number} were generated {getVersionTimeDifference(selectedVersions[0], selectedVersions[1])}.</p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4 text-sm text-gray-200">
                        {selectedVersions.map((version) => (
                          <div key={version.id} className="rounded-xl border border-gray-800 bg-gray-950/50 p-4">
                            <p className="font-medium text-white">Version {version.version_number}</p>
                            <p className="text-gray-400 mt-2">{version.notes}</p>
                            <p className="text-gray-500 mt-2">{formatDate(version.created_at)}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </section>
              )}

              {detailTab === 'alerts' && (
                <section className="card space-y-4">
                  <div className="flex items-center gap-2">
                    <Bell size={18} className="text-prism-300" />
                    <h3 className="text-lg font-semibold text-white">Prediction Alerts</h3>
                  </div>
                  {!alerts.length ? (
                    <p className="text-sm text-gray-400">No alerts yet.</p>
                  ) : (
                    <div className="space-y-4">
                      {alerts.map((alert) => (
                        <div key={alert.id} className={`rounded-xl border p-4 ${alert.is_read ? 'border-gray-800 bg-gray-950/60' : 'border-prism-800 bg-prism-900/10'}`}>
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div>
                              <div className="flex items-center gap-2">
                                <RiskBadge level={alert.severity} />
                                {!alert.is_read && <span className="badge bg-prism-500/15 text-prism-200 border border-prism-500/30">New</span>}
                              </div>
                              <h4 className="text-white font-medium mt-3">{alert.title}</h4>
                              <p className="text-sm text-gray-300 mt-2">{alert.message}</p>
                              <p className="text-xs text-gray-500 mt-3">{formatDate(alert.created_at)}</p>
                            </div>
                            {!alert.is_read && <button className="btn-secondary" onClick={() => handleMarkAlertRead(alert.id)}>Mark as read</button>}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

function safeBaseline(result) {
  if (!result) return 0
  if (result.forecast_data?.length) return result.forecast_data[result.forecast_data.length - 1].value
  if (result.historical_data?.length) return result.historical_data[result.historical_data.length - 1].value
  return 0
}

function getVersionTimeDifference(versionA, versionB) {
  const diffMs = Math.abs(new Date(versionA.created_at) - new Date(versionB.created_at))
  const diffHours = diffMs / 1000 / 60 / 60
  return diffHours < 1 ? 'within the same hour' : 'at different planning times'
}
