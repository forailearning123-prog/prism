"""
Integration Analytics
Provides operational metrics and usage analytics for integrations.
"""

from typing import Any, Optional, Dict, List
from datetime import datetime, timezone
from collections import defaultdict


class IntegrationAnalytics:
    """
    Provides analytics and metrics for integrations.
    Tracks usage, performance, and operational insights.
    """
    
    def __init__(self):
        """Initialize integration analytics."""
        self.metrics: Dict[int, List[dict[str, Any]]] = defaultdict(list)
        self.usage_stats: Dict[int, dict[str, Any]] = {}
    
    def record_execution(
        self,
        integration_id: int,
        execution_data: dict[str, Any]
    ) -> None:
        """
        Record an integration execution.
        
        Args:
            integration_id: Integration ID
            execution_data: Execution metrics and data
        """
        metric = {
            "integration_id": integration_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **execution_data
        }
        
        self.metrics[integration_id].append(metric)
        
        # Keep only last 1000 executions per integration
        if len(self.metrics[integration_id]) > 1000:
            self.metrics[integration_id] = self.metrics[integration_id][-1000:]
        
        # Update usage stats
        self._update_usage_stats(integration_id, execution_data)
    
    def _update_usage_stats(self, integration_id: int, execution_data: dict[str, Any]) -> None:
        """Update usage statistics for an integration."""
        if integration_id not in self.usage_stats:
            self.usage_stats[integration_id] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_records_processed": 0,
                "total_duration_ms": 0,
                "avg_duration_ms": 0,
                "last_execution": None,
                "connector_usage": defaultdict(int)
            }
        
        stats = self.usage_stats[integration_id]
        stats["total_executions"] += 1
        
        if execution_data.get("status") == "success":
            stats["successful_executions"] += 1
        else:
            stats["failed_executions"] += 1
        
        stats["total_records_processed"] += execution_data.get("records_processed", 0)
        stats["total_duration_ms"] += execution_data.get("duration_ms", 0)
        stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["total_executions"]
        stats["last_execution"] = datetime.now(timezone.utc).isoformat()
        
        # Track connector usage
        source_connector = execution_data.get("source_connector")
        dest_connector = execution_data.get("destination_connector")
        
        if source_connector:
            stats["connector_usage"][source_connector] += 1
        if dest_connector:
            stats["connector_usage"][dest_connector] += 1
    
    def get_integration_stats(self, integration_id: int) -> dict[str, Any]:
        """
        Get statistics for a specific integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Statistics dictionary
        """
        stats = self.usage_stats.get(integration_id, {})
        
        if not stats:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "success_rate": 0.0,
                "total_records_processed": 0,
                "avg_duration_ms": 0,
                "last_execution": None
            }
        
        # Calculate success rate
        total = stats["total_executions"]
        successful = stats["successful_executions"]
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": stats["failed_executions"],
            "success_rate": success_rate,
            "total_records_processed": stats["total_records_processed"],
            "avg_duration_ms": stats["avg_duration_ms"],
            "last_execution": stats["last_execution"],
            "connector_usage": dict(stats["connector_usage"])
        }
    
    def get_execution_history(
        self,
        integration_id: int,
        limit: int = 100
    ) -> List[dict[str, Any]]:
        """
        Get execution history for an integration.
        
        Args:
            integration_id: Integration ID
            limit: Maximum number of records
            
        Returns:
            List of execution records
        """
        executions = self.metrics.get(integration_id, [])
        return executions[-limit:]
    
    def get_performance_trends(
        self,
        integration_id: int,
        window_hours: int = 24
    ) -> dict[str, Any]:
        """
        Get performance trends over time.
        
        Args:
            integration_id: Integration ID
            window_hours: Time window in hours
            
        Returns:
            Performance trends
        """
        from datetime import timedelta
        
        executions = self.metrics.get(integration_id, [])
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        
        # Filter executions within time window
        recent = [
            e for e in executions
            if datetime.fromisoformat(e["timestamp"]) >= cutoff
        ]
        
        if not recent:
            return {
                "window_hours": window_hours,
                "total_executions": 0,
                "avg_duration_ms": 0,
                "avg_records_per_execution": 0,
                "success_rate": 0.0
            }
        
        durations = [e.get("duration_ms", 0) for e in recent]
        records = [e.get("records_processed", 0) for e in recent]
        successes = sum(1 for e in recent if e.get("status") == "success")
        
        return {
            "window_hours": window_hours,
            "total_executions": len(recent),
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "avg_records_per_execution": sum(records) / len(records),
            "total_records_processed": sum(records),
            "success_rate": (successes / len(recent) * 100) if recent else 0
        }
    
    def get_most_used_connectors(self, limit: int = 10) -> List[dict[str, Any]]:
        """
        Get most frequently used connectors.
        
        Args:
            limit: Maximum number of connectors
            
        Returns:
            List of connectors with usage counts
        """
        connector_counts = defaultdict(int)
        
        for stats in self.usage_stats.values():
            for connector, count in stats.get("connector_usage", {}).items():
                connector_counts[connector] += count
        
        # Sort by usage
        sorted_connectors = sorted(connector_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {"connector": connector, "usage_count": count}
            for connector, count in sorted_connectors[:limit]
        ]
    
    def get_failure_analysis(self, integration_id: int = None) -> dict[str, Any]:
        """
        Analyze failures across integrations.
        
        Args:
            integration_id: Filter by integration ID
            
        Returns:
            Failure analysis
        """
        failures = []
        
        for integ_id, executions in self.metrics.items():
            if integration_id and integ_id != integration_id:
                continue
            
            for execution in executions:
                if execution.get("status") != "success":
                    failures.append({
                        "integration_id": integ_id,
                        "timestamp": execution.get("timestamp"),
                        "error": execution.get("error", "Unknown error"),
                        "duration_ms": execution.get("duration_ms", 0)
                    })
        
        # Group by error type
        error_counts = defaultdict(int)
        for failure in failures:
            error = failure.get("error", "Unknown")
            # Simplify error message
            error_type = error.split(":")[0] if ":" in error else error
            error_counts[error_type] += 1
        
        return {
            "total_failures": len(failures),
            "recent_failures": failures[-10:],
            "by_error_type": dict(error_counts),
            "failure_rate": self._calculate_failure_rate(integration_id)
        }
    
    def _calculate_failure_rate(self, integration_id: int = None) -> float:
        """Calculate overall failure rate."""
        total_executions = 0
        total_failures = 0
        
        for integ_id, executions in self.metrics.items():
            if integration_id and integ_id != integration_id:
                continue
            
            total_executions += len(executions)
            total_failures += sum(1 for e in executions if e.get("status") != "success")
        
        if total_executions == 0:
            return 0.0
        
        return (total_failures / total_executions) * 100
    
    def get_throughput_analysis(self, window_minutes: int = 60) -> dict[str, Any]:
        """
        Analyze throughput across all integrations.
        
        Args:
            window_minutes: Time window in minutes
            
        Returns:
            Throughput analysis
        """
        from datetime import timedelta
        
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        
        total_records = 0
        total_executions = 0
        integration_throughput = {}
        
        for integration_id, executions in self.metrics.items():
            recent = [
                e for e in executions
                if datetime.fromisoformat(e["timestamp"]) >= cutoff
            ]
            
            if recent:
                records = sum(e.get("records_processed", 0) for e in recent)
                integration_throughput[integration_id] = {
                    "executions": len(recent),
                    "records": records
                }
                total_records += records
                total_executions += len(recent)
        
        return {
            "window_minutes": window_minutes,
            "total_records_processed": total_records,
            "total_executions": total_executions,
            "avg_records_per_execution": total_records / total_executions if total_executions > 0 else 0,
            "by_integration": integration_throughput
        }
    
    def get_executive_summary(self) -> dict[str, Any]:
        """
        Get executive summary of integration health.
        
        Returns:
            Executive summary
        """
        total_integrations = len(self.usage_stats)
        total_executions = sum(s["total_executions"] for s in self.usage_stats.values())
        total_successful = sum(s["successful_executions"] for s in self.usage_stats.values())
        total_records = sum(s["total_records_processed"] for s in self.usage_stats.values())
        
        # Calculate overall success rate
        success_rate = (total_successful / total_executions * 100) if total_executions > 0 else 0
        
        # Get top performers
        top_integrations = sorted(
            self.usage_stats.items(),
            key=lambda x: x[1].get("total_executions", 0),
            reverse=True
        )[:10]
        
        return {
            "total_integrations": total_integrations,
            "total_executions": total_executions,
            "successful_executions": total_successful,
            "failed_executions": total_executions - total_successful,
            "overall_success_rate": success_rate,
            "total_records_processed": total_records,
            "top_integrations": [
                {
                    "integration_id": integ_id,
                    "executions": stats["total_executions"],
                    "success_rate": (stats["successful_executions"] / stats["total_executions"] * 100) if stats["total_executions"] > 0 else 0
                }
                for integ_id, stats in top_integrations
            ],
            "most_used_connectors": self.get_most_used_connectors(limit=5)
        }
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get analytics statistics.
        
        Returns:
            Statistics dictionary
        """
        total_executions = sum(len(executions) for executions in self.metrics.values())
        
        return {
            "total_integrations_tracked": len(self.metrics),
            "total_executions": total_executions,
            "integrations_with_activity": len(self.usage_stats),
            "avg_executions_per_integration": total_executions / len(self.metrics) if self.metrics else 0
        }