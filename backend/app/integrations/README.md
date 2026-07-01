# Enterprise Integration Hub

A comprehensive, production-ready integration framework for building, managing, and monitoring enterprise data integrations.

## Architecture

The Integration Hub is organized into the following modules:

### Core Components

- **Connectors** (`connectors/`) - Pluggable connector framework with authentication handlers
- **Engine** (`engine/`) - Integration orchestration and flow execution
- **Transformations** (`transformations/`) - Data transformation and field mapping
- **Sync** (`sync/`) - Synchronization services with incremental sync and retry logic
- **Events** (`events/`) - Event-driven architecture with webhook support
- **Monitoring** (`monitoring/`) - Health checks, metrics, and alerting
- **Templates** (`templates/`) - Pre-built integration templates and marketplace
- **Governance** (`governance/`) - Versioning, approval workflows, audit logging, and analytics

### Directory Structure

```
backend/app/integrations/
├── __init__.py              # Main module exports
├── models.py                # Data models and schemas
├── schemas.py               # Pydantic schemas for validation
├── exceptions.py            # Custom exceptions
├── router.py                # REST API endpoints
│
├── connectors/              # Connector framework
│   ├── __init__.py
│   ├── base.py              # BaseConnector abstract class
│   ├── registry.py          # ConnectorRegistry for managing connectors
│   ├── auth/                # Authentication handlers
│   │   ├── __init__.py
│   │   ├── base.py          # BaseAuthHandler
│   │   ├── api_key.py       # API Key authentication
│   │   ├── bearer.py        # Bearer token authentication
│   │   ├── basic.py         # Basic authentication
│   │   └── oauth.py         # OAuth2 authentication
│   └── custom/              # Built-in connectors
│       ├── __init__.py
│       ├── rest_api.py      # REST API connector
│       ├── graphql.py       # GraphQL connector
│       └── webhook.py       # Webhook connector
│
├── secrets/                 # Secrets management
│   ├── __init__.py
│   ├── encryption.py        # Encryption utilities
│   └── manager.py           # Secrets manager
│
├── engine/                  # Integration engine
│   ├── __init__.py
│   ├── orchestrator.py      # IntegrationOrchestrator
│   ├── flow_executor.py     # FlowExecutor for running integrations
│   └── conflict_resolver.py # ConflictResolver for data conflicts
│
├── transformations/         # Data transformations
│   ├── __init__.py
│   ├── engine.py            # TransformationEngine
│   ├── field_mapper.py      # Field mapping utilities
│   ├── lookup_tables.py     # Lookup table management
│   └── validators.py        # Validation engine
│
├── sync/                    # Synchronization
│   ├── __init__.py
│   ├── service.py           # SyncService
│   ├── scheduler.py         # SyncScheduler
│   ├── incremental.py       # IncrementalSync
│   └── retry_handler.py     # RetryHandler with strategies
│
├── events/                  # Event processing
│   ├── __init__.py
│   ├── engine.py            # EventEngine
│   ├── router.py            # EventRouter
│   └── webhooks.py          # WebhookHandler
│
├── monitoring/              # Monitoring and alerting
│   ├── __init__.py
│   ├── health.py            # HealthMonitor
│   ├── metrics.py           # MetricsCollector
│   └── alerts.py            # AlertManager
│
├── templates/               # Integration templates
│   ├── __init__.py
│   ├── catalog.py           # TemplateCatalog
│   └── manager.py           # TemplateManager
│
└── governance/              # Governance and compliance
    ├── __init__.py
    ├── versioning.py        # VersionManager
    ├── approval.py          # ApprovalWorkflow
    ├── audit.py             # AuditLogger
    └── analytics.py         # IntegrationAnalytics
```

## Features

### 1. Connector Framework

**Pluggable Architecture**: Register custom connectors with the `@registry.register()` decorator.

**Built-in Connectors**:
- REST API Connector - Connect to any REST API
- GraphQL Connector - Query GraphQL endpoints
- Webhook Connector - Receive and process webhooks

