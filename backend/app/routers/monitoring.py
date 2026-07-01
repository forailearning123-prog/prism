import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    User, Monitor, MonitorRule, MonitorStatus, AlertEvent, AlertStatus,
    MonitorSeverity, AnomalyEvent, WorkflowDefinition, WorkflowExecution,
    WorkflowStep, NotificationConfig, NotificationDelivery, EscalationPolicy,
    EscalationStep, ScheduledInsight, SLAMetric, BusinessHealthScore, AuditRecord,
)
from app.monitoring.schemas import (
    MonitorCreate, MonitorUpdate, MonitorOut, MonitorListResponse,
    RuleOut, AlertOut, AlertListResponse, AlertCommentCreate,
    AlertCommentOut, AlertAcknowledge, AlertResolve, AlertAssign,
    AnomalyOut, AnomalyListResponse,
    WorkflowCreate, WorkflowOut, WorkflowListResponse,
    WorkflowExecutionOut, WorkflowExecutionListResponse,
    NotificationConfigCreate, NotificationConfigOut,
    NotificationDeliveryOut,
    EscalationPolicyCreate, EscalationPolicyOut,
    ScheduledInsightCreate, ScheduledInsightOut, ScheduledInsightListResponse,
    SLAMetricCreate, SLAMetricOut, SLAMetricListResponse,
    BusinessHealthScoreOut, MonitorStats,
    AuditRecordOut, AuditRecordListResponse,
)
from app.monitoring.engine import MonitoringEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])
engine = MonitoringEngine()


# ── Dashboard / Stats ──

@router.get("/stats", response_model=MonitorStats)
async def get_monitoring_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get aggregate monitoring statistics."""
    stats = await engine.get_dashboard_stats(db)
    return stats


# ── Monitors ──

@router.post("/monitors", response_model=MonitorOut, status_code=status.HTTP_201_CREATED)
async def create_monitor(
    data: MonitorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new business monitor."""
    monitor = Monitor(
        name=data.name,
        description=data.description,
        semantic_model_id=data.semantic_model_id,
        kpi_id=data.kpi_id,
        measure_name=data.measure_name,
        frequency=data.frequency,
        severity=data.severity,
        owner_id=current_user.id,
        business_owner=data.business_owner,
        tags=data.tags,
        template_id=data.template_id,
    )
    db.add(monitor)
    await db.commit()
    await db.refresh(monitor)

    # Create rules
    for rule_def in data.rules:
        rule = MonitorRule(
            monitor_id=monitor.id,
            name=rule_def.name,
            rule_type=rule_def.rule_type,
            operator=rule_def.operator,
            threshold_value=rule_def.threshold_value,
            threshold_high=rule_def.threshold_high,
            threshold_low=rule_def.threshold_low,
            percentage=rule_def.percentage,
            comparison_monitor_id=rule_def.comparison_monitor_id,
            trend_window=rule_def.trend_window,
            trend_direction=rule_def.trend_direction,
            time_field=rule_def.time_field,
            time_value=rule_def.time_value,
            time_unit=rule_def.time_unit,
            condition_logic=rule_def.condition_logic,
            priority=rule_def.priority,
        )
        db.add(rule)
    await db.commit()

    await engine.audit_service.log(
        entity_type="monitor", entity_id=monitor.id,
        action="created", user_id=current_user.id,
        changes={"name": monitor.name}, db=db,
    )

    # Reload with rules
    result = await db.execute(
        select(Monitor)
        .where(Monitor.id == monitor.id)
        .options(selectinload(Monitor.rules))
    )
    return result.scalar_one()


