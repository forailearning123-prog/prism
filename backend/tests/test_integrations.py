"""
Integration Hub Tests
Comprehensive test suite for the Enterprise Integration Hub.
"""

import pytest
import asyncio
from datetime import datetime, timezone

from app.integrations import (
    IntegrationOrchestrator,
    ConnectorRegistry,
    SyncService,
    EventEngine,
    HealthMonitor,
    MetricsCollector,
    AlertManager,
    TemplateCatalog,
    TemplateManager,
    VersionManager,
    ApprovalWorkflow,
    AuditLogger,
    IntegrationAnalytics,
    TransformationEngine,
    FieldMapper,
    LookupTableManager,
    ValidationEngine,
    ConflictResolver,
    ConflictResolutionStrategy,
    IncrementalSync,
    RetryHandler,
    RetryStrategy,
    DeadLetterQueue
)


class TestConnectorRegistry:
    """Tests for connector registry."""
    
    def test_register_connector(self):
        """Test registering a connector."""
        registry = ConnectorRegistry()
        
        @registry.register("test_connector")
        class TestConnector:
            pass
        
        assert "test_connector" in registry.connectors
    
    def test_create_instance(self):
        """Test creating connector instance."""
        registry = ConnectorRegistry()
        
        @registry.register("test_connector")
        class TestConnector:
            def __init__(self, config, auth_config):
                self.config = config
                self.auth_config = auth_config
        
        instance = registry.create_instance(
            name="test_connector",
            config={"url": "http://test.com"},
            auth_config={"type": "api_key"}
        )
        
        assert instance is not None
        assert instance.config["url"] == "http://test.com"


class TestTransformationEngine:
    """Tests for transformation engine."""
    
    def test_field_mapping(self):
        """Test field mapping transformation."""
        engine = TransformationEngine()
        record = {"source_field": "value"}
        transformation = {
            "transformation_type": "field_mapping",
            "transformation_config": {
                "source_field": "source_field",
                "dest_field": "dest_field"
            }
        }
        
        result = asyncio.run(engine.apply(record, transformation))
        assert result["dest_field"] == "value"
    
    def test_lookup_transformation(self):
        """Test lookup transformation."""
        engine = TransformationEngine()
        record = {"status": "active"}
        transformation = {
            "transformation_type": "lookup",
            "transformation_config": {
                "source_field": "status",
                "dest_field": "status_label",
                "lookup_table": {"active": "Active", "inactive": "Inactive"}
            }
        }
        
        result = asyncio.run(engine.apply(record, transformation))
        assert result["status_label"] == "Active"
    
    def test_normalization(self):
        """Test normalization transformation."""
        engine = TransformationEngine()
        record = {"name": "  JOHN DOE  "}
        transformation = {
            "transformation_type": "normalization",
            "transformation_config": {
                "field": "name",
                "type": "lowercase"
            }
        }
        
        result = asyncio.run(engine.apply(record, transformation))
        assert result["name"] == "john doe"


class TestFieldMapper:
    """Tests for field mapper utilities."""
    
    def test_map_fields(self):
        """Test field mapping."""
        record = {"first_name": "John", "last_name": "Doe"}
        mapping = {"first_name": "firstName", "last_name": "lastName"}
        
        result = FieldMapper.map_fields(record, mapping)
        assert result["firstName"] == "John"
        assert result["lastName"] == "Doe"
    
    def test_rename_field(self):
        """Test field renaming."""
        record = {"old_name": "value"}
        result = FieldMapper.rename_field(record, "old_name", "new_name")
        assert "new_name" in result
        assert "old_name" not in result
    
    def test_flatten_record(self):
        """Test record flattening."""
        record = {"user": {"name": "John", "age": 30}}
        result = FieldMapper.flatten_record(record)
        assert "user_name" in result
        assert result["user_name"] == "John"


