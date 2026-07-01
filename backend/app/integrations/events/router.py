"""
Event Router
Routes events to appropriate handlers based on rules.
"""

from typing import Any, Optional, Callable, Dict, List
from datetime import datetime, timezone


class EventRouter:
    """
    Routes events to appropriate handlers based on rules.
    """
    
    def __init__(self):
        """Initialize event router."""
        self.routes: Dict[str, List[dict[str, Any]]] = {}
        self.default_handler = None
    
    def add_route(
        self,
        event_type: str,
        handler: Callable,
        condition: Callable = None,
        priority: int = 0
    ) -> None:
        """
        Add a routing rule.
        
        Args:
            event_type: Type of event
            handler: Handler function
            condition: Optional condition function
            priority: Route priority (higher = more important)
        """
        if event_type not in self.routes:
            self.routes[event_type] = []
        
        self.routes[event_type].append({
            "handler": handler,
            "condition": condition,
            "priority": priority
        })
        
        # Sort by priority
        self.routes[event_type].sort(key=lambda x: x["priority"], reverse=True)
    
    def set_default_handler(self, handler: Callable) -> None:
        """
        Set default handler for unmatched events.
        
        Args:
            handler: Default handler function
        """
        self.default_handler = handler
    
    async def route(self, event: Any) -> Optional[Any]:
        """
        Route an event to appropriate handler.
        
        Args:
            event: Event to route
            
        Returns:
            Handler result or None
        """
        event_type = getattr(event, 'event_type', None)
        if not event_type:
            return None
        
        routes = self.routes.get(event_type, [])
        
        # Try matching routes
        for route in routes:
            condition = route.get("condition")
            
            if condition is None or condition(event):
                try:
                    return await route["handler"](event)
                except Exception as e:
                    continue
        
        # Try wildcard routes
        wildcard_routes = self.routes.get("*", [])
        for route in wildcard_routes:
            try:
                return await route["handler"](event)
            except Exception:
                continue
        
        # Use default handler
        if self.default_handler:
            try:
                return await self.default_handler(event)
            except Exception:
                pass
        
        return None
    
    def get_routes(self, event_type: str = None) -> dict[str, Any]:
        """
        Get routing rules.
        
        Args:
            event_type: Filter by event type
            
        Returns:
            Routes dictionary
        """
        if event_type:
            return {event_type: self.routes.get(event_type, [])}
        return self.routes
    
    def remove_route(self, event_type: str, handler: Callable) -> bool:
        """
        Remove a routing rule.
        
        Args:
            event_type: Type of event
            handler: Handler to remove
            
        Returns:
            True if removed, False if not found
        """
        if event_type in self.routes:
            routes = self.routes[event_type]
            for i, route in enumerate(routes):
                if route["handler"] == handler:
                    routes.pop(i)
                    return True
        return False
    
    def clear_routes(self, event_type: str = None) -> None:
        """
        Clear routing rules.
        
        Args:
            event_type: Filter by event type (clears all if None)
        """
        if event_type:
            self.routes.pop(event_type, None)
        else:
            self.routes.clear()