"""
Field Mapper
Utilities for mapping fields between different data formats.
"""

from typing import Any, Optional


class FieldMapper:
    """
    Utility class for field mapping operations.
    Provides methods to map, rename, and transform fields between systems.
    """
    
    @staticmethod
    def map_fields(record: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
        """
        Map fields from source to destination format.
        
        Args:
            record: Source record
            mapping: Dictionary mapping source fields to destination fields
            
        Returns:
            Record with mapped fields
        """
        mapped = {}
        
        for source_field, dest_field in mapping.items():
            if source_field in record:
                mapped[dest_field] = record[source_field]
        
        return mapped
    
    @staticmethod
    def rename_field(record: dict[str, Any], old_name: str, new_name: str) -> dict[str, Any]:
        """
        Rename a field in a record.
        
        Args:
            record: Data record
            old_name: Current field name
            new_name: New field name
            
        Returns:
            Record with renamed field
        """
        if old_name in record:
            record[new_name] = record.pop(old_name)
        return record
    
    @staticmethod
    def remove_fields(record: dict[str, Any], fields: list[str]) -> dict[str, Any]:
        """
        Remove fields from a record.
        
        Args:
            record: Data record
            fields: List of field names to remove
            
        Returns:
            Record with fields removed
        """
        for field in fields:
            record.pop(field, None)
        return record
    
    @staticmethod
    def keep_fields(record: dict[str, Any], fields: list[str]) -> dict[str, Any]:
        """
        Keep only specified fields in a record.
        
        Args:
            record: Data record
            fields: List of field names to keep
            
        Returns:
            Record with only specified fields
        """
        return {key: value for key, value in record.items() if key in fields}
    
    @staticmethod
    def flatten_record(record: dict[str, Any], separator: str = "_") -> dict[str, Any]:
        """
        Flatten a nested record.
        
        Args:
            record: Nested data record
            separator: Separator for nested field names
            
        Returns:
            Flattened record
        """
        flattened = {}
        
        def flatten(obj: Any, prefix: str = ""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{prefix}{separator}{key}" if prefix else key
                    flatten(value, new_key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_key = f"{prefix}{separator}{i}" if prefix else str(i)
                    flatten(item, new_key)
            else:
                flattened[prefix] = obj
        
        flatten(record)
        return flattened
    
    @staticmethod
    def nest_record(record: dict[str, Any], nesting_rules: dict[str, list[str]]) -> dict[str, Any]:
        """
        Nest fields based on rules.
        
        Args:
            record: Flat data record
            nesting_rules: Dictionary mapping parent fields to lists of child fields
            
        Returns:
            Nested record
        """
        nested = record.copy()
        
        for parent_field, child_fields in nesting_rules.items():
            if parent_field not in nested:
                nested[parent_field] = {}
            
            for child_field in child_fields:
                if child_field in nested:
                    nested[parent_field][child_field] = nested.pop(child_field)
        
        return nested
    
    @staticmethod
    def apply_defaults(record: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
        """
        Apply default values for missing fields.
        
        Args:
            record: Data record
            defaults: Dictionary of default values
            
        Returns:
            Record with defaults applied
        """
        for field, default_value in defaults.items():
            if field not in record or record[field] is None:
                record[field] = default_value
        
        return record
    
    @staticmethod
    def transform_field_names(
        record: dict[str, Any],
        transform_func
    ) -> dict[str, Any]:
        """
        Transform field names using a function.
        
        Args:
            record: Data record
            transform_func: Function to transform field names
            
        Returns:
            Record with transformed field names
        """
        return {transform_func(key): value for key, value in record.items()}
    
    @staticmethod
    def to_camel_case(record: dict[str, Any]) -> dict[str, Any]:
        """
        Convert field names to camelCase.
        
        Args:
            record: Data record with snake_case fields
            
        Returns:
            Record with camelCase fields
        """
        def to_camel(snake_str: str) -> str:
            components = snake_str.split("_")
            return components[0] + "".join(x.title() for x in components[1:])
        
        return FieldMapper.transform_field_names(record, to_camel)
    
    @staticmethod
    def to_snake_case(record: dict[str, Any]) -> dict[str, Any]:
        """
        Convert field names to snake_case.
        
        Args:
            record: Data record with camelCase fields
            
        Returns:
            Record with snake_case fields
        """
        import re
        
        def to_snake(camel_str: str) -> str:
            s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", camel_str)
            return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
        
        return FieldMapper.transform_field_names(record, to_snake_case)
    
    @staticmethod
    def to_pascal_case(record: dict[str, Any]) -> dict[str, Any]:
        """
        Convert field names to PascalCase.
        
        Args:
            record: Data record
            
        Returns:
            Record with PascalCase fields
        """
        def to_pascal(snake_str: str) -> str:
            components = snake_str.split("_")
            return "".join(x.title() for x in components)
        
        return FieldMapper.transform_field_names(record, to_pascal)
    
    @staticmethod
    def merge_records(
        base: dict[str, Any],
        override: dict[str, Any],
        strategy: str = "override"
    ) -> dict[str, Any]:
        """
        Merge two records.
        
        Args:
            base: Base record
            override: Override record
            strategy: Merge strategy (override, skip, combine)
            
        Returns:
            Merged record
        """
        merged = base.copy()
        
        for key, value in override.items():
            if strategy == "override":
                merged[key] = value
            elif strategy == "skip":
                if key not in merged:
                    merged[key] = value
            elif strategy == "combine":
                if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key] = FieldMapper.merge_records(merged[key], value, strategy)
                else:
                    merged[key] = value
        
        return merged