**Authentication Support**:
- API Key authentication
- Bearer token authentication
- Basic authentication
- OAuth2 authentication

**Example**:
```python
from app.integrations import ConnectorRegistry

registry = ConnectorRegistry()

@registry.register("my_connector")
class MyConnector(BaseConnector):
    async def connect(self):
        # Implementation
        pass
    
    async def read(self, query=None):
        # Implementation
        pass
    
    async def write(self, data):
        # Implementation
        pass
```

### 2. Data Transformation Engine

**Transformation Types**:
- Field mapping
- Lookup tables
- Data normalization
- Type conversion
- Validation rules
- Custom transformations

**Example**:
```python
from app.integrations import TransformationEngine

engine = TransformationEngine()

transformation = {
    "transformation_type": "field_mapping",
    "transformation_config": {
        "source_field": "first_name",
        "dest_field": "firstName"
    }
}

result = await engine.apply(record, transformation)
```

### 3. Synchronization Service

**Features**:
- Full and incremental sync
- Scheduled sync jobs
- Retry logic with exponential backoff
- Dead letter queue for failed records
- Conflict detection and resolution

**Sync Strategies**:
- Full refresh
- Incremental sync with cursors
- Change data capture (CDC)

**Example**:
```python
from app.integrations import SyncService

service = SyncService()

# Create sync job
job = await service.create_sync_job(flow_id=1, job_type="manual")

# Start sync
await service.start_sync_job(job["id"])

# Monitor progress
job = service.get_job(job["id"])
print(f"Status: {job['status']}, Progress: {job['progress']}%")
```

### 4. Event Processing

**Event-Driven Architecture**:
- Register event handlers
- Emit and route events
- Webhook support for external integrations
- Async event processing

**Example**:
```python
from app.integrations import EventEngine

engine = EventEngine()

@engine.register_handler("user.created")
async def handle_user_created(event):
    # Process event
    print(f"User created: {event.payload}")
    return True

# Emit event
event = await engine.emit("user.created", "source", {"user_id": 123})
```

### 5. Monitoring & Alerting

**Health Monitoring**:
- Configurable health checks
- Availability statistics
- Health history tracking

**Metrics Collection**:
- Record custom metrics
- Aggregated statistics
- Performance trends

**Alerting**:
- Severity levels (critical, high, medium, low)
- Alert acknowledgment
- Alert history

**Example**:
```python
from app.integrations import HealthMonitor, MetricsCollector, AlertManager

# Health monitoring
monitor = HealthMonitor()
result = await monitor.check_health(integration_id, health_check_func)

# Metrics
collector = MetricsCollector()
collector.record_metric(integration_id, "latency", 150.0)

# Alerts
alert_manager = AlertManager()
alert = alert_manager.create_alert(
    integration_id=1,
    severity="critical",
    title="Connection Failed",
    description="Unable to connect to Salesforce"
)
```

### 6. Template Marketplace

**Pre-built Templates**:
- Salesforce to Data Warehouse
- Workday to PostgreSQL
- SAP to BigQuery
- Jira to Slack
- And many more...

**Features**:
- Browse templates by category
- Clone templates to create custom integrations
- Template metadata (difficulty, setup time, popularity)

**Example**:
```python
from app.integrations import TemplateCatalog, TemplateManager

catalog = TemplateCatalog()
template = catalog.get_template("salesforce_to_data_warehouse")

manager = TemplateManager()
cloned = manager.clone_template(
    template_id="salesforce_to_data_warehouse",
    name="My Custom Integration"
)
```

### 7. Governance & Compliance

**Version Management**:
- Automatic versioning (semantic versioning)
- Version history
- Rollback to previous versions
- Version comparison

**Approval Workflows**:
- Multi-level approvals
- Approval notifications
- Workflow tracking

**Audit Logging**:
- Immutable audit trail
- Action tracking
- Search and filter
- Export capabilities

**Analytics**:
- Execution statistics
- Performance trends
- Failure analysis
- Executive summary