class TestLookupTableManager:
    """Tests for lookup table manager."""
    
    def test_register_and_lookup(self):
        """Test registering and looking up tables."""
        manager = LookupTableManager()
        manager.register_table("test", {"key1": "value1", "key2": "value2"})
        
        assert manager.lookup("test", "key1") == "value1"
        assert manager.lookup("test", "key3", "default") == "default"
    
    def test_reverse_lookup(self):
        """Test reverse lookup."""
        manager = LookupTableManager()
        manager.register_table("test", {"key1": "value1"})
        
        assert manager.reverse_lookup("test", "value1") == "key1"


class TestValidationEngine:
    """Tests for validation engine."""
    
    def test_validate_required(self):
        """Test required field validation."""
        engine = ValidationEngine()
        engine.register_rules("test", [
            {"field": "name", "type": "required"}
        ])
        
        is_valid, errors, _ = engine.validate({"name": "John"}, "test")
        assert is_valid
        
        is_valid, errors, _ = engine.validate({}, "test")
        assert not is_valid
    
    def test_validate_pattern(self):
        """Test pattern validation."""
        engine = ValidationEngine()
        engine.register_rules("test", [
            {"field": "email", "type": "pattern", "value": r"^[a-z]+@[a-z]+\.[a-z]+$"}
        ])
        
        is_valid, errors, _ = engine.validate({"email": "test@example.com"}, "test")
        assert is_valid
        
        is_valid, errors, _ = engine.validate({"email": "invalid"}, "test")
        assert not is_valid


class TestConflictResolver:
    """Tests for conflict resolver."""
    
    def test_detect_conflicts(self):
        """Test conflict detection."""
        resolver = ConflictResolver()
        source = {"id": "1", "name": "John", "updated_at": "2024-01-02"}
        dest = {"id": "1", "name": "Jane", "updated_at": "2024-01-01"}
        
        conflicts = resolver.detect_conflicts({"1": source}, {"1": dest})
        assert len(conflicts) > 0
    
    def test_resolve_source_wins(self):
        """Test source wins strategy."""
        resolver = ConflictResolver(ConflictResolutionStrategy.SOURCE_WINS)
        source = {"id": "1", "name": "John"}
        dest = {"id": "1", "name": "Jane"}
        
        source_changes, dest_changes = resolver.resolve(
            {"1": source}, {"1": dest}, []
        )
        
        assert len(dest_changes) > 0
        assert dest_changes[0]["name"] == "John"


class TestIncrementalSync:
    """Tests for incremental sync."""
    
    def test_cursor_management(self):
        """Test cursor save and retrieve."""
        sync = IncrementalSync()
        sync.save_cursor(1, "source1", "2024-01-01T00:00:00")
        
        cursor = sync.get_cursor(1, "source1")
        assert cursor == "2024-01-01T00:00:00"
    
    def test_build_incremental_query(self):
        """Test building incremental query."""
        sync = IncrementalSync()
        query = sync.build_incremental_query(
            {"limit": 100},
            "updated_at",
            "2024-01-01T00:00:00"
        )
        
        assert "updated_at__gt" in query
        assert query["updated_at__gt"] == "2024-01-01T00:00:00"


class TestRetryHandler:
    """Tests for retry handler."""
    
    def test_execute_with_retry_success(self):
        """Test successful execution with retry."""
        async def test_func():
            return "success"
        
        handler = RetryHandler(max_retries=3)
        result = asyncio.run(handler.execute_with_retry("test_op", test_func))
        assert result == "success"
    
    def test_execute_with_retry_failure(self):
        """Test retry on failure."""
        call_count = 0
        
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"
        
        handler = RetryHandler(max_retries=3, strategy=RetryStrategy.FIXED, base_delay=0.1)
        result = asyncio.run(handler.execute_with_retry("test_op", failing_func))
        assert result == "success"
        assert call_count == 3


class TestDeadLetterQueue:
    """Tests for dead letter queue."""
    
    def test_add_and_retrieve(self):
        """Test adding and retrieving from DLQ."""
        dlq = DeadLetterQueue()
        entry = dlq.add(1, {"data": "test"}, "Error", "ConnectionError")
        
        retrieved = dlq.get(entry["id"])
        assert retrieved is not None
        assert retrieved["payload"]["data"] == "test"
    
    def test_retry(self):
        """Test retrying DLQ entry."""
        dlq = DeadLetterQueue()
        entry = dlq.add(1, {"data": "test"}, "Error", "ConnectionError")
        
        retry_result = dlq.retry(entry["id"])
        assert retry_result["retry_count"] == 1
        assert retry_result["status"] == "pending"


