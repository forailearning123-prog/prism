"""
Lookup Tables
Manages lookup tables for data transformations.
"""

from typing import Any, Optional
import json


class LookupTableManager:
    """
    Manages lookup tables for transformations.
    Provides in-memory and persistent lookup table storage.
    """
    
    def __init__(self):
        """Initialize lookup table manager."""
        self.tables: dict[str, dict[str, Any]] = {}
        self.metadata: dict[str, dict[str, Any]] = {}
    
    def register_table(
        self,
        name: str,
        table: dict[str, Any],
        metadata: dict[str, Any] = None
    ) -> None:
        """
        Register a lookup table.
        
        Args:
            name: Table name
            table: Lookup table dictionary
            metadata: Optional metadata (description, version, etc.)
        """
        self.tables[name] = table
        self.metadata[name] = metadata or {}
    
    def lookup(self, table_name: str, key: str, default: Any = None) -> Any:
        """
        Perform a lookup in a table.
        
        Args:
            table_name: Name of the lookup table
            key: Key to look up
            default: Default value if key not found
            
        Returns:
            Looked up value or default
        """
        table = self.tables.get(table_name, {})
        return table.get(str(key), default)
    
    def lookup_multiple(
        self,
        table_name: str,
        keys: list[str],
        default: Any = None
    ) -> list[Any]:
        """
        Perform multiple lookups in a table.
        
        Args:
            table_name: Name of the lookup table
            keys: List of keys to look up
            default: Default value if key not found
            
        Returns:
            List of looked up values
        """
        table = self.tables.get(table_name, {})
        return [table.get(str(key), default) for key in keys]
    
    def reverse_lookup(self, table_name: str, value: Any) -> Optional[str]:
        """
        Perform a reverse lookup (find key by value).
        
        Args:
            table_name: Name of the lookup table
            value: Value to search for
            
        Returns:
            Key that maps to the value, or None
        """
        table = self.tables.get(table_name, {})
        for key, val in table.items():
            if val == value:
                return key
        return None
    
    def get_table(self, name: str) -> dict[str, Any]:
        """
        Get a lookup table by name.
        
        Args:
            name: Table name
            
        Returns:
            Lookup table dictionary
        """
        return self.tables.get(name, {})
    
    def get_table_metadata(self, name: str) -> dict[str, Any]:
        """
        Get metadata for a lookup table.
        
        Args:
            name: Table name
            
        Returns:
            Metadata dictionary
        """
        return self.metadata.get(name, {})
    
    def list_tables(self) -> list[str]:
        """
        List all registered lookup tables.
        
        Returns:
            List of table names
        """
        return list(self.tables.keys())
    
    def remove_table(self, name: str) -> bool:
        """
        Remove a lookup table.
        
        Args:
            name: Table name
            
        Returns:
            True if removed, False if not found
        """
        if name in self.tables:
            del self.tables[name]
            del self.metadata[name]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all lookup tables."""
        self.tables.clear()
        self.metadata.clear()
    
    def load_from_json(self, name: str, json_data: str) -> None:
        """
        Load a lookup table from JSON string.
        
        Args:
            name: Table name
            json_data: JSON string of lookup table
        """
        table = json.loads(json_data)
        self.register_table(name, table)
    
    def export_to_json(self, name: str) -> str:
        """
        Export a lookup table to JSON string.
        
        Args:
            name: Table name
            
        Returns:
            JSON string of lookup table
        """
        table = self.tables.get(name, {})
        return json.dumps(table)
    
    def merge_tables(self, base_name: str, override_name: str, new_name: str = None) -> str:
        """
        Merge two lookup tables.
        
        Args:
            base_name: Base table name
            override_name: Override table name
            new_name: Name for merged table (defaults to base_name)
            
        Returns:
            Name of merged table
        """
        base_table = self.tables.get(base_name, {})
        override_table = self.tables.get(override_name, {})
        
        # Merge with override taking precedence
        merged = {**base_table, **override_table}
        
        new_name = new_name or base_name
        self.register_table(new_name, merged)
        
        return new_name
    
    def filter_table(
        self,
        source_name: str,
        new_name: str,
        filter_func
    ) -> str:
        """
        Create a filtered version of a lookup table.
        
        Args:
            source_name: Source table name
            new_name: New table name
            filter_func: Function that takes (key, value) and returns True to keep
            
        Returns:
            Name of filtered table
        """
        source_table = self.tables.get(source_name, {})
        filtered = {k: v for k, v in source_table.items() if filter_func(k, v)}
        
        self.register_table(new_name, filtered)
        return new_name
    
    def invert_table(self, source_name: str, new_name: str = None) -> str:
        """
        Invert a lookup table (swap keys and values).
        
        Args:
            source_name: Source table name
            new_name: New table name
            
        Returns:
            Name of inverted table
        """
        source_table = self.tables.get(source_name, {})
        inverted = {str(v): k for k, v in source_table.items()}
        
        new_name = new_name or f"{source_name}_inverted"
        self.register_table(new_name, inverted)
        
        return new_name
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about lookup tables.
        
        Returns:
            Statistics dictionary
        """
        return {
            "total_tables": len(self.tables),
            "total_entries": sum(len(table) for table in self.tables.values()),
            "tables": {
                name: {
                    "entries": len(table),
                    "metadata": self.metadata.get(name, {})
                }
                for name, table in self.tables.items()
            }
        }