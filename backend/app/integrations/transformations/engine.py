"""
Transformation Engine
Core engine for applying transformations to data records.
"""

from typing import Any, Optional
import re
from datetime import datetime


class TransformationEngine:
    """
    Engine for applying transformations to data records.
    Supports various transformation types including field mapping, lookups,
    calculations, validations, and more.
    """
    
    def __init__(self):
        """Initialize transformation engine."""
        self.field_mapper = FieldMapper()
        self.lookup_manager = LookupTableManager()
        self.validator = ValidationEngine()
    
    async def apply(self, record: dict[str, Any], transformation: dict[str, Any]) -> dict[str, Any]:
        """
        Apply a transformation to a record.
        
        Args:
            record: Data record to transform
            transformation: Transformation configuration
            
        Returns:
            Transformed record
        """
        transformation_type = transformation.get("transformation_type")
        config = transformation.get("transformation_config", {})
        
        if transformation_type == "field_mapping":
            return await self._apply_field_mapping(record, config)
        elif transformation_type == "lookup":
            return await self._apply_lookup(record, config)
        elif transformation_type == "calculated":
            return await self._apply_calculated(record, config)
        elif transformation_type == "validation":
            return await self._apply_validation(record, config)
        elif transformation_type == "normalization":
            return await self._apply_normalization(record, config)
        elif transformation_type == "conversion":
            return await self._apply_conversion(record, config)
        elif transformation_type == "enrichment":
            return await self._apply_enrichment(record, config)
        else:
            return record
    
    async def apply_batch(
        self,
        records: list[dict[str, Any]],
        transformations: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Apply multiple transformations to a batch of records.
        
        Args:
            records: List of data records
            transformations: List of transformation configurations
            
        Returns:
            List of transformed records
        """
        for record in records:
            for transformation in transformations:
                await self.apply(record, transformation)
        
        return records
    
    async def _apply_field_mapping(self, record: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Apply field mapping transformation."""
        source_field = config.get("source_field")
        dest_field = config.get("dest_field")
        
        if source_field and dest_field and source_field in record:
            record[dest_field] = record[source_field]
        
        return record
    
    async def _apply_lookup(self, record: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Apply lookup table transformation."""
        source_field = config.get("source_field")
        dest_field = config.get("dest_field")
        lookup_table = config.get("lookup_table", {})
        default_value = config.get("default_value")
        
        if source_field and dest_field and source_field in record:
            source_value = str(record[source_field])
            record[dest_field] = lookup_table.get(source_value, default_value or source_value)
        
        return record
    
    async def _apply_calculated(self, record: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Apply calculated field transformation."""
        expression = config.get("expression", "")
        dest_field = config.get("dest_field")
        
        if not expression or not dest_field:
            return record
        
        try:
            # Replace placeholders with actual values
            eval_expression = expression
            for key, value in record.items():
                placeholder = f"{{{key}}}"
                if isinstance(value, (int, float)):
                    eval_expression = eval_expression.replace(placeholder, str(value))
                else:
                    eval_expression = eval_expression.replace(placeholder, f'"{value}"')
            
            # Evaluate expression (safely in production)
            result = eval(eval_expression)
            record[dest_field] = result
        except Exception:
            # If calculation fails, leave field unchanged
            pass
        
        return record
    
    async def _apply_validation(self, record: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Apply validation transformation."""
        field = config.get("field")
        rules = config.get("rules", {})
        action = config.get("action", "mark_invalid")  # mark_invalid, reject, default
        
        if not field or field not in record:
            return record
        
        value = record[field]
        is_valid = True
        error_message = None
        
        # Apply validation rules
        if "required" in rules and rules["required"] and (value is None or value == ""):
            is_valid = False
            error_message = "Field is required"
        
        if "min" in rules and isinstance(value, (int, float)) and value < rules["min"]:
            is_valid = False
            error_message = f"Value must be >= {rules['min']}"
        
        if "max" in rules and isinstance(value, (int, float)) and value > rules["max"]:
            is_valid = False
            error_message = f"Value must be <= {rules['max']}"
        
        if "pattern" in rules and isinstance(value, str):
            if not re.match(rules["pattern"], value):
                is_valid = False
                error_message = f"Value does not match pattern {rules['pattern']}"
        
        if "min_length" in rules and isinstance(value, str) and len(value) < rules["min_length"]:
            is_valid = False
            error_message = f"Length must be >= {rules['min_length']}"
        
        if "max_length" in rules and isinstance(value, str) and len(value) > rules["max_length"]:
            is_valid = False
            error_message = f"Length must be <= {rules['max_length']}"
        
        if "enum" in rules and value not in rules["enum"]:
            is_valid = False
            error_message = f"Value must be one of {rules['enum']}"
        
        # Handle validation result
        if not is_valid:
            if action == "reject":
                record["_validation_error"] = error_message
                record["_is_valid"] = False
            elif action == "default" and "default" in rules:
                record[field] = rules["default"]
                record["_validation_error"] = error_message
            else:
                record["_validation_error"] = error_message
                record["_is_valid"] = False
        
        return record
    
    async def _apply_normalization(self, record: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Apply normalization transformation."""
        field = config.get("field")
        normalization_type = config.get("type", "lowercase")
        
        if not field or field not in record:
            return record
        
        value = record[field]
        
        if normalization_type == "lowercase" and isinstance(value, str):
            record[field] = value.strip().lower()
        elif normalization_type == "uppercase" and isinstance(value, str):
            record[field] = value.strip().upper()
        elif normalization_type == "title" and isinstance(value, str):
            record[field] = value.strip().title()
        elif normalization_type == "trim" and isinstance(value, str):
            record[field] = value.strip()
        elif normalization_type == "remove_special_chars" and isinstance(value, str):
            record[field] = re.sub(r'[^a-zA-Z0-9\s]', '', value)
        elif normalization_type == "remove_whitespace" and isinstance(value, str):
            record[field] = re.sub(r'\s+', ' ', value).strip()
        
        return record
    
    async def _apply_conversion(self, record: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Apply type conversion transformation."""
        field = config.get("field")
        target_type = config.get("target_type", "string")
        
        if not field or field not in record:
            return record
        
        value = record[field]
        
        try:
            if target_type == "string":
                record[field] = str(value) if value is not None else ""
            elif target_type == "integer":
                record[field] = int(float(value)) if value is not None else 0
            elif target_type == "number" or target_type == "float":
                record[field] = float(value) if value is not None else 0.0
            elif target_type == "boolean":
                if isinstance(value, str):
                    record[field] = value.lower() in ("true", "1", "yes", "on")
                else:
                    record[field] = bool(value)
            elif target_type == "date":
                if isinstance(value, str):
                    # Try common date formats
                    for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                        try:
                            record[field] = datetime.strptime(value, fmt).isoformat()
                            break
                        except ValueError:
                            continue
            elif target_type == "json":
                if isinstance(value, str):
                    import json
                    record[field] = json.loads(value)
        except Exception:
            # If conversion fails, leave unchanged
            pass
        
        return record
    
    async def _apply_enrichment(self, record: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Apply enrichment transformation."""
        enrichment_data = config.get("data", {})
        merge_strategy = config.get("merge_strategy", "merge")  # merge, overwrite, skip
        
        if merge_strategy == "merge":
            record.update(enrichment_data)
        elif merge_strategy == "overwrite":
            for key, value in enrichment_data.items():
                record[key] = value
        elif merge_strategy == "skip":
            for key, value in enrichment_data.items():
                if key not in record:
                    record[key] = value
        
        return record
    
    def get_supported_transformations(self) -> list[str]:
        """
        Get list of supported transformation types.
        
        Returns:
            List of transformation type names
        """
        return [
            "field_mapping",
            "lookup",
            "calculated",
            "validation",
            "normalization",
            "conversion",
            "enrichment"
        ]


class FieldMapper:
    """Utility class for field mapping operations."""
    
    @staticmethod
    def map_fields(record: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
        """
        Map fields from source to destination.
        
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


class LookupTableManager:
    """Manages lookup tables for transformations."""
    
    def __init__(self):
        """Initialize lookup table manager."""
        self.tables: dict[str, dict[str, Any]] = {}
    
    def register_table(self, name: str, table: dict[str, Any]) -> None:
        """
        Register a lookup table.
        
        Args:
            name: Table name
            table: Lookup table dictionary
        """
        self.tables[name] = table
    
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
    
    def get_table(self, name: str) -> dict[str, Any]:
        """
        Get a lookup table by name.
        
        Args:
            name: Table name
            
        Returns:
            Lookup table dictionary
        """
        return self.tables.get(name, {})
    
    def list_tables(self) -> list[str]:
        """
        List all registered lookup tables.
        
        Returns:
            List of table names
        """
        return list(self.tables.keys())


class ValidationEngine:
    """Engine for validating data records."""
    
    def __init__(self):
        """Initialize validation engine."""
        self.rules: dict[str, list[dict[str, Any]]] = {}
    
    def register_rules(self, entity_type: str, rules: list[dict[str, Any]]) -> None:
        """
        Register validation rules for an entity type.
        
        Args:
            entity_type: Type of entity (e.g., 'customer', 'order')
            rules: List of validation rules
        """
        self.rules[entity_type] = rules
    
    def validate(self, record: dict[str, Any], entity_type: str) -> tuple[bool, list[str]]:
        """
        Validate a record against rules.
        
        Args:
            record: Data record to validate
            entity_type: Type of entity
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        rules = self.rules.get(entity_type, [])
        errors = []
        
        for rule in rules:
            field = rule.get("field")
            if not field:
                continue
            
            value = record.get(field)
            rule_type = rule.get("type")
            
            if rule_type == "required" and (value is None or value == ""):
                errors.append(f"{field} is required")
            
            elif rule_type == "min_length" and isinstance(value, str) and len(value) < rule.get("value", 0):
                errors.append(f"{field} must be at least {rule.get('value')} characters")
            
            elif rule_type == "max_length" and isinstance(value, str) and len(value) > rule.get("value", 0):
                errors.append(f"{field} must be at most {rule.get('value')} characters")
            
            elif rule_type == "pattern" and isinstance(value, str):
                if not re.match(rule.get("value", ""), value):
                    errors.append(f"{field} format is invalid")
            
            elif rule_type == "min" and isinstance(value, (int, float)) and value < rule.get("value", 0):
                errors.append(f"{field} must be >= {rule.get('value')}")
            
            elif rule_type == "max" and isinstance(value, (int, float)) and value > rule.get("value", 0):
                errors.append(f"{field} must be <= {rule.get('value')}")
            
            elif rule_type == "enum" and value not in rule.get("values", []):
                errors.append(f"{field} must be one of {rule.get('values')}")
        
        return len(errors) == 0, errors