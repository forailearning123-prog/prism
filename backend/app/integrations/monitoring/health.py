"""
Health Monitor
Monitors the health of integrations and connectors.
"""

from typing import Any, Optional, Dict, List
from datetime import datetime, timezone
from enum import Enum


class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    FAILED = "failed"
    UNKNOWN = "unknown"


class HealthMonitor:
    """
    Monitors health of integrations and connectors.
    Tracks status, response times, and availability.
    """
    
    def __init__(self):
        """Initialize health monitor."""
        self.health_checks: Dict[int, List[dict[str, Any]]] = {}
        self.current_status: Dict[int, str] = {}
    
    async def check_health(
        self,
        integration_id: int,
        check_func,
        **kwargs
    ) -> dict[str, Any]:
        """
        Perform a health check.
        
        Args:
            integration_id: Integration ID
            check_func: Async function to perform health check
            **kwargs: Additional parameters for check_func
            
        Returns:
            Health check result
        """
        import time
        start = time.time()
        
        try:
            result = await check_func(**kwargs)
            response_time = int((time.time() - start) * 1000)
            
            health_result = {
                "integration_id": integration_id,
                "status": HealthStatus.HEALTHY if result.get("success", False) else HealthStatus.FAILED,
                "response_time_ms": response_time,
                "message": result.get("message", "Health check completed"),
                "details": result.get("details", {}),
                "checked_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Store health check
            self._record_health_check(integration_id, health_result)
            
            # Update current status
            self.current_status[integration_id] = health_result["status"]
            
            return health_result
        
        except Exception as e:
            response_time = int((time.time() - start) * 1000)
            
            health_result = {
                "integration_id": integration_id,
                "status": HealthStatus.FAILED,
                "response_time_ms": response_time,
                "message": str(e),
                "details": {"error": str(e)},
                "checked_at": datetime.now(timezone.utc).isoformat()
            }
            
            self._record_health_check(integration_id, health_result)
            self.current_status[integration_id] = HealthStatus.FAILED
            
            return health_result
    
    def _record_health_check(self, integration_id: int, result: dict[str, Any]) -> None:
        """
        Record a health check result.
        
        Args:
            integration_id: Integration ID
            result: Health check result
        """
        if integration_id not in self.health_checks:
            self.health_checks[integration_id] = []
        
        self.health_checks[integration_id].append(result)
        
        # Keep only last 100 checks
        if len(self.health_checks[integration_id]) > 100:
            self.health_checks[integration_id] = self.health_checks[integration_id][-100:]
    
    def get_health_status(self, integration_id: int) -> Optional[str]:
        """
        Get current health status for an integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Health status or None
        """
        return self.current_status.get(integration_id)
    
    def get_health_history(
        self,
        integration_id: int,
        limit: int = 100
    ) -> List[dict[str, Any]]:
        """
        Get health check history.
        
        Args:
            integration_id: Integration ID
            limit: Maximum number of records
            
        Returns:
            List of health check results
        """
        checks = self.health_checks.get(integration_id, [])
        return checks[-limit:]
    
    def get_availability_stats(self, integration_id: int) -> dict[str, Any]:
        """
        Calculate availability statistics.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Availability statistics
        """
        checks = self.health_checks.get(integration_id, [])
        
        if not checks:
            return {
                "total_checks": 0,
                "healthy": 0,
                "failed": 0,
                "availability_percentage": 0.0,
                "avg_response_time_ms": 0
            }
        
        healthy = sum(1 for c in checks if c["status"] == HealthStatus.HEALTHY)
        failed = sum(1 for c in checks if c["status"] == HealthStatus.FAILED)
        avg_response = sum(c["response_time_ms"] for c in checks) / len(checks)
        
        return {
            "total_checks": len(checks),
            "healthy": healthy,
            "failed": failed,
            "availability_percentage": (healthy / len(checks)) * 100,
            "avg_response_time_ms": avg_response
        }
    
    def get_all_statuses(self) -> Dict[int, str]:
        """
        Get health status for all integrations.
        
        Returns:
            Dictionary of integration IDs to status
        """
        return self.current_status.copy()
    
    def get_unhealthy_integrations(self) -> List[int]:
        """
        Get list of unhealthy integrations.
        
        Returns:
            List of integration IDs with failed status
        """
        return [
            integration_id
            for integration_id, status in self.current_status.items()
            if status == HealthStatus.FAILED
        ]
    
    def clear_history(self, integration_id: int = None) -> None:
        """
        Clear health check history.
        
        Args:
            integration_id: Integration ID (clears all if None)
        """
        if integration_id:
            self.health_checks.pop(integration_id, None)
            self.current_status.pop(integration_id, None)
        else:
            self.health_checks.clear()
            self.current_status.clear()
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get health monitoring statistics.
        
        Returns:
            Statistics dictionary
        """
        total = len(self.current_status)
        healthy = sum(1 for s in self.current_status.values() if s == HealthStatus.HEALTHY)
        failed = sum(1 for s in self.current_status.values() if s == HealthStatus.FAILED)
        
        return {
            "total_monitored": total,
            "healthy": healthy,
            "failed": failed,
            "unknown": total - healthy - failed,
            "health_percentage": (healthy / total * 100) if total > 0 else 0
        }