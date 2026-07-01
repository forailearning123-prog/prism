import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Monitor, MonitorRule, AlertEvent, AlertComment, AlertStatus,
    MonitorSeverity, EscalationLevel, AnomalyCategory, AnomalyEvent,
)

logger = logging.getLogger(__name__)


class AlertService:
    """Manages alert lifecycle: create, acknowledge, resolve, assign."""

    async def create_alert(
        self,
        monitor: Monitor,
        rule: MonitorRule,
        db: AsyncSession,
        kpi_value: Optional[float] = None,
    ) -> AlertEvent:
        """Create a new alert from a triggered rule."""
        alert = AlertEvent(
            monitor_id=monitor.id,
            rule_id=rule.id,
            title=f"Monitor triggered: {monitor.name}",
            message=self._build_message(monitor, rule, kpi_value),
            severity=monitor.severity,
            status=AlertStatus.open,
            source="rule",
            kpi_value=kpi_value,
            threshold_value=rule.threshold_value,
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        return alert

    async def create_anomaly_alert(
        self,
        monitor: Monitor,
        anomaly: AnomalyEvent,
        db: AsyncSession,
    ) -> AlertEvent:
        """Create an alert from an anomaly detection."""
        alert = AlertEvent(
            monitor_id=monitor.id,
            title=f"Anomaly detected: {anomaly.metric_name}",
            message=anomaly.ai_explanation or f"Unusual pattern detected in {anomaly.metric_name}",
            severity=anomaly.severity,
            status=AlertStatus.open,
            source="anomaly",
            kpi_value=anomaly.metric_value,
            anomaly_score=anomaly.anomaly_score,
            confidence=anomaly.confidence,
            anomaly_category=anomaly.category,
            possible_causes=anomaly.possible_causes,
            suggested_actions=anomaly.suggested_actions,
            ai_explanation=anomaly.ai_explanation,
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        return alert

    async def acknowledge(self, alert_id: int, user_id: int, db: AsyncSession) -> Optional[AlertEvent]:
        """Acknowledge an alert."""
        alert = await db.get(AlertEvent, alert_id)
        if not alert or alert.status != AlertStatus.open:
            return None
        alert.status = AlertStatus.acknowledged
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(alert)
        return alert

    async def resolve(self, alert_id: int, user_id: int, notes: str, db: AsyncSession) -> Optional[AlertEvent]:
        """Resolve an alert."""
        alert = await db.get(AlertEvent, alert_id)
        if not alert or alert.status == AlertStatus.resolved:
            return None
        alert.status = AlertStatus.resolved
        alert.resolved_by = user_id
        alert.resolved_at = datetime.now(timezone.utc)
        alert.resolution_notes = notes
        await db.commit()
        await db.refresh(alert)
        return alert

    async def assign(self, alert_id: int, assigned_to: int, db: AsyncSession) -> Optional[AlertEvent]:
        """Assign an alert to a user."""
        alert = await db.get(AlertEvent, alert_id)
        if not alert:
            return None
        alert.assigned_to = assigned_to
        await db.commit()
        await db.refresh(alert)
        return alert

    async def add_comment(self, alert_id: int, user_id: int, content: str, db: AsyncSession) -> Optional[AlertComment]:
        """Add a comment to an alert."""
        alert = await db.get(AlertEvent, alert_id)
        if not alert:
            return None
        comment = AlertComment(
            alert_id=alert_id,
            user_id=user_id,
            content=content,
        )
        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        return comment

    async def get_alerts(
        self,
        db: AsyncSession,
        monitor_id: Optional[int] = None,
        status: Optional[AlertStatus] = None,
        severity: Optional[MonitorSeverity] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AlertEvent], int]:
        """Get alerts with filtering and pagination."""
        query = select(AlertEvent).options(selectinload(AlertEvent.comments))

        if monitor_id:
            query = query.where(AlertEvent.monitor_id == monitor_id)
        if status:
            query = query.where(AlertEvent.status == status)
        if severity:
            query = query.where(AlertEvent.severity == severity)

        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query) or 0

        query = query.order_by(desc(AlertEvent.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_alert_detail(self, alert_id: int, db: AsyncSession) -> Optional[AlertEvent]:
        """Get full alert details with comments."""
        result = await db.execute(
            select(AlertEvent)
            .where(AlertEvent.id == alert_id)
            .options(selectinload(AlertEvent.comments))
        )
        return result.scalar_one_or_none()

    def _build_message(self, monitor: Monitor, rule: MonitorRule, kpi_value: Optional[float]) -> str:
        """Build a human-readable alert message."""
        severity_label = monitor.severity.value.upper()
        kpi_info = f" (current value: {kpi_value})" if kpi_value is not None else ""
        return (
            f"[{severity_label}] {monitor.name}: Rule '{rule.name or rule.rule_type.value}' triggered{kpi_info}. "
            f"Threshold: {rule.threshold_value}"
        )