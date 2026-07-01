"""
Alert Manager
Manages alerts and notifications for integration issues.
"""

from typing import Any, Optional, Dict, List, Callable
from datetime import datetime, timezone
from enum import Enum


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class Alert:
    """Represents an integration alert."""
    
    def __init__(
        self,
        alert_id: str,
        integration_id: int,
        severity: AlertSeverity,
        title: str,
        description: str,
        source: str = "integration"
    ):
        """
        Initialize alert.
        
        Args:
            alert_id: Unique alert identifier
            integration_id: Integration ID
            severity: Alert severity
            title: Alert title
            description: Alert description
            source: Alert source
        """
        self.alert_id = alert_id
        self.integration_id = integration_id
        self.severity = severity
        self.title = title
        self.description = description
        self.source = source
        self.status = AlertStatus.ACTIVE
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()
        self.acknowledged_at = None
        self.resolved_at = None
        self.acknowledged_by = None
        self.metadata = {}
    
    def to_dict(self) -> dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "integration_id": self.integration_id,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "acknowledged_at": self.acknowledged_at,
            "resolved_at": self.resolved_at,
            "acknowledged_by": self.acknowledged_by,
            "metadata": self.metadata
        }


class AlertManager:
    """
    Manages alerts and notifications for integrations.
    Supports alert creation, routing, and escalation.
    """
    
    def __init__(self):
        """Initialize alert manager."""
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: List[dict[str, Any]] = []
        self.notification_handlers: Dict[str, List[Callable]] = {}
        self.next_alert_id = 1
    
    def create_alert(
        self,
        integration_id: int,
        severity: AlertSeverity,
        title: str,
        description: str,
        source: str = "integration",
        metadata: Dict[str, Any] = None
    ) -> Alert:
        """
        Create a new alert.
        
        Args:
            integration_id: Integration ID
            severity: Alert severity
            title: Alert title
            description: Alert description
            source: Alert source
            metadata: Additional metadata
            
        Returns:
            Created alert
        """
        alert_id = f"alert_{self.next_alert_id}"
        self.next_alert_id += 1
        
        alert = Alert(alert_id, integration_id, severity, title, description, source)
        alert.metadata = metadata or {}
        
        self.alerts[alert_id] = alert
        
        # Send notifications
        self._send_notifications(alert)
        
        return alert
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """
        Get alert by ID.
        
        Args:
            alert_id: Alert ID
            
        Returns:
            Alert or None
        """
        return self.alerts.get(alert_id)
    
    def list_alerts(
        self,
        integration_id: int = None,
        severity: AlertSeverity = None,
        status: AlertStatus = None,
        limit: int = 100
    ) -> List[Alert]:
        """
        List alerts with optional filters.
        
        Args:
            integration_id: Filter by integration ID
            severity: Filter by severity
            status: Filter by status
            limit: Maximum number of alerts
            
        Returns:
            List of alerts
        """
        alerts = list(self.alerts.values())
        
        if integration_id:
            alerts = [a for a in alerts if a.integration_id == integration_id]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if status:
            alerts = [a for a in alerts if a.status == status]
        
        # Sort by created_at descending
        alerts.sort(key=lambda x: x.created_at, reverse=True)
        
        return alerts[:limit]
    
    def acknowledge_alert(self, alert_id: str, user_id: int) -> Optional[Alert]:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert ID
            user_id: User ID who acknowledged
            
        Returns:
            Updated alert or None
        """
        alert = self.alerts.get(alert_id)
        if not alert:
            return None
        
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now(timezone.utc).isoformat()
        alert.acknowledged_by = user_id
        alert.updated_at = datetime.now(timezone.utc).isoformat()
        
        return alert
    
    def resolve_alert(self, alert_id: str, resolution_notes: str = "") -> Optional[Alert]:
        """
        Resolve an alert.
        
        Args:
            alert_id: Alert ID
            resolution_notes: Notes about resolution
            
        Returns:
            Updated alert or None
        """
        alert = self.alerts.get(alert_id)
        if not alert:
            return None
        
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now(timezone.utc).isoformat()
        alert.updated_at = datetime.now(timezone.utc).isoformat()
        alert.metadata["resolution_notes"] = resolution_notes
        
        return alert
    
    def suppress_alert(self, alert_id: str, duration_minutes: int = 60) -> Optional[Alert]:
        """
        Suppress an alert for a duration.
        
        Args:
            alert_id: Alert ID
            duration_minutes: Suppression duration in minutes
            
        Returns:
            Updated alert or None
        """
        alert = self.alerts.get(alert_id)
        if not alert:
            return None
        
        alert.status = AlertStatus.SUPPRESSED
        alert.updated_at = datetime.now(timezone.utc).isoformat()
        alert.metadata["suppressed_until"] = (
            datetime.now(timezone.utc) + __import__('datetime').timedelta(minutes=duration_minutes)
        ).isoformat()
        
        return alert
    
    def add_rule(self, rule: dict[str, Any]) -> None:
        """
        Add an alert rule.
        
        Args:
            rule: Alert rule configuration
        """
        self.alert_rules.append(rule)
    
    def evaluate_rules(self, integration_id: int, metrics: Dict[str, Any]) -> List[Alert]:
        """
        Evaluate alert rules against metrics.
        
        Args:
            integration_id: Integration ID
            metrics: Integration metrics
            
        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        
        for rule in self.alert_rules:
            if self._rule_matches(rule, integration_id, metrics):
                alert = self.create_alert(
                    integration_id=integration_id,
                    severity=rule.get("severity", AlertSeverity.MEDIUM),
                    title=rule.get("title", "Alert triggered"),
                    description=rule.get("description", ""),
                    source=rule.get("source", "rule"),
                    metadata={"rule_id": rule.get("id")}
                )
                triggered_alerts.append(alert)
        
        return triggered_alerts
    
    def _rule_matches(self, rule: dict[str, Any], integration_id: int, metrics: Dict[str, Any]) -> bool:
        """Check if a rule matches the current metrics."""
        # Check integration filter
        rule_integrations = rule.get("integration_ids", [])
        if rule_integrations and integration_id not in rule_integrations:
            return False
        
        # Check conditions
        conditions = rule.get("conditions", [])
        for condition in conditions:
            metric_name = condition.get("metric")
            operator = condition.get("operator")
            threshold = condition.get("threshold")
            
            metric_value = metrics.get(metric_name)
            if metric_value is None:
                return False
            
            if not self._evaluate_condition(metric_value, operator, threshold):
                return False
        
        return True
    
    def _evaluate_condition(self, value: float, operator: str, threshold: float) -> bool:
        """Evaluate a condition."""
        if operator == "gt":
            return value > threshold
        elif operator == "gte":
            return value >= threshold
        elif operator == "lt":
            return value < threshold
        elif operator == "lte":
            return value <= threshold
        elif operator == "eq":
            return value == threshold
        elif operator == "neq":
            return value != threshold
        return False
    
    def register_notification_handler(self, channel: str, handler: Callable) -> None:
        """
        Register a notification handler.
        
        Args:
            channel: Notification channel (email, slack, etc.)
            handler: Handler function
        """
        if channel not in self.notification_handlers:
            self.notification_handlers[channel] = []
        self.notification_handlers[channel].append(handler)
    
    async def _send_notifications(self, alert: Alert) -> None:
        """
        Send notifications for an alert.
        
        Args:
            alert: Alert to send notifications for
        """
        handlers = self.notification_handlers.get("default", [])
        
        for handler in handlers:
            try:
                await handler(alert)
            except Exception:
                pass
    
    def get_active_alerts(self, integration_id: int = None) -> List[Alert]:
        """
        Get active alerts.
        
        Args:
            integration_id: Filter by integration ID
            
        Returns:
            List of active alerts
        """
        return self.list_alerts(integration_id=integration_id, status=AlertStatus.ACTIVE)
    
    def get_critical_alerts(self) -> List[Alert]:
        """
        Get critical alerts.
        
        Returns:
            List of critical alerts
        """
        return self.list_alerts(severity=AlertSeverity.CRITICAL, status=AlertStatus.ACTIVE)
    
    def get_alert_summary(self, integration_id: int = None) -> dict[str, Any]:
        """
        Get alert summary.
        
        Args:
            integration_id: Filter by integration ID
            
        Returns:
            Alert summary
        """
        alerts = self.list_alerts(integration_id=integration_id, limit=1000)
        
        summary = {
            "total_alerts": len(alerts),
            "by_severity": {},
            "by_status": {},
            "active_critical": 0
        }
        
        for alert in alerts:
            # Count by severity
            severity = alert.severity
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            
            # Count by status
            status = alert.status
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            # Count active critical
            if alert.severity == AlertSeverity.CRITICAL and alert.status == AlertStatus.ACTIVE:
                summary["active_critical"] += 1
        
        return summary
    
    def clear_resolved_alerts(self, older_than_days: int = 30) -> int:
        """
        Clear old resolved alerts.
        
        Args:
            older_than_days: Clear alerts older than this many days
            
        Returns:
            Number of alerts cleared
        """
        from datetime import timedelta
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        alerts_to_remove = []
        
        for alert_id, alert in self.alerts.items():
            if alert.status == AlertStatus.RESOLVED:
                resolved_at = datetime.fromisoformat(alert.resolved_at) if alert.resolved_at else None
                if resolved_at and resolved_at < cutoff:
                    alerts_to_remove.append(alert_id)
        
        for alert_id in alerts_to_remove:
            del self.alerts[alert_id]
        
        return len(alerts_to_remove)
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get alert statistics.
        
        Returns:
            Statistics dictionary
        """
        total = len(self.alerts)
        active = sum(1 for a in self.alerts.values() if a.status == AlertStatus.ACTIVE)
        acknowledged = sum(1 for a in self.alerts.values() if a.status == AlertStatus.ACKNOWLEDGED)
        resolved = sum(1 for a in self.alerts.values() if a.status == AlertStatus.RESOLVED)
        
        return {
            "total_alerts": total,
            "active": active,
            "acknowledged": acknowledged,
            "resolved": resolved,
            "by_severity": {
                severity: sum(1 for a in self.alerts.values() if a.severity == severity)
                for severity in AlertSeverity
            }
        }