class TestSyncService:
    """Tests for sync service."""
    
    def test_create_sync_job(self):
        """Test creating sync job."""
        service = SyncService()
        job = asyncio.run(service.create_sync_job(1, "manual"))
        
        assert job["flow_id"] == 1
        assert job["status"] == "pending"
    
    def test_complete_sync_job(self):
        """Test completing sync job."""
        service = SyncService()
        job = asyncio.run(service.create_sync_job(1, "manual"))
        asyncio.run(service.start_sync_job(job["id"]))
        
        completed = asyncio.run(service.complete_sync_job(
            job["id"], "success", 100, 100, 0
        ))
        
        assert completed["status"] == "success"
        assert completed["records_processed"] == 100


class TestEventEngine:
    """Tests for event engine."""
    
    def test_register_handler(self):
        """Test registering event handler."""
        engine = EventEngine()
        
        async def handler(event):
            return True
        
        engine.register_handler("test_event", handler)
        assert "test_event" in engine.handlers
    
    def test_emit_and_process(self):
        """Test emitting and processing events."""
        engine = EventEngine()
        processed = []
        
        async def handler(event):
            processed.append(event)
            return True
        
        engine.register_handler("test_event", handler)
        
        event = asyncio.run(engine.emit_simple("test_event", "test", {"data": "test"}))
        assert event is not None


class TestHealthMonitor:
    """Tests for health monitor."""
    
    def test_record_health_check(self):
        """Test recording health check."""
        monitor = HealthMonitor()
        
        async def check():
            return {"success": True}
        
        result = asyncio.run(monitor.check_health(1, check))
        assert result["status"] == "healthy"
        assert monitor.get_health_status(1) == "healthy"
    
    def test_availability_stats(self):
        """Test availability statistics."""
        monitor = HealthMonitor()
        
        async def check():
            return {"success": True}
        
        asyncio.run(monitor.check_health(1, check))
        stats = monitor.get_availability_stats(1)
        
        assert stats["total_checks"] == 1
        assert stats["availability_percentage"] == 100.0


class TestMetricsCollector:
    """Tests for metrics collector."""
    
    def test_record_and_retrieve(self):
        """Test recording and retrieving metrics."""
        collector = MetricsCollector()
        collector.record_metric(1, "latency", 100.0)
        collector.record_metric(1, "latency", 200.0)
        
        metrics = collector.get_metrics(1, "latency")
        assert len(metrics) == 2
        assert metrics[0]["value"] == 100.0
    
    def test_aggregated_metrics(self):
        """Test aggregated metrics."""
        collector = MetricsCollector()
        collector.record_metric(1, "latency", 100.0)
        collector.record_metric(1, "latency", 200.0)
        
        agg = collector.get_aggregated_metrics(1)
        assert agg["metrics_by_type"]["latency"]["avg"] == 150.0


class TestAlertManager:
    """Tests for alert manager."""
    
    def test_create_alert(self):
        """Test creating alert."""
        manager = AlertManager()
        alert = manager.create_alert(1, "critical", "Test Alert", "Test description")
        
        assert alert.integration_id == 1
        assert alert.severity.value == "critical"
    
    def test_acknowledge_alert(self):
        """Test acknowledging alert."""
        manager = AlertManager()
        alert = manager.create_alert(1, "critical", "Test Alert", "Test description")
        
        updated = manager.acknowledge_alert(alert.alert_id, 1)
        assert updated.status.value == "acknowledged"


