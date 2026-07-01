"""
Validators
Data validation utilities for integration records.
"""

import re
from typing import Any, Optional
from datetime import datetime


class ValidationEngine:
    """
    Engine for validating data records.
    Provides rule-based validation with customizable rules and actions.
    """
    
    def __init__(self):
        """Initialize validation engine."""
        self.rules: dict[str, list[dict[str, Any]]] = {}
        self.validators: dict[str, callable] = {
            "required": self._validate_required,
            "min_length": self._validate_min_length,
            "max_length": self._validate_max_length,
            "pattern": self._validate_pattern,
            "min": self._validate_min,
            "max": self._validate_max,
            "enum": self._validate_enum,
            "email": self._validate_email,
            "url": self._validate_url,
            "date": self._validate_date,
            "number": self._validate_number,
            "integer": self._validate_integer,
            "boolean": self._validate_boolean,
            "json": self._validate_json,
            "custom": self._validate_custom,
        }
    
    def register_rules(self, entity_type: str, rules: list[dict[str, Any]]) -> None:
        """
        Register validation rules for an entity type.
        
        Args:
            entity_type: Type of entity (e.g., 'customer', 'order')
            rules: List of validation rules
        """
        self.rules[entity_type] = rules
    
    def add_rule(self, entity_type: str, rule: dict[str, Any]) -> None:
        """
        Add a single validation rule.
        
        Args:
            entity_type: Type of entity
            rule: Validation rule
        """
        if entity_type not in self.rules:
            self.rules[entity_type] = []
        self.rules[entity_type].append(rule)
    
    def validate(
        self,
        record: dict[str, Any],
        entity_type: str,
        strict: bool = False
    ) -> tuple[bool, list[str], list[dict[str, Any]]]:
        """
        Validate a record against registered rules.
        
        Args:
            record: Data record to validate
            entity_type: Type of entity
            strict: If True, stop on first error
            
        Returns:
            Tuple of (is_valid, list of error messages, list of field errors)
        """
        rules = self.rules.get(entity_type, [])
        errors = []
        field_errors = []
        
        for rule in rules:
            field = rule.get("field")
            if not field:
                continue
            
            value = record.get(field)
            rule_type = rule.get("type")
            validator_func = self.validators.get(rule_type)
            
            if validator_func:
                is_valid, error_msg = validator_func(value, rule)
                
                if not is_valid:
                    errors.append(error_msg)
                    field_errors.append({
                        "field": field,
                        "rule": rule_type,
                        "message": error_msg,
                        "value": value
                    })
                    
                    if strict:
                        break
        
        return len(errors) == 0, errors, field_errors
    
    def validate_batch(
        self,
        records: list[dict[str, Any]],
        entity_type: str
    ) -> dict[str, Any]:
        """
        Validate a batch of records.
        
        Args:
            records: List of data records
            entity_type: Type of entity
            
        Returns:
            Validation summary
        """
        results = {
            "total": len(records),
            "valid": 0,
            "invalid": 0,
            "errors": []
        }
        
        for i, record in enumerate(records):
            is_valid, errors, field_errors = self.validate(record, entity_type)
            
            if is_valid:
                results["valid"] += 1
            else:
                results["invalid"] += 1
                results["errors"].append({
                    "record_index": i,
                    "errors": errors,
                    "field_errors": field_errors
                })
        
        return results
    
    def _validate_required(self, value: Any, rule: dict[str, Any]) -> tuple[bool, str]:
        """Validate required field."""
        if value is None or value == "" or (isinstance(value, list) and len(value) == 0):
            return False, rule.get("message", "Field is required")
        return True, ""
    
    def _validate_min_length(self, value: Any, rule: dict[str, Any]) -> tuple[bool, str]:
        """Validate minimum length."""
        min_length = rule.get("value", 0)
        if isinstance(value, str) and len(value) < min_length:
            return False, rule.get("message", f"Length must be >= {min_length}")
        return True, ""
    
    def _validate_max_length(self, value: Any, rule: dict[str, Any]) -> tuple[bool, str]:
        """Validate maximum length."""
        max_length = rule.get("value", 0)
        if isinstance(value, str) and len(value) > max_length:
            return False, rule.get("message", f"Length must be <= {max_length}")
        return True, ""
    
    def _validate_pattern(self, value: Any, rule: dict[str, Any]) -> tuple[bool, str]:
        """Validate against regex pattern."""
        pattern = rule.get("value", "")
        if isinstance(value, str) and pattern:
            if not re.match(pattern, value):
                return False, rule.get("message", f"Value does not match pattern {pattern}")
        return True, ""
    
    def _validate_min(self, value: Any, rule: dict[str, Any]) -> tuple[bool, str]:
        """Validate minimum value."""
        min_value = rule.get("value", 0)
        if isinstance(value, (int, float)) and value < min_value:
            return False, rule.get("message", f"Value must be >= {min_value}")
        return True, ""
    
    def _validate_max(self, value: Any, rule: dict[str, Any]) -> tuple[bool, str]:
        """Validate maximum value."""
        max_value = rule.get("value", 0)
        if isinstance(value, (int, float)) and value > max_value:
            return False, rule.get("message", f"Value must be <= {max_value}")
        return True, ""
    
    def _validate_enum(self, value: Any, rule: dict[str, Any]) -> tuple[bool, str]:
        """Validate against enum values."""
        allowed_values = rule.get("values", [])
        if value not in allowed_values:
            return False, rule.get("message", f"Value must be one of {allowed_values}")
        return True, ""
    
    def _validate_email(self, value: Any, rule: dict[str, Any]) -> tuple[bool, str]:
        """Validate email format."""
        if isinstance(value, str) and value:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, value):
                return False, rule.get("message", "Invalid email format")
        return True, ""
    
    def _validate_url(self, value: Any, rule: dict[str, Any]) -> tuple[bool, str]:
        """Validate URL format."""
        if isinstance(value, str) and value:
            pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
            if not re.match(pattern, value):
                return False, rule.get("message", "Invalid URL format")
        return True, ""
    
    def _validate_date(self, value: Any, rule: dict[str, Any]) -> tuple[bool, str]:
        """Validate date format."""
        if isinstance(value, str) and value:
            formats = rule.get("formats", ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"])
            for fmt in formats:
                try:
                    datetime.strptime(value, fmt)
                    return True, ""
                except ValueError:
                    continue
            return False, rule.get("message", "Invalid date format")
        return True, ""
    
    def _validate_number(self, value: Any, rule: dict[str, Any]) -> tuple[bool, str]:
        """Validate numeric value."""
        if value is not None and value != "":
            try:
                float(value)
            except (ValueError, TypeError):
                return False, rule.get("message", "Value must be a number")
        return True, ""
    
    def _validate_integer(self, value: Any, rule: dict[str, Any]) -> tuple[bool, str]:
        """Validate integer value."""
        if value is not None and value != "":
            try:
                int(value)
            except (ValueError, TypeError):
                return False, rule.get("message", "Value must be an integer")
        return True, ""
    
    def _validate_boolean(self, value: Any, rule: dict[str, Any]) -> tuple[bool, str]:
        """Validate boolean value."""
        if isinstance(value, str):
            if value.lower() not in ("true", "false", "1", "0", "yes", "no"):
                return False, rule.get("message", "Value must be a boolean")
        return True, ""
    
    def _validate_json(self, value: Any, rule: dict[str, Any]) -> tuple[bool, str]:
        """Validate JSON format."""
        if isinstance(value, str) and value:
            try:
                import json
                json.loads(value)
            except json.JSONDecodeError:
                return False, rule.get("message", "Invalid JSON format")
        return True, ""
    
    def _validate_custom(self, value: Any, rule: dict[str, Any]) -> tuple[bool, str]:
        """Validate using custom validator function."""
        validator_func = rule.get("validator")
        if validator_func and callable(validator_func):
            try:
                result = validator_func(value)
                if not result:
                    return False, rule.get("message", "Custom validation failed")
            except Exception as e:
                return False, f"Custom validation error: {str(e)}"
        return True, ""
    
    def get_rules(self, entity_type: str) -> list[dict[str, Any]]:
        """
        Get rules for an entity type.
        
        Args:
            entity_type: Type of entity
            
        Returns:
            List of validation rules
        """
        return self.rules.get(entity_type, [])
    
    def remove_rules(self, entity_type: str) -> None:
        """
        Remove all rules for an entity type.
        
        Args:
            entity_type: Type of entity
        """
        if entity_type in self.rules:
            del self.rules[entity_type]
    
    def list_entity_types(self) -> list[str]:
        """
        List all entity types with registered rules.
        
        Returns:
            List of entity type names
        """
        return list(self.rules.keys())


class RecordValidator:
    """
    Validates individual records against a schema.
    """
    
    def __init__(self, schema: dict[str, Any]):
        """
        Initialize record validator.
        
        Args:
            schema: Validation schema
        """
        self.schema = schema
        self.required_fields = schema.get("required", [])
        self.properties = schema.get("properties", {})
    
    def validate(self, record: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate a record against the schema.
        
        Args:
            record: Data record to validate
            
        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []
        
        # Check required fields
        for field in self.required_fields:
            if field not in record or record[field] is None or record[field] == "":
                errors.append(f"Required field '{field}' is missing")
        
        # Validate properties
        for field, value in record.items():
            if field in self.properties:
                field_schema = self.properties[field]
                field_errors = self._validate_field(value, field_schema, field)
                errors.extend(field_errors)
        
        return len(errors) == 0, errors
    
    def _validate_field(self, value: Any, field_schema: dict[str, Any], field_name: str) -> list[str]:
        """Validate a single field."""
        errors = []
        
        # Type validation
        expected_type = field_schema.get("type")
        if expected_type and not self._check_type(value, expected_type):
            errors.append(f"Field '{field_name}' must be of type {expected_type}")
        
        # String validations
        if isinstance(value, str):
            min_length = field_schema.get("minLength")
            max_length = field_schema.get("maxLength")
            pattern = field_schema.get("pattern")
            
            if min_length and len(value) < min_length:
                errors.append(f"Field '{field_name}' must be at least {min_length} characters")
            
            if max_length and len(value) > max_length:
                errors.append(f"Field '{field_name}' must be at most {max_length} characters")
            
            if pattern and not re.match(pattern, value):
                errors.append(f"Field '{field_name}' format is invalid")
        
        # Numeric validations
        if isinstance(value, (int, float)):
            minimum = field_schema.get("minimum")
            maximum = field_schema.get("maximum")
            
            if minimum is not None and value < minimum:
                errors.append(f"Field '{field_name}' must be >= {minimum}")
            
            if maximum is not None and value > maximum:
                errors.append(f"Field '{field_name}' must be <= {maximum}")
        
        # Enum validation
        if "enum" in field_schema and value not in field_schema["enum"]:
            errors.append(f"Field '{field_name}' must be one of {field_schema['enum']}")
        
        return errors
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }
        
        expected_python_type = type_map.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True