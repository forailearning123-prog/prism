"""
API Key Authentication Handler
"""

from typing import Any

from .base import BaseAuthHandler


class ApiKeyAuthHandler(BaseAuthHandler):
    """Handles API key authentication."""
    
    def __init__(self, api_key: str, header_name: str = "X-API-Key", **kwargs):
        """
        Initialize API key auth handler.
        
        Args:
            api_key: The API key
            header_name: Header name for the API key (default: X-API-Key)
            **kwargs: Additional configuration
        """
        self.api_key = api_key
        self.header_name = header_name
    
    async def authenticate(self) -> dict[str, Any]:
        """Return API key credentials."""
        return {"api_key": self.api_key}
    
    async def refresh(self) -> dict[str, Any]:
        """API keys typically don't refresh."""
        return {"api_key": self.api_key}
    
    def get_headers(self) -> dict[str, str]:
        """Get headers with API key."""
        return {self.header_name: self.api_key}
    
    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate API key configuration."""
        return "api_key" in config and bool(config["api_key"])