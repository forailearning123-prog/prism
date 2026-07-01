import api from './api'

export const forecastingService = {
  // Workspace
  getWorkspaceSummary: () => api.get('/api/v1/forecasting/workspace'),

  // Forecasts CRUD
  listForecasts: (params) => api.get('/api/v1/forecasting/', { params }),
  createForecast: (data) => api.post('/api/v1/forecasting/', data),
  getForecast: (id) => api.get(`/api/v1/forecasting/${id}`),
  updateForecast: (id, data) => api.put(`/api/v1/forecasting/${id}`, data),
  deleteForecast: (id) => api.delete(`/api/v1/forecasting/${id}`),
  duplicateForecast: (id) => api.post(`/api/v1/forecasting/${id}/duplicate`),
  generateForecast: (id) => api.post(`/api/v1/forecasting/${id}/generate`),
  getForecastResults: (id) => api.get(`/api/v1/forecasting/${id}/results`),
  getLatestResult: (id) => api.get(`/api/v1/forecasting/${id}/results/latest`),

  // Scenarios
  listScenarios: (forecastId) => api.get(`/api/v1/forecasting/${forecastId}/scenarios`),
  createScenario: (forecastId, data) => api.post(`/api/v1/forecasting/${forecastId}/scenarios`, data),
  getScenario: (forecastId, scenarioId) => api.get(`/api/v1/forecasting/${forecastId}/scenarios/${scenarioId}`),
  updateScenario: (forecastId, scenarioId, data) => api.put(`/api/v1/forecasting/${forecastId}/scenarios/${scenarioId}`, data),
  deleteScenario: (forecastId, scenarioId) => api.delete(`/api/v1/forecasting/${forecastId}/scenarios/${scenarioId}`),
  runScenario: (forecastId, scenarioId) => api.post(`/api/v1/forecasting/${forecastId}/scenarios/${scenarioId}/run`),

  // What-If
  runWhatIf: (forecastId, variables) => api.post(`/api/v1/forecasting/${forecastId}/what-if`, { variables }),

  // Drivers
  getDriverAnalysis: (forecastId) => api.get(`/api/v1/forecasting/${forecastId}/drivers`),
  generateDriverAnalysis: (forecastId) => api.post(`/api/v1/forecasting/${forecastId}/drivers/generate`),

  // Risks & Opportunities
  listRisks: (params) => api.get('/api/v1/forecasting/risks', { params }),
  createRisk: (data) => api.post('/api/v1/forecasting/risks', data),
  listOpportunities: (params) => api.get('/api/v1/forecasting/opportunities', { params }),
  generateOpportunities: () => api.post('/api/v1/forecasting/opportunities/generate'),

  // Versions & Alerts
  listVersions: (forecastId) => api.get(`/api/v1/forecasting/${forecastId}/versions`),
  listAlerts: (forecastId) => api.get(`/api/v1/forecasting/${forecastId}/alerts`),
  markAlertRead: (forecastId, alertId) => api.post(`/api/v1/forecasting/${forecastId}/alerts/${alertId}/read`),

  // Recommendations
  getRecommendations: (forecastId) => api.get(`/api/v1/forecasting/${forecastId}/recommendations`),
  generateRecommendations: (forecastId) => api.post(`/api/v1/forecasting/${forecastId}/recommendations/generate`),

  // Export & Compare
  exportForecast: (forecastId, format) => api.post(`/api/v1/forecasting/${forecastId}/export`, { export_format: format }),
  compareForecasts: (data) => api.post('/api/v1/forecasting/compare', data),
}
