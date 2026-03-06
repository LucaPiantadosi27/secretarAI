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
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive.file',   # Read/write files created by this app
    'https://www.googleapis.com/auth/documents',    # Create and edit Google Docs
    'https://www.googleapis.com/auth/gmail.modify', # Read, list, and modify emails
    'https://www.googleapis.com/auth/gmail.send',   # Send emails
]

class GoogleWorkspaceClient:
    """Client for interacting with Google Workspace APIs (Calendar, Drive)."""
    
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = None
        self.service_calendar = None
        self.service_drive = None
        self.service_docs = None
        self.service_gmail = None
        
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
                    # Save the refreshed credentials for the next run
                    with open(self.token_path, 'w') as token:
                        token.write(self.creds.to_json())
                    logger.info("Successfully refreshed and saved Google API token")
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
                self.service_docs = build('docs', 'v1', credentials=self.creds)
                self.service_gmail = build('gmail', 'v1', credentials=self.creds)
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

    # -------------------------------------------------------------------------
    # Google Drive / Docs
    # -------------------------------------------------------------------------

    def create_document(self, title: str, content: str, folder_name: str | None = None) -> str:
        """Create a Google Doc with the given title and content.

        Args:
            title: Document title.
            content: Plain-text content to write into the document.
            folder_name: Optional Drive folder name to place the doc in.

        Returns:
            A user-friendly string with the document link.
        """
        if not self.service_docs or not self.service_drive:
            return "Errore: servizi Google Drive/Docs non disponibili."

        try:
            # 1. Create an empty Google Doc
            doc_body = {'title': title}
            doc = self.service_docs.documents().create(body=doc_body).execute()
            doc_id = doc.get('documentId')

            # 2. Insert the content
            if content:
                requests = [{
                    'insertText': {
                        'location': {'index': 1},
                        'text': content
                    }
                }]
                self.service_docs.documents().batchUpdate(
                    documentId=doc_id, body={'requests': requests}
                ).execute()

            # 3. Move to folder if requested
            if folder_name:
                folder_id = self._get_or_create_folder(folder_name)
                if folder_id:
                    self.service_drive.files().update(
                        fileId=doc_id,
                        addParents=folder_id,
                        removeParents='root',
                        fields='id, parents'
                    ).execute()

            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            logger.info(f"Document created: {doc_id}")
            return f"✅ Documento creato: **{title}**\n🔗 {doc_url}"

        except Exception as e:
            logger.error(f"Drive create_document error: {e}")
            return f"Errore nella creazione del documento: {str(e)}"

    def search_drive_files(self, query: str, max_results: int = 10) -> str:
        """Search for files in Google Drive.

        Args:
            query: Search term (file name or keyword).
            max_results: Maximum number of results to return.

        Returns:
            A formatted string listing matching files.
        """
        if not self.service_drive:
            return "Errore: servizio Google Drive non disponibile."

        try:
            # Search in name and full-text
            q = f"name contains '{query}' and trashed = false"
            results = self.service_drive.files().list(
                q=q,
                pageSize=max_results,
                fields="files(id, name, mimeType, modifiedTime, webViewLink)"
            ).execute()

            files = results.get('files', [])

            if not files:
                return f"📂 Nessun file trovato per '{query}' su Google Drive."

            _MIME_ICONS = {
                'application/vnd.google-apps.document': '📄',
                'application/vnd.google-apps.spreadsheet': '📊',
                'application/vnd.google-apps.presentation': '📑',
                'application/vnd.google-apps.folder': '📁',
                'application/pdf': '📋',
            }

            lines = [f"📂 **File trovati per '{query}':**"]
            for f in files:
                icon = _MIME_ICONS.get(f.get('mimeType', ''), '📎')
                link = f.get('webViewLink', '')
                name = f.get('name', 'Senza titolo')
                lines.append(f"{icon} [{name}]({link})")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Drive search error: {e}")
            return f"Errore nella ricerca Drive: {str(e)}"

    def get_document_content(self, doc_id: str) -> str:
        """Retrieve the plain text content of a Google Doc.

        Args:
            doc_id: Google Doc document ID.

        Returns:
            Plain-text content of the document.
        """
        if not self.service_docs:
            return "Errore: servizio Google Docs non disponibile."

        try:
            doc = self.service_docs.documents().get(documentId=doc_id).execute()
            title = doc.get('title', 'Documento senza titolo')

            # Extract plain text from body elements
            text_parts = []
            body = doc.get('body', {})
            for element in body.get('content', []):
                para = element.get('paragraph')
                if para:
                    for elem in para.get('elements', []):
                        text_run = elem.get('textRun')
                        if text_run:
                            text_parts.append(text_run.get('content', ''))

            full_text = ''.join(text_parts).strip()
            return f"📄 **{title}**\n\n{full_text}"

        except Exception as e:
            logger.error(f"Docs get_content error: {e}")
            return f"Errore nel recupero documento: {str(e)}"

    def _get_or_create_folder(self, folder_name: str) -> str | None:
        """Get folder ID by name, or create it if it doesn't exist."""
        try:
            q = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = self.service_drive.files().list(q=q, fields="files(id)").execute()
            folders = results.get('files', [])

            if folders:
                return folders[0]['id']

            # Create the folder
            folder_meta = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service_drive.files().create(body=folder_meta, fields='id').execute()
            return folder.get('id')

        except Exception as e:
            logger.warning(f"Could not get/create folder '{folder_name}': {e}")
            return None

    # -------------------------------------------------------------------------
    # Gmail
    # -------------------------------------------------------------------------

    def list_emails(self, max_results: int = 10, query: str = "label:INBOX") -> List[dict]:
        """List recent emails from Gmail.
        
        Args:
            max_results: Max number of messages to return.
            query: Gmail search query (e.g. 'label:INBOX', 'is:unread').
        """
        if not self.service_gmail:
            logger.error("Gmail service not available")
            return []

        try:
            results = self.service_gmail.users().messages().list(
                userId='me', q=query, maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            email_details = []
            
            for msg in messages:
                detail = self.get_email_details(msg['id'])
                if detail:
                    email_details.append(detail)
                    
            return email_details

        except Exception as e:
            logger.error(f"Gmail list error: {e}")
            return []

    def get_email_details(self, message_id: str) -> Optional[dict]:
        """Get full details of a specific email."""
        if not self.service_gmail:
            return None

        try:
            msg = self.service_gmail.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()
            
            payload = msg.get('payload', {})
            headers = payload.get('headers', [])
            
            subject = ""
            sender = ""
            date = ""
            
            for header in headers:
                if header['name'] == 'Subject':
                    subject = header['value']
                elif header['name'] == 'From':
                    sender = header['value']
                elif header['name'] == 'Date':
                    date = header['value']

            # Basic snippet
            snippet = msg.get('snippet', '')
            
            # Extract plain text body if possible
            body = self._extract_email_body(payload)
            
            return {
                'id': message_id,
                'threadId': msg.get('threadId'),
                'subject': subject,
                'from': sender,
                'date': date,
                'snippet': snippet,
                'body': body or snippet
            }

        except Exception as e:
            logger.error(f"Gmail get error for {message_id}: {e}")
            return None

    def _extract_email_body(self, payload: dict) -> str:
        """Helper to recursively extract plain text body from email payload."""
        if 'parts' in payload:
            for part in payload['parts']:
                body = self._extract_email_body(part)
                if body:
                    return body
        
        if payload.get('mimeType') == 'text/plain':
            import base64
            data = payload.get('body', {}).get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8')
        
        return ""

    def send_email(self, to: str, subject: str, body: str, thread_id: Optional[str] = None) -> str:
        """Send an email."""
        if not self.service_gmail:
            return "Errore: servizio Gmail non disponibile."

        try:
            import base64
            from email.mime.text import MIMEText
            
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            body_dict = {'raw': raw_message}
            if thread_id:
                body_dict['threadId'] = thread_id

            sent_msg = self.service_gmail.users().messages().send(
                userId='me', body=body_dict
            ).execute()
            
            return f"✅ Email inviata a {to} (ID: {sent_msg['id']})"

        except Exception as e:
            logger.error(f"Gmail send error: {e}")
            return f"Errore nell'invio email: {str(e)}"

# Singleton instance for shared use across the application
try:
    GOOGLE_CLIENT = GoogleWorkspaceClient()
except Exception as e:
    logger.error(f"Failed to initialize global GoogleWorkspaceClient: {e}")
    GOOGLE_CLIENT = None

