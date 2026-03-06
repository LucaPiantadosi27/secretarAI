import logging
from typing import Any, List
from src.core.tools.tool_base import BaseTool
from src.integrations.google_client import GOOGLE_CLIENT
from src.llm import Message

logger = logging.getLogger(__name__)

class ListEmailsTool(BaseTool):
    """Tool to list and summarize recent emails."""
    
    @property
    def name(self) -> str:
        return "list_emails"

    @property
    def description(self) -> str:
        return "Elenca le email recenti, le classifica e ne fornisce un breve riassunto. Utile per avere una panoramica della posta in arrivo."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "Numero massimo di email da recuperare (default: 5)",
                    "default": 5
                },
                "query": {
                    "type": "string",
                    "description": "Query di ricerca Gmail (es: 'is:unread', 'from:paypal'). Default: 'label:INBOX'",
                    "default": "label:INBOX"
                }
            }
        }

    async def execute(self, **kwargs) -> Any:
        if not GOOGLE_CLIENT:
            return "Errore: Google Workspace non configurato."
            
        max_results = kwargs.get("max_results", 5)
        query = kwargs.get("query", "label:INBOX")
        
        emails = GOOGLE_CLIENT.list_emails(max_results=max_results, query=query)
        
        if not emails:
            return f"Nessun'email trovata con la query: '{query}'"
            
        # We need to summarize and classify them using the LLM
        # Importing orchestrator's LLM client for classification
        from src.llm.factory import get_llm_client
        llm = get_llm_client()
        
        summary_prompt = "Analizza queste email e per ognuna scrivi: MITTENTE, OGGETTO, CATEGORIA (Urgent, Work, Personal, Newsletter, Social) e un MINI-RIASSUNTO di 1 riga.\n\n"
        for i, email in enumerate(emails):
            summary_prompt += f"--- EMAIL {i+1} (ID: {email['id']}) ---\n"
            summary_prompt += f"From: {email['from']}\n"
            summary_prompt += f"Subject: {email['subject']}\n"
            summary_prompt += f"Snippet: {email['snippet']}\n\n"
            
        response = await llm.chat(
            messages=[Message(role="user", content=summary_prompt)],
            temperature=0.3
        )
        
        return f"📬 **Ultime Email:**\n\n{response.content}"


class SendEmailTool(BaseTool):
    """Tool to send a new email."""
    
    @property
    def name(self) -> str:
        return "send_email"

    @property
    def description(self) -> str:
        return "Invia una nuova email all'indirizzo specificato."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Indirizzo email del destinatario"
                },
                "subject": {
                    "type": "string",
                    "description": "Oggetto dell'email"
                },
                "body": {
                    "type": "string",
                    "description": "Contenuto dell'email"
                }
            },
            "required": ["to", "subject", "body"]
        }

    async def execute(self, **kwargs) -> Any:
        if not GOOGLE_CLIENT:
            return "Errore: Google Workspace non configurato."
            
        to = kwargs.get("to")
        subject = kwargs.get("subject")
        body = kwargs.get("body")
        
        return GOOGLE_CLIENT.send_email(to, subject, body)


class ReplyEmailTool(BaseTool):
    """Tool to reply to an email thread."""
    
    @property
    def name(self) -> str:
        return "reply_email"

    @property
    def description(self) -> str:
        return "Risponde a un'email esistente mantenendo lo stesso thread. Richiede l'ID dell'email o del thread a cui rispondere."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": "L'ID dell'email a cui rispondere"
                },
                "body": {
                    "type": "string",
                    "description": "Contenuto della risposta"
                }
            },
            "required": ["message_id", "body"]
        }

    async def execute(self, **kwargs) -> Any:
        if not GOOGLE_CLIENT:
            return "Errore: Google Workspace non configurato."
            
        msg_id = kwargs.get("message_id")
        body = kwargs.get("body")
        
        email_detail = GOOGLE_CLIENT.get_email_details(msg_id)
        if not email_detail:
            return f"Errore: Impossibile trovare l'email con ID {msg_id}"
            
        return GOOGLE_CLIENT.send_email(
            to=email_detail['from'],
            subject=f"Re: {email_detail['subject']}",
            body=body,
            thread_id=email_detail['threadId']
        )
