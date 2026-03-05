"""Brain Orchestrator - Core AI logic."""

import logging
import tenacity
from typing import Any

from src.llm import BaseLLMClient, Message, ToolCall, LLMResponse
from src.llm.factory import get_llm_client
from .system_prompt import EXECUTIVE_ASSISTANT_PROMPT, TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

# Max number of messages to keep in conversation history.
# Older messages are trimmed to avoid token bloat and rate limit exhaustion.
MAX_HISTORY_MESSAGES = 20

# Max number of tool-call iterations per user message to prevent infinite loops.
MAX_TOOL_ITERATIONS = 5

# Integration Clients
try:
    from src.integrations.google_client import GoogleWorkspaceClient
    GOOGLE_CLIENT = GoogleWorkspaceClient()
except Exception as e:
    logger.error(f"Failed to initialize Google Client: {e}")
    GOOGLE_CLIENT = None


class BrainOrchestrator:
    """Core AI orchestrator that processes user input and manages tool execution.
    
    This class handles:
    - Conversation management
    - LLM interaction (via the Brain Switch)
    - Tool execution and response handling
    """
    
    def __init__(self):
        """Initialize the Brain with the configured LLM client."""
        self.llm: BaseLLMClient = get_llm_client()
        self.conversation_history: list[Message] = []
        self.tool_handlers: dict[str, callable] = {}
        
        # Register tool handlers
        self.register_tool_handler("get_calendar_events", self._handle_get_calendar)
        self.register_tool_handler("create_calendar_event", self._handle_create_event)
        self.register_tool_handler("create_document", self._handle_create_document)
        self.register_tool_handler("search_drive_files", self._handle_search_drive)
        self.register_tool_handler("get_document_content", self._handle_get_document_content)

        # Placeholders for tools not yet implemented
        for tool_name in ["set_location_reminder", "remember", "recall"]:
             self.register_tool_handler(tool_name, self._default_tool_handler)
        
        logger.info(f"Brain initialized with provider: {self.llm.provider_name}")
    
    def register_tool_handler(self, tool_name: str, handler: callable):
        """Register a handler function for a tool.
        
        Args:
            tool_name: Name matching a tool in TOOL_DEFINITIONS
            handler: Async callable that executes the tool
        """
        self.tool_handlers[tool_name] = handler
        logger.debug(f"Registered handler for tool: {tool_name}")
    
    async def _handle_get_calendar(self, **kwargs):
        """Handle get_calendar_events tool."""
        if not GOOGLE_CLIENT:
            return "Errore: Google Workspace non configurato."
        
        # Handle 'days' robustly (LLM might send null or strings)
        days_val = kwargs.get("days")
        if days_val is None:
            days = 7
        else:
            try:
                days = int(days_val)
            except (ValueError, TypeError):
                days = 7
                
        return GOOGLE_CLIENT.list_calendar_events(days=days)

    async def _handle_create_event(self, **kwargs):
        """Handle create_calendar_event tool."""
        if not GOOGLE_CLIENT:
            return "Errore: Google Workspace non configurato."
            
        summary = kwargs.get("title")  # tool definition uses 'title', not 'summary'
        start_time = kwargs.get("start_time")
        end_time = kwargs.get("end_time")
        description = kwargs.get("description", "")
        
        return GOOGLE_CLIENT.create_calendar_event(summary, start_time, end_time, description)

    async def _handle_create_document(self, **kwargs):
        """Handle create_document tool."""
        if not GOOGLE_CLIENT:
            return "Errore: Google Workspace non configurato."
        title = kwargs.get("title", "Documento senza titolo")
        content = kwargs.get("content", "")
        folder_name = kwargs.get("folder_name")
        return GOOGLE_CLIENT.create_document(title, content, folder_name)

    async def _handle_search_drive(self, **kwargs):
        """Handle search_drive_files tool."""
        if not GOOGLE_CLIENT:
            return "Errore: Google Workspace non configurato."
        query = kwargs.get("query", "")
        max_results = int(kwargs.get("max_results", 10))
        return GOOGLE_CLIENT.search_drive_files(query, max_results)

    async def _handle_get_document_content(self, **kwargs):
        """Handle get_document_content tool."""
        if not GOOGLE_CLIENT:
            return "Errore: Google Workspace non configurato."
        doc_id = kwargs.get("doc_id", "")
        return GOOGLE_CLIENT.get_document_content(doc_id)

    async def _default_tool_handler(self, **kwargs):
        """Default handler for unimplemented tools."""
        return "Funzionalità non ancora implementata nel sistema reale."
    
    async def process_message(
        self,
        user_message: str,
        user_context: dict | None = None,
    ) -> str:
        """Process a user message and return the AI response."""
        try:
            return await self._process_message_internal(user_message, user_context)
        except Exception as e:
            logger.error(f"Global Brain Error: {e}")
            
            # Unwrap tenacity RetryError
            if isinstance(e, tenacity.RetryError):
                e = e.last_attempt.exception()
            
            error_msg = str(e)
            if "429" in error_msg or "Resource exhausted" in error_msg:
                return "⚠️ Sono un po' sovraccarica (Limite API Gemini). Per favore, aspetta 30 secondi e riprova."
            
            return f"⚠️ Mi scusi, ho riscontrato un problema tecnico: {type(e).__name__} - {error_msg}"

    def _trim_history(self):
        """Trim conversation history to MAX_HISTORY_MESSAGES to limit token usage."""
        if len(self.conversation_history) > MAX_HISTORY_MESSAGES:
            trimmed = len(self.conversation_history) - MAX_HISTORY_MESSAGES
            self.conversation_history = self.conversation_history[-MAX_HISTORY_MESSAGES:]
            logger.debug(f"History trimmed: removed {trimmed} old messages, keeping {MAX_HISTORY_MESSAGES}")

    async def _process_message_internal(
        self,
        user_message: str,
        user_context: dict | None = None,
    ) -> str:
        """Internal message processing logic."""
        # Add user message to history
        self.conversation_history.append(
            Message(role="user", content=user_message)
        )

        # Trim history BEFORE sending to LLM to avoid token bloat
        self._trim_history()
        logger.debug(f"History length before LLM call: {len(self.conversation_history)} messages")

        # Build context-aware system prompt
        system_prompt = self._build_system_prompt(user_context)

        # Agentic tool-call loop with a hard cap to prevent infinite iteration
        for iteration in range(MAX_TOOL_ITERATIONS):
            response = await self.llm.chat(
                messages=self.conversation_history,
                tools=TOOL_DEFINITIONS,
                system_prompt=system_prompt,
            )

            if not response.tool_calls:
                # No more tool calls — we have the final answer
                final_response = response.content or "Mi scusi, non ho capito. Può ripetere?"
                self.conversation_history.append(
                    Message(role="assistant", content=final_response)
                )
                return final_response

            # LLM wants to call tools — execute them and loop
            logger.info(f"Tool call iteration {iteration + 1}/{MAX_TOOL_ITERATIONS}: {[tc.name for tc in response.tool_calls]}")
            self.conversation_history.append(
                Message(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
            )
            await self._execute_tool_calls_into_history(response)

        # Safety: if we exit the loop without a final answer, log a warning
        logger.warning(f"Reached MAX_TOOL_ITERATIONS ({MAX_TOOL_ITERATIONS}) — forcing stop.")
        return "Mi scusi, ho impiegato troppi passi per rispondere. Può riformulare la richiesta?"
    
    def _build_system_prompt(self, context: dict | None) -> str:
        """Build system prompt with optional context."""
        prompt = EXECUTIVE_ASSISTANT_PROMPT
        
        if context:
            prompt += "\n\n## Contesto Attuale\n"
            if "location" in context:
                prompt += f"- Posizione: {context['location']}\n"
            if "time" in context:
                prompt += f"- Ora locale: {context['time']}\n"
            if "pending_reminders" in context:
                prompt += f"- Promemoria pendenti: {context['pending_reminders']}\n"
        
        return prompt
    
    async def _execute_tool_calls_into_history(self, response: LLMResponse):
        """Execute all tool calls from a response and append results to history."""
        for tool_call in response.tool_calls:
            result = await self._execute_tool(tool_call)
            self.conversation_history.append(
                Message(
                    role="tool",
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                    content=str(result),
                )
            )
    
    async def _execute_tool(self, tool_call: ToolCall) -> Any:
        """Execute a single tool call.
        
        Args:
            tool_call: The tool call to execute
            
        Returns:
            Tool execution result
        """
        handler = self.tool_handlers.get(tool_call.name)
        
        if handler is None:
            logger.warning(f"No handler for tool: {tool_call.name}")
            return {"error": f"Tool '{tool_call.name}' non disponibile"}
        
        try:
            result = await handler(**tool_call.arguments)
            logger.info(f"Tool '{tool_call.name}' executed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {"error": str(e)}
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_history_length(self) -> int:
        """Get number of messages in history."""
        return len(self.conversation_history)
