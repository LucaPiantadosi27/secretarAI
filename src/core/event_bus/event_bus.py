import asyncio
import logging
from typing import Callable, Awaitable
from collections import defaultdict

from .event_types import Event, EventType

logger = logging.getLogger(__name__)

# Type alias for event handler functions
EventHandler = Callable[[Event], Awaitable[None]]

class EventBus:
    """Central event bus for asynchronous pub/sub communication between AI modules."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern so all modules share the exact same bus."""
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._subscribers: dict[EventType, list[EventHandler]] = defaultdict(list)
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._initialized = True
        logger.info("EventBus initialized")

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Register an async handler function for a specific event type."""
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
            logger.debug(f"Subscribed handler {handler.__name__} to {event_type.name}")

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Remove a previously registered handler."""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            logger.debug(f"Unsubscribed handler {handler.__name__} from {event_type.name}")

    async def emit(self, event: Event) -> None:
        """Put an event on the queue to be processed asynchronously."""
        await self._queue.put(event)
        logger.debug(f"Emitted event: {event.type.name}")

    async def start(self) -> None:
        """Start the background task that processes the event queue."""
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._process_events())
            logger.info("EventBus background worker started")

    async def stop(self) -> None:
        """Stop the background worker."""
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
            logger.info("EventBus background worker stopped")

    async def _process_events(self) -> None:
        """Worker loop that gets events from the queue and calls subscribers."""
        try:
            while True:
                event = await self._queue.get()
                
                handlers = self._subscribers.get(event.type, [])
                if handlers:
                    # Run all handlers for this event concurrently
                    tasks = [asyncio.create_task(handler(event)) for handler in handlers]
                    # Fire and forget (errors logged inside handlers ideally, or via asyncio exception handler)
                    for t in tasks:
                        t.add_done_callback(self._handle_task_result)
                        
                self._queue.task_done()
        except asyncio.CancelledError:
            logger.debug("EventBus process_events loop cancelled")
            
    def _handle_task_result(self, task: asyncio.Task) -> None:
        """Callback to log any unhandled exceptions in event handlers."""
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in EventBus handler task: {e}", exc_info=True)

# Global singleton instance
bus = EventBus()
