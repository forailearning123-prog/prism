"""
Basic Authentication Handler
"""

from typing import Any

from .base import BaseAuthHandler


class BasicAuthHandler(BaseAuthHandler):
    """Handles HTTP Basic authentication."""
    
    import base64
    
    def __init__(self, username: str, password: str, **kwargs):
        """
        Initialize Basic auth handler.
        
        Args:
            username: Username
            password: Password
            **kwargs: Additional configuration
        """
        self.username = username
        self.password = password
    
    async def authenticate(self) -> dict[str, Any]:
        """Return basic auth credentials."""
        return {
            "username": self.username,
            "password": self.password
        }
    
    async def refresh(self) -> dict[str, Any]:
        """Basic auth typically doesn't refresh."""
        return {
            "username": self.username,
            "password": self.password
        }
    
    def get_headers(self) -> dict[str, str]:
        """Get headers with Basic authentication."""
        credentials = f"{self.username}:{self.password}"
        encoded = self.base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded}"}
    
    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate basic auth configuration."""
        return (
            "username" in config and bool(config["username"]) and
            "password" in config and bool(config["password"])
        )