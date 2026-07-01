import React, { useState, useEffect } from 'react'
import {
  listAgents,
  listTemplates,
  getPerformanceDashboard,
  getActivityFeed,
  getLeaderboard,
} from '../services/agents'

export default function Agents() {
  const [agents, setAgents] = useState([])
  const [templates, setTemplates] = useState([])
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [performance, setPerformance] = useState(null)
  const [activities, setActivities] = useState([])
  const [leaderboard, setLeaderboard] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('agents')

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (selectedAgent) {
      loadAgentDetails()
    }
  }, [selectedAgent])

  const loadData = async () => {
    try {
      const [agentsRes, templatesRes, leaderboardRes] = await Promise.all([
        listAgents(),
        listTemplates(),
        getLeaderboard(),
      ])
      setAgents(agentsRes.data.items || [])
      setTemplates(templatesRes.data.items || [])
      setLeaderboard(leaderboardRes.data.items || [])
      if (agentsRes.data.items?.length > 0) {
        setSelectedAgent(agentsRes.data.items[0])
      }
    } catch (err) {
      console.error('Failed to load agents:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadAgentDetails = async () => {
    if (!selectedAgent) return
    try {
      const [perfRes, activityRes] = await Promise.all([
        getPerformanceDashboard(selectedAgent.id),
        getActivityFeed(selectedAgent.id),
      ])
      setPerformance(perfRes.data)
      setActivities(activityRes.data.items || [])
    } catch (err) {
      console.error('Failed to load agent details:', err)
    }
  }

  if (loading) {
    return <div className="p-6 text-gray-400">Loading agents...</div>
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white mb-1">AI Agents</h1>
        <p className="text-gray-400">Manage and monitor your AI agent workforce</p>
      </div>

      <div className="flex gap-2 mb-6 border-b border-gray-800">
        {[
          { key: 'agents', label: 'My Agents' },
          { key: 'templates', label: 'Templates' },
          { key: 'leaderboard', label: 'Leaderboard' },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? 'text-prism-300 border-b-2 border-prism-500'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'agents' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-white">My Agents</h3>
              <button className="px-4 py-2 bg-prism-600 text-white rounded-lg hover:bg-prism-500 text-sm">
                Create Agent
              </button>
            </div>
            {agents.length === 0 ? (
              <p className="text-gray-400 text-center py-8">No agents yet. Create your first agent to get started.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {agents.map(agent => (
                  <div
                    key={agent.id}
                    onClick={() => setSelectedAgent(agent)}
                    className={`bg-gray-900 border rounded-lg p-4 cursor-pointer transition-colors ${
                      selectedAgent?.id === agent.id ? 'border-prism-500' : 'border-gray-800 hover:border-gray-700'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="text-white font-medium">{agent.display_name}</h4>
                      <span className={`px-2 py-1 text-xs rounded ${
                        agent.status === 'active' ? 'bg-green-900 text-green-300' :
                        agent.status === 'inactive' ? 'bg-gray-800 text-gray-300' :
                        'bg-yellow-900 text-yellow-300'
                      }`}>
                        {agent.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400 mb-2">{agent.description}</p>
                    <div className="flex gap-4 text-xs text-gray-500">
                      <span>Type: {agent.agent_type}</span>
                      <span>Tasks: {agent.tasks_completed}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="space-y-6">
            {selectedAgent && (
              <>
                <AgentDetailsCard agent={selectedAgent} performance={performance} />
                <AgentActivityCard activities={activities} />
              </>
            )}
          </div>
        </div>
      )}

      {activeTab === 'templates' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map(template => (
            <div key={template.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <h4 className="text-white font-medium mb-1">{template.display_name}</h4>
              <p className="text-sm text-gray-400 mb-2">{template.description}</p>
              <div className="flex justify-between items-center text-xs text-gray-500">
                <span>Type: {template.agent_type}</span>
                <span>{template.deployment_count} deployments</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'leaderboard' && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-800">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Rank</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Agent</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Type</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Tasks</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Rating</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {leaderboard.map((agent, index) => (
                <tr key={agent.agent_id} className="hover:bg-gray-800/50">
                  <td className="px-4 py-3 text-sm text-white">#{index + 1}</td>
                  <td className="px-4 py-3 text-sm text-white">{agent.display_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-400">{agent.agent_type}</td>
                  <td className="px-4 py-3 text-sm text-gray-400">{agent.tasks_completed}</td>
                  <td className="px-4 py-3 text-sm text-yellow-400">{agent.user_rating || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function AgentDetailsCard({ agent, performance }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Agent Details</h3>
      <div className="space-y-3 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">Name</span>
          <span className="text-white">{agent.display_name}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Type</span>
          <span className="text-white capitalize">{agent.agent_type}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Status</span>
          <span className="text-white capitalize">{agent.status}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Model</span>
          <span className="text-white">{agent.model_name}</span>
        </div>
        {performance && (
          <>
            <div className="pt-3 border-t border-gray-800">
              <p className="text-gray-400 mb-2">Performance</p>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <p className="text-xs text-gray-500">Tasks Completed</p>
                  <p className="text-white font-medium">{performance.tasks_completed}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Success Rate</p>
                  <p className="text-white font-medium">{performance.success_rate}%</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Avg Execution</p>
                  <p className="text-white font-medium">{performance.avg_execution_time_ms}ms</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Confidence</p>
                  <p className="text-white font-medium">{performance.avg_confidence_score}</p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function AgentActivityCard({ activities }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
      {activities.length === 0 ? (
        <p className="text-sm text-gray-400">No recent activity</p>
      ) : (
        <div className="space-y-3">
          {activities.slice(0, 5).map(activity => (
            <div key={activity.id} className="text-sm">
              <p className="text-white font-medium">{activity.title}</p>
              <p className="text-xs text-gray-400">{activity.description}</p>
              <p className="text-xs text-gray-500 mt-1">{new Date(activity.created_at).toLocaleString()}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}