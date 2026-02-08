"""Location processing for geo-awareness."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Placeholder for stored locations and reminders
# In production, these would be in a database
_saved_locations: dict[str, dict] = {}
_location_reminders: list[dict] = []


async def process_location_update(
    user_id: int,
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    """Process a location update and check for triggered reminders.
    
    Args:
        user_id: Telegram user ID
        latitude: Current latitude
        longitude: Current longitude
        
    Returns:
        Dict with triggered_reminders list if any
    """
    from src.config import settings
    
    triggered = []
    geofence_radius = settings.default_geofence_radius_meters
    
    # Check each saved location for geofence triggers
    for location_name, location_data in _saved_locations.items():
        distance = _calculate_distance(
            latitude, longitude,
            location_data["latitude"], location_data["longitude"]
        )
        
        was_inside = location_data.get("user_inside", False)
        is_inside = distance <= geofence_radius
        
        # Check for arrival/departure triggers
        if is_inside and not was_inside:
            # User just arrived
            triggered.extend(
                _get_triggered_reminders(user_id, location_name, "arrive")
            )
            location_data["user_inside"] = True
            
        elif not is_inside and was_inside:
            # User just left
            triggered.extend(
                _get_triggered_reminders(user_id, location_name, "leave")
            )
            location_data["user_inside"] = False
    
    return {"triggered_reminders": triggered}


def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters using Haversine formula."""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371000  # Earth radius in meters
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c


def _get_triggered_reminders(user_id: int, location_name: str, trigger: str) -> list[str]:
    """Get reminders that should be triggered.
    
    Args:
        user_id: User to check reminders for
        location_name: Location that was entered/exited
        trigger: "arrive" or "leave"
        
    Returns:
        List of reminder messages to send
    """
    triggered = []
    remaining = []
    
    for reminder in _location_reminders:
        if (reminder["user_id"] == user_id and 
            reminder["location_name"].lower() == location_name.lower() and
            reminder["trigger"] == trigger):
            triggered.append(reminder["message"])
            # Mark as triggered (one-time reminder)
        else:
            remaining.append(reminder)
    
    # Remove triggered reminders
    _location_reminders.clear()
    _location_reminders.extend(remaining)
    
    return triggered


async def save_location(user_id: int, name: str, latitude: float, longitude: float):
    """Save a named location for a user.
    
    Args:
        user_id: Telegram user ID
        name: Location name (e.g., "Ufficio", "Casa")
        latitude: Location latitude
        longitude: Location longitude
    """
    key = f"{user_id}:{name.lower()}"
    _saved_locations[key] = {
        "name": name,
        "latitude": latitude,
        "longitude": longitude,
        "user_inside": False,
    }
    logger.info(f"Saved location '{name}' for user {user_id}")


async def add_location_reminder(
    user_id: int,
    message: str,
    location_name: str,
    trigger: str,
):
    """Add a location-based reminder.
    
    Args:
        user_id: Telegram user ID
        message: Reminder text
        location_name: Name of the location
        trigger: "arrive" or "leave"
    """
    _location_reminders.append({
        "user_id": user_id,
        "message": message,
        "location_name": location_name,
        "trigger": trigger,
    })
    logger.info(f"Added reminder for user {user_id} at '{location_name}'")