**Example**:
```python
from app.integrations import VersionManager, ApprovalWorkflow, AuditLogger

# Versioning
version_manager = VersionManager()
version = version_manager.create_version(
    integration_id=1,
    config={"mappings": [...]},
    created_by=1,
    change_description="Added new field mapping"
)

# Approval workflow
approval = ApprovalWorkflow()
workflow = approval.create_workflow(
    integration_id=1,
    change_type="config_update",
    change_description="Update field mappings",
    required_approvers=[1, 2, 3]
)

# Audit logging
audit = AuditLogger()
audit.log(
    integration_id=1,
    action="update",
    user_id=1,
    description="Updated integration configuration"
)
```

## REST API Endpoints

### Integration Management
- `POST /integrations/` - Create integration
- `GET /integrations/` - List integrations
- `GET /integrations/{id}` - Get integration
- `PUT /integrations/{id}` - Update integration
- `DELETE /integrations/{id}` - Delete integration

### Connection Testing
- `POST /integrations/test-connection` - Test connector connection
- `GET /integrations/{id}/health` - Get integration health

### Synchronization
- `POST /integrations/{id}/sync` - Trigger sync
- `GET /integrations/{id}/sync-jobs` - List sync jobs
- `GET /integrations/sync-jobs/{job_id}` - Get sync job details
- `POST /integrations/sync-jobs/{job_id}/cancel` - Cancel sync job
- `POST /integrations/sync-jobs/{job_id}/retry` - Retry failed job

### Templates
- `GET /integrations/templates` - List templates
- `GET /integrations/templates/{id}` - Get template
- `POST /integrations/templates/{id}/clone` - Clone template
- `GET /integrations/templates/categories` - Get categories

### Monitoring
- `GET /integrations/{id}/metrics` - Get metrics
- `GET /integrations/{id}/health-history` - Get health history
- `GET /integrations/alerts` - List alerts

### Analytics
- `GET /integrations/{id}/analytics` - Get analytics
- `GET /integrations/analytics/executive-summary` - Executive summary
- `GET /integrations/analytics/failure-analysis` - Failure analysis

### Governance
- `GET /integrations/{id}/versions` - List versions
- `POST /integrations/{id}/versions/{version_id}/rollback` - Rollback version
- `GET /integrations/{id}/audit-log` - Get audit log

### Statistics
- `GET /integrations/statistics/overview` - Overview statistics

## Testing

Run the test suite:

```bash
# Run all tests
pytest backend/tests/test_integrations.py -v

# Run specific test class
pytest backend/tests/test_integrations.py::TestSyncService -v

# Run with coverage
pytest backend/tests/test_integrations.py --cov=app.integrations
```

## Configuration

### Environment Variables

```env
# Integration Hub Configuration
INTEGRATION_MAX_RETRIES=3
INTEGRATION_RETRY_DELAY=1.0
INTEGRATION_TIMEOUT=300
INTEGRATION_BATCH_SIZE=1000

# Secrets Management
SECRETS_ENCRYPTION_KEY=your-encryption-key
SECRETS_PROVIDER=local  # or aws, azure, gcp

# Monitoring
HEALTH_CHECK_INTERVAL=60
METRICS_RETENTION_DAYS=30
ALERT_NOTIFICATION_ENABLED=true

# Event Processing
EVENT_QUEUE_SIZE=10000
EVENT_PROCESSING_TIMEOUT=30
WEBHOOK_TIMEOUT=10
```

## Usage Examples

### Creating an Integration

