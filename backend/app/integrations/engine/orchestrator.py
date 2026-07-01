"""
Integration Orchestrator
Coordinates the execution of integration flows.
"""

from typing import Any, Optional
import asyncio
from datetime import datetime, timezone

from app.integrations.connectors.registry import connector_registry
from app.integrations.secrets.manager import SecretsManager
from app.integrations.exceptions import IntegrationError


class IntegrationOrchestrator:
    """
    Orchestrates integration flow execution.
    Manages connector lifecycle, data flow, and error handling.
    """
    
    def __init__(self, secrets_manager: Optional[SecretsManager] = None):
        """
        Initialize orchestrator.
        
        Args:
            secrets_manager: Secrets manager for credential decryption
        """
        self.secrets_manager = secrets_manager or SecretsManager()
        self._active_flows: dict[int, Any] = {}
    
    async def execute_flow(
        self,
        flow_id: int,
        source_config: dict[str, Any],
        dest_config: dict[str, Any],
        mappings: list[dict[str, Any]],
        transformations: list[dict[str, Any]] = None,
        batch_size: int = 1000,
        **kwargs
    ) -> dict[str, Any]:
        """
        Execute an integration flow.
        
        Args:
            flow_id: Integration flow ID
            source_config: Source connector configuration
            dest_config: Destination connector configuration
            mappings: Data mappings
            transformations: Transformation rules
            batch_size: Number of records per batch
            **kwargs: Additional execution parameters
            
        Returns:
            Execution result dictionary
        """
        result = {
            "flow_id": flow_id,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "records_processed": 0,
            "records_succeeded": 0,
            "records_failed": 0,
            "errors": []
        }
        
        try:
            # Get connector instances
            source_connector = self._get_connector(source_config)
            dest_connector = self._get_connector(dest_config)
            
            # Connect to both systems
            async with source_connector, dest_connector:
                # Read from source
                read_result = await source_connector.read(
                    source=source_config.get("source", ""),
                    limit=batch_size,
                    **kwargs
                )
                
                if not read_result.success:
                    raise IntegrationError(f"Source read failed: {read_result.error}")
                
                records = read_result.records
                result["records_processed"] = len(records)
                
                # Apply transformations
                if transformations:
                    records = await self._apply_transformations(records, transformations)
                
                # Apply data mappings
                records = await self._apply_mappings(records, mappings)
                
                # Write to destination
                write_result = await dest_connector.write(
                    destination=dest_config.get("destination", ""),
                    records=records,
                    mode=kwargs.get("write_mode", "upsert")
                )
                
                if write_result.success:
                    result["records_succeeded"] = write_result.records_written
                    result["status"] = "success"
                else:
                    result["records_failed"] = write_result.records_failed
                    result["errors"].append(write_result.error)
                    result["status"] = "partial_failure"
        
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
        
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        return result
    
    def _get_connector(self, config: dict[str, Any]):
        """
        Get connector instance from configuration.
        
        Args:
            config: Connector configuration
            
        Returns:
            Connector instance
        """
        connector_name = config.get("connector_name")
        if not connector_name:
            raise ValueError("connector_name is required in configuration")
        
        # Decrypt credentials
        encrypted_credentials = config.get("encrypted_credentials")
        if encrypted_credentials:
            auth_config = self.secrets_manager.decrypt_credentials(encrypted_credentials)
        else:
            auth_config = config.get("auth_config", {})
        
        # Get connector config
        connector_config = config.get("connector_config", {})
        
        # Create connector instance
        return connector_registry.create_instance(
            name=connector_name,
            config=connector_config,
            auth_config=auth_config
        )
    
    async def _apply_transformations(
        self,
        records: list[dict[str, Any]],
        transformations: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Apply transformations to records.
        
        Args:
            records: List of records
            transformations: List of transformation rules
            
        Returns:
            Transformed records
        """
        from app.integrations.transformations.engine import TransformationEngine
        
        engine = TransformationEngine()
        
        for record in records:
            for transformation in transformations:
                await engine.apply(record, transformation)
        
        return records
    
    async def _apply_mappings(
        self,
        records: list[dict[str, Any]],
        mappings: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Apply field mappings to records.
        
        Args:
            records: List of records
            mappings: List of field mappings
            
        Returns:
            Mapped records
        """
        mapped_records = []
        
        for record in records:
            mapped = {}
            
            for mapping in mappings:
                source_field = mapping.get("source_field")
                dest_field = mapping.get("destination_field")
                transformation_type = mapping.get("transformation_type")
                transformation_config = mapping.get("transformation_config", {})
                default_value = mapping.get("default_value")
                
                # Get value from source
                value = record.get(source_field)
                
                # Apply transformation
                if value is not None and transformation_type != "field_mapping":
                    value = await self._transform_value(value, transformation_type, transformation_config)
                
                # Use default if value is None
                if value is None and default_value is not None:
                    value = default_value
                
                # Set in destination
                if value is not None:
                    mapped[dest_field] = value
            
            mapped_records.append(mapped)
        
        return mapped_records
    
    async def _transform_value(
        self,
        value: Any,
        transformation_type: str,
        config: dict[str, Any]
    ) -> Any:
        """
        Transform a single value.
        
        Args:
            value: Value to transform
            transformation_type: Type of transformation
            config: Transformation configuration
            
        Returns:
            Transformed value
        """
        if transformation_type == "lookup":
            lookup_table = config.get("lookup_table", {})
            return lookup_table.get(str(value), value)
        
        elif transformation_type == "calculated":
            expression = config.get("expression", "")
            # Simple expression evaluation (in production, use a proper expression engine)
            try:
                return eval(expression.replace("{value}", str(value)))
            except:
                return value
        
        elif transformation_type == "normalization":
            # Normalize string values
            if isinstance(value, str):
                return value.strip().lower()
            return value
        
        elif transformation_type == "conversion":
            # Type conversion
            target_type = config.get("target_type", "string")
            try:
                if target_type == "string":
                    return str(value)
                elif target_type == "number":
                    return float(value)
                elif target_type == "integer":
                    return int(value)
                elif target_type == "boolean":
                    return bool(value)
            except:
                return value
        
        elif transformation_type == "validation":
            # Validation (returns value if valid, None otherwise)
            rules = config.get("rules", {})
            min_val = rules.get("min")
            max_val = rules.get("max")
            pattern = rules.get("pattern")
            
            if min_val is not None and isinstance(value, (int, float)) and value < min_val:
                return None
            if max_val is not None and isinstance(value, (int, float)) and value > max_val:
                return None
            if pattern and isinstance(value, str):
                import re
                if not re.match(pattern, value):
                    return None
            
            return value
        
        elif transformation_type == "enrichment":
            # Enrich with additional data
            enrichment_data = config.get("enrichment_data", {})
            if isinstance(value, dict):
                value.update(enrichment_data)
            return value
        
        return value
    
    async def test_connection(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Test a connector connection.
        
        Args:
            config: Connector configuration
            
        Returns:
            Test result
        """
        try:
            connector = self._get_connector(config)
            async with connector:
                result = await connector.test_connection()
                return {
                    "success": result.success,
                    "message": result.message,
                    "details": result.details
                }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "details": {}
            }
    
    async def health_check(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Perform health check on a connector.
        
        Args:
            config: Connector configuration
            
        Returns:
            Health check result
        """
        try:
            connector = self._get_connector(config)
            async with connector:
                result = await connector.health_check()
                return {
                    "status": result.status,
                    "response_time_ms": result.response_time_ms,
                    "message": result.message,
                    "details": result.details
                }
        except Exception as e:
            return {
                "status": "failed",
                "response_time_ms": 0,
                "message": str(e),
                "details": {}
            }