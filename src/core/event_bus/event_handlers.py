import logging
from .event_types import Event

logger = logging.getLogger(__name__)

async def debug_event_logger(event: Event) -> None:
    """A generic handler that logs every event that passes through the bus."""
    logger.debug(f"[EVENT BUS] {event.type.name} - payload={event.payload}")
    
# We will define more specific event handlers here as features grow.
