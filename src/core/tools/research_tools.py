import logging
import httpx
import re
from typing import Any, List
from src.core.tools.tool_base import BaseTool
from src.llm import Message
from src.llm.factory import get_llm_client

logger = logging.getLogger(__name__)

class SummarizeUrlTool(BaseTool):
    """Tool to fetch and summarize content from a URL."""
    
    @property
    def name(self) -> str:
        return "summarize_url"

    @property
    def description(self) -> str:
        return "Scarica il contenuto di una pagina web e ne fornisce un riassunto strutturato. Utile per leggere articoli o documentazione."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "L'URL della pagina da analizzare"
                }
            },
            "required": ["url"]
        }

    async def execute(self, **kwargs) -> Any:
        url = kwargs.get("url")
        
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                # Basic HTML cleaning (just remove tags for a quick and dirty text extraction)
                # In a real production app, we'd use BeautifulSoup or a dedicated readability service
                text = response.text
                text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
                clean_text = re.sub(r'<.*?>', ' ', text)
                clean_text = ' '.join(clean_text.split())[:10000] # Cap at 10k chars
                
                llm = get_llm_client()
                prompt = f"Riassumi in modo professionale il seguente contenuto estratto dalla pagina {url}. Usa punti elenco e evidenzia le informazioni chiave.\n\nCONTENUTO:\n{clean_text}"
                
                res = await llm.chat(
                    messages=[Message(role="user", content=prompt)],
                    temperature=0.3
                )
                
                return res.content

        except Exception as e:
            logger.error(f"URL summarize error for {url}: {e}")
            return f"Errore durante l'analisi dell'URL: {str(e)}"


class WebSearchTool(BaseTool):
    """Tool to perform a web search (Placeholder for now, uses basic scraping or suggests API)."""
    
    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Cerca informazioni sul web su un determinato argomento."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "L'argomento della ricerca"
                }
            },
            "required": ["query"]
        }

    async def execute(self, **kwargs) -> Any:
        query = kwargs.get("query")
        
        # For now, we'll use a public search engine with basic scraping
        # WARNING: This is fragile. Proper implementation should use Serper, Tavily or Google Search API.
        try:
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"User-Agent": "Mozilla/5.0"}
                response = await client.get(search_url, headers=headers)
                
                if response.status_code == 200:
                    # Very basic "extraction" - in a real app, use a real API
                    return f"Ho effettuato la ricerca per '{query}'. Purtroppo senza un'API di ricerca dedicata (come Serper o Tavily), non posso estrarre i link in modo affidabile, ma posso provare ad analizzare una URL specifica se me la fornisci."
                else:
                    return f"Ricerca per '{query}' fallita con status {response.status_code}."
        except Exception as e:
            return f"Errore nella ricerca: {str(e)}"
