"""
Event Engine
Core event processing and routing for integrations.
"""

from typing import Any, Optional, Callable, Dict, List
from datetime import datetime, timezone
from enum import Enum
import asyncio


class EventStatus(str, Enum):
    """Event processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class Event:
    """Represents an integration event."""
    
    def __init__(
        self,
        event_id: str,
        event_type: str,
        source: str,
        payload: dict[str, Any],
        metadata: dict[str, Any] = None
    ):
        """
        Initialize event.
        
        Args:
            event_id: Unique event identifier
            event_type: Type of event
            source: Event source
            payload: Event data
            metadata: Additional metadata
        """
        self.event_id = event_id
        self.event_type = event_type
        self.source = source
        self.payload = payload
        self.metadata = metadata or {}
        self.status = EventStatus.PENDING
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.processed_at = None
        self.error = None
        self.retry_count = 0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "payload": self.payload,
            "metadata": self.metadata,
            "status": self.status,
            "created_at": self.created_at,
            "processed_at": self.processed_at,
            "error": self.error,
            "retry_count": self.retry_count
        }


class EventEngine:
    """
    Engine for processing integration events.
    Manages event routing, handlers, and processing lifecycle.
    """
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 5.0):
        """
        Initialize event engine.
        
        Args:
            max_retries: Maximum retry attempts for failed events
            retry_delay: Delay between retries in seconds
        """
        self.handlers: Dict[str, List[Callable]] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processing = False
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.processed_events: List[Event] = []
        self.failed_events: List[Event] = []
    
    def register_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register an event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Async function to handle the event
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    def unregister_handler(self, event_type: str, handler: Callable) -> bool:
        """
        Unregister an event handler.
        
        Args:
            event_type: Type of event
            handler: Handler to remove
            
        Returns:
            True if removed, False if not found
        """
        if event_type in self.handlers:
            try:
                self.handlers[event_type].remove(handler)
                return True
            except ValueError:
                pass
        return False
    
    async def emit(self, event: Event) -> None:
        """
        Emit an event to the queue.
        
        Args:
            event: Event to emit
        """
        await self.event_queue.put(event)
    
    async def emit_simple(
        self,
        event_type: str,
        source: str,
        payload: dict[str, Any],
        metadata: dict[str, Any] = None
    ) -> Event:
        """
        Emit a simple event.
        
        Args:
            event_type: Type of event
            source: Event source
            payload: Event data
            metadata: Additional metadata
            
        Returns:
            Created event
        """
        event_id = f"{event_type}_{datetime.now(timezone.utc).timestamp()}"
        event = Event(event_id, event_type, source, payload, metadata)
        await self.emit(event)
        return event
    
    async def start_processing(self) -> None:
        """Start processing events from the queue."""
        if self.processing:
            return
        
        self.processing = True
        
        while self.processing:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                await self._process_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                pass
    
    async def stop_processing(self) -> None:
        """Stop processing events."""
        self.processing = False
    
    async def _process_event(self, event: Event) -> None:
        """
        Process a single event.
        
        Args:
            event: Event to process
        """
        event.status = EventStatus.PROCESSING
        
        handlers = self.handlers.get(event.event_type, [])
        
        if not handlers:
            # Try wildcard handler
            handlers = self.handlers.get("*", [])
        
        if not handlers:
            event.status = EventStatus.FAILED
            event.error = f"No handlers registered for event type: {event.event_type}"
            self.failed_events.append(event)
            return
        
        # Execute handlers
        success = False
        last_error = None        
        for handler in handlers:
            try:
                result = await handler(event)
                
                if result:
                    success = True
                    event.status = EventStatus.SUCCESS
                    event.processed_at = datetime.now(timezone.utc).isoformat()
                    self.processed_events.append(event)
                    break
            except Exception as e:
                last_error = str(e)
                continue
        
        if not success:
            event.status = EventStatus.FAILED
            event.error = last_error or "All handlers failed"
            
            # Retry if under limit
            if event.retry_count < self.max_retries:
                event.retry_count += 1
                event.status = EventStatus.RETRYING
                await asyncio.sleep(self.retry_delay)
                await self.emit(event)
            else:
                self.failed_events.append(event)
    
    async def process_event_immediately(self, event: Event) -> bool:
        """
        Process an event immediately without queueing.
        
        Args:
            event: Event to process
            
        Returns:
            True if processed successfully
        """
        await self._process_event(event)
        return event.status == EventStatus.SUCCESS
    
    def get_processed_events(self, limit: int = 100) -> List[Event]:
        """
        Get recently processed events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of processed events
        """
        return self.processed_events[-limit:]
    
    def get_failed_events(self, limit: int = 100) -> List[Event]:
        """
        Get failed events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of failed events
        """
        return self.failed_events[-limit:]
    
    def clear_history(self) -> None:
        """Clear event history."""
        self.processed_events.clear()
        self.failed_events.clear()
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get event engine statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "queue_size": self.event_queue.qsize(),
            "processing": self.processing,
            "registered_handlers": {
                event_type: len(handlers)
                for event_type, handlers in self.handlers.items()
            },
            "total_processed": len(self.processed_events),
            "total_failed": len(self.failed_events),
            "max_retries": self.max_retries
        }


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
    
    async def route(self, event: Event) -> Optional[Any]:
        """
        Route an event to appropriate handler.
        
        Args:
            event: Event to route
            
        Returns:
            Handler result or None
        """
        routes = self.routes.get(event.event_type, [])
        
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