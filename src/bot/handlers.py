"""Telegram Bot Handlers."""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from src.config import settings
from src.brain import BrainOrchestrator
from .voice import transcribe_voice_message
from .location import process_location_update

logger = logging.getLogger(__name__)


class BotHandlers:
    """Telegram bot message handlers."""
    
    def __init__(self):
        """Initialize handlers with Brain orchestrator."""
        self.brain = BrainOrchestrator()
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register placeholder tool handlers."""
        # These will be replaced with real implementations
        async def placeholder_handler(**kwargs):
            return {"status": "Tool non ancora implementato", "args": kwargs}
        
        for tool_name in ["get_calendar_events", "create_calendar_event", 
                          "create_document", "set_location_reminder",
                          "remember", "recall"]:
            self.brain.register_tool_handler(tool_name, placeholder_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = """👋 Benvenuto! Sono **SecretarAI**, la tua assistente personale.

Posso aiutarti con:
📅 Gestione del calendario
📄 Creazione di documenti
📍 Promemoria basati sulla posizione
💾 Memorizzazione di informazioni

Scrivimi cosa ti serve o inviami un messaggio vocale!"""
        
        await update.message.reply_text(welcome_message, parse_mode="Markdown")
        logger.info(f"User {update.effective_user.id} started the bot")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """🔧 **Comandi disponibili:**

/start - Messaggio di benvenuto
/help - Mostra questo aiuto
/clear - Pulisci la cronologia conversazione

💡 **Esempi di richieste:**
- "Cosa ho in agenda domani?"
- "Crea un evento per lunedì alle 10"
- "Prepara una bozza per il cliente X"
- "Ricordami di chiamare Mario quando arrivo in ufficio"
"""
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command - reset conversation."""
        self.brain.clear_history()
        await update.message.reply_text("🗑️ Cronologia conversazione cancellata.")
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        user_message = update.message.text
        user_id = update.effective_user.id
        
        logger.info(f"Text from {user_id}: {user_message[:50]}...")
        
        # Build context
        user_context = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "user_id": user_id,
        }
        
        # Show typing indicator
        await update.message.chat.send_action("typing")
        
        try:
            # Process through Brain
            response = await self.brain.process_message(user_message, user_context)
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await update.message.reply_text(
                "⚠️ Mi scusi, si è verificato un errore. Riprovi tra poco."
            )
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages."""
        user_id = update.effective_user.id
        logger.info(f"Voice message from {user_id}")
        
        await update.message.reply_text("🎤 Sto trascrivendo il messaggio vocale...")
        
        try:
            # Download voice file
            voice = update.message.voice
            voice_file = await context.bot.get_file(voice.file_id)
            voice_bytes = await voice_file.download_as_bytearray()
            
            # Transcribe
            transcription = await transcribe_voice_message(bytes(voice_bytes))
            
            if transcription:
                await update.message.reply_text(f"📝 _\"{transcription}\"_", parse_mode="Markdown")
                
                # Process transcribed text through Brain
                user_context = {
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "user_id": user_id,
                    "input_type": "voice",
                }
                
                response = await self.brain.process_message(transcription, user_context)
                await update.message.reply_text(response)
            else:
                await update.message.reply_text("❌ Non sono riuscita a trascrivere il messaggio.")
                
        except Exception as e:
            logger.error(f"Error processing voice: {e}")
            await update.message.reply_text(
                "⚠️ Errore nella trascrizione. Riprovi con un altro messaggio."
            )
    
    async def handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle location updates."""
        user_id = update.effective_user.id
        location = update.message.location
        
        logger.info(f"Location from {user_id}: {location.latitude}, {location.longitude}")
        
        try:
            # Process location for geofencing
            result = await process_location_update(
                user_id=user_id,
                latitude=location.latitude,
                longitude=location.longitude,
            )
            
            if result.get("triggered_reminders"):
                for reminder in result["triggered_reminders"]:
                    await update.message.reply_text(f"📍 Promemoria: {reminder}")
            else:
                await update.message.reply_text("📍 Posizione ricevuta!")
                
        except Exception as e:
            logger.error(f"Error processing location: {e}")


def create_bot() -> Application:
    """Create and configure the Telegram bot application."""
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required")
    
    # Create application
    application = Application.builder().token(settings.telegram_bot_token).build()
    
    # Initialize handlers
    handlers = BotHandlers()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("clear", handlers.clear_command))
    
    # Register message handlers
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_text)
    )
    application.add_handler(
        MessageHandler(filters.VOICE, handlers.handle_voice)
    )
    application.add_handler(
        MessageHandler(filters.LOCATION, handlers.handle_location)
    )
    
    logger.info("Telegram bot configured successfully")
    return application
