"""Tests for LLM Switch functionality."""

import pytest
from unittest.mock import patch, MagicMock

from src.config.settings import LLMProvider
from src.llm.base import Message, LLMResponse
from src.llm.factory import get_llm_client, get_provider_info


class TestLLMFactory:
    """Test the LLM factory (Brain Switch)."""
    
    def test_get_provider_info_gemini(self):
        """Test provider info with Gemini configuration."""
        with patch("src.llm.factory.settings") as mock_settings:
            mock_settings.llm_provider = LLMProvider.GEMINI
            mock_settings.is_gemini_mode.return_value = True
            mock_settings.is_claude_mode.return_value = False
            
            info = get_provider_info()
            
            assert info["provider"] == "gemini"
            assert info["is_gemini"] is True
            assert info["is_claude"] is False
            assert info["computer_use_available"] is False
    
    def test_get_provider_info_claude(self):
        """Test provider info with Claude configuration."""
        with patch("src.llm.factory.settings") as mock_settings:
            mock_settings.llm_provider = LLMProvider.CLAUDE
            mock_settings.is_gemini_mode.return_value = False
            mock_settings.is_claude_mode.return_value = True
            
            info = get_provider_info()
            
            assert info["provider"] == "claude"
            assert info["is_gemini"] is False
            assert info["is_claude"] is True
            assert info["computer_use_available"] is True
    
    def test_get_llm_client_gemini(self):
        """Test factory returns GeminiClient when configured."""
        with patch("src.llm.factory.settings") as mock_settings:
            mock_settings.llm_provider = LLMProvider.GEMINI
            mock_settings.gemini_api_key = "test-key"
            
            # Factory uses a local import, so patch the class in its own module
            with patch("src.llm.gemini_client.GeminiClient") as mock_client:
                mock_client.return_value = MagicMock()
                
                client = get_llm_client()
                
                mock_client.assert_called_once_with(api_key="test-key")
    
    def test_get_llm_client_claude(self):
        """Test factory returns ClaudeClient when configured."""
        with patch("src.llm.factory.settings") as mock_settings:
            mock_settings.llm_provider = LLMProvider.CLAUDE
            mock_settings.anthropic_api_key = "test-key"
            
            # Factory uses a local import, so patch the class in its own module
            with patch("src.llm.claude_client.ClaudeClient") as mock_client:
                mock_client.return_value = MagicMock()
                
                client = get_llm_client()
                
                mock_client.assert_called_once_with(api_key="test-key")
    
    def test_get_llm_client_missing_gemini_key(self):
        """Test factory raises error when Gemini key is missing."""
        with patch("src.llm.factory.settings") as mock_settings:
            mock_settings.llm_provider = LLMProvider.GEMINI
            mock_settings.gemini_api_key = ""
            
            with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
                get_llm_client()
    
    def test_get_llm_client_missing_claude_key(self):
        """Test factory raises error when Claude key is missing."""
        with patch("src.llm.factory.settings") as mock_settings:
            mock_settings.llm_provider = LLMProvider.CLAUDE
            mock_settings.anthropic_api_key = ""
            
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
                get_llm_client()


class TestMessageModels:
    """Test Pydantic models."""
    
    def test_message_creation(self):
        """Test Message model creation."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
    
    def test_llm_response_creation(self):
        """Test LLMResponse model creation."""
        response = LLMResponse(
            content="Hello back!",
            tool_calls=None,
            finish_reason="stop",
        )
        assert response.content == "Hello back!"
        assert response.tool_calls is None
