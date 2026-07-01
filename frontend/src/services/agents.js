import axios from './api'

const API_BASE = '/api/v1/agents'

// Agents
export const createAgent = (data) => axios.post(API_BASE, data)
export const listAgents = (params = {}) => axios.get(API_BASE, { params })
export const getAgent = (id) => axios.get(`${API_BASE}/${id}`)
export const updateAgent = (id, data) => axios.put(`${API_BASE}/${id}`, data)
export const archiveAgent = (id) => axios.delete(`${API_BASE}/${id}`)
export const enableAgent = (id) => axios.post(`${API_BASE}/${id}/enable`)
export const disableAgent = (id) => axios.post(`${API_BASE}/${id}/disable`)

// Templates
export const listTemplates = (params = {}) => axios.get(`${API_BASE}/templates`, { params })
export const getTemplate = (id) => axios.get(`${API_BASE}/templates/${id}`)
export const deployTemplate = (templateId, data) => axios.post(`${API_BASE}/templates/${templateId}/deploy`, data)

// Tasks
export const createTask = (agentId, data) => axios.post(`${API_BASE}/${agentId}/tasks`, data)
export const listTasks = (agentId, params = {}) => axios.get(`${API_BASE}/${agentId}/tasks`, { params })
export const getTask = (agentId, taskId) => axios.get(`${API_BASE}/${agentId}/tasks/${taskId}`)
export const updateTask = (agentId, taskId, data) => axios.put(`${API_BASE}/${agentId}/tasks/${taskId}`, data)

// Execution
export const executeAgent = (agentId, data) => axios.post(`${API_BASE}/${agentId}/execute`, data)
export const listExecutions = (agentId, params = {}) => axios.get(`${API_BASE}/${agentId}/executions`, { params })

// Memory
export const createMemory = (agentId, data) => axios.post(`${API_BASE}/${agentId}/memory`, data)
export const listMemories = (agentId, params = {}) => axios.get(`${API_BASE}/${agentId}/memory`, { params })
export const updateMemory = (agentId, memoryId, data) => axios.put(`${API_BASE}/${agentId}/memory/${memoryId}`, data)

// Recommendations
export const listRecommendations = (agentId, params = {}) => axios.get(`${API_BASE}/${agentId}/recommendations`, { params })
export const markRecommendationViewed = (agentId, recommendationId) => axios.post(`${API_BASE}/${agentId}/recommendations/${recommendationId}/view`)
export const markRecommendationActioned = (agentId, recommendationId) => axios.post(`${API_BASE}/${agentId}/recommendations/${recommendationId}/action`)

// Collaboration
export const sendCollaborationMessage = (agentId, data) => axios.post(`${API_BASE}/${agentId}/collaborate`, data)
export const listMessages = (agentId, params = {}) => axios.get(`${API_BASE}/${agentId}/messages`, { params })

// Approvals
export const createApproval = (agentId, data) => axios.post(`${API_BASE}/${agentId}/approvals`, data)
export const listApprovals = (agentId, params = {}) => axios.get(`${API_BASE}/${agentId}/approvals`, { params })
export const processApproval = (agentId, approvalId, data) => axios.post(`${API_BASE}/${agentId}/approvals/${approvalId}/action`, data)

// Performance
export const getPerformanceDashboard = (agentId) => axios.get(`${API_BASE}/${agentId}/performance`)
export const listMetrics = (agentId, params = {}) => axios.get(`${API_BASE}/${agentId}/metrics`, { params })
export const getLeaderboard = (params = {}) => axios.get(`${API_BASE}/leaderboard/top`, { params })

// Activity
export const getActivityFeed = (agentId, params = {}) => axios.get(`${API_BASE}/${agentId}/activity`, { params })

// Permissions
export const createPermission = (agentId, data) => axios.post(`${API_BASE}/${agentId}/permissions`, data)

// Scheduling
export const updateSchedule = (agentId, data) => axios.put(`${API_BASE}/${agentId}/schedule`, data)

// Governance
export const getAuditTrail = (agentId, params = {}) => axios.get(`${API_BASE}/${agentId}/audit-trail`, { params })
export const getGovernanceSummary = (agentId) => axios.get(`${API_BASE}/${agentId}/governance`)