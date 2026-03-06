import logging
import json
from src.memory.memory_store import MemoryStore
from src.llm import BaseLLMClient, Message

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages high-level memory operations including LLM extraction."""
    
    def __init__(self, store: MemoryStore, llm: BaseLLMClient):
        self.store = store
        self.llm = llm
        
    async def extract_and_store(self, conversation: list[Message]) -> int:
        """Analyze a conversation and extract facts to remember.
        
        Returns:
            Number of new memories stored.
        """
        # We only need the last few messages to extract context
        recent = conversation[-4:] if len(conversation) > 4 else conversation
        
        transcript = []
        for msg in recent:
            if msg.role in ("user", "assistant") and msg.content:
                transcript.append(f"{msg.role.upper()}: {msg.content}")
                
        if not transcript:
            return 0
            
        transcript_text = "\n".join(transcript)
        
        prompt = f"""
    Analizza la seguente conversazione recente tra l'utente e l'assistente.
    Il tuo compito è estrarre fatti persistenti, preferenze o informazioni di contatto sull'utente che potrebbero essere utili in futuro.
    
    ESEMPI DI FATTI DA ESTRARRE:
    - "Il mio capo si chiama Marco" -> type: contact, content: Il capo dell'utente si chiama Marco.
    - "Sono intollerante al lattosio" -> type: preference, content: L'utente è intollerante al lattosio.
    - "Sto lavorando al progetto Apollo" -> type: project, content: L'utente sta lavorando al progetto Apollo.
    
    ESEMPI DA IGNORARE:
    - "Che ore sono?"
    - "Ricordami di comprare il latte domani" (questo è un task, non una memoria a lungo termine)
    
    CONVERSAZIONE:
    {transcript_text}
    
    Rispondi SOLO con un array JSON valido di oggetti. Se non c'è nulla da estrarre, rispondi con [].
    Formato:
    [
      {{"type": "contact", "content": "Il fratello dell'utente si chiama Giovanni", "importance": 0.8}}
    ]
    """
        
        try:
            response = await self.llm.chat(
                messages=[Message(role="user", content=prompt)],
                temperature=0.1
            )
            
            content = response.content or "[]"
            # Pulizia grezza se l'LLM aggiunge markdown
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
                
            extracted = json.loads(content.strip())
            
            count = 0
            for item in extracted:
                if "type" in item and "content" in item:
                    await self.store.add_memory(
                        type_category=item["type"],
                        content=item["content"],
                        importance=float(item.get("importance", 0.5))
                    )
                    count += 1
                    
            if count > 0:
                logger.info(f"Extracted and stored {count} new memories from conversation")
                
            return count
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from memory extraction")
        except Exception as e:
            logger.error(f"Memory extraction failed: {e}")
            
        return 0

    async def get_relevant_context(self, user_query: str) -> str:
        """Retrieve memories relevant to the current user query."""
        try:
            memories = await self.store.search_memories(user_query, limit=3)
            if not memories:
                return ""
                
            context_lines = ["\n## Memorie Rilevanti:"]
            for m in memories:
                context_lines.append(f"- [{m.type}] {m.content}")
                
            return "\n".join(context_lines) + "\n"
        except Exception as e:
            logger.error(f"Failed to get relevant context: {e}")
            return ""
