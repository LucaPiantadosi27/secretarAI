"""Application settings loaded from environment variables."""

from enum import Enum
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GEMINI = "gemini"
    CLAUDE = "claude"


class VoiceProvider(str, Enum):
    """Supported voice transcription providers."""
    WHISPER = "whisper"
    GEMINI = "gemini"


class PCAutomationMode(str, Enum):
    """PC automation modes."""
    PYAUTOGUI = "pyautogui"
    CLAUDE_COMPUTER_USE = "claude_computer_use"


class Settings(BaseSettings):
    """Application settings with environment variable loading."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # LLM Configuration
    llm_provider: LLMProvider = Field(default=LLMProvider.GEMINI)
    gemini_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")
    
    # Telegram
    telegram_bot_token: str = Field(default="")
    telegram_webhook_url: str = Field(default="")
    allowed_user_ids: list[int] = Field(default_factory=list)
    
    # Google OAuth
    google_client_id: str = Field(default="")
    google_client_secret: str = Field(default="")
    google_redirect_uri: str = Field(default="http://localhost:8080/oauth/callback")
    
    # Voice Transcription
    openai_api_key: str = Field(default="")
    voice_provider: VoiceProvider = Field(default=VoiceProvider.WHISPER)
    
    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///./secretarai.db")
    
    # Geo Settings
    default_geofence_radius_meters: int = Field(default=100)
    
    # PC Automation
    pc_automation_enabled: bool = Field(default=False)
    pc_automation_mode: PCAutomationMode = Field(default=PCAutomationMode.PYAUTOGUI)
    
    def is_gemini_mode(self) -> bool:
        """Check if using Gemini provider."""
        return self.llm_provider == LLMProvider.GEMINI
    
    def is_claude_mode(self) -> bool:
        """Check if using Claude provider."""
        return self.llm_provider == LLMProvider.CLAUDE


# Singleton instance
settings = Settings()
