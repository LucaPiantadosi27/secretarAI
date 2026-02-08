"""LLM Provider Factory - The Brain Switch."""

from src.config.settings import settings, LLMProvider
from .base import BaseLLMClient


def get_llm_client() -> BaseLLMClient:
    """Factory function to get the configured LLM client.
    
    This is THE BRAIN SWITCH - reads LLM_PROVIDER from environment
    and returns the appropriate client instance.
    
    Returns:
        BaseLLMClient: Configured LLM client (Gemini or Claude)
        
    Raises:
        ValueError: If provider is not supported
        ValueError: If API key is missing for the selected provider
    """
    provider = settings.llm_provider
    
    if provider == LLMProvider.GEMINI:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        
        from .gemini_client import GeminiClient
        return GeminiClient(api_key=settings.gemini_api_key)
    
    elif provider == LLMProvider.CLAUDE:
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=claude")
        
        from .claude_client import ClaudeClient
        return ClaudeClient(api_key=settings.anthropic_api_key)
    
    raise ValueError(f"Unsupported LLM provider: {provider}")


def get_provider_info() -> dict:
    """Get information about the current LLM provider configuration.
    
    Returns:
        dict: Provider name and capabilities
    """
    return {
        "provider": settings.llm_provider.value,
        "is_gemini": settings.is_gemini_mode(),
        "is_claude": settings.is_claude_mode(),
        "computer_use_available": settings.is_claude_mode(),
    }
