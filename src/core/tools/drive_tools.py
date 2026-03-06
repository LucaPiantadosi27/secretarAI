import logging
from typing import Any
from src.core.tools.tool_base import BaseTool

from src.integrations.google_client import GOOGLE_CLIENT

logger = logging.getLogger(__name__)

class CreateDocumentTool(BaseTool):
    """Tool to create a Google Doc."""
    
    @property
    def name(self) -> str:
        return "create_document"

    @property
    def description(self) -> str:
        return "Crea un nuovo Google Doc con titolo e contenuto specificati."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Titolo del documento"
                },
                "content": {
                    "type": "string",
                    "description": "Contenuto iniziale del documento"
                },
                "folder_name": {
                    "type": "string",
                    "description": "Nome della cartella Drive dove salvare (opzionale)"
                }
            },
            "required": ["title", "content"]
        }

    async def execute(self, **kwargs) -> Any:
        if not GOOGLE_CLIENT:
            return "Errore: Google Workspace non configurato."
            
        title = kwargs.get("title", "Documento senza titolo")
        content = kwargs.get("content", "")
        folder_name = kwargs.get("folder_name")
        return GOOGLE_CLIENT.create_document(title, content, folder_name)


class SearchDriveFilesTool(BaseTool):
    """Tool to search Drive files."""
    
    @property
    def name(self) -> str:
        return "search_drive_files"

    @property
    def description(self) -> str:
        return "Cerca file nel Google Drive dell'utente per nome o parola chiave."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Termine di ricerca (nome file o parola chiave)"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Numero massimo di risultati (default: 10)",
                    "default": 10
                }
            },
            "required": ["query"]
        }

    async def execute(self, **kwargs) -> Any:
        if not GOOGLE_CLIENT:
            return "Errore: Google Workspace non configurato."
            
        query = kwargs.get("query", "")
        try:
            max_results = int(kwargs.get("max_results", 10))
        except (ValueError, TypeError):
            max_results = 10
            
        return GOOGLE_CLIENT.search_drive_files(query, max_results)


class GetDocumentContentTool(BaseTool):
    """Tool to read Google Doc content."""
    
    @property
    def name(self) -> str:
        return "get_document_content"

    @property
    def description(self) -> str:
        return "Recupera il contenuto testuale di un Google Doc tramite il suo ID."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "doc_id": {
                    "type": "string",
                    "description": "ID del documento Google (dalla URL: /document/d/DOC_ID/edit)"
                }
            },
            "required": ["doc_id"]
        }

    async def execute(self, **kwargs) -> Any:
        if not GOOGLE_CLIENT:
            return "Errore: Google Workspace non configurato."
            
        doc_id = kwargs.get("doc_id", "")
        return GOOGLE_CLIENT.get_document_content(doc_id)
