import logging
from typing import Any
from src.core.tools.tool_base import BaseTool

logger = logging.getLogger(__name__)

# Note: We import the shared GOOGLE_CLIENT from orchestrator for now, 
# until Integration modules are fully refactored.
from src.integrations.google_client import GOOGLE_CLIENT

class GetCalendarEventsTool(BaseTool):
    """Tool to fetch upcoming Google Calendar events."""
    
    @property
    def name(self) -> str:
        return "get_calendar_events"

    @property
    def description(self) -> str:
        return "Recupera i prossimi eventi e appuntamenti dal Google Calendar dell'utente."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Numero di giorni in avanti da controllare (default: 7)",
                    "default": 7
                }
            }
        }

    async def execute(self, **kwargs) -> Any:
        if not GOOGLE_CLIENT:
            return "Errore: Google Workspace non configurato."
        
        days_val = kwargs.get("days", 7)
        try:
            days = int(days_val)
        except (ValueError, TypeError):
            days = 7
            
        return GOOGLE_CLIENT.list_calendar_events(days=days)


class CreateCalendarEventTool(BaseTool):
    """Tool to create a new event in Google Calendar."""
    
    @property
    def name(self) -> str:
        return "create_calendar_event"

    @property
    def description(self) -> str:
        return "Crea un nuovo evento o promemoria nel Google Calendar dell'utente."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Titolo o oggetto dell'evento"
                },
                "start_time": {
                    "type": "string",
                    "description": "Data e ora di inizio in formato ISO 8601 (es: '2023-10-25T14:30:00+02:00'). USA SEMPRE IL FUSO ORARIO LOCALE fornito nel contesto (+01:00 o +02:00 in Italia)."
                },
                "end_time": {
                    "type": "string",
                    "description": "Data e ora di fine in formato ISO 8601"
                },
                "description": {
                    "type": "string",
                    "description": "Dettagli o note aggiuntive per l'evento (opzionale)"
                }
            },
            "required": ["title", "start_time", "end_time"]
        }

    async def execute(self, **kwargs) -> Any:
        if not GOOGLE_CLIENT:
            return "Errore: Google Workspace non configurato."
            
        title = kwargs.get("title")
        start_time = kwargs.get("start_time")
        end_time = kwargs.get("end_time")
        description = kwargs.get("description", "")
        
        return GOOGLE_CLIENT.create_calendar_event(title, start_time, end_time, description)