class TestTemplateCatalog:
    """Tests for template catalog."""
    
    def test_get_template(self):
        """Test getting template."""
        catalog = TemplateCatalog()
        template = catalog.get_template("salesforce_to_data_warehouse")
        
        assert template is not None
        assert template["name"] == "Salesforce to Data Warehouse"
    
    def test_list_templates(self):
        """Test listing templates."""
        catalog = TemplateCatalog()
        templates = catalog.list_templates()
        
        assert len(templates) > 0
    
    def test_search_templates(self):
        """Test searching templates."""
        catalog = TemplateCatalog()
        results = catalog.search_templates("salesforce")
        
        assert len(results) > 0
        assert "salesforce" in results[0]["name"].lower()


class TestTemplateManager:
    """Tests for template manager."""
    
    def test_clone_template(self):
        """Test cloning template."""
        manager = TemplateManager()
        cloned = manager.clone_template(
            "salesforce_to_data_warehouse",
            "My Custom Integration"
        )
        
        assert cloned["name"] == "My Custom Integration"
        assert cloned["source_template_id"] == "salesforce_to_data_warehouse"
    
    def test_create_instance(self):
        """Test creating instance."""
        manager = TemplateManager()
        instance = manager.create_instance("salesforce_to_data_warehouse", {
            "name": "Test Instance"
        })
        
        assert instance["name"] == "Test Instance"
        assert instance["status"] == "draft"


class TestVersionManager:
    """Tests for version manager."""
    
    def test_create_version(self):
        """Test creating version."""
        manager = VersionManager()
        version = manager.create_version(1, {"mappings": []}, 1, "Initial version")
        
        assert version["integration_id"] == 1
        assert version["version"] == "1.0.0"
    
    def test_version_increment(self):
        """Test version increment."""
        manager = VersionManager()
        manager.create_version(1, {}, 1)
        version2 = manager.create_version(1, {}, 1, "Second version")
        
        assert version2["version"] == "1.0.1"


class TestApprovalWorkflow:
    """Tests for approval workflow."""
    
    def test_create_and_approve(self):
        """Test creating and approving workflow."""
        workflow = ApprovalWorkflow()
        w = workflow.create_workflow(1, "config_update", "Update config", [1, 2])
        
        assert w["status"] == "pending"
        
        approved = workflow.approve(w["id"], 1, "Looks good")
        assert approved["current_approver_index"] == 1
    
    def test_reject_workflow(self):
        """Test rejecting workflow."""
        workflow = ApprovalWorkflow()
        w = workflow.create_workflow(1, "config_update", "Update config", [1])
        
        rejected = workflow.reject(w["id"], 1, "Not approved")
        assert rejected["status"] == "rejected"


class TestAuditLogger:
    """Tests for audit logger."""
    
    def test_log_action(self):
        """Test logging action."""
        logger = AuditLogger()
        log = logger.log(1, "create", 1, "Created integration")
        
        assert log["integration_id"] == 1
        assert log["action"] == "create"
    
    def test_query_logs(self):
        """Test querying logs."""
        logger = AuditLogger()
        logger.log(1, "create", 1, "Created integration")
        logger.log(1, "update", 1, "Updated integration")
        
        logs = logger.list_logs(integration_id=1)
        assert len(logs) == 2


class TestIntegrationAnalytics:
    """Tests for integration analytics."""
    
    def test_record_execution(self):
        """Test recording execution."""
        analytics = IntegrationAnalytics()
        analytics.record_execution(1, {
            "status": "success",
            "records_processed": 100,
            "duration_ms": 500
        })
        
        stats = analytics.get_integration_stats(1)
        assert stats["total_executions"] == 1
        assert stats["success_rate"] == 100.0
    
    def test_failure_analysis(self):
        """Test failure analysis."""
        analytics = IntegrationAnalytics()
        analytics.record_execution(1, {"status": "success"})
        analytics.record_execution(1, {"status": "failed", "error": "Connection error"})
        
        analysis = analytics.get_failure_analysis(1)
        assert analysis["total_failures"] == 1


class TestIntegrationOrchestrator:
    """Tests for integration orchestrator."""
    
    def test_test_connection(self):
        """Test connection testing."""
        orchestrator = IntegrationOrchestrator()
        # This would require a mock connector
        pass
    
    def test_health_check(self):
        """Test health checking."""
        orchestrator = IntegrationOrchestrator()
        # This would require a mock connector
        pass


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])