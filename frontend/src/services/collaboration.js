import axios from './api'

const API_BASE = '/api/v1/collaboration'

// Workspaces
export const createWorkspace = (data) => axios.post(`${API_BASE}/workspaces`, data)
export const listWorkspaces = (params = {}) => axios.get(`${API_BASE}/workspaces`, { params })
export const getWorkspace = (id) => axios.get(`${API_BASE}/workspaces/${id}`)
export const updateWorkspace = (id, data) => axios.put(`${API_BASE}/workspaces/${id}`, data)
export const archiveWorkspace = (id) => axios.delete(`${API_BASE}/workspaces/${id}`)
export const addWorkspaceMember = (workspaceId, data) => axios.post(`${API_BASE}/workspaces/${workspaceId}/members`, data)
export const updateMemberRole = (workspaceId, userId, data) => axios.put(`${API_BASE}/workspaces/${workspaceId}/members/${userId}`, data)
export const removeWorkspaceMember = (workspaceId, userId) => axios.delete(`${API_BASE}/workspaces/${workspaceId}/members/${userId}`)
export const listWorkspaceMembers = (workspaceId) => axios.get(`${API_BASE}/workspaces/${workspaceId}/members`)

// Discussions
export const createDiscussion = (data) => axios.post(`${API_BASE}/discussions`, data)
export const listDiscussions = (params = {}) => axios.get(`${API_BASE}/discussions`, { params })
export const getDiscussion = (id) => axios.get(`${API_BASE}/discussions/${id}`)
export const updateDiscussion = (id, data) => axios.put(`${API_BASE}/discussions/${id}`, data)
export const archiveDiscussion = (id) => axios.delete(`${API_BASE}/discussions/${id}`)
export const togglePinDiscussion = (id) => axios.patch(`${API_BASE}/discussions/${id}/pin`)

// Comments
export const createComment = (data) => axios.post(`${API_BASE}/comments`, data)
export const listComments = (discussionId, params = {}) => axios.get(`${API_BASE}/discussions/${discussionId}/comments`, { params })
export const updateComment = (id, data) => axios.put(`${API_BASE}/comments/${id}`, data)
export const deleteComment = (id) => axios.delete(`${API_BASE}/comments/${id}`)
export const toggleReaction = (commentId, data) => axios.post(`${API_BASE}/comments/${commentId}/reactions`, data)

// Decisions
export const createDecision = (data) => axios.post(`${API_BASE}/decisions`, data)
export const listDecisions = (params = {}) => axios.get(`${API_BASE}/decisions`, { params })
export const getDecision = (id) => axios.get(`${API_BASE}/decisions/${id}`)
export const updateDecision = (id, data) => axios.put(`${API_BASE}/decisions/${id}`, data)
export const addDecisionParticipant = (decisionId, data) => axios.post(`${API_BASE}/decisions/${decisionId}/participants`, data)
export const removeDecisionParticipant = (decisionId, userId) => axios.delete(`${API_BASE}/decisions/${decisionId}/participants/${userId}`)
export const listDecisionParticipants = (decisionId) => axios.get(`${API_BASE}/decisions/${decisionId}/participants`)
export const getDecisionHistory = (decisionId) => axios.get(`${API_BASE}/decisions/${decisionId}/history`)

// Actions
export const createAction = (data) => axios.post(`${API_BASE}/actions`, data)
export const listActions = (params = {}) => axios.get(`${API_BASE}/actions`, { params })
export const getAction = (id) => axios.get(`${API_BASE}/actions/${id}`)
export const updateAction = (id, data) => axios.put(`${API_BASE}/actions/${id}`, data)
export const completeAction = (id) => axios.patch(`${API_BASE}/actions/${id}/complete`)
export const getActionCalendar = (params = {}) => axios.get(`${API_BASE}/actions/calendar`, { params })
export const getActionKanban = (params = {}) => axios.get(`${API_BASE}/actions/kanban`, { params })

// Approvals
export const createApprovalWorkflow = (data) => axios.post(`${API_BASE}/approval-workflows`, data)
export const listApprovalWorkflows = (params = {}) => axios.get(`${API_BASE}/approval-workflows`, { params })
export const addApprovalStep = (workflowId, data) => axios.post(`${API_BASE}/approval-workflows/${workflowId}/steps`, data)
export const submitForApproval = (data) => axios.post(`${API_BASE}/approval-requests`, data)
export const listApprovalRequests = (params = {}) => axios.get(`${API_BASE}/approval-requests`, { params })
export const processApprovalAction = (instanceId, data) => axios.post(`${API_BASE}/approval-requests/${instanceId}/action`, data)

// Meetings
export const generateMeetingPack = (data) => axios.post(`${API_BASE}/meeting-packs`, data)
export const listMeetingPacks = (params = {}) => axios.get(`${API_BASE}/meeting-packs`, { params })
export const getMeetingPack = (id) => axios.get(`${API_BASE}/meeting-packs/${id}`)
export const createMeetingSummary = (data) => axios.post(`${API_BASE}/meeting-summaries`, data)
export const listMeetingSummaries = (params = {}) => axios.get(`${API_BASE}/meeting-summaries`, { params })
export const updateMeetingSummary = (id, data) => axios.put(`${API_BASE}/meeting-summaries/${id}`, data)

// AI Assistant
export const generateAgenda = (data) => axios.post(`${API_BASE}/ai-assistant/agenda`, data)
export const generateSummary = (data) => axios.post(`${API_BASE}/ai-assistant/summarize`, data)

// Knowledge
export const createKnowledgeArticle = (data) => axios.post(`${API_BASE}/knowledge-articles`, data)
export const listKnowledgeArticles = (params = {}) => axios.get(`${API_BASE}/knowledge-articles`, { params })
export const getKnowledgeArticle = (id) => axios.get(`${API_BASE}/knowledge-articles/${id}`)
export const updateKnowledgeArticle = (id, data) => axios.put(`${API_BASE}/knowledge-articles/${id}`, data)
export const deleteKnowledgeArticle = (id) => axios.delete(`${API_BASE}/knowledge-articles/${id}`)
export const searchKnowledge = (data) => axios.post(`${API_BASE}/knowledge-articles/search`, data)

// Notifications
export const listNotifications = (params = {}) => axios.get(`${API_BASE}/notifications`, { params })
export const markNotificationRead = (id) => axios.put(`${API_BASE}/notifications/${id}/read`)
export const markAllNotificationsRead = () => axios.put(`${API_BASE}/notifications/read-all`)
export const getUnreadCount = () => axios.get(`${API_BASE}/notifications/unread-count`)
export const getNotificationPreferences = () => axios.get(`${API_BASE}/notifications/preferences`)
export const updateNotificationPreference = (data) => axios.put(`${API_BASE}/notifications/preferences`, data)

// Analytics
export const getCollaborationAnalytics = (workspaceId) => axios.get(`${API_BASE}/analytics/dashboard`, { params: { workspace_id: workspaceId } })
export const getCollaborationMetrics = (params = {}) => axios.get(`${API_BASE}/analytics/metrics`, { params })

// Impact Tracking
export const createDecisionImpact = (data) => axios.post(`${API_BASE}/decision-impacts`, data)
export const getDecisionImpact = (decisionId) => axios.get(`${API_BASE}/decision-impacts/${decisionId}`)
export const updateDecisionImpact = (decisionId, data) => axios.put(`${API_BASE}/decision-impacts/${decisionId}`, data)

// Timeline
export const getTimeline = (params = {}) => axios.get(`${API_BASE}/timeline`, { params })