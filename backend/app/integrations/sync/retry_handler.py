"""
Retry Handler
Manages retry logic for failed sync operations.
"""

from typing import Any, Optional, Callable
from datetime import datetime, timezone
from enum import Enum
import asyncio


class RetryStrategy(str, Enum):
    """Retry strategies."""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    RANDOM = "random"


class RetryHandler:
    """
    Handles retry logic for failed operations.
    Supports various retry strategies and error classification.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0
    ):
        """
        Initialize retry handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            strategy: Retry strategy
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            backoff_factor: Multiplier for exponential backoff
        """
        self.max_retries = max_retries
        self.strategy = strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.retry_history: dict[str, list[dict[str, Any]]] = {}
    
    async def execute_with_retry(
        self,
        operation_id: str,
        operation: Callable,
        *args,
        retryable_errors: list[type] = None,
        **kwargs
    ) -> Any:
        """
        Execute an operation with retry logic.
        
        Args:
            operation_id: Unique identifier for the operation
            operation: Async function to execute
            *args: Positional arguments for operation
            retryable_errors: List of exception types to retry
            **kwargs: Keyword arguments for operation
            
        Returns:
            Operation result
            
        Raises:
            Last exception if all retries fail
        """
        retryable_errors = retryable_errors or [Exception]
        last_error = None
        attempts = []
        
        for attempt in range(self.max_retries + 1):
            try:
                result = await operation(*args, **kwargs)
                
                # Success - record and return
                self._record_attempt(operation_id, attempt, "success")
                return result
            
            except tuple(retryable_errors) as e:
                last_error = e
                
                # Record failed attempt
                attempt_record = {
                    "attempt": attempt + 1,
                    "status": "failed",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                attempts.append(attempt_record)
                
                # Don't wait after last attempt
                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    await asyncio.sleep(delay)
        
        # All retries failed
        self._record_attempt(operation_id, self.max_retries, "failed", last_error)
        
        raise last_error
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay before next retry.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        if self.strategy == RetryStrategy.FIXED:
            delay = self.base_delay
        
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (self.backoff_factor ** attempt)
        
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * (attempt + 1)
        
        elif self.strategy == RetryStrategy.RANDOM:
            import random
            delay = random.uniform(0, self.base_delay * (attempt + 1))
        
        else:
            delay = self.base_delay
        
        # Cap at max delay
        return min(delay, self.max_delay)
    
    def _record_attempt(
        self,
        operation_id: str,
        attempt: int,
        status: str,
        error: Exception = None
    ) -> None:
        """
        Record an attempt in history.
        
        Args:
            operation_id: Operation identifier
            attempt: Attempt number
            status: Status (success/failed)
            error: Exception if failed
        """
        if operation_id not in self.retry_history:
            self.retry_history[operation_id] = []
        
        self.retry_history[operation_id].append({
            "attempt": attempt + 1,
            "status": status,
            "error": str(error) if error else None,
            "error_type": type(error).__name__ if error else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def get_retry_history(self, operation_id: str) -> list[dict[str, Any]]:
        """
        Get retry history for an operation.
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            List of attempt records
        """
        return self.retry_history.get(operation_id, [])
    
    def clear_history(self, operation_id: str = None) -> None:
        """
        Clear retry history.
        
        Args:
            operation_id: Operation identifier (clears all if None)
        """
        if operation_id:
            self.retry_history.pop(operation_id, None)
        else:
            self.retry_history.clear()
    
    def should_retry(
        self,
        error: Exception,
        attempt: int,
        retryable_errors: list[type] = None
    ) -> bool:
        """
        Determine if an error should be retried.
        
        Args:
            error: Exception that occurred
            attempt: Current attempt number
            retryable_errors: List of retryable exception types
            
        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.max_retries:
            return False
        
        if retryable_errors:
            return isinstance(error, tuple(retryable_errors))
        
        # Default: retry on common transient errors
        transient_errors = [
            ConnectionError,
            TimeoutError,
            # Add more as needed
        ]
        return isinstance(error, tuple(transient_errors))
    
    def get_next_delay(self, attempt: int) -> float:
        """
        Get delay for next retry attempt.
        
        Args:
            attempt: Current attempt number
            
        Returns:
            Delay in seconds
        """
        return self._calculate_delay(attempt)
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get retry statistics.
        
        Returns:
            Statistics dictionary
        """
        total_attempts = sum(len(history) for history in self.retry_history.values())
        successful_operations = sum(
            1 for history in self.retry_history.values()
            if any(attempt["status"] == "success" for attempt in history)
        )
        failed_operations = sum(
            1 for history in self.retry_history.values()
            if all(attempt["status"] == "failed" for attempt in history)
        )
        
        return {
            "total_operations": len(self.retry_history),
            "total_attempts": total_attempts,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "avg_attempts_per_operation": total_attempts / len(self.retry_history) if self.retry_history else 0
        }


class DeadLetterQueue:
    """
    Queue for messages that failed after all retry attempts.
    Supports manual replay and recovery.
    """
    
    def __init__(self):
        """Initialize dead letter queue."""
        self.queue: dict[int, dict[str, Any]] = {}
        self.next_id = 1
    
    def add(
        self,
        flow_id: int,
        payload: dict[str, Any],
        error: str,
        error_type: str,
        max_retries: int = 3,
        metadata: dict[str, Any] = None
    ) -> dict[str, Any]:
        """
        Add a failed message to the queue.
        
        Args:
            flow_id: Integration flow ID
            payload: Failed message payload
            error: Error message
            error_type: Type of error
            max_retries: Maximum retry attempts
            metadata: Additional metadata
            
        Returns:
            Queue entry dictionary
        """
        entry = {
            "id": self.next_id,
            "flow_id": flow_id,
            "payload": payload,
            "error_message": error,
            "error_type": error_type,
            "retry_count": 0,
            "max_retries": max_retries,
            "status": "pending",
            "next_retry_at": self._calculate_next_retry(0),
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.queue[self.next_id] = entry
        self.next_id += 1
        
        return entry
    
    def get(self, entry_id: int) -> Optional[dict[str, Any]]:
        """
        Get a queue entry by ID.
        
        Args:
            entry_id: Entry ID
            
        Returns:
            Entry dictionary or None
        """
        return self.queue.get(entry_id)
    
    def get_pending(self, flow_id: int = None) -> list[dict[str, Any]]:
        """
        Get pending entries.
        
        Args:
            flow_id: Filter by flow ID
            
        Returns:
            List of pending entries
        """
        entries = [e for e in self.queue.values() if e["status"] == "pending"]
        
        if flow_id:
            entries = [e for e in entries if e["flow_id"] == flow_id]
        
        return entries
    
    def retry(self, entry_id: int) -> Optional[dict[str, Any]]:
        """
        Retry a failed entry.
        
        Args:
            entry_id: Entry ID
            
        Returns:
            Updated entry or None
        """
        entry = self.queue.get(entry_id)
        if not entry:
            return None
        
        if entry["retry_count"] >= entry["max_retries"]:
            entry["status"] = "exhausted"
        else:
            entry["retry_count"] += 1
            entry["status"] = "pending"
            entry["next_retry_at"] = self._calculate_next_retry(entry["retry_count"])
        
        entry["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return entry
    
    def resolve(self, entry_id: int, resolution_notes: str = "") -> Optional[dict[str, Any]]:
        """
        Mark an entry as resolved.
        
        Args:
            entry_id: Entry ID
            resolution_notes: Notes about resolution
            
        Returns:
            Updated entry or None
        """
        entry = self.queue.get(entry_id)
        if not entry:
            return None
        
        entry["status"] = "resolved"
        entry["resolution_notes"] = resolution_notes
        entry["resolved_at"] = datetime.now(timezone.utc).isoformat()
        entry["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return entry
    
    def discard(self, entry_id: int, reason: str = "") -> Optional[dict[str, Any]]:
        """
        Discard an entry from the queue.
        
        Args:
            entry_id: Entry ID
            reason: Reason for discarding
            
        Returns:
            Updated entry or None
        """
        entry = self.queue.get(entry_id)
        if not entry:
            return None
        
        entry["status"] = "discarded"
        entry["discard_reason"] = reason
        entry["discarded_at"] = datetime.now(timezone.utc).isoformat()
        entry["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return entry
    
    def remove(self, entry_id: int) -> bool:
        """
        Remove an entry from the queue.
        
        Args:
            entry_id: Entry ID
            
        Returns:
            True if removed, False if not found
        """
        if entry_id in self.queue:
            del self.queue[entry_id]
            return True
        return False
    
    def _calculate_next_retry(self, retry_count: int) -> str:
        """
        Calculate next retry time.
        
        Args:
            retry_count: Current retry count
            
        Returns:
            ISO format datetime string
        """
        from datetime import timedelta
        next_retry = datetime.now(timezone.utc) + timedelta(minutes=5 * (retry_count + 1))
        return next_retry.isoformat()
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get queue statistics.
        
        Returns:
            Statistics dictionary
        """
        status_counts = {}
        for entry in self.queue.values():
            status = entry["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_entries": len(self.queue),
            "by_status": status_counts,
            "pending": status_counts.get("pending", 0),
            "resolved": status_counts.get("resolved", 0),
            "discarded": status_counts.get("discarded", 0),
            "exhausted": status_counts.get("exhausted", 0)
        }