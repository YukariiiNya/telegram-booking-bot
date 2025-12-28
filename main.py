import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from config import settings
from database import init_db
from handlers.bot_handlers import router as bot_router
from handlers.webhook_handlers import handle_webhook
from services.scheduler import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def on_startup(app: web.Application):
    """Initialize bot and database on startup"""
    logger.info("Starting bot...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Start scheduler
    start_scheduler()
    logger.info("Scheduler started")
    
    # Start bot polling in background
    bot = app['bot']
    dp = app['dp']
    
    asyncio.create_task(dp.start_polling(bot))
    logger.info("Bot polling started")


async def on_shutdown(app: web.Application):
    """Cleanup on shutdown"""
    logger.info("Shutting down...")
    
    # Stop scheduler
    stop_scheduler()
    
    # Close bot session
    bot = app['bot']
    await bot.session.close()
    
    logger.info("Shutdown complete")


def create_app() -> web.Application:
    """Create and configure the application"""
    # Initialize bot and dispatcher
    bot = Bot(token=settings.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register handlers
    dp.include_router(bot_router)
    
    # Create web application
    app = web.Application()
    app['bot'] = bot
    app['dp'] = dp
    
    # Register webhook endpoint
    app.router.add_post(settings.webhook_path, handle_webhook)
    
    # Register startup/shutdown handlers
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    return app


if __name__ == '__main__':
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=8080)
