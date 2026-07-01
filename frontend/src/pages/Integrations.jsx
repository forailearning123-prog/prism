import React, { useState, useEffect } from 'react';
import {
  integrationService,
  syncService,
  templateService,
  monitoringService,
  analyticsService,
  governanceService,
} from '../services/integrations';

/**
 * Integrations Page
 * Main dashboard for managing enterprise integrations
 */
export default function Integrations() {
  const [integrations, setIntegrations] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('integrations');
  const [selectedIntegration, setSelectedIntegration] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);

  // Form states
  const [createForm, setCreateForm] = useState({
    name: '',
    description: '',
    source_connector: '',
    destination_connector: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [integrationsData, templatesData, alertsData] = await Promise.all([
        integrationService.getIntegrations(),
        templateService.getTemplates(),
        monitoringService.getAlerts(),
      ]);
      setIntegrations(integrationsData.integrations || []);
      setTemplates(templatesData.templates || []);
      setAlerts(alertsData.alerts || []);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateIntegration = async (e) => {
    e.preventDefault();
    try {
      await integrationService.createIntegration(createForm);
      setShowCreateModal(false);
      setCreateForm({
        name: '',
        description: '',
        source_connector: '',
        destination_connector: '',
      });
      loadData();
    } catch (error) {
      console.error('Failed to create integration:', error);
    }
  };

  const handleSync = async (integrationId) => {
    try {
      await syncService.triggerSync(integrationId);
      alert('Sync triggered successfully');
      loadData();
    } catch (error) {
      console.error('Failed to trigger sync:', error);
    }
  };

  const handleDelete = async (integrationId) => {
    if (!confirm('Are you sure you want to delete this integration?')) return;
    try {
      await integrationService.deleteIntegration(integrationId);
      loadData();
    } catch (error) {
      console.error('Failed to delete integration:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-gray-600">Loading integrations...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Integration Hub</h1>
          <p className="text-gray-600 mt-1">
            Manage your enterprise integrations, connectors, and data flows
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowTemplateModal(true)}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
          >
            Browse Templates
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            + New Integration
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="text-sm text-gray-600">Active Integrations</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">
            {integrations.filter((i) => i.status === 'active').length}
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="text-sm text-gray-600">Total Integrations</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">{integrations.length}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="text-sm text-gray-600">Active Alerts</div>
          <div className="text-3xl font-bold text-red-600 mt-2">
            {alerts.filter((a) => a.status === 'active').length}
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="text-sm text-gray-600">Available Templates</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">{templates.length}</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-4">
          {['integrations', 'templates', 'alerts', 'monitoring'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 border-b-2 transition ${
                activeTab === tab
                  ? 'border-blue-600 text-blue-600 font-medium'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'integrations' && (
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">Your Integrations</h2>
            {integrations.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500 mb-4">No integrations yet</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Create Your First Integration
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {integrations.map((integration) => (
                  <div
                    key={integration.id}
                    className="border rounded-lg p-4 hover:shadow-md transition"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <h3 className="font-semibold text-lg">{integration.name}</h3>
                          <span
                            className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(
                              integration.status
                            )}`}
                          >
                            {integration.status}
                          </span>
                        </div>
                        <p className="text-gray-600 text-sm mt-1">{integration.description}</p>
                        <div className="flex gap-4 mt-3 text-sm text-gray-600">
                          <span>
                            Source: <span className="font-medium">{integration.source_connector}</span>
                          </span>
                          <span>
                            Destination: <span className="font-medium">{integration.destination_connector}</span>
                          </span>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleSync(integration.id)}
                          className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                        >
                          Sync
                        </button>
                        <button
                          onClick={() => setSelectedIntegration(integration)}
                          className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                        >
                          View
                        </button>
                        <button
                          onClick={() => handleDelete(integration.id)}
                          className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'templates' && (
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">Integration Templates</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {templates.map((template) => (
                <div
                  key={template.id}
                  className="border rounded-lg p-4 hover:shadow-md transition cursor-pointer"
                  onClick={() => {
                    setSelectedIntegration(template);
                    setShowTemplateModal(true);
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold">{template.name}</h3>
                      <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                      <div className="flex gap-2 mt-3">
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                          {template.category}
                        </span>
                        <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">
                          {template.metadata?.difficulty}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'alerts' && (
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">Active Alerts</h2>
            {alerts.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No active alerts</p>
            ) : (
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <div
                    key={alert.alert_id}
                    className={`border rounded-lg p-4 ${getSeverityColor(alert.severity)}`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold">{alert.title}</h3>
                        <p className="text-sm mt-1">{alert.description}</p>
                        <div className="text-xs mt-2 opacity-75">
                          Integration #{alert.integration_id} • {alert.source}
                        </div>
                      </div>
                      <span className="text-xs px-2 py-1 bg-white bg-opacity-50 rounded">
                        {alert.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'monitoring' && (
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">System Monitoring</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-medium mb-3">Health Status</h3>
                <div className="space-y-2">
                  {integrations.map((integration) => (
                    <div key={integration.id} className="flex justify-between items-center">
                      <span className="text-sm">{integration.name}</span>
                      <span className="text-sm text-gray-600">
                        {integration.status === 'active' ? '✓ Healthy' : '○ Unknown'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="font-medium mb-3">Quick Stats</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Executions</span>
                    <span className="font-medium">1,234</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Success Rate</span>
                    <span className="font-medium text-green-600">98.5%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Avg Latency</span>
                    <span className="font-medium">245ms</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Integration Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold">Create New Integration</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleCreateIntegration} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <input
                  type="text"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  rows="3"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Source Connector</label>
                  <select
                    value={createForm.source_connector}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, source_connector: e.target.value })
                    }
                    className="w-full px-3 py-2 border rounded-lg"
                    required
                  >
                    <option value="">Select source</option>
                    <option value="salesforce">Salesforce</option>
                    <option value="workday">Workday</option>
                    <option value="sap">SAP</option>
                    <option value="jira">Jira</option>
                    <option value="rest_api">REST API</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Destination Connector</label>
                  <select
                    value={createForm.destination_connector}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, destination_connector: e.target.value })
                    }
                    className="w-full px-3 py-2 border rounded-lg"
                    required
                  >
                    <option value="">Select destination</option>
                    <option value="snowflake">Snowflake</option>
                    <option value="bigquery">BigQuery</option>
                    <option value="redshift">Redshift</option>
                    <option value="postgresql">PostgreSQL</option>
                    <option value="rest_api">REST API</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Create Integration
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Template Modal */}
      {showTemplateModal && selectedIntegration && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold">{selectedIntegration.name}</h2>
              <button
                onClick={() => {
                  setShowTemplateModal(false);
                  setSelectedIntegration(null);
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <p className="text-gray-600 mb-4">{selectedIntegration.description}</p>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Category</h3>
                <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded">
                  {selectedIntegration.category}
                </span>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Source</h3>
                <p className="text-sm text-gray-600">{selectedIntegration.source_connector}</p>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Destination</h3>
                <p className="text-sm text-gray-600">{selectedIntegration.destination_connector}</p>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Metadata</h3>
                <div className="text-sm text-gray-600 space-y-1">
                  <p>Difficulty: {selectedIntegration.metadata?.difficulty}</p>
                  <p>Setup Time: {selectedIntegration.metadata?.estimated_setup_time}</p>
                  <p>Popularity: {selectedIntegration.metadata?.popularity}/100</p>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-6">
              <button
                onClick={() => {
                  setShowTemplateModal(false);
                  setSelectedIntegration(null);
                }}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Close
              </button>
              <button
                onClick={() => {
                  setShowTemplateModal(false);
                  setShowCreateModal(true);
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Use This Template
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}