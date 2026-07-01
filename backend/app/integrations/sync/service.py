"""
Sync Service
Core service for managing synchronization jobs.
"""

from typing import Any, Optional
from datetime import datetime, timezone
from enum import Enum

from app.integrations.exceptions import SyncJobError


class SyncService:
    """
    Service for managing synchronization jobs.
    Coordinates sync execution, monitoring, and error handling.
    """
    
    def __init__(self):
        """Initialize sync service."""
        self.active_jobs: dict[int, Any] = {}
        self.job_history: dict[int, list[dict[str, Any]]] = {}
    
    async def create_sync_job(
        self,
        flow_id: int,
        job_type: str,
        scheduled_at: Optional[datetime] = None,
        triggered_by: Optional[int] = None,
        trigger_event: Optional[str] = None,
        metadata: dict[str, Any] = None
    ) -> dict[str, Any]:
        """
        Create a new sync job.
        
        Args:
            flow_id: Integration flow ID
            job_type: Type of sync (manual, scheduled, event_driven, etc.)
            scheduled_at: When to run the job (for scheduled jobs)
            triggered_by: User ID who triggered the job
            trigger_event: Event that triggered the job
            metadata: Additional metadata
            
        Returns:
            Created job dictionary
        """
        job = {
            "id": len(self.active_jobs) + 1,
            "flow_id": flow_id,
            "job_type": job_type,
            "status": "pending",
            "scheduled_at": scheduled_at,
            "triggered_by": triggered_by,
            "trigger_event": trigger_event,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.active_jobs[job["id"]] = job
        
        return job
    
    async def start_sync_job(self, job_id: int) -> dict[str, Any]:
        """
        Start a sync job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Updated job dictionary
        """
        job = self.active_jobs.get(job_id)
        if not job:
            raise SyncJobError(f"Job {job_id} not found")
        
        job["status"] = "running"
        job["started_at"] = datetime.now(timezone.utc).isoformat()
        job["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return job
    
    async def complete_sync_job(
        self,
        job_id: int,
        status: str,
        records_processed: int = 0,
        records_succeeded: int = 0,
        records_failed: int = 0,
        error_message: Optional[str] = None,
        error_details: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Complete a sync job.
        
        Args:
            job_id: Job ID
            status: Final status (success, failed, partial_failure)
            records_processed: Total records processed
            records_succeeded: Records successfully synced
            records_failed: Records that failed
            error_message: Error message if failed
            error_details: Detailed error information
            
        Returns:
            Updated job dictionary
        """
        job = self.active_jobs.get(job_id)
        if not job:
            raise SyncJobError(f"Job {job_id} not found")
        
        job["status"] = status
        job["completed_at"] = datetime.now(timezone.utc).isoformat()
        job["updated_at"] = datetime.now(timezone.utc).isoformat()
        job["records_processed"] = records_processed
        job["records_succeeded"] = records_succeeded
        job["records_failed"] = records_failed
        
        if error_message:
            job["error_message"] = error_message
        if error_details:
            job["error_details"] = error_details
        
        # Calculate duration
        if job.get("started_at"):
            started = datetime.fromisoformat(job["started_at"])
            completed = datetime.fromisoformat(job["completed_at"])
            duration_ms = int((completed - started).total_seconds() * 1000)
            job["duration_ms"] = duration_ms
        
        # Move to history
        if job_id not in self.job_history:
            self.job_history[job_id] = []
        self.job_history[job_id].append(job.copy())
        
        return job
    
    async def cancel_sync_job(self, job_id: int) -> dict[str, Any]:
        """
        Cancel a running sync job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Updated job dictionary
        """
        job = self.active_jobs.get(job_id)
        if not job:
            raise SyncJobError(f"Job {job_id} not found")
        
        if job["status"] != "running":
            raise SyncJobError(f"Job {job_id} is not running")
        
        job["status"] = "cancelled"
        job["completed_at"] = datetime.now(timezone.utc).isoformat()
        job["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return job
    
    async def retry_sync_job(self, job_id: int) -> dict[str, Any]:
        """
        Retry a failed sync job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Updated job dictionary
        """
        job = self.active_jobs.get(job_id)
        if not job:
            raise SyncJobError(f"Job {job_id} not found")
        
        if job["status"] not in ["failed", "partial_failure"]:
            raise SyncJobError(f"Job {job_id} cannot be retried")
        
        # Reset job status
        job["status"] = "pending"
        job["retry_count"] = job.get("retry_count", 0) + 1
        job["error_message"] = None
        job["error_details"] = None
        job["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return job
    
    def get_job(self, job_id: int) -> Optional[dict[str, Any]]:
        """
        Get job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job dictionary or None
        """
        return self.active_jobs.get(job_id)
    
    def get_job_history(self, job_id: int) -> list[dict[str, Any]]:
        """
        Get job execution history.
        
        Args:
            job_id: Job ID
            
        Returns:
            List of job executions
        """
        return self.job_history.get(job_id, [])
    
    def list_jobs(
        self,
        flow_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        List sync jobs with optional filters.
        
        Args:
            flow_id: Filter by flow ID
            status: Filter by status
            limit: Maximum number of jobs to return
            
        Returns:
            List of job dictionaries
        """
        jobs = list(self.active_jobs.values())
        
        if flow_id:
            jobs = [j for j in jobs if j.get("flow_id") == flow_id]
        
        if status:
            jobs = [j for j in jobs if j.get("status") == status]
        
        # Sort by created_at descending
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return jobs[:limit]
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get sync service statistics.
        
        Returns:
            Statistics dictionary
        """
        all_jobs = list(self.active_jobs.values()) + [
            job for history in self.job_history.values() for job in history
        ]
        
        return {
            "total_jobs": len(all_jobs),
            "active_jobs": len([j for j in self.active_jobs.values() if j.get("status") == "running"]),
            "pending_jobs": len([j for j in self.active_jobs.values() if j.get("status") == "pending"]),
            "completed_jobs": len([j for j in all_jobs if j.get("status") == "success"]),
            "failed_jobs": len([j for j in all_jobs if j.get("status") == "failed"]),
            "total_records_processed": sum(j.get("records_processed", 0) for j in all_jobs),
            "total_records_succeeded": sum(j.get("records_succeeded", 0) for j in all_jobs),
            "total_records_failed": sum(j.get("records_failed", 0) for j in all_jobs)
        }