"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel


class Message(BaseModel):
    """Chat message structure."""
    role: str  # "user" | "assistant" | "system"
    content: str


class ToolCall(BaseModel):
    """Tool/function call request from LLM."""
    id: str
    name: str
    arguments: dict[str, Any]


class LLMResponse(BaseModel):
    """Standardized response from any LLM provider."""
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    finish_reason: str | None = None
    raw_response: Any = None  # Provider-specific response for debugging

    class Config:
        arbitrary_types_allowed = True


class BaseLLMClient(ABC):
    """Abstract base class for LLM providers.
    
    All LLM implementations must inherit from this class and implement
    the required methods. This enables the "Brain Switch" pattern.
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'gemini', 'claude')."""
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send messages and get a response.
        
        Args:
            messages: Conversation history
            tools: Optional list of tool definitions for function calling
            system_prompt: Optional system prompt to set context
            temperature: Creativity parameter (0.0 - 1.0)
            max_tokens: Maximum response length
            
        Returns:
            Standardized LLMResponse
        """
        pass
    
    @abstractmethod
    async def chat_with_vision(
        self,
        messages: list[Message],
        images: list[bytes],
        tools: list[dict] | None = None,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Chat with image understanding capability.
        
        Used for multimodal tasks and Computer Use features.
        
        Args:
            messages: Conversation history
            images: List of image bytes
            tools: Optional tool definitions
            system_prompt: Optional system prompt
            
        Returns:
            Standardized LLMResponse
        """
        pass
    
    def format_tools_for_provider(self, tools: list[dict]) -> list[dict]:
        """Convert generic tool definitions to provider-specific format.
        
        Override this in subclasses if the provider requires specific formatting.
        Default implementation returns tools unchanged.
        """
        return tools
