"""
Webhook Connector
Handles incoming and outgoing webhooks.
"""

from typing import Any
import httpx
from datetime import datetime

from ..base import BaseConnector, ConnectorCapabilities, ReadResult, WriteResult, ConnectionTestResult, HealthCheckResult
from app.integrations.exceptions import ConnectionError


class WebhookConnector(BaseConnector):
    """
    Webhook connector for receiving and sending webhooks.
    """
    
    def __init__(self, config: dict[str, Any], auth_config: dict[str, Any]):
        """
        Initialize webhook connector.
        
        Args:
            config: Configuration with webhook URL, secret, etc.
            auth_config: Authentication configuration
        """
        super().__init__(config, auth_config)
        self.webhook_url = config.get("webhook_url", "")
        self.webhook_secret = config.get("webhook_secret", "")
        self.timeout = config.get("timeout_seconds", 30)
        self.client = None
    
    async def connect(self) -> None:
        """Initialize webhook client."""
        try:
            self.client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._get_auth_headers()
            )
            self._set_connected(True)
        except Exception as e:
            raise ConnectionError(f"Failed to initialize webhook client: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close webhook client."""
        if self.client:
            await self.client.aclose()
            self.client = None
        self._set_connected(False)
    
    async def test_connection(self) -> ConnectionTestResult:
        """
        Test webhook endpoint by sending a test payload.
        
        Returns:
            ConnectionTestResult
        """
        try:
            test_payload = {
                "event": "test",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Webhook connection test"
            }
            
            response = await self.send_webhook(test_payload)
            
            return ConnectionTestResult(
                success=response.get("success", False),
                message="Webhook test completed",
                details=response
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"Webhook test failed: {str(e)}"
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
                    message="Webhook endpoint is healthy"
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
        Read webhook events (for polling mode).
        
        Args:
            source: Event type or endpoint
            fields: Fields to retrieve
            filter: Filter conditions
            limit: Maximum events
            offset: Offset
            **kwargs: Additional parameters
            
        Returns:
            ReadResult
        """
        # Webhooks are push-based, but some systems support polling
        if not self.client:
            await self.connect()
        
        try:
            # Poll for events if the endpoint supports it
            response = await self.client.get(
                source,
                params={"limit": limit, "offset": offset}
            )
            response.raise_for_status()
            
            data = response.json()
            events = data if isinstance(data, list) else [data]
            
            return ReadResult(
                success=True,
                records=events,
                total_count=len(events),
                has_more=False
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
        Send webhook notifications.
        
        Args:
            destination: Event type or webhook path
            records: Records/events to send
            mode: Not used for webhooks
            **kwargs: Additional parameters
            
        Returns:
            WriteResult
        """
        if not self.client:
            await self.connect()
        
        try:
            results = []
            for record in records:
                payload = {
                    "event": destination,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": record,
                    "webhook_secret": self.webhook_secret if self.webhook_secret else None
                }
                
                response = await self.send_webhook(payload)
                results.append(response)
            
            success_count = sum(1 for r in results if r.get("success", False))
            
            return WriteResult(
                success=success_count == len(records),
                records_written=success_count,
                records_failed=len(records) - success_count,
                metadata={"results": results}
            )
        except Exception as e:
            return WriteResult(
                success=False,
                records_written=0,
                records_failed=len(records),
                error=str(e)
            )
    
    async def send_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Send a webhook payload.
        
        Args:
            payload: Webhook payload
            
        Returns:
            Response dictionary
        """
        if not self.client:
            await self.connect()
        
        try:
            response = await self.client.post(
                self.webhook_url,
                json=payload,
                headers=self._get_auth_headers()
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "status_code": response.status_code,
                "response": response.text
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "status_code": e.response.status_code,
                "error": f"HTTP {e.response.status_code}: {e.response.text}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def receive_webhook(self, payload: dict[str, Any], signature: str = None) -> dict[str, Any]:
        """
        Process incoming webhook payload.
        
        Args:
            payload: Webhook payload
            signature: Webhook signature for verification
            
        Returns:
            Processed payload
        """
        # Verify signature if secret is configured
        if self.webhook_secret and signature:
            if not self._verify_signature(payload, signature):
                raise ValueError("Invalid webhook signature")
        
        # Process the webhook
        return {
            "success": True,
            "event": payload.get("event"),
            "data": payload.get("data"),
            "timestamp": payload.get("timestamp")
        }
    
    def _verify_signature(self, payload: dict[str, Any], signature: str) -> bool:
        """
        Verify webhook signature.
        
        Args:
            payload: Webhook payload
            signature: Signature to verify
            
        Returns:
            True if valid, False otherwise
        """
        import hmac
        import hashlib
        
        # Create expected signature
        payload_str = str(payload)
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers."""
        headers = {}
        
        if self.webhook_secret:
            headers["X-Webhook-Secret"] = self.webhook_secret
        
        # Add additional auth from auth_config
        auth_type = self.auth_config.get("type", "none")
        
        if auth_type == "bearer":
            from app.integrations.connectors.auth import BearerTokenHandler
            handler = BearerTokenHandler(self.auth_config.get("token", ""))
            headers.update(handler.get_headers())
        elif auth_type == "api_key":
            from app.integrations.connectors.auth import ApiKeyAuthHandler
            handler = ApiKeyAuthHandler(
                self.auth_config.get("api_key", ""),
                self.auth_config.get("header_name", "X-API-Key")
            )
            headers.update(handler.get_headers())
        
        return headers
    
    async def get_capabilities(self) -> ConnectorCapabilities:
        """Return webhook connector capabilities."""
        return ConnectorCapabilities(
            supports_events=True,
            supported_auth_types=["none", "api_key", "bearer", "basic"],
            supported_operations=["read", "write"]
        )