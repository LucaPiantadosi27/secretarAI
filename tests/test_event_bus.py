import pytest
import asyncio
from src.core.event_bus import EventBus, Event, EventType

@pytest.mark.asyncio
async def test_event_bus_pub_sub():
    """Test basic pub/sub functionality of EventBus."""
    bus = EventBus()
    # Reset singleton state for testing
    bus._subscribers.clear()
    bus._queue = asyncio.Queue()
    
    received_events = []
    
    async def dummy_handler(event: Event):
        received_events.append(event)
        
    bus.subscribe(EventType.MESSAGE_RECEIVED, dummy_handler)
    
    # Start worker and emit event
    await bus.start()
    test_event = Event(EventType.MESSAGE_RECEIVED, {"text": "hello"})
    await bus.emit(test_event)
    
    # Wait for queue to process
    await asyncio.sleep(0.1)
    await bus.stop()
    
    assert len(received_events) == 1
    assert received_events[0].payload["text"] == "hello"
    
@pytest.mark.asyncio
async def test_event_bus_unsubscribe():
    """Test unsubscribing from EventBus."""
    bus = EventBus()
    bus._subscribers.clear()
    
    received = False
    async def handler(e: Event):
        nonlocal received
        received = True
        
    bus.subscribe(EventType.SYSTEM_STARTUP, handler)
    bus.unsubscribe(EventType.SYSTEM_STARTUP, handler)
    
    await bus.start()
    await bus.emit(Event(EventType.SYSTEM_STARTUP))
    await asyncio.sleep(0.1)
    await bus.stop()
    
    assert not received
