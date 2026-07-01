"""
REST API Connector
Generic connector for REST APIs.
"""

from typing import Any
import httpx

from ..base import BaseConnector, ConnectorCapabilities, ReadResult, WriteResult, ConnectionTestResult, HealthCheckResult
from app.integrations.exceptions import AuthenticationError, ConnectionError


class RestApiConnector(BaseConnector):
    """
    Generic REST API connector.
    Supports any REST API with configurable authentication.
    """
    
    def __init__(self, config: dict[str, Any], auth_config: dict[str, Any]):
        """
        Initialize REST API connector.
        
        Args:
            config: Configuration with base_url, headers, etc.
            auth_config: Authentication configuration
        """
        super().__init__(config, auth_config)
        self.client = None
        self.base_url = config.get("base_url", "").rstrip("/")
        self.timeout = config.get("timeout_seconds", 30)
    
    async def connect(self) -> None:
        """Establish connection by initializing HTTP client."""
        try:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._get_auth_headers()
            )
            self._set_connected(True)
        except Exception as e:
            raise ConnectionError(f"Failed to initialize REST client: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
        self._set_connected(False)
    
    async def test_connection(self) -> ConnectionTestResult:
        """
        Test connection by making a health check request.
        
        Returns:
            ConnectionTestResult
        """
        try:
            health_endpoint = self.config.get("health_endpoint", "/health")
            
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._get_auth_headers()
            ) as client:
                response = await client.get(health_endpoint)
                response.raise_for_status()
            
            return ConnectionTestResult(
                success=True,
                message="Connection successful",
                details={"status_code": response.status_code}
            )
        except httpx.HTTPStatusError as e:
            return ConnectionTestResult(
                success=False,
                message=f"HTTP error: {e.response.status_code}",
                details={"status_code": e.response.status_code}
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
                    message="API is healthy"
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
        Read data from REST API endpoint.
        
        Args:
            source: API endpoint path
            fields: Fields to select (if supported)
            filter: Query parameters for filtering
            limit: Maximum records to return
            offset: Offset for pagination
            **kwargs: Additional parameters (method, body, etc.)
            
        Returns:
            ReadResult
        """
        if not self.client:
            await self.connect()
        
        try:
            # Build query parameters
            params = {}
            if filter:
                params.update(filter)
            
            # Add pagination
            params["limit"] = limit
            params["offset"] = offset
            
            # Make request
            method = kwargs.get("method", "GET")
            endpoint = source.lstrip("/")
            
            if method.upper() == "GET":
                response = await self.client.get(endpoint, params=params)
            elif method.upper() == "POST":
                body = kwargs.get("body", {})
                response = await self.client.post(endpoint, json=body, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, list):
                records = data
                total_count = len(data)
                has_more = False
            elif isinstance(data, dict):
                # Try common pagination patterns
                records = data.get("data", data.get("results", data.get("items", [data])))
                total_count = data.get("total", data.get("count", len(records)))
                has_more = data.get("has_more", False)
            else:
                records = [data]
                total_count = 1
                has_more = False
            
            return ReadResult(
                success=True,
                records=records if isinstance(records, list) else [records],
                total_count=total_count,
                has_more=has_more,
                metadata={"endpoint": endpoint, "method": method}
            )
            
        except httpx.HTTPStatusError as e:
            return ReadResult(
                success=False,
                records=[],
                total_count=0,
                has_more=False,
                error=f"HTTP {e.response.status_code}: {e.response.text}"
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
        Write data to REST API endpoint.
        
        Args:
            destination: API endpoint path
            records: Records to write
            mode: Write mode (insert, update, upsert)
            **kwargs: Additional parameters
            
        Returns:
            WriteResult
        """
        if not self.client:
            await self.connect()
        
        try:
            endpoint = destination.lstrip("/")
            method = "POST" if mode == "insert" else "PUT" if mode == "update" else "POST"
            
            response = await self.client.request(
                method,
                endpoint,
                json={"data": records} if len(records) > 1 else records[0]
            )
            
            response.raise_for_status()
            
            return WriteResult(
                success=True,
                records_written=len(records),
                records_failed=0,
                metadata={"endpoint": endpoint, "method": method}
            )
            
        except httpx.HTTPStatusError as e:
            return WriteResult(
                success=False,
                records_written=0,
                records_failed=len(records),
                error=f"HTTP {e.response.status_code}: {e.response.text}"
            )
        except Exception as e:
            return WriteResult(
                success=False,
                records_written=0,
                records_failed=len(records),
                error=str(e)
            )
    
    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers based on auth type."""
        from app.integrations.connectors.auth import (
            ApiKeyAuthHandler,
            BearerTokenHandler,
            BasicAuthHandler,
            OAuth2Handler
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
        elif auth_type == "oauth2":
            # OAuth2 requires async initialization, return empty for now
            return {}
        
        return {}
    
    async def get_capabilities(self) -> ConnectorCapabilities:
        """Return REST API connector capabilities."""
        return ConnectorCapabilities(
            supports_batch_operations=True,
            max_batch_size=self.config.get("max_batch_size", 1000),
            supported_auth_types=["api_key", "bearer", "basic", "oauth2"],
            supported_operations=["read", "write"]
        )