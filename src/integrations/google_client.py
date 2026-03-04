"""Google Workspace Integration Client."""

import os
import os.path
import logging
from typing import Any, List, Optional
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/drive.readonly']

class GoogleWorkspaceClient:
    """Client for interacting with Google Workspace APIs (Calendar, Drive)."""
    
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = None
        self.service_calendar = None
        self.service_drive = None
        
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google APIs using OAuth 2.0."""
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Failed to refresh token: {e}")
                    self.creds = None
            
            if not self.creds:
                if not os.path.exists(self.credentials_path):
                    logger.error(f"Credentials file not found at {self.credentials_path}")
                    return

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES
                    )
                    # Use a fixed port if possible, or 0 for random free port
                    self.creds = flow.run_local_server(port=0)
                    
                    # Save the credentials for the next run
                    with open(self.token_path, 'w') as token:
                        token.write(self.creds.to_json())
                        
                except Exception as e:
                    logger.error(f"Authentication failed: {e}")
                    return

        # Build services
        if self.creds:
            try:
                self.service_calendar = build('calendar', 'v3', credentials=self.creds)
                self.service_drive = build('drive', 'v3', credentials=self.creds)
                logger.info("Google Workspace services initialized successfully")
            except Exception as e:
                logger.error(f"Failed to build services: {e}")

    def list_calendar_events(self, max_results: int = 10, days: int = 7) -> str:
        """List upcoming calendar events."""
        if not self.service_calendar:
            return "Errore: Connessione al calendario non disponibile."

        try:
            now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            time_max = (datetime.utcnow() + timedelta(days=days)).isoformat() + 'Z'
            
            events_result = self.service_calendar.events().list(
                calendarId='primary', 
                timeMin=now,
                timeMax=time_max,
                maxResults=max_results, 
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])

            if not events:
                return "Non ci sono eventi in programma per i prossimi giorni."

            result_str = f"📅 **Eventi in programma (prossimi {days} giorni):**\n"
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                # Simple formatting
                if 'T' in start:
                    dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    start_str = dt.strftime("%Y-%m-%d %H:%M")
                else:
                    start_str = start # All day event
                    
                result_str += f"- `{start_str}`: {event['summary']}\n"
                
            return result_str

        except Exception as e:
            logger.error(f"Calendar API error: {e}")
            return f"Errore nel recupero eventi: {str(e)}"

    def create_calendar_event(self, summary: str, start_time: str, end_time: str, description: str = "") -> str:
        """Create a new calendar event.
        
        Args:
            summary: Event title
            start_time: ISO format string (e.g. '2023-10-27T10:00:00')
            end_time: ISO format string
            description: Optional description
        """
        if not self.service_calendar:
            return "Errore: Connessione al calendario non disponibile."

        try:
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'Europe/Rome', # Hardcoded for now, could be config
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'Europe/Rome',
                },
            }

            event = self.service_calendar.events().insert(calendarId='primary', body=event).execute()
            return f"✅ Evento creato: **{event.get('htmlLink')}**"

        except Exception as e:
            logger.error(f"Calendar Create Error: {e}")
            return f"Errore nella creazione evento: {str(e)}"
