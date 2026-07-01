import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models import (
    Monitor, MonitorRule, MonitorStatus, MonitorFrequency, AlertEvent, AlertStatus,
    MonitorSeverity, AnomalyEvent, AnomalyCategory, WorkflowDefinition, WorkflowExecution,
    WorkflowTriggerType, NotificationDelivery, NotificationChannelType, AuditRecord,
    BusinessHealthScore, SLAMetric, ScheduledInsight,
)
from app.monitoring.rule_evaluator import RuleEvaluator
from app.monitoring.anomaly_detector import AnomalyDetector
from app.monitoring.alert_service import AlertService
from app.monitoring.notification_service import NotificationService
from app.monitoring.workflow_engine import WorkflowEngine
from app.monitoring.escalation_service import EscalationService
from app.monitoring.health_score import HealthScoreCalculator
from app.monitoring.sla_monitor import SLAMonitor
from app.monitoring.scheduler import InsightScheduler
from app.monitoring.audit_service import AuditService

logger = logging.getLogger(__name__)


class MonitoringEngine:
    """Core engine that orchestrates monitoring, evaluation, alerting, and automation."""

    def __init__(self):
        self.rule_evaluator = RuleEvaluator()
        self.anomaly_detector = AnomalyDetector()
        self.alert_service = AlertService()
        self.notification_service = NotificationService()
        self.workflow_engine = WorkflowEngine()
        self.escalation_service = EscalationService()
        self.health_score_calculator = HealthScoreCalculator()
        self.sla_monitor = SLAMonitor()
        self.insight_scheduler = InsightScheduler()
        self.audit_service = AuditService()

    async def evaluate_monitor(self, monitor_id: int, db: AsyncSession) -> Optional[AlertEvent]:
        """Evaluate a single monitor's rules and generate alerts if triggered."""
        result = await db.execute(
            select(Monitor)
            .where(Monitor.id == monitor_id, Monitor.status == MonitorStatus.active)
            .options(selectinload(Monitor.rules))
        )
        monitor = result.scalar_one_or_none()
        if not monitor:
            return None

        monitor.evaluation_count += 1
        monitor.last_evaluated_at = datetime.now(timezone.utc)

        triggered_rules = []
        for rule in monitor.rules:
            if not rule.is_active:
                continue
            triggered = await self.rule_evaluator.evaluate(rule, monitor, db)
            if triggered:
                triggered_rules.append(rule)

        if not triggered_rules:
            await db.commit()
            return None

        # Create alert for the highest-priority triggered rule
        primary_rule = max(triggered_rules, key=lambda r: r.priority)
        alert = await self.alert_service.create_alert(
            monitor=monitor,
            rule=primary_rule,
            db=db,
        )

        monitor.alert_count += 1
        monitor.last_alerted_at = datetime.now(timezone.utc)
        await db.commit()

        # Fire post-alert actions asynchronously
        await self._handle_post_alert(alert, db)
        return alert

    async def evaluate_all_active_monitors(self, db: AsyncSession):
        """Evaluate all active monitors."""
        result = await db.execute(
            select(Monitor).where(Monitor.status == MonitorStatus.active)
        )
        monitors = result.scalars().all()
        for monitor in monitors:
            try:
                await self.evaluate_monitor(monitor.id, db)
            except Exception as e:
                logger.error(f"Error evaluating monitor {monitor.id}: {e}")

    async def run_anomaly_detection(self, db: AsyncSession):
        """Run AI anomaly detection across all active monitors."""
        result = await db.execute(
            select(Monitor).where(Monitor.status == MonitorStatus.active)
        )
        monitors = result.scalars().all()
        for monitor in monitors:
            try:
                anomaly = await self.anomaly_detector.detect(monitor, db)
                if anomaly:
                    alert = await self.alert_service.create_anomaly_alert(
                        monitor=monitor,
                        anomaly=anomaly,
                        db=db,
                    )
                    await self._handle_post_alert(alert, db)
            except Exception as e:
                logger.error(f"Error detecting anomalies for monitor {monitor.id}: {e}")

    async def _handle_post_alert(self, alert: AlertEvent, db: AsyncSession):
        """Execute post-alert actions: notifications, workflows, escalations."""
        # Send notifications
        await self.notification_service.deliver(alert, db)

        # Trigger workflows
        await self.workflow_engine.trigger_for_alert(alert, db)

        # Check escalation
        await self.escalation_service.check(alert, db)

        # Audit
        await self.audit_service.log(
            entity_type="alert",
            entity_id=alert.id,
            action="created",
            user_id=None,
            changes={"severity": alert.severity.value, "monitor_id": alert.monitor_id},
            db=db,
        )

    async def calculate_health_score(self, db: AsyncSession) -> BusinessHealthScore:
        """Calculate and store the current business health score."""
        score = await self.health_score_calculator.calculate(db)
        db.add(score)
        await db.commit()
        await db.refresh(score)
        return score

    async def check_slas(self, db: AsyncSession):
        """Check all active SLA metrics for breaches."""
        await self.sla_monitor.check_all(db)

    async def process_scheduled_insights(self, db: AsyncSession):
        """Generate and deliver scheduled insights that are due."""
        await self.insight_scheduler.process_due(db)

    async def get_dashboard_stats(self, db: AsyncSession) -> dict:
        """Get aggregate stats for the monitoring dashboard."""
        total = await db.scalar(select(func.count(Monitor.id)))
        active = await db.scalar(
            select(func.count(Monitor.id)).where(Monitor.status == MonitorStatus.active)
        )
        total_alerts = await db.scalar(select(func.count(AlertEvent.id)))
        open_alerts = await db.scalar(
            select(func.count(AlertEvent.id)).where(AlertEvent.status == AlertStatus.open)
        )
        critical_alerts = await db.scalar(
            select(func.count(AlertEvent.id)).where(
                AlertEvent.severity == MonitorSeverity.critical,
                AlertEvent.status == AlertStatus.open,
            )
        )
        recent_anomalies = await db.scalar(
            select(func.count(AnomalyEvent.id)).where(
                AnomalyEvent.is_resolved == False
            )
        )
        latest_health = await db.scalar(
            select(BusinessHealthScore).order_by(desc(BusinessHealthScore.created_at))
        )

        return {
            "total_monitors": total or 0,
            "active_monitors": active or 0,
            "total_alerts": total_alerts or 0,
            "open_alerts": open_alerts or 0,
            "critical_alerts": critical_alerts or 0,
            "recent_anomalies": recent_anomalies or 0,
            "health_score": latest_health.overall_score if latest_health else None,
        }