@router.get("/monitors", response_model=MonitorListResponse)
async def list_monitors(
    status_filter: Optional[MonitorStatus] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List monitors with filtering and pagination."""
    query = select(Monitor).options(selectinload(Monitor.rules))

    if status_filter:
        query = query.where(Monitor.status == status_filter)
    if search:
        query = query.where(Monitor.name.ilike(f"%{search}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(desc(Monitor.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return MonitorListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/monitors/{monitor_id}", response_model=MonitorOut)
async def get_monitor(
    monitor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single monitor with its rules."""
    result = await db.execute(
        select(Monitor)
        .where(Monitor.id == monitor_id)
        .options(selectinload(Monitor.rules))
    )
    monitor = result.scalar_one_or_none()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return monitor


@router.put("/monitors/{monitor_id}", response_model=MonitorOut)
async def update_monitor(
    monitor_id: int,
    data: MonitorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a monitor."""
    result = await db.execute(
        select(Monitor)
        .where(Monitor.id == monitor_id)
        .options(selectinload(Monitor.rules))
    )
    monitor = result.scalar_one_or_none()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(monitor, key, value)
    monitor.updated_at = datetime.now(timezone.utc)

    await engine.audit_service.log(
        entity_type="monitor", entity_id=monitor.id,
        action="updated", user_id=current_user.id,
        changes=update_data, db=db,
    )

    await db.commit()
    await db.refresh(monitor)
    return monitor


@router.delete("/monitors/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitor(
    monitor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Archive a monitor (soft delete)."""
    monitor = await db.get(Monitor, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    monitor.status = MonitorStatus.archived
    monitor.archived_at = datetime.now(timezone.utc)

    await engine.audit_service.log(
        entity_type="monitor", entity_id=monitor.id,
        action="archived", user_id=current_user.id, db=db,
    )
    await db.commit()


@router.post("/monitors/{monitor_id}/toggle", response_model=MonitorOut)
async def toggle_monitor(
    monitor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle monitor between active and inactive."""
    result = await db.execute(
        select(Monitor)
        .where(Monitor.id == monitor_id)
        .options(selectinload(Monitor.rules))
    )
    monitor = result.scalar_one_or_none()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    monitor.status = MonitorStatus.inactive if monitor.status == MonitorStatus.active else MonitorStatus.active
    monitor.updated_at = datetime.now(timezone.utc)

    await engine.audit_service.log(
        entity_type="monitor", entity_id=monitor.id,
        action="toggled", user_id=current_user.id,
        changes={"new_status": monitor.status.value}, db=db,
    )
    await db.commit()
    await db.refresh(monitor)
    return monitor


@router.post("/monitors/{monitor_id}/duplicate", response_model=MonitorOut, status_code=status.HTTP_201_CREATED)
async def duplicate_monitor(
    monitor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Duplicate a monitor with its rules."""
    original = await db.get(Monitor, monitor_id)
    if not original:
        raise HTTPException(status_code=404, detail="Monitor not found")

    monitor = Monitor(
        name=f"{original.name} (Copy)",
        description=original.description,
        semantic_model_id=original.semantic_model_id,
        kpi_id=original.kpi_id,
        measure_name=original.measure_name,
        frequency=original.frequency,
        severity=original.severity,
        owner_id=current_user.id,
        business_owner=original.business_owner,
        tags=original.tags,
    )
    db.add(monitor)
    await db.commit()
    await db.refresh(monitor)
    return monitor


@router.post("/monitors/{monitor_id}/evaluate")
async def evaluate_monitor(
    monitor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger evaluation of a monitor."""
    alert = await engine.evaluate_monitor(monitor_id, db)
    return {"evaluated": True, "alert_created": alert is not None}


# ── Alerts ──

@router.get("/alerts", response_model=AlertListResponse)
async def list_alerts(
    monitor_id: Optional[int] = Query(None),
    status: Optional[AlertStatus] = Query(None),
    severity: Optional[MonitorSeverity] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List alerts with filtering and pagination."""
    items, total = await engine.alert_service.get_alerts(
        db, monitor_id=monitor_id, status=status,
        severity=severity, page=page, page_size=page_size,
    )
    return AlertListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/alerts/{alert_id}", response_model=AlertOut)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full alert details."""
    alert = await engine.alert_service.get_alert_detail(alert_id, db)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertOut)
async def acknowledge_alert(
    alert_id: int,
    data: AlertAcknowledge,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Acknowledge an alert."""
    alert = await engine.alert_service.acknowledge(alert_id, current_user.id, db)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found or already acknowledged")
    return alert


@router.post("/alerts/{alert_id}/resolve", response_model=AlertOut)
async def resolve_alert(
    alert_id: int,
    data: AlertResolve,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resolve an alert."""
    alert = await engine.alert_service.resolve(alert_id, current_user.id, data.resolution_notes, db)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/assign", response_model=AlertOut)
async def assign_alert(
    alert_id: int,
    data: AlertAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign an alert to a user."""
    alert = await engine.alert_service.assign(alert_id, data.assigned_to, db)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/comments", response_model=AlertCommentOut, status_code=status.HTTP_201_CREATED)
async def add_alert_comment(
    alert_id: int,
    data: AlertCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a comment to an alert."""
    comment = await engine.alert_service.add_comment(alert_id, current_user.id, data.content, db)
    if not comment:
        raise HTTPException(status_code=404, detail="Alert not found")
    return comment


# ── Anomalies ──

@router.get("/anomalies", response_model=AnomalyListResponse)
async def list_anomalies(
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List detected anomalies."""
    query = select(AnomalyEvent)
    if category:
        query = query.where(AnomalyEvent.category == category)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(desc(AnomalyEvent.detected_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return AnomalyListResponse(items=items, total=total, page=page, page_size=page_size)


# ── Workflows ──

@router.post("/workflows", response_model=WorkflowOut, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    data: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an automation workflow."""
    workflow = WorkflowDefinition(
        name=data.name,
        description=data.description,
        trigger_type=data.trigger_type,
        trigger_config=data.trigger_config,
        owner_id=current_user.id,
        template_id=data.template_id,
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)

    for step_def in data.steps:
        step = WorkflowStep(
            workflow_id=workflow.id,
            name=step_def.name,
            step_type=step_def.step_type,
            order=step_def.order,
            config=step_def.config,
            condition=step_def.condition,
            timeout_seconds=step_def.timeout_seconds,
            is_parallel=step_def.is_parallel,
        )
        db.add(step)
    await db.commit()

    # Reload with steps
    result = await db.execute(
        select(WorkflowDefinition)
        .where(WorkflowDefinition.id == workflow.id)
        .options(selectinload(WorkflowDefinition.steps))
    )
    return result.scalar_one()


@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List workflow definitions."""
    query = select(WorkflowDefinition).options(selectinload(WorkflowDefinition.steps))
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(desc(WorkflowDefinition.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return WorkflowListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/workflows/{workflow_id}", response_model=WorkflowOut)
async def get_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a workflow definition."""
    result = await db.execute(
        select(WorkflowDefinition)
        .where(WorkflowDefinition.id == workflow_id)
        .options(selectinload(WorkflowDefinition.steps))
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.post("/workflows/{workflow_id}/execute", response_model=WorkflowExecutionOut)
async def execute_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger a workflow execution."""
    result = await db.execute(
        select(WorkflowDefinition)
        .where(WorkflowDefinition.id == workflow_id)
        .options(selectinload(WorkflowDefinition.steps))
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    execution = await engine.workflow_engine.execute(workflow, db=db)
    return execution


@router.get("/workflows/{workflow_id}/executions", response_model=WorkflowExecutionListResponse)
async def list_workflow_executions(
    workflow_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get execution history for a workflow."""
    items, total = await engine.workflow_engine.get_executions(
        db, workflow_id=workflow_id, page=page, page_size=page_size,
    )
    return WorkflowExecutionListResponse(items=items, total=total, page=page, page_size=page_size)


# ── Notification Config ──

@router.get("/notifications/config", response_model=list[NotificationConfigOut])
async def get_notification_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get notification configurations for current user."""
    result = await db.execute(
        select(NotificationConfig).where(NotificationConfig.user_id == current_user.id)
    )
    return list(result.scalars().all())


@router.post("/notifications/config", response_model=NotificationConfigOut)
async def create_notification_config(
    data: NotificationConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create or update a notification configuration."""
    existing = await db.execute(
        select(NotificationConfig).where(
            NotificationConfig.user_id == current_user.id,
            NotificationConfig.channel == data.channel,
        )
    )
    config = existing.scalar_one_or_none()
    if config:
        config.enabled = data.enabled
        config.config = data.config
        config.min_severity = data.min_severity
        config.quiet_hours_start = data.quiet_hours_start
        config.quiet_hours_end = data.quiet_hours_end
    else:
        config = NotificationConfig(
            user_id=current_user.id,
            channel=data.channel,
            enabled=data.enabled,
            config=data.config,
            min_severity=data.min_severity,
            quiet_hours_start=data.quiet_hours_start,
            quiet_hours_end=data.quiet_hours_end,
        )
        db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


@router.get("/notifications/deliveries", response_model=list[NotificationDeliveryOut])
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get notification deliveries for current user."""
    items, _ = await engine.notification_service.get_user_notifications(
        current_user.id, db, page=page, page_size=page_size,
    )
    return items


@router.get("/notifications/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get unread notification count."""
    count = await engine.notification_service.get_unread_count(current_user.id, db)
    return {"count": count}


@router.post("/notifications/{delivery_id}/read")
async def mark_notification_read(
    delivery_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a notification as read."""
    delivery = await engine.notification_service.mark_as_read(delivery_id, db)
    if not delivery:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "read"}


# ── Escalation Policies ──

@router.post("/escalation-policies", response_model=EscalationPolicyOut, status_code=status.HTTP_201_CREATED)
async def create_escalation_policy(
    data: EscalationPolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an escalation policy."""
    policy = EscalationPolicy(
        monitor_id=data.monitor_id,
        name=data.name,
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)

    for step_def in data.steps:
        step = EscalationStep(
            policy_id=policy.id,
            level_order=step_def.level_order,
            level=step_def.level,
            notify_user_id=step_def.notify_user_id,
            notify_role=step_def.notify_role,
            delay_minutes=step_def.delay_minutes,
            notify_channels=step_def.notify_channels,
            message_template=step_def.message_template,
        )
        db.add(step)
    await db.commit()

    # Reload with steps
    result = await db.execute(
        select(EscalationPolicy)
        .where(EscalationPolicy.id == policy.id)
        .options(selectinload(EscalationPolicy.steps))
    )
    return result.scalar_one()


@router.get("/escalation-policies", response_model=list[EscalationPolicyOut])
async def list_escalation_policies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List escalation policies."""
    result = await db.execute(
        select(EscalationPolicy).options(selectinload(EscalationPolicy.steps))
    )
    return list(result.scalars().all())


# ── Scheduled Insights ──

@router.post("/scheduled-insights", response_model=ScheduledInsightOut, status_code=status.HTTP_201_CREATED)
async def create_scheduled_insight(
    data: ScheduledInsightCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a scheduled insight."""
    insight = ScheduledInsight(
        name=data.name,
        description=data.description,
        owner_id=current_user.id,
        schedule_cron=data.schedule_cron,
        timezone=data.timezone,
        format=data.format,
        recipients=data.recipients,
        included_kpis=data.included_kpis,
        monitor_ids=data.monitor_ids,
        filters=data.filters,
    )
    db.add(insight)
    await db.commit()
    await db.refresh(insight)
    return insight


@router.get("/scheduled-insights", response_model=ScheduledInsightListResponse)
async def list_scheduled_insights(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List scheduled insights."""
    query = select(ScheduledInsight).where(ScheduledInsight.owner_id == current_user.id)
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(desc(ScheduledInsight.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return ScheduledInsightListResponse(items=items, total=total, page=page, page_size=page_size)


# ── SLA Metrics ──

@router.post("/sla-metrics", response_model=SLAMetricOut, status_code=status.HTTP_201_CREATED)
async def create_sla_metric(
    data: SLAMetricCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an SLA metric."""
    metric = SLAMetric(
        name=data.name,
        description=data.description,
        owner_id=current_user.id,
        target_value=data.target_value,
        target_unit=data.target_unit,
        breach_threshold=data.breach_threshold,
        measurement_period=data.measurement_period,
    )
    db.add(metric)
    await db.commit()
    await db.refresh(metric)
    return metric


@router.get("/sla-metrics", response_model=SLAMetricListResponse)
async def list_sla_metrics(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List SLA metrics."""
    query = select(SLAMetric)
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(desc(SLAMetric.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return SLAMetricListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/sla-metrics/{sla_id}/measure")
async def measure_sla(
    sla_id: int,
    value: float = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a measurement for an SLA metric."""
    metric = await engine.sla_monitor.measure(sla_id, value, db)
    return {"id": metric.id, "status": metric.status, "current_value": metric.current_value}


# ── Business Health Score ──

@router.get("/health-score", response_model=BusinessHealthScoreOut)
async def get_latest_health_score(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the latest business health score."""
    result = await db.execute(
        select(BusinessHealthScore).order_by(desc(BusinessHealthScore.created_at))
    )
    score = result.scalar_one_or_none()
    if not score:
        # Calculate on first request
        score = await engine.calculate_health_score(db)
    return score


@router.post("/health-score/refresh", response_model=BusinessHealthScoreOut)
async def refresh_health_score(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually recalculate the business health score."""
    score = await engine.calculate_health_score(db)
    return score


# ── Audit ──

@router.get("/audit", response_model=AuditRecordListResponse)
async def list_audit_records(
    entity_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List audit records with filtering."""
    items, total = await engine.audit_service.get_records(
        db, entity_type=entity_type, action=action,
        page=page, page_size=page_size,
    )
    return AuditRecordListResponse(items=items, total=total, page=page, page_size=page_size)


# ── Templates ──

MONITOR_TEMPLATES = {
    "revenue_monitoring": {
        "name": "Revenue Monitoring",
        "description": "Monitor revenue against targets and detect anomalies",
        "frequency": "daily",
        "severity": "high",
        "tags": ["finance", "revenue"],
        "rules": [
            {"name": "Revenue below target", "rule_type": "threshold", "operator": "lt", "threshold_value": 100000},
        ],
    },
    "inventory_monitoring": {
        "name": "Inventory Level Monitoring",
        "description": "Track inventory levels and detect critical stock situations",
        "frequency": "every_hour",
        "severity": "high",
        "tags": ["supply_chain", "inventory"],
        "rules": [
            {"name": "Stock below minimum", "rule_type": "threshold", "operator": "lt", "threshold_value": 500},
        ],
    },
    "employee_attrition": {
        "name": "Employee Attrition Monitor",
        "description": "Monitor employee turnover rates",
        "frequency": "monthly",
        "severity": "medium",
        "tags": ["hr", "workforce"],
        "rules": [
            {"name": "Attrition above threshold", "rule_type": "threshold", "operator": "gt", "threshold_value": 10},
        ],
    },
    "customer_churn": {
        "name": "Customer Churn Risk",
        "description": "Monitor customer churn probability",
        "frequency": "weekly",
        "severity": "high",
        "tags": ["sales", "customers"],
        "rules": [
            {"name": "Churn risk above limit", "rule_type": "percentage_change", "operator": "gt", "percentage": 5},
        ],
    },
    "cash_flow": {
        "name": "Cash Flow Monitor",
        "description": "Monitor cash flow against minimum operating level",
        "frequency": "daily",
        "severity": "critical",
        "tags": ["finance", "cash_flow"],
        "rules": [
            {"name": "Cash below minimum", "rule_type": "threshold", "operator": "lt", "threshold_value": 50000},
        ],
    },
}


@router.get("/templates")
async def list_templates():
    """List available monitor templates."""
    return [
        {"id": key, **value}
        for key, value in MONITOR_TEMPLATES.items()
    ]


@router.post("/templates/{template_id}/apply", response_model=MonitorOut, status_code=status.HTTP_201_CREATED)
async def apply_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a monitor from a template."""
    template = MONITOR_TEMPLATES.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    monitor = Monitor(
        name=template["name"],
        description=template["description"],
        frequency=template["frequency"],
        severity=template["severity"],
        owner_id=current_user.id,
        tags=template["tags"],
        template_id=template_id,
    )
    db.add(monitor)
    await db.commit()
    await db.refresh(monitor)

    for rule_def in template["rules"]:
        rule = MonitorRule(
            monitor_id=monitor.id,
            name=rule_def["name"],
            rule_type=rule_def["rule_type"],
            operator=rule_def["operator"],
            threshold_value=rule_def.get("threshold_value"),
            percentage=rule_def.get("percentage"),
        )
        db.add(rule)
    await db.commit()

    result = await db.execute(
        select(Monitor)
        .where(Monitor.id == monitor.id)
        .options(selectinload(Monitor.rules))
    )
    return result.scalar_one()


# ── Automation / Engine Control ──

@router.post("/engine/evaluate-all")
async def evaluate_all_monitors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger evaluation of all active monitors."""
    await engine.evaluate_all_active_monitors(db)
    return {"status": "evaluation_triggered"}


@router.post("/engine/detect-anomalies")
async def detect_anomalies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger AI anomaly detection across all monitors."""
    await engine.run_anomaly_detection(db)
    return {"status": "anomaly_detection_triggered"}


@router.post("/engine/calculate-health-score", response_model=BusinessHealthScoreOut)
async def calculate_health_score(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recalculate the business health score."""
    score = await engine.calculate_health_score(db)
    return score