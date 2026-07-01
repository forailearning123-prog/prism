"""
Integration Hub Router
REST API endpoints for managing integrations.
"""

from typing import Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel

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
    IntegrationAnalytics
)

router = APIRouter(prefix="/integrations", tags=["integrations"])

# Initialize services
orchestrator = IntegrationOrchestrator()
sync_service = SyncService()
event_engine = EventEngine()
health_monitor = HealthMonitor()
metrics_collector = MetricsCollector()
alert_manager = AlertManager()
template_catalog = TemplateCatalog()
template_manager = TemplateManager()
version_manager = VersionManager()
approval_workflow = ApprovalWorkflow()
audit_logger = AuditLogger()
integration_analytics = IntegrationAnalytics()


# Request/Response Models
class IntegrationCreateRequest(BaseModel):
    name: str
    description: str
    source_connector: str
    destination_connector: str
    source_config: dict[str, Any]
    dest_config: dict[str, Any]
    mappings: list[dict[str, Any]]
    transformations: list[dict[str, Any]] = []
    sync_config: dict[str, Any] = {}


class IntegrationUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    source_config: Optional[dict[str, Any]] = None
    dest_config: Optional[dict[str, Any]] = None
    mappings: Optional[list[dict[str, Any]]] = None
    transformations: Optional[list[dict[str, Any]]] = None
    sync_config: Optional[dict[str, Any]] = None


class ConnectionTestRequest(BaseModel):
    connector_name: str
    config: dict[str, Any]
    auth_config: dict[str, Any]


class SyncJobRequest(BaseModel):
    flow_id: int
    job_type: str = "manual"
    sync_type: str = "full_refresh"


class TemplateCloneRequest(BaseModel):
    template_id: str
    name: str
    description: Optional[str] = None


