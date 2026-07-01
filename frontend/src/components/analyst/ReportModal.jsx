import React, { useState } from 'react'
import { X, FileText, Loader2 } from 'lucide-react'
import { analystApi } from '../../services/analyst'

const REPORT_TYPES = [
  { value: 'executive_summary', label: 'Executive Summary', description: 'High-level overview for senior leadership' },
  { value: 'business_review', label: 'Business Review', description: 'Comprehensive business performance analysis' },
  { value: 'department_report', label: 'Department Report', description: 'Department-level performance and insights' },
  { value: 'kpi_report', label: 'KPI Report', description: 'KPI performance against targets' },
  { value: 'operational_report', label: 'Operational Report', description: 'Operational metrics and efficiency analysis' },
  { value: 'monthly_review', label: 'Monthly Review', description: 'Monthly performance review with trends' },
  { value: 'quarterly_review', label: 'Quarterly Review', description: 'Quarterly business review and forecasts' },
]

export default function ReportModal({ conversationId, onClose }) {
  const [reportType, setReportType] = useState('executive_summary')
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState(null)
  const [error, setError] = useState('')

  const handleGenerate = async () => {
    setLoading(true)
    setError('')

    try {
      const res = await analystApi.generateReport({
        report_type: reportType,
        conversation_id: conversationId || null,
      })
      setReport(res.data)
    } catch (e) {
      setError(e.message || 'Failed to generate report')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-2xl bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <FileText size={18} className="text-prism-400" />
            <h2 className="text-white font-semibold">Generate Report</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white transition-colors">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {!report ? (
            <div className="space-y-4">
              <p className="text-sm text-gray-400">Select the type of report to generate. The AI will create a comprehensive report based on your conversation context and available data.</p>
              <div className="grid grid-cols-1 gap-2">
                {REPORT_TYPES.map((reportOption) => (
                  <button
                    key={reportOption.value}
                    onClick={() => setReportType(reportOption.value)}
                    className={`text-left px-4 py-3 rounded-lg border transition-colors ${
                      reportType === reportOption.value
                        ? 'border-prism-600 bg-prism-900/40 text-white'
                        : 'border-gray-700 hover:border-gray-600 text-gray-300'
                    }`}
                  >
                    <p className="text-sm font-medium">{reportOption.label}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{reportOption.description}</p>
                  </button>
                ))}
              </div>
              {error && <p className="text-red-400 text-sm">{error}</p>}
            </div>
          ) : (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-white">{report.content?.title || report.title}</h3>
                <p className="text-sm text-gray-400 mt-1">{report.content?.executive_summary}</p>
              </div>
              {report.content?.kpis && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Key Performance Indicators</h4>
                  <div className="grid grid-cols-2 gap-3">
                    {report.content.kpis.map((kpi, i) => (
                      <div
                        key={i}
                        className={`p-3 rounded-lg border ${
                          kpi.status === 'good' ? 'bg-emerald-500/10 border-emerald-500/30' :
                          kpi.status === 'warning' ? 'bg-amber-500/10 border-amber-500/30' :
                          'bg-red-500/10 border-red-500/30'
                        }`}
                      >
                        <p className="text-xs text-gray-400">{kpi.name}</p>
                        <p className="text-lg font-bold text-white">{kpi.value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {report.content?.sections?.map((section, i) => (
                <div key={i}>
                  <h4 className="text-sm font-semibold text-gray-200 mb-2">{section.heading}</h4>
                  <p className="text-sm text-gray-400 leading-relaxed">{section.content}</p>
                  {section.key_points && (
                    <ul className="mt-2 space-y-1">
                      {section.key_points.map((point, j) => (
                        <li key={j} className="flex items-start gap-2 text-xs text-gray-400">
                          <span className="mt-1.5 w-1 h-1 rounded-full bg-prism-400 flex-shrink-0" />
                          {point}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
              {report.content?.recommendations && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Recommendations</h4>
                  <ul className="space-y-2">
                    {report.content.recommendations.map((recommendation, i) => (
                      <li key={i} className="text-sm">
                        <span className={`inline-block text-xs px-2 py-0.5 rounded-full mr-2 ${
                          recommendation.priority === 'high' ? 'bg-red-500/20 text-red-400' :
                          recommendation.priority === 'medium' ? 'bg-amber-500/20 text-amber-400' :
                          'bg-gray-700 text-gray-400'
                        }`}>{recommendation.priority}</span>
                        <span className="text-gray-200">{recommendation.action}</span>
                        {recommendation.rationale && <p className="text-xs text-gray-500 mt-0.5 ml-14">{recommendation.rationale}</p>}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-gray-800 flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-gray-800 transition-colors">
            Close
          </button>
          {!report ? (
            <button
              onClick={handleGenerate}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-prism-600 hover:bg-prism-500 text-white text-sm font-medium transition-colors disabled:opacity-50"
            >
              {loading ? <><Loader2 size={14} className="animate-spin" /> Generating…</> : 'Generate Report'}
            </button>
          ) : (
            <button
              onClick={() => setReport(null)}
              className="px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white text-sm transition-colors"
            >
              Generate Another
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
