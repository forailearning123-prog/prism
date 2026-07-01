"""
Webhook Handler
Handles incoming and outgoing webhooks for event-driven integrations.
"""

from typing import Any, Optional, Dict, List
from datetime import datetime, timezone
import hmac
import hashlib
import json


class WebhookHandler:
    """
    Handles webhook operations for integrations.
    Supports receiving, validating, and sending webhooks.
    """
    
    def __init__(self):
        """Initialize webhook handler."""
        self.webhooks: Dict[int, dict[str, Any]] = {}
        self.next_id = 1
    
    def register_webhook(
        self,
        url: str,
        event_types: List[str],
        secret: str = None,
        headers: Dict[str, str] = None,
        metadata: Dict[str, Any] = None
    ) -> dict[str, Any]:
        """
        Register a webhook endpoint.
        
        Args:
            url: Webhook URL
            event_types: List of event types to subscribe to
            secret: Webhook secret for signature validation
            headers: Additional headers to send
            metadata: Additional metadata
            
        Returns:
            Webhook registration dictionary
        """
        webhook = {
            "id": self.next_id,
            "url": url,
            "event_types": event_types,
            "secret": secret,
            "headers": headers or {},
            "metadata": metadata or {},
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.webhooks[self.next_id] = webhook
        self.next_id += 1
        
        return webhook
    
    def unregister_webhook(self, webhook_id: int) -> bool:
        """
        Unregister a webhook.
        
        Args:
            webhook_id: Webhook ID
            
        Returns:
            True if unregistered, False if not found
        """
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            return True
        return False
    
    def get_webhook(self, webhook_id: int) -> Optional[dict[str, Any]]:
        """
        Get webhook by ID.
        
        Args:
            webhook_id: Webhook ID
            
        Returns:
            Webhook dictionary or None
        """
        return self.webhooks.get(webhook_id)
    
    def list_webhooks(self, event_type: str = None) -> List[dict[str, Any]]:
        """
        List registered webhooks.
        
        Args:
            event_type: Filter by event type
            
        Returns:
            List of webhook dictionaries
        """
        webhooks = list(self.webhooks.values())
        
        if event_type:
            webhooks = [w for w in webhooks if event_type in w.get("event_types", [])]
        
        return webhooks
    
    async def send_webhook(
        self,
        webhook_id: int,
        event_type: str,
        payload: dict[str, Any],
        metadata: Dict[str, Any] = None
    ) -> dict[str, Any]:
        """
        Send a webhook notification.
        
        Args:
            webhook_id: Webhook ID
            event_type: Type of event
            payload: Event payload
            metadata: Additional metadata
            
        Returns:
            Response dictionary
        """
        import httpx
        
        webhook = self.webhooks.get(webhook_id)
        if not webhook:
            return {"success": False, "error": "Webhook not found"}
        
        if not webhook.get("is_active"):
            return {"success": False, "error": "Webhook is not active"}
        
        if event_type not in webhook.get("event_types", []):
            return {"success": False, "error": "Event type not subscribed"}
        
        # Prepare payload
        webhook_payload = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
            "metadata": metadata or {}
        }
        
        # Generate signature if secret is provided
        headers = webhook.get("headers", {}).copy()
        if webhook.get("secret"):
            signature = self._generate_signature(webhook["secret"], webhook_payload)
            headers["X-Webhook-Signature"] = signature
        
        # Send webhook
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook["url"],
                    json=webhook_payload,
                    headers=headers,
                    timeout=30.0
                )
                
                return {
                    "success": response.is_success,
                    "status_code": response.status_code,
                    "response": response.text,
                    "webhook_id": webhook_id
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "webhook_id": webhook_id
            }
    
    async def receive_webhook(
        self,
        payload: dict[str, Any],
        signature: str = None,
        secret: str = None
    ) -> dict[str, Any]:
        """
        Process an incoming webhook.
        
        Args:
            payload: Webhook payload
            signature: Webhook signature
            secret: Expected secret for validation
            
        Returns:
            Processed webhook data
        """
        # Validate signature if provided
        if signature and secret:
            if not self._validate_signature(payload, signature, secret):
                return {
                    "success": False,
                    "error": "Invalid webhook signature"
                }
        
        # Extract event information
        event_type = payload.get("event_type")
        event_payload = payload.get("payload", {})
        event_metadata = payload.get("metadata", {})
        
        return {
            "success": True,
            "event_type": event_type,
            "payload": event_payload,
            "metadata": event_metadata,
            "timestamp": payload.get("timestamp")
        }
    
    def _generate_signature(self, secret: str, payload: dict[str, Any]) -> str:
        """
        Generate webhook signature.
        
        Args:
            secret: Webhook secret
            payload: Webhook payload
            
        Returns:
            HMAC signature
        """
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _validate_signature(
        self,
        payload: dict[str, Any],
        signature: str,
        secret: str
    ) -> bool:
        """
        Validate webhook signature.
        
        Args:
            payload: Webhook payload
            signature: Provided signature
            secret: Expected secret
            
        Returns:
            True if valid, False otherwise
        """
        expected_signature = self._generate_signature(secret, payload)
        return hmac.compare_digest(signature, expected_signature)
    
    def enable_webhook(self, webhook_id: int) -> Optional[dict[str, Any]]:
        """
        Enable a webhook.
        
        Args:
            webhook_id: Webhook ID
            
        Returns:
            Updated webhook or None
        """
        webhook = self.webhooks.get(webhook_id)
        if webhook:
            webhook["is_active"] = True
            webhook["updated_at"] = datetime.now(timezone.utc).isoformat()
            return webhook
        return None
    
    def disable_webhook(self, webhook_id: int) -> Optional[dict[str, Any]]:
        """
        Disable a webhook.
        
        Args:
            webhook_id: Webhook ID
            
        Returns:
            Updated webhook or None
        """
        webhook = self.webhooks.get(webhook_id)
        if webhook:
            webhook["is_active"] = False
            webhook["updated_at"] = datetime.now(timezone.utc).isoformat()
            return webhook
        return None
    
    def update_webhook(
        self,
        webhook_id: int,
        url: str = None,
        event_types: List[str] = None,
        secret: str = None,
        headers: Dict[str, str] = None
    ) -> Optional[dict[str, Any]]:
        """
        Update webhook configuration.
        
        Args:
            webhook_id: Webhook ID
            url: New URL
            event_types: New event types
            secret: New secret
            headers: New headers
            
        Returns:
            Updated webhook or None
        """
        webhook = self.webhooks.get(webhook_id)
        if not webhook:
            return None
        
        if url is not None:
            webhook["url"] = url
        if event_types is not None:
            webhook["event_types"] = event_types
        if secret is not None:
            webhook["secret"] = secret
        if headers is not None:
            webhook["headers"] = headers
        
        webhook["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return webhook
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get webhook statistics.
        
        Returns:
            Statistics dictionary
        """
        active = sum(1 for w in self.webhooks.values() if w.get("is_active"))
        
        return {
            "total_webhooks": len(self.webhooks),
            "active_webhooks": active,
            "inactive_webhooks": len(self.webhooks) - active
        }