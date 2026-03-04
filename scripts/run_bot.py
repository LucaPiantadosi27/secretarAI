#!/usr/bin/env python3
"""SecretarAI Bot Entry Point.

This script initializes and runs the Telegram bot with the configured LLM provider.
"""

import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import settings
from src.llm.factory import get_provider_info

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def test_llm_connection():
    """Test that the LLM client is properly configured."""
    from src.llm import get_llm_client, Message
    
    logger.info("Testing LLM connection...")
    
    try:
        client = get_llm_client()
        logger.info(f"✓ LLM Provider: {client.provider_name}")
        
        # Simple test message
        response = await client.chat(
            messages=[Message(role="user", content="Rispondi solo 'OK' se funzioni.")],
            system_prompt="Sei un assistente di test. Rispondi in modo brevissimo.",
        )
        
        logger.info(f"✓ LLM Response: {response.content}")
        return True
        
    except Exception as e:
        logger.error(f"✗ LLM connection failed: {e}")
        return False


async def run_bot():
    """Initialize and run the Telegram bot."""
    from src.bot import create_bot
    
    logger.info("Starting Telegram bot...")
    
    app = create_bot()
    
    # Run with polling (for development)
    # For production, use webhooks instead
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    logger.info("Bot is running! Press Ctrl+C to stop.")
    
    # Keep running until interrupted
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


async def main():
    """Main entry point."""
    logger.info("=" * 50)
    logger.info("SecretarAI - Starting...")
    logger.info("=" * 50)
    
    # Show provider info
    provider_info = get_provider_info()
    logger.info(f"LLM Provider: {provider_info['provider']}")
    logger.info(f"Computer Use available: {provider_info['computer_use_available']}")
    
    # Check Telegram token
    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is required. Add it to your .env file.")
        return
    
    # Test LLM connection
    try:
        success = await test_llm_connection()
        if not success:
            logger.warning("⚠️ LLM connection test failed. Bot will start, but AI features may be unavailable.")
            # We continue anyway to allow Google Auth to proceed
    except Exception as e:
        logger.error(f"Unexpected error during LLM startup check: {e}")
        # Continue anyway
    
    logger.info("-" * 50)
    logger.info("All systems ready. Starting bot...")
    logger.info("-" * 50)
    
    # Run the bot
    await run_bot()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
