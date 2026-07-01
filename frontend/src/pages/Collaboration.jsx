import React, { useState, useEffect } from 'react'
import { listWorkspaces, listDiscussions, listDecisions, listActions, getCollaborationAnalytics } from '../services/collaboration'

export default function Collaboration() {
  const [workspaces, setWorkspaces] = useState([])
  const [selectedWorkspace, setSelectedWorkspace] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadWorkspaces()
  }, [])

  useEffect(() => {
    if (selectedWorkspace) {
      loadWorkspaceData()
    }
  }, [selectedWorkspace, activeTab])

  const loadWorkspaces = async () => {
    try {
      const res = await listWorkspaces()
      setWorkspaces(res.data.items || [])
      if (res.data.items?.length > 0) {
        setSelectedWorkspace(res.data.items[0])
      }
    } catch (err) {
      console.error('Failed to load workspaces:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadWorkspaceData = async () => {
    if (!selectedWorkspace) return
    // Data will be loaded by individual tab components
  }

  if (loading) {
    return <div className="p-6 text-gray-400">Loading collaboration workspace...</div>
  }

  if (!selectedWorkspace) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-white mb-2">Welcome to Collaboration</h2>
          <p className="text-gray-400 mb-6">Create or select a workspace to get started</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white mb-1">{selectedWorkspace.name}</h1>
        <p className="text-gray-400">{selectedWorkspace.description || 'Collaboration workspace'}</p>
      </div>

      <div className="flex gap-2 mb-6 border-b border-gray-800">
        {[
          { key: 'overview', label: 'Overview' },
          { key: 'discussions', label: 'Discussions' },
          { key: 'decisions', label: 'Decisions' },
          { key: 'actions', label: 'Actions' },
          { key: 'approvals', label: 'Approvals' },
          { key: 'meetings', label: 'Meetings' },
          { key: 'knowledge', label: 'Knowledge' },
          { key: 'analytics', label: 'Analytics' },
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          {activeTab === 'overview' && <OverviewTab workspace={selectedWorkspace} />}
          {activeTab === 'discussions' && <DiscussionsTab workspaceId={selectedWorkspace.id} />}
          {activeTab === 'decisions' && <DecisionsTab workspaceId={selectedWorkspace.id} />}
          {activeTab === 'actions' && <ActionsTab workspaceId={selectedWorkspace.id} />}
          {activeTab === 'approvals' && <ApprovalsTab workspaceId={selectedWorkspace.id} />}
          {activeTab === 'meetings' && <MeetingsTab workspaceId={selectedWorkspace.id} />}
          {activeTab === 'knowledge' && <KnowledgeTab workspaceId={selectedWorkspace.id} />}
          {activeTab === 'analytics' && <AnalyticsTab workspaceId={selectedWorkspace.id} />}
        </div>
        <div className="space-y-6">
          <WorkspaceInfoCard workspace={selectedWorkspace} />
          <RecentActivityCard workspaceId={selectedWorkspace.id} />
        </div>
      </div>
    </div>
  )
}

function OverviewTab({ workspace }) {
  const [stats, setStats] = useState({ discussions: 0, decisions: 0, actions: 0, members: 0 })

  useEffect(() => {
    // Load summary stats
    setStats({
      discussions: workspace.discussion_count || 0,
      decisions: workspace.decision_count || 0,
      actions: workspace.action_count || 0,
      members: workspace.member_count || 0,
    })
  }, [workspace])

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="Discussions" value={stats.discussions} color="blue" />
        <StatCard title="Decisions" value={stats.decisions} color="green" />
        <StatCard title="Actions" value={stats.actions} color="yellow" />
        <StatCard title="Members" value={stats.members} color="purple" />
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
        <div className="grid grid-cols-2 gap-3">
          <QuickAction label="New Discussion" icon="💬" />
          <QuickAction label="New Decision" icon="✅" />
          <QuickAction label="New Action" icon="📋" />
          <QuickAction label="Generate Meeting Pack" icon="📊" />
        </div>
      </div>
    </div>
  )
}

function DiscussionsTab({ workspaceId }) {
  const [discussions, setDiscussions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDiscussions()
  }, [workspaceId])

  const loadDiscussions = async () => {
    try {
      const res = await listDiscussions({ workspace_id: workspaceId })
      setDiscussions(res.data.items || [])
    } catch (err) {
      console.error('Failed to load discussions:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="text-gray-400">Loading discussions...</div>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-white">Discussions</h3>
        <button className="px-4 py-2 bg-prism-600 text-white rounded-lg hover:bg-prism-500 text-sm">
          New Discussion
        </button>
      </div>
      {discussions.length === 0 ? (
        <p className="text-gray-400 text-center py-8">No discussions yet</p>
      ) : (
        <div className="space-y-3">
          {discussions.map(d => (
            <div key={d.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-colors">
              <h4 className="text-white font-medium mb-1">{d.title}</h4>
              <p className="text-sm text-gray-400">
                {d.comment_count} comments · Created by {d.creator_name} · {new Date(d.created_at).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function DecisionsTab({ workspaceId }) {
  const [decisions, setDecisions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDecisions()
  }, [workspaceId])

  const loadDecisions = async () => {
    try {
      const res = await listDecisions({ workspace_id: workspaceId })
      setDecisions(res.data.items || [])
    } catch (err) {
      console.error('Failed to load decisions:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="text-gray-400">Loading decisions...</div>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-white">Decisions</h3>
        <button className="px-4 py-2 bg-prism-600 text-white rounded-lg hover:bg-prism-500 text-sm">
          New Decision
        </button>
      </div>
      {decisions.length === 0 ? (
        <p className="text-gray-400 text-center py-8">No decisions yet</p>
      ) : (
        <div className="space-y-3">
          {decisions.map(d => (
            <div key={d.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <h4 className="text-white font-medium">{d.title}</h4>
                <span className={`px-2 py-1 text-xs rounded ${
                  d.status === 'approved' ? 'bg-green-900 text-green-300' :
                  d.status === 'open' ? 'bg-yellow-900 text-yellow-300' :
                  'bg-gray-800 text-gray-300'
                }`}>
                  {d.status}
                </span>
              </div>
              <p className="text-sm text-gray-400 mb-2">{d.description}</p>
              <div className="flex gap-4 text-xs text-gray-500">
                <span>Priority: {d.priority}</span>
                <span>Owner: {d.owner_name}</span>
                {d.due_date && <span>Due: {new Date(d.due_date).toLocaleDateString()}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ActionsTab({ workspaceId }) {
  const [actions, setActions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadActions()
  }, [workspaceId])

  const loadActions = async () => {
    try {
      const res = await listActions({ workspace_id: workspaceId })
      setActions(res.data.items || [])
    } catch (err) {
      console.error('Failed to load actions:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="text-gray-400">Loading actions...</div>

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-white">Actions</h3>
        <button className="px-4 py-2 bg-prism-600 text-white rounded-lg hover:bg-prism-500 text-sm">
          New Action
        </button>
      </div>
      {actions.length === 0 ? (
        <p className="text-gray-400 text-center py-8">No actions yet</p>
      ) : (
        <div className="space-y-3">
          {actions.map(a => (
            <div key={a.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <h4 className="text-white font-medium">{a.title}</h4>
                <span className={`px-2 py-1 text-xs rounded ${
                  a.status === 'completed' ? 'bg-green-900 text-green-300' :
                  a.status === 'in_progress' ? 'bg-blue-900 text-blue-300' :
                  a.status === 'blocked' ? 'bg-red-900 text-red-300' :
                  'bg-gray-800 text-gray-300'
                }`}>
                  {a.status.replace('_', ' ')}
                </span>
              </div>
              <div className="flex gap-4 text-xs text-gray-500">
                {a.assignee_name && <span>Assignee: {a.assignee_name}</span>}
                {a.due_date && <span>Due: {new Date(a.due_date).toLocaleDateString()}</span>}
                <span>Priority: {a.priority}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ApprovalsTab({ workspaceId }) {
  return (
    <div className="text-center py-12">
      <p className="text-gray-400">Approval workflows will be displayed here</p>
    </div>
  )
}

function MeetingsTab({ workspaceId }) {
  return (
    <div className="text-center py-12">
      <p className="text-gray-400">Meeting packs and summaries will be displayed here</p>
    </div>
  )
}

function KnowledgeTab({ workspaceId }) {
  return (
    <div className="text-center py-12">
      <p className="text-gray-400">Knowledge articles will be displayed here</p>
    </div>
  )
}

function AnalyticsTab({ workspaceId }) {
  const [analytics, setAnalytics] = useState(null)

  useEffect(() => {
    loadAnalytics()
  }, [workspaceId])

  const loadAnalytics = async () => {
    try {
      const res = await getCollaborationAnalytics(workspaceId)
      setAnalytics(res.data)
    } catch (err) {
      console.error('Failed to load analytics:', err)
    }
  }

  if (!analytics) return <div className="text-gray-400">Loading analytics...</div>

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-white">Collaboration Analytics</h3>
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-sm text-gray-400 mb-1">Avg Decision Time</p>
          <p className="text-2xl font-bold text-white">{analytics.avg_decision_time_hours}h</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-sm text-gray-400 mb-1">Approval Cycle Time</p>
          <p className="text-2xl font-bold text-white">{analytics.approval_cycle_time_hours}h</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-sm text-gray-400 mb-1">Action Completion Rate</p>
          <p className="text-2xl font-bold text-white">{analytics.action_completion_rate}%</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-sm text-gray-400 mb-1">Team Participation</p>
          <p className="text-2xl font-bold text-white">{analytics.team_participation_count}</p>
        </div>
      </div>
    </div>
  )
}

function WorkspaceInfoCard({ workspace }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Workspace Info</h3>
      <div className="space-y-3 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">Type</span>
          <span className="text-white capitalize">{workspace.workspace_type}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Members</span>
          <span className="text-white">{workspace.member_count || 0}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Discussions</span>
          <span className="text-white">{workspace.discussion_count || 0}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Decisions</span>
          <span className="text-white">{workspace.decision_count || 0}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Actions</span>
          <span className="text-white">{workspace.action_count || 0}</span>
        </div>
      </div>
    </div>
  )
}

function RecentActivityCard({ workspaceId }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
      <p className="text-sm text-gray-400">Activity feed will appear here</p>
    </div>
  )
}

function StatCard({ title, value, color }) {
  const colors = {
    blue: 'text-blue-400',
    green: 'text-green-400',
    yellow: 'text-yellow-400',
    purple: 'text-purple-400',
  }
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <p className="text-sm text-gray-400 mb-1">{title}</p>
      <p className={`text-2xl font-bold ${colors[color] || 'text-white'}`}>{value}</p>
    </div>
  )
}

function QuickAction({ label, icon }) {
  return (
    <button className="flex items-center gap-2 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-600 transition-colors">
      <span className="text-xl">{icon}</span>
      <span className="text-sm text-gray-200">{label}</span>
    </button>
  )
}