"""
Audit Logger
Tracks all integration changes and activities for compliance.
"""

from typing import Any, Optional, Dict, List
from datetime import datetime, timezone
from enum import Enum


class AuditAction(str, Enum):
    """Types of audit actions."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    CONFIGURE = "configure"
    APPROVE = "approve"
    REJECT = "reject"
    DEPLOY = "deploy"
    DISABLE = "disable"
    ENABLE = "enable"
    TEST = "test"
    ROLLBACK = "rollback"


class AuditLogger:
    """
    Logs all integration activities for audit and compliance.
    Provides immutable audit trail with search capabilities.
    """
    
    def __init__(self):
        """Initialize audit logger."""
        self.audit_logs: List[dict[str, Any]] = []
        self.max_logs = 10000  # Keep last 10000 logs in memory
    
    def log(
        self,
        integration_id: int,
        action: AuditAction,
        user_id: int,
        description: str,
        before_state: Dict[str, Any] = None,
        after_state: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> dict[str, Any]:
        """
        Log an audit event.
        
        Args:
            integration_id: Integration ID
            action: Action performed
            user_id: User ID who performed the action
            description: Description of the action
            before_state: State before the action
            after_state: State after the action
            metadata: Additional metadata
            
        Returns:
            Audit log entry
        """
        log_entry = {
            "id": len(self.audit_logs) + 1,
            "integration_id": integration_id,
            "action": action,
            "user_id": user_id,
            "description": description,
            "before_state": before_state or {},
            "after_state": after_state or {},
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ip_address": metadata.get("ip_address") if metadata else None,
            "user_agent": metadata.get("user_agent") if metadata else None
        }
        
        self.audit_logs.append(log_entry)
        
        # Trim old logs if exceeding max
        if len(self.audit_logs) > self.max_logs:
            self.audit_logs = self.audit_logs[-self.max_logs:]
        
        return log_entry
    
    def get_log(self, log_id: int) -> Optional[dict[str, Any]]:
        """
        Get a specific audit log entry.
        
        Args:
            log_id: Log entry ID
            
        Returns:
            Log entry or None
        """
        for log in self.audit_logs:
            if log["id"] == log_id:
                return log
        return None
    
    def list_logs(
        self,
        integration_id: int = None,
        action: AuditAction = None,
        user_id: int = None,
        start_time: str = None,
        end_time: str = None,
        limit: int = 100
    ) -> List[dict[str, Any]]:
        """
        List audit logs with filters.
        
        Args:
            integration_id: Filter by integration ID
            action: Filter by action type
            user_id: Filter by user ID
            start_time: Filter by start time (ISO format)
            end_time: Filter by end time (ISO format)
            limit: Maximum number of logs
            
        Returns:
            List of audit log entries
        """
        logs = self.audit_logs
        
        if integration_id:
            logs = [l for l in logs if l.get("integration_id") == integration_id]
        
        if action:
            logs = [l for l in logs if l.get("action") == action]
        
        if user_id:
            logs = [l for l in logs if l.get("user_id") == user_id]
        
        if start_time:
            logs = [l for l in logs if l.get("timestamp", "") >= start_time]
        
        if end_time:
            logs = [l for l in logs if l.get("timestamp", "") <= end_time]
        
        # Sort by timestamp descending
        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return logs[:limit]
    
    def get_integration_history(self, integration_id: int, limit: int = 100) -> List[dict[str, Any]]:
        """
        Get complete history for an integration.
        
        Args:
            integration_id: Integration ID
            limit: Maximum number of entries
            
        Returns:
            List of audit log entries
        """
        return self.list_logs(integration_id=integration_id, limit=limit)
    
    def get_user_activity(self, user_id: int, limit: int = 100) -> List[dict[str, Any]]:
        """
        Get activity for a specific user.
        
        Args:
            user_id: User ID
            limit: Maximum number of entries
            
        Returns:
            List of audit log entries
        """
        return self.list_logs(user_id=user_id, limit=limit)
    
    def search_logs(self, query: str, limit: int = 100) -> List[dict[str, Any]]:
        """
        Search audit logs by description.
        
        Args:
            query: Search query
            limit: Maximum number of entries
            
        Returns:
            List of matching audit log entries
        """
        query_lower = query.lower()
        results = []
        
        for log in self.audit_logs:
            description = log.get("description", "").lower()
            if query_lower in description:
                results.append(log)
        
        # Sort by timestamp descending
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return results[:limit]
    
    def get_changes_summary(
        self,
        integration_id: int,
        start_time: str = None,
        end_time: str = None
    ) -> dict[str, Any]:
        """
        Get summary of changes for an integration.
        
        Args:
            integration_id: Integration ID
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            Changes summary
        """
        logs = self.list_logs(
            integration_id=integration_id,
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        
        summary = {
            "total_changes": len(logs),
            "by_action": {},
            "by_user": {},
            "timeline": []
        }
        
        for log in logs:
            # Count by action
            action = log.get("action", "unknown")
            summary["by_action"][action] = summary["by_action"].get(action, 0) + 1
            
            # Count by user
            user_id = log.get("user_id")
            summary["by_user"][user_id] = summary["by_user"].get(user_id, 0) + 1
            
            # Add to timeline
            summary["timeline"].append({
                "timestamp": log.get("timestamp"),
                "action": action,
                "description": log.get("description"),
                "user_id": user_id
            })
        
        return summary
    
    def export_logs(
        self,
        integration_id: int = None,
        start_time: str = None,
        end_time: str = None,
        format: str = "json"
    ) -> str:
        """
        Export audit logs.
        
        Args:
            integration_id: Filter by integration ID
            start_time: Start time filter
            end_time: End time filter
            format: Export format (json, csv)
            
        Returns:
            Exported logs as string
        """
        logs = self.list_logs(
            integration_id=integration_id,
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        if format == "json":
            import json
            return json.dumps(logs, indent=2)
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=logs[0].keys())
                writer.writeheader()
                writer.writerows(logs)
            
            return output.getvalue()
        
        return ""
    
    def clear_logs(self, older_than_days: int = 90) -> int:
        """
        Clear old audit logs.
        
        Args:
            older_than_days: Clear logs older than this many days
            
        Returns:
            Number of logs cleared
        """
        from datetime import timedelta
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        logs_to_keep = []
        logs_removed = 0
        
        for log in self.audit_logs:
            log_time = datetime.fromisoformat(log["timestamp"])
            if log_time >= cutoff:
                logs_to_keep.append(log)
            else:
                logs_removed += 1
        
        self.audit_logs = logs_to_keep
        
        return logs_removed
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get audit logger statistics.
        
        Returns:
            Statistics dictionary
        """
        total_logs = len(self.audit_logs)
        
        # Count by action
        by_action = {}
        for log in self.audit_logs:
            action = log.get("action", "unknown")
            by_action[action] = by_action.get(action, 0) + 1
        
        # Count by integration
        by_integration = {}
        for log in self.audit_logs:
            integration_id = log.get("integration_id")
            by_integration[integration_id] = by_integration.get(integration_id, 0) + 1
        
        return {
            "total_logs": total_logs,
            "by_action": by_action,
            "by_integration": by_integration,
            "unique_integrations": len(by_integration),
            "unique_users": len(set(log.get("user_id") for log in self.audit_logs))
        }