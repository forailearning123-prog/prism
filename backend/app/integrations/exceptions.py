"""
Enterprise Integration Hub - Custom Exceptions
"""


class IntegrationError(Exception):
    """Base exception for integration errors."""
    pass


class ConnectorNotFoundError(IntegrationError):
    """Raised when a connector is not found."""
    pass


class ConnectorConfigurationError(IntegrationError):
    """Raised when there's a configuration error."""
    pass


class AuthenticationError(IntegrationError):
    """Raised when authentication fails."""
    pass


class ConnectionError(IntegrationError):
    """Raised when connection to external system fails."""
    pass


class SyncJobError(IntegrationError):
    """Raised when a sync job encounters an error."""
    pass


class TransformationError(IntegrationError):
    """Raised when a transformation fails."""
    pass


class ValidationError(IntegrationError):
    """Raised when data validation fails."""
    pass


class RateLimitError(IntegrationError):
    """Raised when rate limit is exceeded."""
    pass


class TimeoutError(IntegrationError):
    """Raised when an operation times out."""
    pass


class DeadLetterQueueError(IntegrationError):
    """Raised when dead letter queue operations fail."""
    pass


class EventProcessingError(IntegrationError):
    """Raised when event processing fails."""
    pass


class GovernanceError(IntegrationError):
    """Raised when governance rules are violated."""
    pass


class SecretsManagementError(IntegrationError):
    """Raised when secrets management operations fail."""
    pass