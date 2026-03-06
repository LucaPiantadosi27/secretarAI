from .event_types import EventType, Event
from .event_bus import EventBus

# A single shared instance for the whole application
bus = EventBus()

__all__ = ["bus", "EventType", "Event", "EventBus"]
