"""Google Gemini LLM Client implementation."""

import logging
from google import genai
from google.genai import types

from .base import BaseLLMClient, Message, ToolCall, LLMResponse

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    """Google Gemini API client using the new google-genai SDK.
    
    Recommended for DEV/TEST mode.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-flash-latest",
    ):
        """Initialize Gemini client.
        
        Args:
            api_key: Google AI API key
            model: Model name (default: gemini-1.5-flash)
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = model
    
    @property
    def provider_name(self) -> str:
        return "gemini"
    
    def _convert_messages_to_gemini_format(
        self,
        messages: list[Message],
        system_prompt: str | None = None
    ) -> tuple[list[types.Content], types.Content | None]:
        """Convert messages to Gemini format.
        
        Returns:
            Tuple of (contents, system_instruction)
        """
        contents = []
        system_instruction = None
        
        if system_prompt:
            system_instruction = types.Content(
                role="system",
                parts=[types.Part.from_text(text=system_prompt)]
            )
        
        for msg in messages:
            if msg.role == "system":
                # If system prompt is in messages, override/set it
                system_instruction = types.Content(
                    role="system",
                    parts=[types.Part.from_text(text=msg.content)]
                )
            elif msg.role == "tool":
                # Handle tool response
                # google-genai expects function_response part in a 'user' role content
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_function_response(
                        name=msg.name,
                        response={"result": msg.content}
                    )]
                ))
            elif msg.role == "assistant" and msg.tool_calls:
                # Handle assistant tool call
                parts = []
                if msg.content:
                    parts.append(types.Part.from_text(text=msg.content))
                
                for tc in msg.tool_calls:
                    parts.append(types.Part(
                        function_call=types.FunctionCall(
                            name=tc.name,
                            args=tc.arguments
                        ),
                        thought=tc.metadata.get("thought") if tc.metadata else None,
                        thought_signature=tc.metadata.get("thought_signature") if tc.metadata else None
                    ))
                
                contents.append(types.Content(
                    role="model",
                    parts=parts
                ))
            else:
                # Standard text message
                role = "user" if msg.role == "user" else "model"
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg.content or "")]
                ))
        
        return contents, system_instruction

    def _convert_tools_to_gemini_format(self, tools: list[dict]) -> list[types.Tool] | None:
        """Convert generic tool definitions to Gemini format."""
        if not tools:
            return None
            
        function_declarations = []
        for tool in tools:
            func_decl = types.FunctionDeclaration(
                name=tool["name"],
                description=tool.get("description", ""),
                parameters=tool.get("parameters", {}),
            )
            function_declarations.append(func_decl)
            
        return [types.Tool(function_declarations=function_declarations)]

    async def chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send messages to Gemini and get response."""
        contents, system_instruction = self._convert_messages_to_gemini_format(
            messages, system_prompt
        )
        
        gemini_tools = self._convert_tools_to_gemini_format(tools)
        
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            tools=gemini_tools,
            system_instruction=system_instruction,
            # Disable automatic function calling since our Brain orchestrator handles the tool loop
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
        )
        
        try:
            from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
            from google.genai.errors import ClientError

            def _is_retryable(exc: BaseException) -> bool:
                """Retry only on transient server errors, NOT on 429 rate limits."""
                if isinstance(exc, ClientError):
                    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
                    if status == 429:
                        logger.warning("Gemini rate limit hit (429) — NOT retrying to avoid wasting quota.")
                        return False
                    # Retry on 5xx server-side errors
                    if status is not None and 500 <= int(status) < 600:
                        return True
                return False

            @retry(
                retry=retry_if_exception(_is_retryable),
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=10)
            )
            async def generate_with_retry():
                return await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                )

            response = await generate_with_retry()
            
            return self._parse_response(response)
            
        except Exception as e:
            logger.error(f"Gemini API error after retries: {e}")
            raise

    async def chat_with_vision(
        self,
        messages: list[Message],
        images: list[bytes],
        tools: list[dict] | None = None,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Send messages with images to Gemini."""
        parts = []
        
        for img_bytes in images:
            parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/png"))
            
        if messages:
            parts.append(types.Part.from_text(text=messages[-1].content))
            
        content = types.Content(role="user", parts=parts)
        
        # We need to construct history if there are previous messages
        # checking the logic, messages[:-1] logic similar to chat needed if we support full history + vision
        # For simplicity in this method, let's just send the current multimodal message as a single turn 
        # or minimal history if needed. 
        # The prompt implies we want full chat.
        
        history_contents, system_instruction = self._convert_messages_to_gemini_format(
            messages[:-1], system_prompt
        )
        contents = history_contents + [content]

        gemini_tools = self._convert_tools_to_gemini_format(tools)
        
        config = types.GenerateContentConfig(
            tools=gemini_tools,
            system_instruction=system_instruction,
        )

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config,
        )
        
        return self._parse_response(response)

    def _parse_response(self, response) -> LLMResponse:
        """Parse Gemini response into standardized format."""
        content = None
        tool_calls = None
        
        # google-genai response object structure
        if response.candidates:
            candidate = response.candidates[0]
            
            # Check content parts
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if part.text:
                        content = part.text
                    elif part.function_call:
                        if tool_calls is None:
                            tool_calls = []
                        fc = part.function_call
                        tool_calls.append(ToolCall(
                            id=f"call_{len(tool_calls)}", # Gemini doesn't always provide IDs
                            name=fc.name,
                            arguments=fc.args if fc.args else {},
                            metadata={
                                "thought": part.thought,
                                "thought_signature": part.thought_signature
                            }
                        ))
        
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=str(response.candidates[0].finish_reason) if response.candidates else None,
            raw_response=response,
        )
