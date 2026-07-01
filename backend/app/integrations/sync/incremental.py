"""
Incremental Sync
Handles incremental synchronization using cursors.
"""

from typing import Any, Optional
from datetime import datetime, timezone


class IncrementalSync:
    """
    Manages incremental synchronization.
    Tracks cursors to only sync changed records.
    """
    
    def __init__(self):
        """Initialize incremental sync."""
        self.cursors: dict[int, dict[str, Any]] = {}
    
    def get_cursor(self, flow_id: int, source: str) -> Optional[str]:
        """
        Get the last cursor for a flow and source.
        
        Args:
            flow_id: Integration flow ID
            source: Source identifier
            
        Returns:
            Last cursor value or None
        """
        key = f"{flow_id}:{source}"
        cursor_data = self.cursors.get(key)
        if cursor_data:
            return cursor_data.get("cursor")
        return None
    
    def save_cursor(
        self,
        flow_id: int,
        source: str,
        cursor: str,
        metadata: dict[str, Any] = None
    ) -> None:
        """
        Save a cursor for a flow and source.
        
        Args:
            flow_id: Integration flow ID
            source: Source identifier
            cursor: Cursor value
            metadata: Additional metadata
        """
        key = f"{flow_id}:{source}"
        self.cursors[key] = {
            "cursor": cursor,
            "metadata": metadata or {},
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    
    def build_incremental_query(
        self,
        base_query: dict[str, Any],
        cursor_field: str,
        last_cursor: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Build a query for incremental sync.
        
        Args:
            base_query: Base query parameters
            cursor_field: Field to use as cursor
            last_cursor: Last cursor value
            
        Returns:
            Updated query with cursor filter
        """
        query = base_query.copy()
        
        if last_cursor:
            query[f"{cursor_field}__gt"] = last_cursor
        
        # Sort by cursor field to ensure consistent ordering
        query["order_by"] = cursor_field
        
        return query
    
    def extract_cursor(
        self,
        record: dict[str, Any],
        cursor_field: str
    ) -> Optional[str]:
        """
        Extract cursor value from a record.
        
        Args:
            record: Data record
            cursor_field: Field to use as cursor
            
        Returns:
            Cursor value or None
        """
        return record.get(cursor_field)
    
    def update_cursor_from_batch(
        self,
        records: list[dict[str, Any]],
        cursor_field: str,
        current_cursor: Optional[str] = None
    ) -> str:
        """
        Update cursor based on a batch of records.
        
        Args:
            records: List of records
            cursor_field: Field to use as cursor
            current_cursor: Current cursor value
            
        Returns:
            New cursor value
        """
        if not records:
            return current_cursor or ""
        
        # Find the maximum cursor value in the batch
        max_cursor = current_cursor
        
        for record in records:
            cursor_value = self.extract_cursor(record, cursor_field)
            if cursor_value and (max_cursor is None or cursor_value > max_cursor):
                max_cursor = cursor_value
        
        return max_cursor or ""
    
    def get_cursor_history(self, flow_id: int, source: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get cursor history for a flow and source.
        
        Args:
            flow_id: Integration flow ID
            source: Source identifier
            limit: Maximum number of records
            
        Returns:
            List of cursor history entries
        """
        key = f"{flow_id}:{source}"
        cursor_data = self.cursors.get(key)
        
        if not cursor_data:
            return []
        
        # In a real implementation, this would query a database
        # For now, return the current cursor data
        return [cursor_data]
    
    def clear_cursor(self, flow_id: int, source: str) -> bool:
        """
        Clear cursor for a flow and source.
        
        Args:
            flow_id: Integration flow ID
            source: Source identifier
            
        Returns:
            True if cleared, False if not found
        """
        key = f"{flow_id}:{source}"
        if key in self.cursors:
            del self.cursors[key]
            return True
        return False
    
    def clear_all_cursors(self, flow_id: int) -> int:
        """
        Clear all cursors for a flow.
        
        Args:
            flow_id: Integration flow ID
            
        Returns:
            Number of cursors cleared
        """
        keys_to_remove = [key for key in self.cursors.keys() if key.startswith(f"{flow_id}:")]
        
        for key in keys_to_remove:
            del self.cursors[key]
        
        return len(keys_to_remove)
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about incremental sync.
        
        Returns:
            Statistics dictionary
        """
        return {
            "total_cursors": len(self.cursors),
            "cursors": [
                {
                    "flow_id": key.split(":")[0],
                    "source": key.split(":")[1],
                    "cursor": data.get("cursor"),
                    "updated_at": data.get("updated_at")
                }
                for key, data in self.cursors.items()
            ]
        }