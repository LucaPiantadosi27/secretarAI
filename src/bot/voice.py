"""Voice message transcription."""

import logging
from src.config import settings, VoiceProvider

logger = logging.getLogger(__name__)


async def transcribe_voice_message(audio_bytes: bytes) -> str | None:
    """Transcribe voice message to text.
    
    Uses either OpenAI Whisper or Gemini based on VOICE_PROVIDER setting.
    
    Args:
        audio_bytes: Raw audio data (OGG format from Telegram)
        
    Returns:
        Transcribed text or None if failed
    """
    provider = settings.voice_provider
    
    if provider == VoiceProvider.WHISPER:
        return await _transcribe_with_whisper(audio_bytes)
    elif provider == VoiceProvider.GEMINI:
        return await _transcribe_with_gemini(audio_bytes)
    else:
        logger.error(f"Unknown voice provider: {provider}")
        return None


async def _transcribe_with_whisper(audio_bytes: bytes) -> str | None:
    """Transcribe using OpenAI Whisper API."""
    try:
        from openai import AsyncOpenAI
        
        if not settings.openai_api_key:
            logger.error("OPENAI_API_KEY required for Whisper transcription")
            return None
        
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        # Whisper expects a file-like object
        import io
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "voice.ogg"
        
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="it",  # Italian
        )
        
        return response.text
        
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        return None


async def _transcribe_with_gemini(audio_bytes: bytes) -> str | None:
    """Transcribe using Gemini multimodal capabilities."""
    try:
        from google import genai
        from google.genai import types
        
        if not settings.gemini_api_key:
            logger.error("GEMINI_API_KEY required for Gemini transcription")
            return None
        
        client = genai.Client(api_key=settings.gemini_api_key)
        
        # Create multimodal content
        prompt = "Trascrivi esattamente questo messaggio audio in italiano. Rispondi solo con la trascrizione, senza commenti."
        
        parts = [
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=audio_bytes, mime_type="audio/ogg")
        ]
        
        response = await client.aio.models.generate_content(
            model="gemini-flash-latest",
            contents=[types.Content(role="user", parts=parts)]
        )
        
        return response.text
        
    except Exception as e:
        logger.error(f"Gemini transcription failed: {e}")
        return None
