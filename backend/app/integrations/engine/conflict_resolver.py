"""
Conflict Resolver
Handles conflict resolution for bidirectional sync.
"""

from typing import Any, Optional
from enum import Enum


class ConflictResolutionStrategy(str, Enum):
    """Strategies for resolving conflicts."""
    SOURCE_WINS = "source_wins"
    DESTINATION_WINS = "destination_wins"
    LATEST_WINS = "latest_wins"
    MANUAL = "manual"
    SKIP = "skip"


class ConflictResolver:
    """
    Resolves conflicts between source and destination records
    during bidirectional synchronization.
    """
    
    def __init__(self, strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.SOURCE_WINS):
        """
        Initialize conflict resolver.
        
        Args:
            strategy: Default conflict resolution strategy
        """
        self.strategy = strategy
        self.conflict_fields = ["updated_at", "modified_at", "last_modified"]
    
    def detect_conflicts(
        self,
        source_records: dict[str, dict[str, Any]],
        dest_records: dict[str, dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Detect conflicts between source and destination records.
        
        Args:
            source_records: Dictionary of source records (keyed by ID)
            dest_records: Dictionary of destination records (keyed by ID)
            
        Returns:
            List of conflicts
        """
        conflicts = []
        
        # Find records that exist in both systems
        common_ids = set(source_records.keys()) & set(dest_records.keys())
        
        for record_id in common_ids:
            source = source_records[record_id]
            dest = dest_records[record_id]
            
            # Check for conflicts
            conflict_fields = self._find_conflicting_fields(source, dest)
            
            if conflict_fields:
                conflicts.append({
                    "record_id": record_id,
                    "source": source,
                    "destination": dest,
                    "conflicting_fields": conflict_fields,
                    "resolved": False
                })
        
        return conflicts
    
    def _find_conflicting_fields(
        self,
        source: dict[str, Any],
        dest: dict[str, Any]
    ) -> list[str]:
        """
        Find fields with conflicting values.
        
        Args:
            source: Source record
            dest: Destination record
            
        Returns:
            List of conflicting field names
        """
        conflicts = []
        
        for field in self.conflict_fields:
            source_value = source.get(field)
            dest_value = dest.get(field)
            
            if source_value != dest_value and source_value is not None and dest_value is not None:
                conflicts.append(field)
        
        return conflicts
    
    def resolve(
        self,
        source_records: dict[str, dict[str, Any]],
        dest_records: dict[str, dict[str, Any]],
        conflicts: list[dict[str, Any]],
        strategy: Optional[ConflictResolutionStrategy] = None
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Resolve conflicts and determine which records to update.
        
        Args:
            source_records: Source records
            dest_records: Destination records
            conflicts: List of detected conflicts
            strategy: Override default strategy
            
        Returns:
            Tuple of (source_changes, dest_changes)
        """
        strategy = strategy or self.strategy
        
        source_changes = []
        dest_changes = []
        
        for conflict in conflicts:
            record_id = conflict["record_id"]
            source = conflict["source"]
            dest = conflict["destination"]
            
            resolved_source, resolved_dest = self._resolve_single_conflict(
                record_id,
                source,
                dest,
                strategy
            )
            
            if resolved_source:
                source_changes.append(resolved_source)
            if resolved_dest:
                dest_changes.append(resolved_dest)
            
            conflict["resolved"] = True
            conflict["resolution_strategy"] = strategy.value
        
        # Find records only in source (add to destination)
        source_only_ids = set(source_records.keys()) - set(dest_records.keys())
        for record_id in source_only_ids:
            source_changes.append(source_records[record_id])
        
        # Find records only in destination (add to source)
        dest_only_ids = set(dest_records.keys()) - set(source_records.keys())
        for record_id in dest_only_ids:
            dest_changes.append(dest_records[record_id])
        
        return source_changes, dest_changes
    
    def _resolve_single_conflict(
        self,
        record_id: str,
        source: dict[str, Any],
        dest: dict[str, Any],
        strategy: ConflictResolutionStrategy
    ) -> tuple[Optional[dict[str, Any]], Optional[dict[str, Any]]]:
        """
        Resolve a single conflict.
        
        Args:
            record_id: Record ID
            source: Source record
            dest: Destination record
            strategy: Resolution strategy
            
        Returns:
            Tuple of (source_change, dest_change)
        """
        if strategy == ConflictResolutionStrategy.SOURCE_WINS:
            # Source wins - update destination with source
            return None, source
        
        elif strategy == ConflictResolutionStrategy.DESTINATION_WINS:
            # Destination wins - update source with destination
            return dest, None
        
        elif strategy == ConflictResolutionStrategy.LATEST_WINS:
            # Latest modified wins
            source_modified = source.get("updated_at") or source.get("modified_at") or ""
            dest_modified = dest.get("updated_at") or dest.get("modified_at") or ""
            
            if source_modified > dest_modified:
                return None, source
            elif dest_modified > source_modified:
                return dest, None
            else:
                # Same timestamp, source wins
                return None, source
        
        elif strategy == ConflictResolutionStrategy.MANUAL:
            # Mark for manual resolution
            return None, None
        
        elif strategy == ConflictResolutionStrategy.SKIP:
            # Skip the conflict
            return None, None
        
        return None, None
    
    def get_conflict_summary(self, conflicts: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Get summary of conflicts.
        
        Args:
            conflicts: List of conflicts
            
        Returns:
            Summary dictionary
        """
        return {
            "total_conflicts": len(conflicts),
            "resolved": sum(1 for c in conflicts if c.get("resolved", False)),
            "unresolved": sum(1 for c in conflicts if not c.get("resolved", False)),
            "by_strategy": self._count_by_strategy(conflicts)
        }
    
    def _count_by_strategy(self, conflicts: list[dict[str, Any]]) -> dict[str, int]:
        """Count conflicts by resolution strategy."""
        counts = {}
        for conflict in conflicts:
            strategy = conflict.get("resolution_strategy", "unresolved")
            counts[strategy] = counts.get(strategy, 0) + 1
        return counts