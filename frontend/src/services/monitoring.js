import api from './api';

export const monitoringService = {
  // Dashboard
  getStats: () => api.get('/monitoring/stats'),

  // Monitors
  getMonitors: (params) => api.get('/monitoring/monitors', { params }),
  getMonitor: (id) => api.get(`/monitoring/monitors/${id}`),
  createMonitor: (data) => api.post('/monitoring/monitors', data),
  updateMonitor: (id, data) => api.put(`/monitoring/monitors/${id}`, data),
  deleteMonitor: (id) => api.delete(`/monitoring/monitors/${id}`),
  toggleMonitor: (id) => api.post(`/monitoring/monitors/${id}/toggle`),
  duplicateMonitor: (id) => api.post(`/monitoring/monitors/${id}/duplicate`),
  evaluateMonitor: (id) => api.post(`/monitoring/monitors/${id}/evaluate`),

  // Alerts
  getAlerts: (params) => api.get('/monitoring/alerts', { params }),
  getAlert: (id) => api.get(`/monitoring/alerts/${id}`),
  acknowledgeAlert: (id) => api.post(`/monitoring/alerts/${id}/acknowledge`),
  resolveAlert: (id, data) => api.post(`/monitoring/alerts/${id}/resolve`, data),
  assignAlert: (id, data) => api.post(`/monitoring/alerts/${id}/assign`, data),
  addAlertComment: (id, data) => api.post(`/monitoring/alerts/${id}/comments`, data),

  // Anomalies
  getAnomalies: (params) => api.get('/monitoring/anomalies', { params }),

  // Workflows
  getWorkflows: (params) => api.get('/monitoring/workflows', { params }),
  getWorkflow: (id) => api.get(`/monitoring/workflows/${id}`),
  createWorkflow: (data) => api.post('/monitoring/workflows', data),
  executeWorkflow: (id) => api.post(`/monitoring/workflows/${id}/execute`),
  getWorkflowExecutions: (id, params) => api.get(`/monitoring/workflows/${id}/executions`, { params }),

  // Notifications
  getNotificationConfigs: () => api.get('/monitoring/notifications/config'),
  createNotificationConfig: (data) => api.post('/monitoring/notifications/config', data),
  getNotifications: (params) => api.get('/monitoring/notifications/deliveries', { params }),
  getUnreadCount: () => api.get('/monitoring/notifications/unread-count'),
  markNotificationRead: (id) => api.post(`/monitoring/notifications/${id}/read`),

  // Escalation Policies
  getEscalationPolicies: () => api.get('/monitoring/escalation-policies'),
  createEscalationPolicy: (data) => api.post('/monitoring/escalation-policies', data),

  // Scheduled Insights
  getScheduledInsights: (params) => api.get('/monitoring/scheduled-insights', { params }),
  createScheduledInsight: (data) => api.post('/monitoring/scheduled-insights', data),

  // SLA Metrics
  getSLAMetrics: (params) => api.get('/monitoring/sla-metrics', { params }),
  createSLAMetric: (data) => api.post('/monitoring/sla-metrics', data),
  measureSLA: (id, value) => api.post(`/monitoring/sla-metrics/${id}/measure`, null, { params: { value } }),

  // Health Score
  getHealthScore: () => api.get('/monitoring/health-score'),
  refreshHealthScore: () => api.post('/monitoring/health-score/refresh'),

  // Audit
  getAuditRecords: (params) => api.get('/monitoring/audit', { params }),

  // Templates
  getTemplates: () => api.get('/monitoring/templates'),
  applyTemplate: (id) => api.post(`/monitoring/templates/${id}/apply`),

  // Engine
  evaluateAll: () => api.post('/monitoring/engine/evaluate-all'),
  detectAnomalies: () => api.post('/monitoring/engine/detect-anomalies'),
};