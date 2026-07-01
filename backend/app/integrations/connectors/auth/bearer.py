"""
Bearer Token Authentication Handler
"""

from typing import Any

from .base import BaseAuthHandler


class BearerTokenHandler(BaseAuthHandler):
    """Handles Bearer token authentication."""
    
    def __init__(self, token: str, **kwargs):
        """
        Initialize Bearer token auth handler.
        
        Args:
            token: The bearer token
            **kwargs: Additional configuration
        """
        self.token = token
    
    async def authenticate(self) -> dict[str, Any]:
        """Return bearer token credentials."""
        return {"token": self.token}
    
    async def refresh(self) -> dict[str, Any]:
        """Bearer tokens typically don't refresh."""
        return {"token": self.token}
    
    def get_headers(self) -> dict[str, str]:
        """Get headers with Bearer token."""
        return {"Authorization": f"Bearer {self.token}"}
    
    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate bearer token configuration."""
        return "token" in config and bool(config["token"])