from typing import Any
from src.memory.memory_store import store
from src.core.tools.tool_base import BaseTool

class RememberTool(BaseTool):
    """Tool to explicitly store a memory."""
    
    @property
    def name(self) -> str:
        return "remember"

    @property
    def description(self) -> str:
        return "Salva un'informazione importante sull'utente a lungo termine. Usa questo tool per ricordare fatti, preferenze, persone o progetti che potrebbero servire in futuro."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "description": "Categoria dell'informazione (es. 'contact', 'preference', 'project', 'fact')",
                    "enum": ["contact", "preference", "project", "fact"]
                },
                "content": {
                    "type": "string",
                    "description": "L'informazione da ricordare in modo chiaro e conciso"
                },
                "importance": {
                    "type": "number",
                    "description": "Importanza da 0.0 a 10.0 (default 5.0)",
                    "default": 5.0
                }
            },
            "required": ["type", "content"]
        }

    async def execute(self, **kwargs) -> Any:
        mem_type = kwargs.get("type", "fact")
        content = kwargs.get("content", "")
        importance = float(kwargs.get("importance", 5.0))
        
        mem_id = await store.add_memory(mem_type, content, importance)
        return f"Memoria salvata correttamente con ID {mem_id}"


class RecallTool(BaseTool):
    """Tool to search the memory store."""
    
    @property
    def name(self) -> str:
        return "recall"

    @property
    def description(self) -> str:
        return "Cerca nella memoria a lungo termine informazioni passate sull'utente tramite parole chiave."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "La parola chiave o frase da cercare in memoria"
                },
                "limit": {
                    "type": "integer",
                    "description": "Numero massimo di risultati da restituire (default 3)",
                    "default": 3
                }
            },
            "required": ["query"]
        }

    async def execute(self, **kwargs) -> Any:
        query = kwargs.get("query", "")
        limit = int(kwargs.get("limit", 3))
        
        results = await store.search_memories(query, limit)
        
        if not results:
            return f"Nessuna memoria trovata per: '{query}'"
            
        lines = [f"Recuperate {len(results)} memorie per '{query}':"]
        for r in results:
            lines.append(f"- [{r.type}] {r.content} (Importanza: {r.importance})")
            
        return "\n".join(lines)
