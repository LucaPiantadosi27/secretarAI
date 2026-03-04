"""Brain Orchestrator - Core AI logic."""

import logging
from typing import Any

from src.llm import BaseLLMClient, Message, ToolCall
from src.llm.factory import get_llm_client
from .system_prompt import EXECUTIVE_ASSISTANT_PROMPT, TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

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
        
        # Placeholders for others
        for tool_name in ["create_document", "set_location_reminder", "remember", "recall"]:
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
        
        days = kwargs.get("days", 3)
        return GOOGLE_CLIENT.list_calendar_events(days=int(days))

    async def _handle_create_event(self, **kwargs):
        """Handle create_calendar_event tool."""
        if not GOOGLE_CLIENT:
            return "Errore: Google Workspace non configurato."
            
        summary = kwargs.get("summary")
        start_time = kwargs.get("start_time")
        end_time = kwargs.get("end_time")
        description = kwargs.get("description", "")
        
        return GOOGLE_CLIENT.create_calendar_event(summary, start_time, end_time, description)

    async def _default_tool_handler(self, **kwargs):
        """Default handler for unimplemented tools."""
        return "Funzionalità non ancora implementata nel sistema reale."
    
    async def process_message(
        self,
        user_message: str,
        user_context: dict | None = None,
    ) -> str:
        """Process a user message and return the AI response.
        
        Args:
            user_message: The user's text input
            user_context: Optional context (location, time, etc.)
            
        Returns:
            The AI's text response
        """
        # Add user message to history
        self.conversation_history.append(
            Message(role="user", content=user_message)
        )
        
        # Build context-aware system prompt
        system_prompt = self._build_system_prompt(user_context)
        
        # Call LLM
        try:
            response = await self.llm.chat(
                messages=self.conversation_history,
                tools=TOOL_DEFINITIONS,
                system_prompt=system_prompt,
            )
        except Exception as e:
            logger.error(f"LLM Chat Error: {e}")
            
            # Unwrap tenacity RetryError
            import tenacity
            if isinstance(e, tenacity.RetryError):
                e = e.last_attempt.exception()
            
            error_msg = str(e)
            if "429" in error_msg or "Resource exhausted" in error_msg:
                return "⚠️ Sono un po' sovraccarica (Limite API Gemini). Riprova tra un attimo."
            return f"⚠️ Errore AI: {type(e).__name__} - {error_msg}"
        
        # Handle tool calls if present
        if response.tool_calls:
            # Add the assistant's tool call message to history
            self.conversation_history.append(
                Message(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls
                )
            )
            final_response = await self._handle_tool_calls(response)
        else:
            final_response = response.content or "Mi scusi, non ho capito. Può ripetere?"
            # Add assistant response to history
            self.conversation_history.append(
                Message(role="assistant", content=final_response)
            )
        
        return final_response
    
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
    
    async def _handle_tool_calls(self, response: LLMResponse) -> str:
        """Execute tool calls and get final response.
        
        Args:
            response: LLM response containing tool calls
            
        Returns:
            Final text response after tool execution
        """
        tool_results = []
        
        for tool_call in response.tool_calls:
            result = await self._execute_tool(tool_call)
            tool_results.append({
                "tool": tool_call.name,
                "result": result,
            })
        
        # Send tool results back to LLM for final response
        # Create a Tool Message for each result
        for tool_result in tool_results:
            self.conversation_history.append(
                Message(
                    role="tool",
                    tool_call_id=tool_result["tool"], # Gemini uses function name as ID often, or we generate one
                    name=tool_result["tool"],
                    content=str(tool_result["result"])
                )
            )
            
        try:    
            final_response_obj = await self.llm.chat(
                messages=self.conversation_history,
                system_prompt=EXECUTIVE_ASSISTANT_PROMPT,
            )
        except Exception as e:
            logger.error(f"LLM Tool Loop Error: {e}")
            if "429" in str(e):
                return "⚠️ Ho eseguito l'azione, ma non riesco a generare la risposta finale (Limite API). Controlla il calendario!"
            raise e
        
        # Add final response to history
        self.conversation_history.append(
            Message(role="assistant", content=final_response_obj.content)
        )
        
        return final_response_obj.content or "Operazione completata."
    
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
