import api from './api'

export const analystApi = {
  createConversation: (data) => api.post('/api/v1/analyst/conversations', data),
  listConversations: (params) => api.get('/api/v1/analyst/conversations', { params }),
  getConversation: (id) => api.get(`/api/v1/analyst/conversations/${id}`),
  updateConversation: (id, data) => api.patch(`/api/v1/analyst/conversations/${id}`, data),
  deleteConversation: (id) => api.delete(`/api/v1/analyst/conversations/${id}`),

  getMessages: (conversationId) => api.get(`/api/v1/analyst/conversations/${conversationId}/messages`),
  sendQuestion: (conversationId, data) => api.post(`/api/v1/analyst/conversations/${conversationId}/messages`, data),

  saveInsight: (conversationId, data) => api.post(`/api/v1/analyst/conversations/${conversationId}/insights`, data),
  listInsights: () => api.get('/api/v1/analyst/insights'),

  submitFeedback: (messageId, data) => api.post(`/api/v1/analyst/messages/${messageId}/feedback`, data),

  getSuggestedQuestions: (conversationId) => api.get('/api/v1/analyst/suggested-questions', {
    params: conversationId ? { conversation_id: conversationId } : {},
  }),

  generateReport: (data) => api.post('/api/v1/analyst/reports', data),
  listReports: () => api.get('/api/v1/analyst/reports'),
  getReport: (id) => api.get(`/api/v1/analyst/reports/${id}`),

  explainDashboard: (data) => api.post('/api/v1/analyst/explain-dashboard', data),

  streamQuestion: async (conversationId, question, token) => {
    const baseUrl = import.meta.env.VITE_API_URL || ''
    return fetch(`${baseUrl}/api/v1/analyst/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: 'Bearer ' + token } : {}),
      },
      body: JSON.stringify({ question, stream: true }),
    })
  },
}
