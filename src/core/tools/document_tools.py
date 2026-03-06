import logging
from typing import Any
from src.core.tools.tool_base import BaseTool
from src.documents.document_store import doc_store
from src.integrations.google_client import GOOGLE_CLIENT
from src.llm.factory import get_llm_client
from src.llm import Message

logger = logging.getLogger(__name__)

class IndexDriveDocTool(BaseTool):
    """Tool to index a Google Doc into the semantic document store."""
    
    @property
    def name(self) -> str:
        return "index_document"

    @property
    def description(self) -> str:
        return "Scarica un Google Doc, lo divide in frammenti e lo indicizza per ricerche avanzate. Usa questo tool quando l'utente vuole 'analizzare' o 'imparare' il contenuto di un file specifico."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "doc_id": {
                    "type": "string",
                    "description": "L'ID del documento Google da indicizzare"
                },
                "title": {
                    "type": "string",
                    "description": "Titolo del documento (opzionale)"
                }
            },
            "required": ["doc_id"]
        }

    async def execute(self, **kwargs) -> Any:
        if not GOOGLE_CLIENT:
            return "Errore: Google Workspace non disponibile."
            
        doc_id = kwargs.get("doc_id")
        title = kwargs.get("title")
        
        try:
            # Get content using existing integration
            doc_content_res = GOOGLE_CLIENT.get_document_content(doc_id)
            if doc_content_res.startswith("Errore"):
                return doc_content_res
            
            # Extract content after title if present in the response string
            # (Note: get_document_content returns '📄 **Title**\n\nContent')
            lines = doc_content_res.split("\n\n", 1)
            content = lines[1] if len(lines) > 1 else doc_content_res
            if not title:
                title = lines[0].replace("📄 **", "").replace("**", "") or "Documento senza titolo"

            # Index it
            await doc_store.initialize()
            await doc_store.index_document(title, content, doc_id)
            
            return f"✅ Documento '{title}' indicizzato con successo. Ora puoi interrogarne il contenuto con 'search_documents'."

        except Exception as e:
            logger.error(f"Index drive doc error: {e}")
            return f"Errore durante l'indicizzazione: {str(e)}"


class SearchDocumentsTool(BaseTool):
    """Tool to search across indexed documents."""
    
    @property
    def name(self) -> str:
        return "search_documents"

    @property
    def description(self) -> str:
        return "Cerca informazioni all'interno dei documenti precedentemente indicizzati."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Cosa stai cercando nei documenti?"
                }
            },
            "required": ["query"]
        }

    async def execute(self, **kwargs) -> Any:
        query = kwargs.get("query")
        
        await doc_store.initialize()
        results = await doc_store.search_documents(query)
        
        if not results:
            return f"Nessuna informazione trovata per '{query}' nei documenti indicizzati."
            
        context = "📄 **Risultati dalla ricerca documenti:**\n\n"
        for i, res in enumerate(results):
            context += f"--- Da: {res['title']} ---\n{res['content']}\n\n"
            
        # Use LLM to synthesize the results
        llm = get_llm_client()
        prompt = f"Basandoti SOLO sui frammenti di documenti forniti, rispondi alla domanda: '{query}'. Se non trovi la risposta, dillo chiaramente.\n\nCONTESTO:\n{context}"
        
        summary = await llm.chat(
            messages=[Message(role="user", content=prompt)],
            temperature=0.2
        )
        
        return summary.content