```python
from app.integrations import IntegrationOrchestrator

orchestrator = IntegrationOrchestrator()

integration = await orchestrator.create_integration({
    "name": "Salesforce to PostgreSQL",
    "description": "Sync accounts from Salesforce to PostgreSQL",
    "source_connector": "salesforce",
    "destination_connector": "postgresql",
    "source_config": {
        "instance_url": "https://myinstance.salesforce.com",
        "api_version": "v58.0"
    },
    "dest_config": {
        "host": "localhost",
        "port": 5432,
        "database": "mydb"
    },
    "mappings": [
        {
            "source_field": "Name",
            "dest_field": "name",
            "type": "string"
        },
        {
            "source_field": "AnnualRevenue",
            "dest_field": "annual_revenue",
            "type": "decimal"
        }
    ],
    "transformations": [
        {
            "transformation_type": "normalization",
            "transformation_config": {
                "field": "name",
                "type": "trim"
            }
        }
    ],
    "sync_config": {
        "schedule": "0 */6 * * *",  # Every 6 hours
        "sync_type": "incremental",
        "cursor_field": "LastModifiedDate"
    }
})
```

### Running a Sync Job

```python
from app.integrations import SyncService

sync_service = SyncService()

# Create and start sync job
job = await sync_service.create_sync_job(
    flow_id=integration_id,
    job_type="manual",
    triggered_by=user_id
)

await sync_service.start_sync_job(job["id"])

# Monitor progress
while True:
    job = sync_service.get_job(job["id"])
    if job["status"] in ["success", "failed", "cancelled"]:
        break
    print(f"Progress: {job['progress']}%")
    await asyncio.sleep(1)

print(f"Sync completed: {job['status']}")
print(f"Records processed: {job['records_processed']}")
```

### Handling Events

```python
from app.integrations import EventEngine

event_engine = EventEngine()

# Register handler
@event_engine.register_handler("integration.sync_completed")
async def on_sync_completed(event):
    integration_id = event.payload["integration_id"]
    records = event.payload["records_processed"]
    
    # Send notification
    await send_notification(
        f"Sync completed for integration {integration_id}: {records} records"
    )
    
    # Update metrics
    metrics_collector.record_metric(integration_id, "sync_completed", records)
    
    return True

# Emit event
await event_engine.emit(
    event_type="integration.sync_completed",
    source="sync_service",
    payload={
        "integration_id": 1,
        "records_processed": 1000,
        "duration_ms": 5000
    }
)
```

## Best Practices

1. **Connector Development**
   - Always inherit from `BaseConnector`
   - Implement all required methods
   - Handle errors gracefully
   - Use appropriate authentication handlers

2. **Data Transformations**
   - Keep transformations simple and focused
   - Use lookup tables for static mappings
   - Validate data before transformations
   - Log transformation errors

3. **Synchronization**
   - Use incremental sync for large datasets
   - Implement proper error handling
   - Configure appropriate batch sizes
   - Monitor sync job performance

4. **Monitoring**
   - Set up health checks for all integrations
   - Configure alerts for critical failures
   - Track key metrics (latency, throughput, error rate)
   - Review metrics regularly

5. **Governance**
   - Use version control for all changes
   - Implement approval workflows for production changes
   - Maintain audit logs for compliance
   - Review analytics regularly

## Performance Considerations

- **Batch Processing**: Use batch processing for large datasets
- **Connection Pooling**: Reuse connections where possible
- **Caching**: Cache frequently accessed data
- **Async Operations**: Use async/await for I/O operations
- **Resource Management**: Clean up resources properly

## Security

- **Secrets Management**: Never hardcode credentials
- **Encryption**: Encrypt sensitive data at rest and in transit
- **Access Control**: Implement proper authentication and authorization
- **Audit Logging**: Log all sensitive operations
- **Input Validation**: Validate all inputs

## Troubleshooting

### Common Issues

1. **Connection Failures**
   - Check connector configuration
   - Verify authentication credentials
   - Test network connectivity
   - Review firewall rules

2. **Sync Job Failures**
   - Check error logs
   - Verify data formats
   - Review transformation rules
   - Check destination capacity

3. **Performance Issues**
   - Review batch sizes
   - Check for bottlenecks
   - Monitor resource usage
   - Optimize transformations

## Contributing

When adding new features:

1. Follow the existing code structure
2. Add comprehensive tests
3. Update documentation
4. Follow PEP 8 style guidelines
5. Add type hints

## License

Proprietary - Prism Platform