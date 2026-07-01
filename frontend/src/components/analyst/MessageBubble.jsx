import React, { useState } from 'react'
import {
  ChevronDown,
  ChevronUp,
  ThumbsUp,
  ThumbsDown,
  TrendingUp,
  Lightbulb,
  Database,
} from 'lucide-react'
import SimpleChart from './SimpleChart'
import { analystApi } from '../../services/analyst'

export default function MessageBubble({ message, onQuestionClick }) {
  const [showEvidence, setShowEvidence] = useState(false)
  const [feedbackGiven, setFeedbackGiven] = useState(null)

  const isUser = message.role === 'user'

  const handleFeedback = async (rating) => {
    try {
      await analystApi.submitFeedback(message.id, { rating, feedback_type: 'rating' })
      setFeedbackGiven(rating)
    } catch (e) {
      // silent
    }
  }

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-xl bg-prism-600/20 border border-prism-800/50 rounded-2xl rounded-tr-sm px-4 py-3">
          <p className="text-white text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    )
  }

  const {
    executive_summary,
    key_findings,
    supporting_evidence,
    business_interpretation,
    confidence_level,
    data_sources_used,
    visualizations,
    recommendations,
    suggested_questions,
    intent,
  } = message

  return (
    <div className="mb-6 space-y-3">
      {intent && (
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 text-xs bg-prism-900/40 text-prism-300 border border-prism-800/50 rounded-full px-2 py-0.5">
            <TrendingUp size={10} />
            {intent.replace(/_/g, ' ')}
          </span>
          {confidence_level != null && (
            <span className="text-xs text-gray-500">{confidence_level}% confidence</span>
          )}
        </div>
      )}

      {executive_summary && (
        <div className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-4">
          <p className="text-gray-100 text-sm leading-relaxed whitespace-pre-wrap">{executive_summary}</p>
        </div>
      )}

      {visualizations && visualizations.length > 0 && (
        <div className="grid grid-cols-1 gap-3">
          {visualizations.map((viz, i) => (
            <div key={i} className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-4">
              <SimpleChart visualization={viz} />
            </div>
          ))}
        </div>
      )}

      {key_findings && key_findings.length > 0 && (
        <div className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-4">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3 flex items-center gap-1.5">
            <Lightbulb size={12} />
            Key Findings
          </h4>
          <ul className="space-y-2">
            {key_findings.map((finding, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-200">
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-prism-400 flex-shrink-0" />
                {finding}
              </li>
            ))}
          </ul>
        </div>
      )}

      {business_interpretation && (
        <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4">
          <h4 className="text-xs font-semibold text-amber-400 uppercase tracking-wide mb-2">
            Business Interpretation
          </h4>
          <p className="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">{business_interpretation}</p>
        </div>
      )}

      {recommendations && recommendations.length > 0 && (
        <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-4">
          <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wide mb-3">
            Recommended Actions
          </h4>
          <ul className="space-y-3">
            {recommendations.map((recommendation, i) => (
              <li key={i} className="text-sm">
                <p className="text-emerald-300 font-medium">{recommendation.action || recommendation}</p>
                {recommendation.rationale && (
                  <p className="text-gray-400 text-xs mt-0.5">{recommendation.rationale}</p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {supporting_evidence && supporting_evidence.length > 0 && (
        <div className="bg-gray-800/30 border border-gray-700/30 rounded-xl overflow-hidden">
          <button
            onClick={() => setShowEvidence(!showEvidence)}
            className="w-full flex items-center justify-between px-4 py-3 text-xs text-gray-400 hover:text-gray-200 transition-colors"
          >
            <span className="flex items-center gap-1.5">
              <Database size={12} />
              Supporting Evidence ({supporting_evidence.length} sources)
            </span>
            {showEvidence ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          {showEvidence && (
            <div className="px-4 pb-3 space-y-2 border-t border-gray-700/30">
              {supporting_evidence.map((evidence, i) => (
                <div key={i} className="flex items-center gap-3 text-xs flex-wrap">
                  <span className="text-gray-500">{evidence.source}</span>
                  {evidence.metric && <span className="text-gray-400">{evidence.metric}:</span>}
                  {evidence.value && <span className="text-prism-300 font-mono">{evidence.value}</span>}
                </div>
              ))}
              {data_sources_used && (
                <div className="flex items-center gap-2 text-xs text-gray-600 mt-1 pt-1 border-t border-gray-700/30 flex-wrap">
                  <span>Sources:</span>
                  {data_sources_used.map((source, i) => (
                    <span key={i} className="text-gray-500">{source}</span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-1">
          <button
            onClick={() => handleFeedback(5)}
            className={`p-1.5 rounded-lg transition-colors ${feedbackGiven === 5 ? 'text-emerald-400 bg-emerald-500/10' : 'text-gray-600 hover:text-gray-300 hover:bg-gray-800'}`}
            title="Helpful"
          >
            <ThumbsUp size={13} />
          </button>
          <button
            onClick={() => handleFeedback(1)}
            className={`p-1.5 rounded-lg transition-colors ${feedbackGiven === 1 ? 'text-red-400 bg-red-500/10' : 'text-gray-600 hover:text-gray-300 hover:bg-gray-800'}`}
            title="Not helpful"
          >
            <ThumbsDown size={13} />
          </button>
        </div>
        {suggested_questions && suggested_questions.length > 0 && onQuestionClick && (
          <div className="flex items-center gap-1 flex-wrap justify-end">
            {suggested_questions.slice(0, 3).map((suggestion, i) => (
              <button
                key={i}
                onClick={() => onQuestionClick(suggestion)}
                className="text-xs bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-400 hover:text-gray-200 rounded-full px-2.5 py-1 transition-colors"
              >
                {suggestion.length > 35 ? `${suggestion.slice(0, 35)}…` : suggestion}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
