"""Anthropic Claude LLM Client implementation."""

import base64
from anthropic import AsyncAnthropic

from .base import BaseLLMClient, Message, ToolCall, LLMResponse


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude API client.
    
    Recommended for PROD mode - superior reasoning and Computer Use capability.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
    ):
        """Initialize Claude client.
        
        Args:
            api_key: Anthropic API key
            model: Model name (default: claude-sonnet-4-20250514)
        """
        self.client = AsyncAnthropic(api_key=api_key)
        self.model_name = model
    
    @property
    def provider_name(self) -> str:
        return "claude"
    
    def _convert_messages_to_claude_format(
        self,
        messages: list[Message]
    ) -> tuple[list[dict], str | None]:
        """Convert messages to Claude format.
        
        Returns:
            Tuple of (messages, system_prompt)
        """
        claude_messages = []
        system_prompt = None
        
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            elif msg.role == "tool":
                # Claude requires tool results as user messages with a tool_result block
                claude_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id or msg.name or "",
                        "content": msg.content or "",
                    }],
                })
            else:
                claude_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })
        
        return claude_messages, system_prompt
    
    def _convert_tools_to_claude_format(self, tools: list[dict]) -> list[dict]:
        """Convert generic tool definitions to Claude format."""
        claude_tools = []
        
        for tool in tools:
            claude_tool = {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "input_schema": tool.get("parameters", {"type": "object", "properties": {}}),
            }
            claude_tools.append(claude_tool)
        
        return claude_tools
    
    async def chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send messages to Claude and get response."""
        claude_messages, extracted_system = self._convert_messages_to_claude_format(messages)
        
        # Use provided system_prompt or extracted from messages
        final_system = system_prompt or extracted_system
        
        # Build request kwargs
        kwargs = {
            "model": self.model_name,
            "max_tokens": max_tokens,
            "messages": claude_messages,
            "temperature": temperature,
        }
        
        if final_system:
            kwargs["system"] = final_system
        
        if tools:
            kwargs["tools"] = self._convert_tools_to_claude_format(tools)
        
        response = await self.client.messages.create(**kwargs)
        
        return self._parse_response(response)
    
    async def chat_with_vision(
        self,
        messages: list[Message],
        images: list[bytes],
        tools: list[dict] | None = None,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Send messages with images to Claude.
        
        This method supports Claude's Computer Use capability when
        combined with appropriate tools.
        """
        claude_messages, extracted_system = self._convert_messages_to_claude_format(messages)
        
        # Build content with images for the last user message
        if claude_messages and images:
            # Create multimodal content
            content_parts = []
            
            for img_bytes in images:
                b64_image = base64.standard_b64encode(img_bytes).decode("utf-8")
                content_parts.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": b64_image,
                    },
                })
            
            # Add text from the last message
            if messages:
                content_parts.append({
                    "type": "text",
                    "text": messages[-1].content,
                })
            
            # Replace last message content with multimodal content
            if claude_messages:
                claude_messages[-1]["content"] = content_parts
        
        final_system = system_prompt or extracted_system
        
        kwargs = {
            "model": self.model_name,
            "max_tokens": 4096,
            "messages": claude_messages,
        }
        
        if final_system:
            kwargs["system"] = final_system
        
        if tools:
            kwargs["tools"] = self._convert_tools_to_claude_format(tools)
        
        response = await self.client.messages.create(**kwargs)
        
        return self._parse_response(response)
    
    def _parse_response(self, response) -> LLMResponse:
        """Parse Claude response into standardized format."""
        content = None
        tool_calls = None
        
        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input,
                ))
        
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=response.stop_reason,
            raw_response=response,
        )
