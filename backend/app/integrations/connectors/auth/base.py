"""
Base Authentication Handler
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAuthHandler(ABC):
    """Base class for authentication handlers."""
    
    @abstractmethod
    async def authenticate(self) -> dict[str, Any]:
        """
        Perform authentication and return credentials.
        
        Returns:
            Dictionary with authentication credentials
        """
        pass
    
    @abstractmethod
    async def refresh(self) -> dict[str, Any]:
        """
        Refresh authentication if supported.
        
        Returns:
            Updated credentials
        """
        pass
    
    @abstractmethod
    def get_headers(self) -> dict[str, str]:
        """
        Get authentication headers for requests.
        
        Returns:
            Dictionary of headers
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate authentication configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass