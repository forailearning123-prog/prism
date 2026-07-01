"""
GraphQL Connector
Generic connector for GraphQL APIs.
"""

from typing import Any
import httpx

from ..base import BaseConnector, ConnectorCapabilities, ReadResult, WriteResult, ConnectionTestResult, HealthCheckResult
from app.integrations.exceptions import ConnectionError


class GraphQLConnector(BaseConnector):
    """
    Generic GraphQL connector.
    Supports any GraphQL API with configurable authentication.
    """
    
    def __init__(self, config: dict[str, Any], auth_config: dict[str, Any]):
        """
        Initialize GraphQL connector.
        
        Args:
            config: Configuration with endpoint, queries, etc.
            auth_config: Authentication configuration
        """
        super().__init__(config, auth_config)
        self.client = None
        self.endpoint = config.get("endpoint", "")
        self.timeout = config.get("timeout_seconds", 30)
    
    async def connect(self) -> None:
        """Establish connection by initializing HTTP client."""
        try:
            self.client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._get_auth_headers()
            )
            self._set_connected(True)
        except Exception as e:
            raise ConnectionError(f"Failed to initialize GraphQL client: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
        self._set_connected(False)
    
    async def test_connection(self) -> ConnectionTestResult:
        """
        Test connection by running introspection query.
        
        Returns:
            ConnectionTestResult
        """
        try:
            introspection_query = """
            {
                __schema {
                    queryType {
                        name
                    }
                }
            }
            """
            
            response = await self._execute_query(introspection_query)
            
            if response.get("data"):
                return ConnectionTestResult(
                    success=True,
                    message="GraphQL connection successful",
                    details={"schema": response["data"]}
                )
            else:
                return ConnectionTestResult(
                    success=False,
                    message="Failed to introspect GraphQL schema"
                )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"Connection failed: {str(e)}"
            )
    
    async def health_check(self) -> HealthCheckResult:
        """
        Perform health check.
        
        Returns:
            HealthCheckResult
        """
        import time
        start = time.time()
        
        try:
            result = await self.test_connection()
            response_time = int((time.time() - start) * 1000)
            
            if result.success:
                return HealthCheckResult(
                    status="healthy",
                    response_time_ms=response_time,
                    message="GraphQL API is healthy"
                )
            else:
                return HealthCheckResult(
                    status="failed",
                    response_time_ms=response_time,
                    message=result.message
                )
        except Exception as e:
            return HealthCheckResult(
                status="failed",
                response_time_ms=0,
                message=str(e)
            )
    
    async def read(
        self,
        source: str,
        fields: list[str] = None,
        filter: dict = None,
        limit: int = 1000,
        offset: int = 0,
        **kwargs
    ) -> ReadResult:
        """
        Read data using GraphQL query.
        
        Args:
            source: GraphQL query name or custom query
            fields: Fields to select
            filter: Filter arguments
            limit: Maximum records
            offset: Offset for pagination
            **kwargs: Additional parameters
            
        Returns:
            ReadResult
        """
        try:
            # Build GraphQL query
            if source.startswith("{"):
                # Custom query provided
                query = source
            else:
                # Build query from parameters
                field_list = ", ".join(fields) if fields else "*"
                filter_args = self._build_filter_args(filter) if filter else ""
                pagination = f"limit: {limit}, offset: {offset}" if limit > 0 else ""
                
                args = ", ".join(filter(filter_args, pagination))
                args_str = f"({args})" if args else ""
                
                query = f"""
                {{
                    {source}{args_str} {{
                        {field_list}
                    }}
                }}
                """
            
            response = await self._execute_query(query)
            
            if "errors" in response:
                return ReadResult(
                    success=False,
                    records=[],
                    total_count=0,
                    has_more=False,
                    error=f"GraphQL errors: {response['errors']}"
                )
            
            data = response.get("data", {})
            records = self._extract_records(data, source)
            
            return ReadResult(
                success=True,
                records=records,
                total_count=len(records),
                has_more=False,
                metadata={"query": query}
            )
            
        except Exception as e:
            return ReadResult(
                success=False,
                records=[],
                total_count=0,
                has_more=False,
                error=str(e)
            )
    
    async def write(
        self,
        destination: str,
        records: list[dict],
        mode: str = "upsert",
        **kwargs
    ) -> WriteResult:
        """
        Write data using GraphQL mutation.
        
        Args:
            destination: GraphQL mutation name
            records: Records to write
            mode: Write mode (insert, update, upsert)
            **kwargs: Additional parameters
            
        Returns:
            WriteResult
        """
        try:
            mutation_name = kwargs.get("mutation_name", f"{destination.capitalize()}Mutation")
            
            # Build mutation
            mutations = []
            for record in records:
                input_args = ", ".join([f'{k}: "{v}"' if isinstance(v, str) else f"{k}: {v}" for k, v in record.items()])
                mutations.append(f"{mutation_name}(input: {{{input_args}}}) {{ id success }}")
            
            query = f"""
            mutation {{
                {mutations[0] if len(records) == 1 else ""}
            }}
            """
            
            response = await self._execute_query(query)
            
            if "errors" in response:
                return WriteResult(
                    success=False,
                    records_written=0,
                    records_failed=len(records),
                    error=f"GraphQL errors: {response['errors']}"
                )
            
            return WriteResult(
                success=True,
                records_written=len(records),
                records_failed=0,
                metadata={"mutation": mutation_name}
            )
            
        except Exception as e:
            return WriteResult(
                success=False,
                records_written=0,
                records_failed=len(records),
                error=str(e)
            )
    
    async def _execute_query(self, query: str, variables: dict = None) -> dict:
        """
        Execute a GraphQL query.
        
        Args:
            query: GraphQL query string
            variables: Query variables
            
        Returns:
            Response data
        """
        if not self.client:
            await self.connect()
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        response = await self.client.post(self.endpoint, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def _build_filter_args(self, filter: dict) -> str:
        """Build GraphQL filter arguments from dictionary."""
        args = []
        for key, value in filter.items():
            if isinstance(value, str):
                args.append(f'{key}: "{value}"')
            elif isinstance(value, bool):
                args.append(f"{key}: {str(value).lower()}")
            elif value is not None:
                args.append(f"{key}: {value}")
        return ", ".join(args)
    
    def _extract_records(self, data: dict, source: str) -> list[dict]:
        """Extract records from GraphQL response."""
        if not data:
            return []
        
        # Get the data for the requested source
        source_data = data.get(source, data)
        
        if isinstance(source_data, list):
            return source_data
        elif isinstance(source_data, dict):
            # Try to find list in response
            for key, value in source_data.items():
                if isinstance(value, list):
                    return value
            return [source_data]
        
        return []
    
    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers."""
        from app.integrations.connectors.auth import (
            ApiKeyAuthHandler,
            BearerTokenHandler,
            BasicAuthHandler
        )
        
        auth_type = self.auth_config.get("type", "none")
        
        if auth_type == "api_key":
            handler = ApiKeyAuthHandler(
                self.auth_config.get("api_key", ""),
                self.auth_config.get("header_name", "X-API-Key")
            )
            return handler.get_headers()
        elif auth_type == "bearer":
            handler = BearerTokenHandler(self.auth_config.get("token", ""))
            return handler.get_headers()
        elif auth_type == "basic":
            handler = BasicAuthHandler(
                self.auth_config.get("username", ""),
                self.auth_config.get("password", "")
            )
            return handler.get_headers()
        
        return {}
    
    async def get_capabilities(self) -> ConnectorCapabilities:
        """Return GraphQL connector capabilities."""
        return ConnectorCapabilities(
            supports_batch_operations=True,
            max_batch_size=self.config.get("max_batch_size", 100),
            supported_auth_types=["api_key", "bearer", "basic", "oauth2"],
            supported_operations=["read", "write"]
        )