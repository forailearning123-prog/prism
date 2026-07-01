"""
Sync Scheduler
Schedules and manages recurring sync jobs.
"""

from typing import Any, Optional
from datetime import datetime, timezone
from enum import Enum
import asyncio


class ScheduleType(str, Enum):
    """Types of schedules."""
    CRON = "cron"
    INTERVAL = "interval"
    ONE_TIME = "one_time"


class SyncScheduler:
    """
    Scheduler for sync jobs.
    Supports cron expressions, intervals, and one-time schedules.
    """
    
    def __init__(self):
        """Initialize sync scheduler."""
        self.schedules: dict[int, dict[str, Any]] = {}
        self.running_tasks: dict[int, asyncio.Task] = {}
        self.is_running = False
    
    async def start(self) -> None:
        """Start the scheduler."""
        if self.is_running:
            return
        
        self.is_running = True
        # In production, this would start a background task
        # that periodically checks for jobs to run
    
    async def stop(self) -> None:
        """Stop the scheduler."""
        self.is_running = False
        
        # Cancel all running tasks
        for task in self.running_tasks.values():
            task.cancel()
        
        self.running_tasks.clear()
    
    def add_schedule(
        self,
        job_id: int,
        schedule_type: ScheduleType,
        cron_expression: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        start_time: Optional[datetime] = None,
        metadata: dict[str, Any] = None
    ) -> dict[str, Any]:
        """
        Add a schedule for a sync job.
        
        Args:
            job_id: Sync job ID
            schedule_type: Type of schedule
            cron_expression: Cron expression (for CRON type)
            interval_seconds: Interval in seconds (for INTERVAL type)
            start_time: When to start (for ONE_TIME type)
            metadata: Additional metadata
            
        Returns:
            Schedule dictionary
        """
        schedule = {
            "job_id": job_id,
            "schedule_type": schedule_type,
            "cron_expression": cron_expression,
            "interval_seconds": interval_seconds,
            "start_time": start_time,
            "is_active": True,
            "last_run": None,
            "next_run": self._calculate_next_run(schedule_type, cron_expression, interval_seconds, start_time),
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.schedules[job_id] = schedule
        return schedule
    
    def remove_schedule(self, job_id: int) -> bool:
        """
        Remove a schedule.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if removed, False if not found
        """
        if job_id in self.schedules:
            del self.schedules[job_id]
            
            # Cancel running task if any
            if job_id in self.running_tasks:
                self.running_tasks[job_id].cancel()
                del self.running_tasks[job_id]
            
            return True
        return False
    
    def get_schedule(self, job_id: int) -> Optional[dict[str, Any]]:
        """
        Get schedule for a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Schedule dictionary or None
        """
        return self.schedules.get(job_id)
    
    def list_schedules(self, is_active: bool = None) -> list[dict[str, Any]]:
        """
        List all schedules.
        
        Args:
            is_active: Filter by active status
            
        Returns:
            List of schedule dictionaries
        """
        schedules = list(self.schedules.values())
        
        if is_active is not None:
            schedules = [s for s in schedules if s.get("is_active") == is_active]
        
        return schedules
    
    def get_due_jobs(self) -> list[int]:
        """
        Get jobs that are due to run.
        
        Returns:
            List of job IDs
        """
        now = datetime.now(timezone.utc)
        due_jobs = []
        
        for job_id, schedule in self.schedules.items():
            if not schedule.get("is_active"):
                continue
            
            next_run = schedule.get("next_run")
            if next_run:
                next_run_dt = datetime.fromisoformat(next_run) if isinstance(next_run, str) else next_run
                if next_run_dt <= now:
                    due_jobs.append(job_id)
        
        return due_jobs
    
    def update_next_run(self, job_id: int) -> Optional[dict[str, Any]]:
        """
        Update the next run time for a schedule.
        
        Args:
            job_id: Job ID
            
        Returns:
            Updated schedule or None
        """
        schedule = self.schedules.get(job_id)
        if not schedule:
            return None
        
        schedule["last_run"] = datetime.now(timezone.utc).isoformat()
        schedule["next_run"] = self._calculate_next_run(
            schedule["schedule_type"],
            schedule.get("cron_expression"),
            schedule.get("interval_seconds"),
            schedule.get("start_time")
        )
        
        return schedule
    
    def _calculate_next_run(
        self,
        schedule_type: ScheduleType,
        cron_expression: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        start_time: Optional[datetime] = None
    ) -> Optional[str]:
        """
        Calculate next run time.
        
        Args:
            schedule_type: Type of schedule
            cron_expression: Cron expression
            interval_seconds: Interval in seconds
            start_time: Start time for one-time schedules
            
        Returns:
            ISO format datetime string or None
        """
        now = datetime.now(timezone.utc)
        
        if schedule_type == ScheduleType.ONE_TIME:
            return start_time.isoformat() if start_time else None
        
        elif schedule_type == ScheduleType.INTERVAL:
            if interval_seconds:
                next_run = now + __import__('datetime').timedelta(seconds=interval_seconds)
                return next_run.isoformat()
            return None
        
        elif schedule_type == ScheduleType.CRON:
            # Simplified cron parsing - in production use a proper cron library
            # like croniter or python-crontab
            if cron_expression:
                # Default to every hour if can't parse
                next_run = now + __import__('datetime').timedelta(hours=1)
                return next_run.isoformat()
            return None
        
        return None
    
    def enable_schedule(self, job_id: int) -> Optional[dict[str, Any]]:
        """
        Enable a schedule.
        
        Args:
            job_id: Job ID
            
        Returns:
            Updated schedule or None
        """
        schedule = self.schedules.get(job_id)
        if schedule:
            schedule["is_active"] = True
            schedule["next_run"] = self._calculate_next_run(
                schedule["schedule_type"],
                schedule.get("cron_expression"),
                schedule.get("interval_seconds"),
                schedule.get("start_time")
            )
            return schedule
        return None
    
    def disable_schedule(self, job_id: int) -> Optional[dict[str, Any]]:
        """
        Disable a schedule.
        
        Args:
            job_id: Job ID
            
        Returns:
            Updated schedule or None
        """
        schedule = self.schedules.get(job_id)
        if schedule:
            schedule["is_active"] = False
            schedule["next_run"] = None
            return schedule
        return None
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get scheduler statistics.
        
        Returns:
            Statistics dictionary
        """
        active_schedules = [s for s in self.schedules.values() if s.get("is_active")]
        
        return {
            "total_schedules": len(self.schedules),
            "active_schedules": len(active_schedules),
            "inactive_schedules": len(self.schedules) - len(active_schedules),
            "running_tasks": len(self.running_tasks),
            "scheduler_running": self.is_running
        }