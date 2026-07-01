"""
OAuth Authentication Handlers
Supports OAuth 1.0 and OAuth 2.0 flows.
"""

from typing import Any
import httpx

from .base import BaseAuthHandler


class OAuth2Handler(BaseAuthHandler):
    """Handles OAuth 2.0 authentication with token refresh support."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        access_token: str = None,
        refresh_token: str = None,
        scope: str = None,
        **kwargs
    ):
        """
        Initialize OAuth2 handler.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            token_url: Token endpoint URL
            access_token: Current access token (optional)
            refresh_token: Refresh token (optional)
            scope: OAuth scope (optional)
            **kwargs: Additional configuration
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.scope = scope
        self._token_expires_at = None
    
    async def authenticate(self) -> dict[str, Any]:
        """
        Authenticate using OAuth2 and get access token.
        
        Returns:
            Dictionary with access token
        """
        if not self.access_token or self._is_token_expired():
            await self._fetch_token()
        
        return {"access_token": self.access_token}
    
    async def _fetch_token(self) -> None:
        """Fetch new access token using client credentials or refresh token."""
        async with httpx.AsyncClient() as client:
            if self.refresh_token:
                # Use refresh token flow
                response = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": self.refresh_token,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    }
                )
            else:
                # Use client credentials flow
                response = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "scope": self.scope,
                    }
                )
            
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token", self.refresh_token)
            
            # Calculate expiration time
            expires_in = token_data.get("expires_in", 3600)
            from datetime import datetime, timedelta
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    
    async def refresh(self) -> dict[str, Any]:
        """
        Refresh the access token.
        
        Returns:
            Updated credentials with new access token
        """
        if not self.refresh_token:
            raise ValueError("No refresh token available")
        
        await self._fetch_token()
        return await self.authenticate()
    
    def _is_token_expired(self) -> bool:
        """Check if the access token is expired."""
        if not self._token_expires_at:
            return True
        
        from datetime import datetime
        return datetime.utcnow() >= self._token_expires_at
    
    def get_headers(self) -> dict[str, str]:
        """Get headers with Bearer token."""
        if not self.access_token:
            raise ValueError("No access token available. Call authenticate() first.")
        
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate OAuth2 configuration."""
        return (
            "client_id" in config and bool(config["client_id"]) and
            "client_secret" in config and bool(config["client_secret"]) and
            "token_url" in config and bool(config["token_url"])
        )


class OAuth1Handler(BaseAuthHandler):
    """Handles OAuth 1.0 authentication."""
    
    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        access_token: str = None,
        access_token_secret: str = None,
        **kwargs
    ):
        """
        Initialize OAuth1 handler.
        
        Args:
            consumer_key: OAuth consumer key
            consumer_secret: OAuth consumer secret
            access_token: Access token (optional)
            access_token_secret: Access token secret (optional)
            **kwargs: Additional configuration
        """
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
    
    async def authenticate(self) -> dict[str, Any]:
        """
        Return OAuth1 credentials.
        
        Returns:
            Dictionary with OAuth1 credentials
        """
        return {
            "consumer_key": self.consumer_key,
            "consumer_secret": self.consumer_secret,
            "access_token": self.access_token,
            "access_token_secret": self.access_token_secret,
        }
    
    async def refresh(self) -> dict[str, Any]:
        """OAuth1 tokens typically don't refresh."""
        return await self.authenticate()
    
    def get_headers(self) -> dict[str, str]:
        """
        Get OAuth1 authorization header.
        
        Note: This is a simplified implementation. In production, use a proper
        OAuth1 library like oauthlib for signature generation.
        """
        if not self.access_token:
            raise ValueError("No access token available")
        
        # Simplified - in production, generate proper OAuth1 signature
        return {
            "Authorization": f"OAuth oauth_consumer_key=\"{self.consumer_key}\", "
                           f"oauth_token=\"{self.access_token}\""
        }
    
    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate OAuth1 configuration."""
        return (
            "consumer_key" in config and bool(config["consumer_key"]) and
            "consumer_secret" in config and bool(config["consumer_secret"])
        )