# Integration Management Endpoints
@router.post("/")
async def create_integration(request: IntegrationCreateRequest):
    """Create a new integration."""
    try:
        integration = {
            "id": 1,  # In production, use database ID
            "name": request.name,
            "description": request.description,
            "source_connector": request.source_connector,
            "destination_connector": request.destination_connector,
            "source_config": request.source_config,
            "dest_config": request.dest_config,
            "mappings": request.mappings,
            "transformations": request.transformations,
            "sync_config": request.sync_config,
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Log audit event
        audit_logger.log(
            integration_id=integration["id"],
            action="create",
            user_id=1,  # In production, get from auth
            description=f"Created integration: {request.name}"
        )
        
        return integration
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def list_integrations(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(100)
):
    """List all integrations."""
    # In production, query from database
    integrations = []
    
    return {
        "integrations": integrations,
        "total": len(integrations),
        "limit": limit
    }


@router.get("/{integration_id}")
async def get_integration(integration_id: int):
    """Get integration by ID."""
    # In production, query from database
    integration = None
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    return integration


@router.put("/{integration_id}")
async def update_integration(integration_id: int, request: IntegrationUpdateRequest):
    """Update an integration."""
    try:
        # In production, update in database
        integration = {
            "id": integration_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Log audit event
        audit_logger.log(
            integration_id=integration_id,
            action="update",
            user_id=1,
            description="Updated integration configuration"
        )
        
        return integration
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{integration_id}")
async def delete_integration(integration_id: int):
    """Delete an integration."""
    try:
        # In production, delete from database
        
        # Log audit event
        audit_logger.log(
            integration_id=integration_id,
            action="delete",
            user_id=1,
            description="Deleted integration"
        )
        
        return {"message": "Integration deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Connection Testing
@router.post("/test-connection")
async def test_connection(request: ConnectionTestRequest):
    """Test a connector connection."""
    try:
        result = await orchestrator.test_connection({
            "connector_name": request.connector_name,
            "connector_config": request.config,
            "auth_config": request.auth_config
        })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{integration_id}/health")
async def get_integration_health(integration_id: int):
    """Get integration health status."""
    try:
        # In production, get from database
        config = {}
        
        result = await orchestrator.health_check(config)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Synchronization Endpoints
@router.post("/{integration_id}/sync")
async def trigger_sync(integration_id: int, request: SyncJobRequest):
    """Trigger a synchronization job."""
    try:
        # Create sync job
        job = await sync_service.create_sync_job(
            flow_id=request.flow_id,
            job_type=request.job_type,
            triggered_by=1  # In production, get from auth
        )
        
        # Start sync
        await sync_service.start_sync_job(job["id"])
        
        # Log audit event
        audit_logger.log(
            integration_id=integration_id,
            action="execute",
            user_id=1,
            description=f"Triggered {request.sync_type} sync"
        )
        
        return job
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{integration_id}/sync-jobs")
async def list_sync_jobs(
    integration_id: int,
    status: Optional[str] = Query(None),
    limit: int = Query(100)
):
    """List sync jobs for an integration."""
    jobs = sync_service.list_jobs(flow_id=integration_id, status=status, limit=limit)
    return {"jobs": jobs, "total": len(jobs)}


@router.get("/sync-jobs/{job_id}")
async def get_sync_job(job_id: int):
    """Get sync job details."""
    job = sync_service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Sync job not found")
    
    return job


@router.post("/sync-jobs/{job_id}/cancel")
async def cancel_sync_job(job_id: int):
    """Cancel a running sync job."""
    try:
        job = await sync_service.cancel_sync_job(job_id)
        return job
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync-jobs/{job_id}/retry")
async def retry_sync_job(job_id: int):
    """Retry a failed sync job."""
    try:
        job = await sync_service.retry_sync_job(job_id)
        return job
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Template Endpoints
@router.get("/templates")
async def list_templates(
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    limit: int = Query(100)
):
    """List integration templates."""
    templates = template_catalog.list_templates(
        category=category,
        difficulty=difficulty,
        limit=limit
    )
    return {"templates": templates, "total": len(templates)}


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """Get template by ID."""
    template = template_catalog.get_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template


@router.post("/templates/{template_id}/clone")
async def clone_template(template_id: str, request: TemplateCloneRequest):
    """Clone a template to create a custom integration."""
    try:
        cloned = template_manager.clone_template(
            template_id=template_id,
            name=request.name,
            description=request.description
        )
        return cloned
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates/categories")
async def get_template_categories():
    """Get all template categories."""
    categories = template_catalog.get_categories()
    return {"categories": categories}


# Monitoring Endpoints
@router.get("/{integration_id}/metrics")
async def get_integration_metrics(integration_id: int):
    """Get metrics for an integration."""
    metrics = metrics_collector.get_aggregated_metrics(integration_id)
    return metrics


@router.get("/{integration_id}/health-history")
async def get_health_history(integration_id: int, limit: int = Query(100)):
    """Get health check history."""
    history = health_monitor.get_health_history(integration_id, limit=limit)
    return {"history": history}


@router.get("/alerts")
async def list_alerts(
    integration_id: Optional[int] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100)
):
    """List alerts."""
    from app.integrations.monitoring.alerts import AlertSeverity, AlertStatus
    
    severity_enum = AlertSeverity(severity) if severity else None
    status_enum = AlertStatus(status) if status else None
    
    alerts = alert_manager.list_alerts(
        integration_id=integration_id,
        severity=severity_enum,
        status=status_enum,
        limit=limit
    )
    
    return {"alerts": [alert.to_dict() for alert in alerts], "total": len(alerts)}


# Analytics Endpoints
@router.get("/{integration_id}/analytics")
async def get_integration_analytics(integration_id: int):
    """Get analytics for an integration."""
    stats = integration_analytics.get_integration_stats(integration_id)
    performance = integration_analytics.get_performance_trends(integration_id)
    
    return {
        "stats": stats,
        "performance": performance
    }


@router.get("/analytics/executive-summary")
async def get_executive_summary():
    """Get executive summary of all integrations."""
    summary = integration_analytics.get_executive_summary()
    return summary


@router.get("/analytics/failure-analysis")
async def get_failure_analysis(integration_id: Optional[int] = Query(None)):
    """Get failure analysis."""
    analysis = integration_analytics.get_failure_analysis(integration_id)
    return analysis


# Governance Endpoints
@router.get("/{integration_id}/versions")
async def list_versions(integration_id: int, limit: int = Query(100)):
    """List versions for an integration."""
    versions = version_manager.list_versions(integration_id, limit=limit)
    return {"versions": versions, "total": len(versions)}


@router.post("/{integration_id}/versions/{version_id}/rollback")
async def rollback_version(integration_id: int, version_id: int):
    """Rollback to a previous version."""
    try:
        version = version_manager.rollback(integration_id, version_id, user_id=1)
        return version
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{integration_id}/audit-log")
async def get_audit_log(
    integration_id: int,
    limit: int = Query(100),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None)
):
    """Get audit log for an integration."""
    logs = audit_logger.list_logs(
        integration_id=integration_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    return {"logs": logs, "total": len(logs)}


# Statistics Endpoints
@router.get("/statistics/overview")
async def get_overview_statistics():
    """Get overview statistics."""
    return {
        "sync_service": sync_service.get_stats(),
        "health_monitor": health_monitor.get_stats(),
        "metrics_collector": metrics_collector.get_stats(),
        "alert_manager": alert_manager.get_stats(),
        "template_manager": template_manager.get_stats(),
        "version_manager": version_manager.get_stats(),
        "approval_workflow": approval_workflow.get_stats(),
        "audit_logger": audit_logger.get_stats(),
        "integration_analytics": integration_analytics.get_stats()
    }