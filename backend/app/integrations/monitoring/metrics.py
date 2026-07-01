"""
Metrics Collector
Collects and aggregates integration metrics.
"""

from typing import Any, Optional, Dict, List
from datetime import datetime, timezone
from collections import defaultdict


class MetricsCollector:
    """
    Collects and aggregates metrics for integrations.
    Tracks performance, throughput, and reliability metrics.
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self.metrics: Dict[int, List[dict[str, Any]]] = defaultdict(list)
        self.aggregated_metrics: Dict[int, dict[str, Any]] = {}
    
    def record_metric(
        self,
        integration_id: int,
        metric_type: str,
        value: float,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Record a metric value.
        
        Args:
            integration_id: Integration ID
            metric_type: Type of metric (latency, throughput, etc.)
            value: Metric value
            metadata: Additional metadata
        """
        metric = {
            "integration_id": integration_id,
            "metric_type": metric_type,
            "value": value,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.metrics[integration_id].append(metric)
        
        # Keep only last 1000 metrics per integration
        if len(self.metrics[integration_id]) > 1000:
            self.metrics[integration_id] = self.metrics[integration_id][-1000:]
        
        # Update aggregated metrics
        self._update_aggregated(integration_id, metric_type, value)
    
    def _update_aggregated(self, integration_id: int, metric_type: str, value: float) -> None:
        """
        Update aggregated metrics.
        
        Args:
            integration_id: Integration ID
            metric_type: Type of metric
            value: Metric value
        """
        if integration_id not in self.aggregated_metrics:
            self.aggregated_metrics[integration_id] = {
                "total_metrics": 0,
                "metrics_by_type": defaultdict(list)
            }
        
        agg = self.aggregated_metrics[integration_id]
        agg["total_metrics"] += 1
        agg["metrics_by_type"][metric_type].append(value)
    
    def get_metrics(
        self,
        integration_id: int,
        metric_type: str = None,
        limit: int = 100
    ) -> List[dict[str, Any]]:
        """
        Get metrics for an integration.
        
        Args:
            integration_id: Integration ID
            metric_type: Filter by metric type
            limit: Maximum number of metrics
            
        Returns:
            List of metric dictionaries
        """
        metrics = self.metrics.get(integration_id, [])
        
        if metric_type:
            metrics = [m for m in metrics if m["metric_type"] == metric_type]
        
        return metrics[-limit:]
    
    def get_aggregated_metrics(self, integration_id: int) -> dict[str, Any]:
        """
        Get aggregated metrics for an integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Aggregated metrics dictionary
        """
        agg = self.aggregated_metrics.get(integration_id, {})
        
        if not agg:
            return {
                "total_metrics": 0,
                "metrics_by_type": {}
            }
        
        # Calculate statistics for each metric type
        stats = {
            "total_metrics": agg["total_metrics"],
            "metrics_by_type": {}
        }
        
        for metric_type, values in agg.get("metrics_by_type", {}).items():
            if values:
                stats["metrics_by_type"][metric_type] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "latest": values[-1]
                }
        
        return stats
    
    def get_performance_metrics(self, integration_id: int) -> dict[str, Any]:
        """
        Get performance metrics for an integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Performance metrics dictionary
        """
        metrics = self.metrics.get(integration_id, [])
        
        # Filter performance-related metrics
        latency_metrics = [m for m in metrics if m["metric_type"] == "latency"]
        throughput_metrics = [m for m in metrics if m["metric_type"] == "throughput"]
        error_metrics = [m for m in metrics if m["metric_type"] == "error_rate"]
        
        result = {
            "integration_id": integration_id,
            "latency": self._calculate_stats(latency_metrics),
            "throughput": self._calculate_stats(throughput_metrics),
            "error_rate": self._calculate_stats(error_metrics)
        }
        
        return result
    
    def _calculate_stats(self, metrics: List[dict[str, Any]]) -> dict[str, Any]:
        """Calculate statistics for a list of metrics."""
        if not metrics:
            return {
                "count": 0,
                "min": 0,
                "max": 0,
                "avg": 0,
                "latest": 0
            }
        
        values = [m["value"] for m in metrics]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1]
        }
    
    def get_throughput_stats(self, integration_id: int, window_minutes: int = 60) -> dict[str, Any]:
        """
        Get throughput statistics for a time window.
        
        Args:
            integration_id: Integration ID
            window_minutes: Time window in minutes
            
        Returns:
            Throughput statistics
        """
        from datetime import timedelta
        
        metrics = self.metrics.get(integration_id, [])
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        
        # Filter metrics within time window
        recent_metrics = [
            m for m in metrics
            if datetime.fromisoformat(m["timestamp"]) >= cutoff
            and m["metric_type"] == "throughput"
        ]
        
        if not recent_metrics:
            return {
                "window_minutes": window_minutes,
                "total_records": 0,
                "avg_throughput_rps": 0,
                "peak_throughput_rps": 0
            }
        
        values = [m["value"] for m in recent_metrics]
        
        return {
            "window_minutes": window_minutes,
            "total_records": sum(values),
            "avg_throughput_rps": sum(values) / len(values),
            "peak_throughput_rps": max(values)
        }
    
    def get_error_stats(self, integration_id: int) -> dict[str, Any]:
        """
        Get error statistics for an integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Error statistics
        """
        metrics = self.metrics.get(integration_id, [])
        
        error_metrics = [m for m in metrics if m["metric_type"] == "error_rate"]
        retry_metrics = [m for m in metrics if m["metric_type"] == "retry_count"]
        
        return {
            "integration_id": integration_id,
            "error_rate": self._calculate_stats(error_metrics),
            "retry_count": self._calculate_stats(retry_metrics),
            "total_errors": sum(m["value"] for m in error_metrics),
            "total_retries": sum(m["value"] for m in retry_metrics)
        }
    
    def get_all_metrics_summary(self) -> dict[str, Any]:
        """
        Get summary of all metrics.
        
        Returns:
            Summary dictionary
        """
        total_metrics = sum(len(metrics) for metrics in self.metrics.values())
        
        return {
            "total_integrations": len(self.metrics),
            "total_metrics": total_metrics,
            "integrations": {
                integration_id: {
                    "metric_count": len(metrics),
                    "latest_metrics": metrics[-5:] if metrics else []
                }
                for integration_id, metrics in self.metrics.items()
            }
        }
    
    def clear_metrics(self, integration_id: int = None) -> None:
        """
        Clear metrics.
        
        Args:
            integration_id: Integration ID (clears all if None)
        """
        if integration_id:
            self.metrics.pop(integration_id, None)
            self.aggregated_metrics.pop(integration_id, None)
        else:
            self.metrics.clear()
            self.aggregated_metrics.clear()