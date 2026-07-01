/**
 * Integration Hub Service
 * API client for managing integrations, connectors, and sync jobs.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Integration Management
 */
export const integrationService = {
  /**
   * Create a new integration
   */
  async createIntegration(data) {
    const response = await fetch(`${API_BASE_URL}/integrations/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create integration');
    return response.json();
  },

  /**
   * Get all integrations
   */
  async getIntegrations(filters = {}) {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.category) params.append('category', filters.category);
    if (filters.limit) params.append('limit', filters.limit);

    const response = await fetch(`${API_BASE_URL}/integrations/?${params}`);
    if (!response.ok) throw new Error('Failed to fetch integrations');
    return response.json();
  },

  /**
   * Get integration by ID
   */
  async getIntegration(id) {
    const response = await fetch(`${API_BASE_URL}/integrations/${id}`);
    if (!response.ok) throw new Error('Failed to fetch integration');
    return response.json();
  },

  /**
   * Update integration
   */
  async updateIntegration(id, data) {
    const response = await fetch(`${API_BASE_URL}/integrations/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update integration');
    return response.json();
  },

  /**
   * Delete integration
   */
  async deleteIntegration(id) {
    const response = await fetch(`${API_BASE_URL}/integrations/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete integration');
    return response.json();
  },

  /**
   * Test connection
   */
  async testConnection(data) {
    const response = await fetch(`${API_BASE_URL}/integrations/test-connection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to test connection');
    return response.json();
  },

  /**
   * Get integration health
   */
  async getHealth(id) {
    const response = await fetch(`${API_BASE_URL}/integrations/${id}/health`);
    if (!response.ok) throw new Error('Failed to fetch health status');
    return response.json();
  },
};

/**
 * Synchronization
 */
export const syncService = {
  /**
   * Trigger sync
   */
  async triggerSync(integrationId, data = {}) {
    const response = await fetch(`${API_BASE_URL}/integrations/${integrationId}/sync`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        flow_id: integrationId,
        job_type: data.job_type || 'manual',
        sync_type: data.sync_type || 'full_refresh',
      }),
    });
    if (!response.ok) throw new Error('Failed to trigger sync');
    return response.json();
  },

  /**
   * List sync jobs
   */
  async getSyncJobs(integrationId, filters = {}) {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.limit) params.append('limit', filters.limit);

    const response = await fetch(
      `${API_BASE_URL}/integrations/${integrationId}/sync-jobs?${params}`
    );
    if (!response.ok) throw new Error('Failed to fetch sync jobs');
    return response.json();
  },

  /**
   * Get sync job details
   */
  async getSyncJob(jobId) {
    const response = await fetch(`${API_BASE_URL}/integrations/sync-jobs/${jobId}`);
    if (!response.ok) throw new Error('Failed to fetch sync job');
    return response.json();
  },

  /**
   * Cancel sync job
   */
  async cancelSyncJob(jobId) {
    const response = await fetch(`${API_BASE_URL}/integrations/sync-jobs/${jobId}/cancel`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to cancel sync job');
    return response.json();
  },

  /**
   * Retry sync job
   */
  async retrySyncJob(jobId) {
    const response = await fetch(`${API_BASE_URL}/integrations/sync-jobs/${jobId}/retry`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to retry sync job');
    return response.json();
  },
};

/**
 * Templates
 */
export const templateService = {
  /**
   * List templates
   */
  async getTemplates(filters = {}) {
    const params = new URLSearchParams();
    if (filters.category) params.append('category', filters.category);
    if (filters.difficulty) params.append('difficulty', filters.difficulty);
    if (filters.limit) params.append('limit', filters.limit);

    const response = await fetch(`${API_BASE_URL}/integrations/templates?${params}`);
    if (!response.ok) throw new Error('Failed to fetch templates');
    return response.json();
  },

  /**
   * Get template by ID
   */
  async getTemplate(id) {
    const response = await fetch(`${API_BASE_URL}/integrations/templates/${id}`);
    if (!response.ok) throw new Error('Failed to fetch template');
    return response.json();
  },

  /**
   * Clone template
   */
  async cloneTemplate(templateId, data) {
    const response = await fetch(
      `${API_BASE_URL}/integrations/templates/${templateId}/clone`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    if (!response.ok) throw new Error('Failed to clone template');
    return response.json();
  },

  /**
   * Get template categories
   */
  async getCategories() {
    const response = await fetch(`${API_BASE_URL}/integrations/templates/categories`);
    if (!response.ok) throw new Error('Failed to fetch categories');
    return response.json();
  },
};

/**
 * Monitoring
 */
export const monitoringService = {
  /**
   * Get integration metrics
   */
  async getMetrics(integrationId) {
    const response = await fetch(`${API_BASE_URL}/integrations/${integrationId}/metrics`);
    if (!response.ok) throw new Error('Failed to fetch metrics');
    return response.json();
  },

  /**
   * Get health history
   */
  async getHealthHistory(integrationId, limit = 100) {
    const response = await fetch(
      `${API_BASE_URL}/integrations/${integrationId}/health-history?limit=${limit}`
    );
    if (!response.ok) throw new Error('Failed to fetch health history');
    return response.json();
  },

  /**
   * List alerts
   */
  async getAlerts(filters = {}) {
    const params = new URLSearchParams();
    if (filters.integrationId) params.append('integration_id', filters.integrationId);
    if (filters.severity) params.append('severity', filters.severity);
    if (filters.status) params.append('status', filters.status);
    if (filters.limit) params.append('limit', filters.limit);

    const response = await fetch(`${API_BASE_URL}/integrations/alerts?${params}`);
    if (!response.ok) throw new Error('Failed to fetch alerts');
    return response.json();
  },
};

/**
 * Analytics
 */
export const analyticsService = {
  /**
   * Get integration analytics
   */
  async getIntegrationAnalytics(integrationId) {
    const response = await fetch(`${API_BASE_URL}/integrations/${integrationId}/analytics`);
    if (!response.ok) throw new Error('Failed to fetch analytics');
    return response.json();
  },

  /**
   * Get executive summary
   */
  async getExecutiveSummary() {
    const response = await fetch(`${API_BASE_URL}/integrations/analytics/executive-summary`);
    if (!response.ok) throw new Error('Failed to fetch executive summary');
    return response.json();
  },

  /**
   * Get failure analysis
   */
  async getFailureAnalysis(integrationId = null) {
    const params = integrationId ? `?integration_id=${integrationId}` : '';
    const response = await fetch(
      `${API_BASE_URL}/integrations/analytics/failure-analysis${params}`
    );
    if (!response.ok) throw new Error('Failed to fetch failure analysis');
    return response.json();
  },
};

/**
 * Governance
 */
export const governanceService = {
  /**
   * List versions
   */
  async getVersions(integrationId, limit = 100) {
    const response = await fetch(
      `${API_BASE_URL}/integrations/${integrationId}/versions?limit=${limit}`
    );
    if (!response.ok) throw new Error('Failed to fetch versions');
    return response.json();
  },

  /**
   * Rollback version
   */
  async rollbackVersion(integrationId, versionId) {
    const response = await fetch(
      `${API_BASE_URL}/integrations/${integrationId}/versions/${versionId}/rollback`,
      { method: 'POST' }
    );
    if (!response.ok) throw new Error('Failed to rollback version');
    return response.json();
  },

  /**
   * Get audit log
   */
  async getAuditLog(integrationId, filters = {}) {
    const params = new URLSearchParams();
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.startTime) params.append('start_time', filters.startTime);
    if (filters.endTime) params.append('end_time', filters.endTime);

    const response = await fetch(
      `${API_BASE_URL}/integrations/${integrationId}/audit-log?${params}`
    );
    if (!response.ok) throw new Error('Failed to fetch audit log');
    return response.json();
  },
};

/**
 * Statistics
 */
export const statisticsService = {
  /**
   * Get overview statistics
   */
  async getOverview() {
    const response = await fetch(`${API_BASE_URL}/integrations/statistics/overview`);
    if (!response.ok) throw new Error('Failed to fetch statistics');
    return response.json();
  },
};