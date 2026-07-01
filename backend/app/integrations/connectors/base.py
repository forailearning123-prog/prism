"""
Base Connector Interface
Abstract base class that all connectors must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ConnectorCapabilities:
    """Defines what a connector can do."""
    
    def __init__(
        self,
        supports_incremental_sync: bool = False,
        supports_bidirectional_sync: bool = False,
        supports_events: bool = False,
        supports_batch_operations: bool = False,
        supports_streaming: bool = False,
        max_batch_size: int = 1000,
        supported_auth_types: list[str] = None,
        supported_operations: list[str] = None,
    ):
        self.supports_incremental_sync = supports_incremental_sync
        self.supports_bidirectional_sync = supports_bidirectional_sync
        self.supports_events = supports_events
        self.supports_batch_operations = supports_batch_operations
        self.supports_streaming = supports_streaming
        self.max_batch_size = max_batch_size
        self.supported_auth_types = supported_auth_types or []
        self.supported_operations = supported_operations or ["read", "write"]


class HealthStatus(str, Enum):
    """Health status of a connector."""
    healthy = "healthy"
    warning = "warning"
    failed = "failed"
    unknown = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    status: HealthStatus
    response_time_ms: int
    message: str
    details: dict = field(default_factory=dict)
    checked_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConnectionTestResult:
    """Result of a connection test."""
    success: bool
    message: str
    details: dict = field(default_factory=dict)
    capabilities: Optional[ConnectorCapabilities] = None


@dataclass
class ReadResult:
    """Result of a read operation."""
    success: bool
    records: list[dict]
    total_count: int
    has_more: bool
    metadata: dict = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class WriteResult:
    """Result of a write operation."""
    success: bool
    records_written: int
    records_failed: int
    metadata: dict = field(default_factory=dict)
    error: Optional[str] = None


class BaseConnector(ABC):
    """
    Abstract base class for all connectors.
    All connectors must inherit from this class and implement the abstract methods.
    """
    
    def __init__(self, config: dict[str, Any], auth_config: dict[str, Any]):
        """
        Initialize the connector.
        
        Args:
            config: Connector configuration (endpoint, settings, etc.)
            auth_config: Authentication configuration (credentials, tokens, etc.)
        """
        self.config = config
        self.auth_config = auth_config
        self._client = None
        self._is_connected = False
    
    # ========================================================================
    # Abstract Methods - Must be implemented by all connectors
    # ========================================================================
    
    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to the external system.
        Should authenticate and initialize the client.
        
        Raises:
            AuthenticationError: If authentication fails
            ConnectionError: If connection fails
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection and cleanup resources."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> ConnectionTestResult:
        """
        Test the connection without performing any operations.
        
        Returns:
            ConnectionTestResult with success status and details
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> HealthCheckResult:
        """
        Perform a health check on the connector.
        
        Returns:
            HealthCheckResult with status and details
        """
        pass
    
    @abstractmethod
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
        Read data from the source system.
        
        Args:
            source: Source identifier (table, endpoint, etc.)
            fields: List of fields to retrieve
            filter: Filter conditions
            limit: Maximum number of records
            offset: Offset for pagination
            **kwargs: Additional provider-specific parameters
            
        Returns:
            ReadResult with records and metadata
        """
        pass
    
    @abstractmethod
    async def write(
        self,
        destination: str,
        records: list[dict],
        mode: str = "upsert",
        **kwargs
    ) -> WriteResult:
        """
        Write data to the destination system.
        
        Args:
            destination: Destination identifier (table, endpoint, etc.)
            records: List of records to write
            mode: Write mode (insert, update, upsert, delete)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            WriteResult with success status and counts
        """
        pass
    
    # ========================================================================
    # Optional Methods - Can be overridden for advanced features
    # ========================================================================
    
    async def read_incremental(
        self,
        source: str,
        cursor: Optional[str] = None,
        fields: list[str] = None,
        limit: int = 1000,
        **kwargs
    ) -> ReadResult:
        """
        Read only changed records since last sync (incremental sync).
        
        Args:
            source: Source identifier
            cursor: Cursor from previous sync (timestamp, ID, etc.)
            fields: List of fields to retrieve
            limit: Maximum number of records
            **kwargs: Additional parameters
            
        Returns:
            ReadResult with changed records and new cursor
        """
        raise NotImplementedError("Incremental read not supported by this connector")
    
    async def get_capabilities(self) -> ConnectorCapabilities:
        """
        Return connector capabilities.
        
        Returns:
            ConnectorCapabilities object
        """
        return ConnectorCapabilities()
    
    async def discover_schema(self, source: str) -> dict[str, Any]:
        """
        Discover the schema of a source (tables, fields, types).
        
        Args:
            source: Source identifier
            
        Returns:
            Schema definition
        """
        raise NotImplementedError("Schema discovery not supported by this connector")
    
    async def validate_credentials(self) -> ConnectionTestResult:
        """
        Validate that the provided credentials are valid.
        
        Returns:
            ConnectionTestResult with validation status
        """
        return await self.test_connection()
    
    async def get_metadata(self) -> dict[str, Any]:
        """
        Get connector metadata (version, limits, etc.).
        
        Returns:
            Metadata dictionary
        """
        return {}
    
    # ========================================================================
    # Helper Methods - Common functionality
    # ========================================================================
    
    def is_connected(self) -> bool:
        """Check if connector is currently connected."""
        return self._is_connected
    
    def _set_connected(self, connected: bool) -> None:
        """Set connection status."""
        self._is_connected = connected
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        return False
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(config={self.config})"