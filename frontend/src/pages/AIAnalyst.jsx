import React, { useState, useEffect, useRef, useCallback } from 'react'
import {
  Send,
  Loader2,
  Bot,
  FileText,
  Search,
  Sparkles,
  MessageSquare,
  ChevronRight,
} from 'lucide-react'
import { analystApi } from '../services/analyst'
import ConversationList from '../components/analyst/ConversationList'
import MessageBubble from '../components/analyst/MessageBubble'
import ReportModal from '../components/analyst/ReportModal'
import { useAuth } from '../context/AuthContext'

const STARTER_QUESTIONS = [
  'What were total sales last month?',
  'Why did revenue decrease?',
  'Which region performed best this quarter?',
  'Show employee attrition by department',
  'Which customers are at risk of churning?',
  "Summarise today's business performance",
  'What are the top five products by profit?',
  'Forecast revenue for next quarter',
]

function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 px-4 py-3 mb-4">
      <div className="flex items-center gap-1.5 bg-gray-800/60 border border-gray-700/50 rounded-2xl px-4 py-2.5">
        <div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-prism-400 animate-bounce"
              style={{ animationDelay: `${i * 150}ms` }}
            />
          ))}
        </div>
        <span className="text-xs text-gray-400 ml-1">Analysing…</span>
      </div>
    </div>
  )
}

