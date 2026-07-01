"""
Flow Executor
Executes integration flows with retry logic, error handling, and monitoring.
"""

import asyncio
import time
from typing import Any, Optional
from datetime import datetime, timezone

from app.integrations.exceptions import (
    IntegrationError,
    SyncJobError,
    TimeoutError,
    RateLimitError
)


class FlowExecutor:
    """
    Executes integration flows with robust error handling and retry logic.
    """
    
    def __init__(self, max_retries: int = 3, retry_delay: int = 60):
        """
        Initialize flow executor.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    async def execute_with_retry(
        self,
        flow_id: int,
        execute_func,
        *args,
        **kwargs
    ) -> dict[str, Any]:
        """
        Execute a flow function with retry logic.
        
        Args:
            flow_id: Integration flow ID
            execute_func: Async function to execute
            *args: Positional arguments for execute_func
            **kwargs: Keyword arguments for execute_func
            
        Returns:
            Execution result
        """
        result = {
            "flow_id": flow_id,
            "status": "running",
            "attempts": 0,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "records_processed": 0,
            "records_succeeded": 0,
            "records_failed": 0,
            "errors": []
        }
        
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            result["attempts"] = attempt + 1
            
            try:
                # Execute the flow
                execution_result = await asyncio.wait_for(
                    execute_func(*args, **kwargs),
                    timeout=kwargs.get("timeout_seconds", 300)
                )
                
                # Success
                result.update(execution_result)
                result["status"] = "success"
                result["completed_at"] = datetime.now(timezone.utc).isoformat()
                return result
            
            except asyncio.TimeoutError:
                last_error = TimeoutError("Flow execution timed out")
                result["errors"].append(f"Timeout on attempt {attempt + 1}")
            
            except RateLimitError as e:
                last_error = e
                result["errors"].append(f"Rate limited on attempt {attempt + 1}")
                # Wait longer for rate limit errors
                await asyncio.sleep(self.retry_delay * (attempt + 1))
                continue
            
            except IntegrationError as e:
                last_error = e
                result["errors"].append(f"Integration error on attempt {attempt + 1}: {str(e)}")
            
            except Exception as e:
                last_error = e
                result["errors"].append(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
            
            # Don't sleep after the last attempt
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay)
        
        # All attempts failed
        result["status"] = "failed"
        result["error"] = str(last_error)
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        return result
    
    async def execute_batch(
        self,
        flow_id: int,
        read_func,
        write_func,
        batch_size: int = 1000,
        **kwargs
    ) -> dict[str, Any]:
        """
        Execute flow in batches.
        
        Args:
            flow_id: Integration flow ID
            read_func: Async function to read data
            write_func: Async function to write data
            batch_size: Number of records per batch
            **kwargs: Additional parameters
            
        Returns:
            Execution result
        """
        result = {
            "flow_id": flow_id,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "total_batches": 0,
            "completed_batches": 0,
            "records_processed": 0,
            "records_succeeded": 0,
            "records_failed": 0,
            "errors": []
        }
        
        try:
            offset = 0
            has_more = True
            
            while has_more:
                # Read batch
                read_result = await read_func(limit=batch_size, offset=offset)
                
                if not read_result.get("success", False):
                    result["errors"].append(read_result.get("error", "Read failed"))
                    result["status"] = "failed"
                    break
                
                records = read_result.get("records", [])
                if not records:
                    has_more = False
                    break
                
                result["total_batches"] += 1
                
                # Write batch
                write_result = await write_func(records)
                
                if write_result.get("success", False):
                    result["completed_batches"] += 1
                    result["records_succeeded"] += write_result.get("records_written", 0)
                else:
                    result["records_failed"] += write_result.get("records_failed", 0)
                    result["errors"].append(write_result.get("error", "Write failed"))
                
                result["records_processed"] += len(records)
                
                # Check if there are more records
                has_more = read_result.get("has_more", False)
                offset += batch_size
            
            result["status"] = "success" if result["records_failed"] == 0 else "partial_failure"
        
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
        
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        return result
    
    async def execute_incremental(
        self,
        flow_id: int,
        read_func,
        write_func,
        cursor_field: str,
        last_cursor: Optional[str] = None,
        batch_size: int = 1000,
        **kwargs
    ) -> dict[str, Any]:
        """
        Execute incremental sync.
        
        Args:
            flow_id: Integration flow ID
            read_func: Async function to read data
            write_func: Async function to write data
            cursor_field: Field to use as cursor (e.g., 'updated_at')
            last_cursor: Last cursor value from previous sync
            batch_size: Number of records per batch
            **kwargs: Additional parameters
            
        Returns:
            Execution result with new cursor
        """
        result = {
            "flow_id": flow_id,
            "status": "running",
            "sync_type": "incremental",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "last_cursor": last_cursor,
            "new_cursor": last_cursor,
            "records_processed": 0,
            "records_succeeded": 0,
            "records_failed": 0,
            "errors": []
        }
        
        try:
            offset = 0
            has_more = True
            max_cursor = last_cursor
            
            while has_more:
                # Read batch with cursor
                read_result = await read_func(
                    filter={cursor_field: last_cursor} if last_cursor else {},
                    limit=batch_size,
                    offset=offset
                )
                
                if not read_result.get("success", False):
                    result["errors"].append(read_result.get("error", "Read failed"))
                    result["status"] = "failed"
                    break
                
                records = read_result.get("records", [])
                if not records:
                    has_more = False
                    break
                
                # Update cursor
                for record in records:
                    record_cursor = record.get(cursor_field)
                    if record_cursor and (max_cursor is None or record_cursor > max_cursor):
                        max_cursor = record_cursor
                
                # Write batch
                write_result = await write_func(records)
                
                if write_result.get("success", False):
                    result["records_succeeded"] += write_result.get("records_written", 0)
                else:
                    result["records_failed"] += write_result.get("records_failed", 0)
                    result["errors"].append(write_result.get("error", "Write failed"))
                
                result["records_processed"] += len(records)
                
                has_more = read_result.get("has_more", False)
                offset += batch_size
            
            result["new_cursor"] = max_cursor
            result["status"] = "success" if result["records_failed"] == 0 else "partial_failure"
        
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
        
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        return result
    
    async def execute_bidirectional(
        self,
        flow_id: int,
        source_read_func,
        source_write_func,
        dest_read_func,
        dest_write_func,
        conflict_resolver,
        batch_size: int = 1000,
        **kwargs
    ) -> dict[str, Any]:
        """
        Execute bidirectional sync with conflict resolution.
        
        Args:
            flow_id: Integration flow ID
            source_read_func: Function to read from source
            source_write_func: Function to write to source
            dest_read_func: Function to read from destination
            dest_write_func: Function to write to destination
            conflict_resolver: ConflictResolver instance
            batch_size: Number of records per batch
            **kwargs: Additional parameters
            
        Returns:
            Execution result
        """
        result = {
            "flow_id": flow_id,
            "status": "running",
            "sync_type": "bidirectional",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "source_records": 0,
            "dest_records": 0,
            "conflicts_resolved": 0,
            "records_processed": 0,
            "records_succeeded": 0,
            "records_failed": 0,
            "errors": []
        }
        
        try:
            # Read from both systems
            source_data = await source_read_func(limit=batch_size)
            dest_data = await dest_read_func(limit=batch_size)
            
            if not source_data.get("success") or not dest_data.get("success"):
                result["errors"].append("Failed to read from one or both systems")
                result["status"] = "failed"
                return result
            
            source_records = {r["id"]: r for r in source_data.get("records", []) if "id" in r}
            dest_records = {r["id"]: r for r in dest_data.get("records", []) if "id" in r}
            
            result["source_records"] = len(source_records)
            result["dest_records"] = len(dest_records)
            
            # Detect conflicts
            conflicts = conflict_resolver.detect_conflicts(source_records, dest_records)
            result["conflicts_resolved"] = len(conflicts)
            
            # Resolve conflicts and determine changes
            source_changes, dest_changes = conflict_resolver.resolve(
                source_records,
                dest_records,
                conflicts
            )
            
            # Apply changes
            if source_changes:
                source_write_result = await source_write_func(source_changes)
                if source_write_result.get("success"):
                    result["records_succeeded"] += source_write_result.get("records_written", 0)
                else:
                    result["records_failed"] += source_write_result.get("records_failed", 0)
                    result["errors"].append(source_write_result.get("error"))
            
            if dest_changes:
                dest_write_result = await dest_write_func(dest_changes)
                if dest_write_result.get("success"):
                    result["records_succeeded"] += dest_write_result.get("records_written", 0)
                else:
                    result["records_failed"] += dest_write_result.get("records_failed", 0)
                    result["errors"].append(dest_write_result.get("error"))
            
            result["records_processed"] = result["records_succeeded"] + result["records_failed"]
            result["status"] = "success" if result["records_failed"] == 0 else "partial_failure"
        
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
        
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        return result