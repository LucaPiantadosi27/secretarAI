from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

class EventType(Enum):
    """Enumeration of all system events."""
    # Core system
    SYSTEM_STARTUP = auto()
    SYSTEM_SHUTDOWN = auto()
    
    # Message lifecycle
    MESSAGE_RECEIVED = auto()
    MESSAGE_PROCESSED = auto()
    RESPONSE_GENERATED = auto()
    
    # Tool execution
    TOOL_START = auto()
    TOOL_END = auto()
    TOOL_ERROR = auto()
    
    # Memory
    MEMORY_STORED = auto()
    MEMORY_RECALLED = auto()
    
    # Integrations
    EMAIL_RECEIVED = auto()
    CALENDAR_EVENT_SOON = auto()
    TASK_CREATED = auto()
    TASK_COMPLETED = auto()

@dataclass
class Event:
    """Base Event object mapping an EventType to its payload data."""
    type: EventType
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