export default function AIAnalyst() {
  const { user } = useAuth()
  const [conversations, setConversations] = useState([])
  const [activeConversationId, setActiveConversationId] = useState(null)
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [typing, setTyping] = useState(false)
  const [suggestedQuestions, setSuggestedQuestions] = useState(STARTER_QUESTIONS)
  const [showReport, setShowReport] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const token = localStorage.getItem('prism_token')

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  const loadConversations = useCallback(async () => {
    try {
      const res = await analystApi.listConversations({ status: 'active' })
      setConversations(res.data)
    } catch (e) {
      // silent
    }
  }, [])

  const loadGlobalSuggestions = useCallback(async () => {
    try {
      const res = await analystApi.getSuggestedQuestions()
      setSuggestedQuestions(res.data.questions || STARTER_QUESTIONS)
    } catch (e) {
      setSuggestedQuestions(STARTER_QUESTIONS)
    }
  }, [])

  useEffect(() => {
    loadConversations()
    loadGlobalSuggestions()
  }, [loadConversations, loadGlobalSuggestions])

  useEffect(() => {
    scrollToBottom()
  }, [messages, typing, scrollToBottom])

  const loadConversation = async (id) => {
    setActiveConversationId(id)

    try {
      const [msgsRes, sqRes] = await Promise.all([
        analystApi.getMessages(id),
        analystApi.getSuggestedQuestions(id),
      ])
      setMessages(msgsRes.data)
      setSuggestedQuestions(sqRes.data.questions || STARTER_QUESTIONS)
    } catch (e) {
      setMessages([])
    }
  }

  const createConversation = async () => {
    try {
      const res = await analystApi.createConversation({ title: 'New Conversation' })
      const conv = res.data
      setConversations((prev) => [conv, ...prev])
      setActiveConversationId(conv.id)
      setMessages([])
      setSuggestedQuestions(STARTER_QUESTIONS)
      inputRef.current?.focus()
    } catch (e) {
      // silent
    }
  }

  const sendQuestion = async (q) => {
    const text = (q || question).trim()
    if (!text || loading) return

    let convId = activeConversationId
    if (!convId) {
      try {
        const res = await analystApi.createConversation({ title: text.slice(0, 100) })
        convId = res.data.id
        setActiveConversationId(convId)
        setConversations((prev) => [res.data, ...prev])
      } catch (e) {
        return
      }
    }

    const userMsg = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMsg])
    setQuestion('')
    setTyping(true)
    setLoading(true)

    try {
      const response = await analystApi.streamQuestion(convId, text, token)
      if (!response.ok) throw new Error('Stream failed')

      const reader = response.body?.getReader()
      if (!reader) throw new Error('Stream unavailable')

      const decoder = new TextDecoder()
      let buffer = ''
      let resultPayload = null

      setTyping(false)

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ') || line === 'data: [DONE]') continue

          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'result') {
              resultPayload = data.value
            }
          } catch (e) {
            // skip malformed chunks
          }
        }
      }

      if (resultPayload) {
        const assistantMsg = {
          id: `stream-${Date.now()}`,
          role: 'assistant',
          content: resultPayload.executive_summary || 'Analysis complete.',
          ...resultPayload,
          created_at: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, assistantMsg])
        if (resultPayload.suggested_questions) {
          setSuggestedQuestions(resultPayload.suggested_questions)
        }
      }

      await loadConversations()
    } catch (e) {
      setTyping(false)

      try {
        const res = await analystApi.sendQuestion(convId, { question: text, stream: false })
        setMessages((prev) => [...prev, { ...res.data, created_at: res.data.created_at || new Date().toISOString() }])
        if (res.data.suggested_questions) setSuggestedQuestions(res.data.suggested_questions)
        await loadConversations()
      } catch (err) {
        setMessages((prev) => [...prev, {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: 'Sorry, I encountered an error processing your question. Please try again.',
          executive_summary: 'Sorry, I encountered an error processing your question. Please try again.',
          created_at: new Date().toISOString(),
        }])
      }
    } finally {
      setTyping(false)
      setLoading(false)
      inputRef.current?.focus()
      requestAnimationFrame(() => {
        if (inputRef.current) inputRef.current.style.height = '48px'
      })
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendQuestion()
    }
  }

  const activeConversation = conversations.find((conversation) => conversation.id === activeConversationId)
  const filteredConversations = searchQuery
    ? conversations.filter((conversation) => conversation.title.toLowerCase().includes(searchQuery.toLowerCase()))
    : conversations

  return (
    <div className="flex h-full overflow-hidden -m-6 bg-gray-950">
      {sidebarOpen && (
        <div className="w-64 flex-shrink-0 flex flex-col border-r border-gray-800 bg-gray-900/50">
          <div className="px-3 py-3 border-b border-gray-800">
            <div className="flex items-center gap-2 mb-3">
              <Bot size={16} className="text-prism-400" />
              <span className="text-sm font-semibold text-white">AI Analyst</span>
            </div>
            <div className="relative">
              <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" />
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search conversations…"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-gray-300 placeholder-gray-600 outline-none focus:border-prism-600 transition-colors"
              />
            </div>
          </div>
          <ConversationList
            conversations={filteredConversations}
            activeId={activeConversationId}
            onSelect={loadConversation}
            onRefresh={loadConversations}
            onNew={createConversation}
          />
        </div>
      )}

      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-6 py-3 border-b border-gray-800 bg-gray-900/30">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-1.5 rounded-lg hover:bg-gray-800 text-gray-500 hover:text-gray-300 transition-colors"
            >
              <ChevronRight size={16} className={`transition-transform ${sidebarOpen ? 'rotate-180' : ''}`} />
            </button>
            <div className="min-w-0">
              <h1 className="text-sm font-semibold text-white truncate">
                {activeConversation?.title || 'AI Business Analyst'}
              </h1>
              {activeConversation ? (
                <p className="text-xs text-gray-500">{activeConversation.message_count} messages</p>
              ) : (
                <p className="text-xs text-gray-500">Conversational analysis workspace</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {activeConversationId && (
              <button
                onClick={() => setShowReport(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white text-xs font-medium transition-colors border border-gray-700"
              >
                <FileText size={13} />
                Generate Report
              </button>
            )}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-6">
          {messages.length === 0 && !typing ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-14 h-14 bg-prism-900/60 border border-prism-800 rounded-2xl flex items-center justify-center mb-4">
                <Sparkles size={24} className="text-prism-400" />
              </div>
              <h2 className="text-lg font-semibold text-white mb-2">Ask anything about your business</h2>
              <p className="text-sm text-gray-400 mb-8 max-w-md">
                Ask questions in plain English. The AI analyst will interpret your intent, analyse your data, and explain findings with evidence and recommendations.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-w-xl w-full">
                {suggestedQuestions.slice(0, 8).map((starterQuestion, i) => (
                  <button
                    key={i}
                    onClick={() => sendQuestion(starterQuestion)}
                    className="text-left text-sm px-4 py-3 rounded-xl bg-gray-800/60 border border-gray-700/50 hover:border-prism-700/50 hover:bg-gray-800 text-gray-300 hover:text-white transition-colors"
                  >
                    {starterQuestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-2">
              {messages.map((msg, i) => (
                <MessageBubble key={msg.id || i} message={msg} onQuestionClick={sendQuestion} />
              ))}
              {typing && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-gray-800 bg-gray-900/30">
          {messages.length > 0 && suggestedQuestions.length > 0 && (
            <div className="flex items-center gap-2 mb-3 flex-wrap">
              <MessageSquare size={12} className="text-gray-600 flex-shrink-0" />
              {suggestedQuestions.slice(0, 4).map((suggestion, i) => (
                <button
                  key={i}
                  onClick={() => sendQuestion(suggestion)}
                  disabled={loading}
                  className="text-xs bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-400 hover:text-gray-200 rounded-full px-3 py-1 transition-colors disabled:opacity-50 truncate max-w-[200px]"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}

          <div className="flex items-end gap-3">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a business question… (Enter to send, Shift+Enter for new line)"
                rows={1}
                disabled={loading}
                className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 outline-none focus:border-prism-600 transition-colors resize-none overflow-hidden disabled:opacity-50"
                style={{ minHeight: '48px', maxHeight: '120px' }}
                onInput={(e) => {
                  e.target.style.height = 'auto'
                  e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`
                }}
              />
            </div>
            <button
              onClick={() => sendQuestion()}
              disabled={!question.trim() || loading}
              className="flex-shrink-0 w-11 h-11 flex items-center justify-center rounded-xl bg-prism-600 hover:bg-prism-500 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            </button>
          </div>
          <p className="text-xs text-gray-700 mt-2 text-center">
            AI Analyst uses your semantic model and business glossary to answer questions accurately.
          </p>
        </div>
      </div>

      {showReport && (
        <ReportModal conversationId={activeConversationId} onClose={() => setShowReport(false)} />
      )}
    </div>
  )
}
