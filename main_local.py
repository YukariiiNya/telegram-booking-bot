import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings
from database import init_db
from handlers.bot_handlers import router as bot_router
from services.scheduler import start_scheduler, stop_scheduler
from bot_setup import setup_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function for local development with polling"""
    logger.info("Starting bot in LOCAL mode (polling)...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Start scheduler
    start_scheduler()
    logger.info("Scheduler started")
    
    # Initialize bot and dispatcher
    bot = Bot(token=settings.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register handlers
    dp.include_router(bot_router)
    
    # Setup bot (commands, description, etc.)
    await setup_bot(bot)
    
    logger.info("Bot started! Press Ctrl+C to stop.")
    
    try:
        # Start polling
        await dp.start_polling(bot)
    finally:
        # Cleanup
        stop_scheduler()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == '__main__':
    asyncio.run(main())
