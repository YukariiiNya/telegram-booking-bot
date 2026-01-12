"""
Hybrid mode: Telegram polling + Bukza webhook server
Use this for local development with ngrok/localtunnel
"""
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
from bot_setup import setup_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def start_webhook_server(app: web.Application):
    """Start webhook server for Bukza"""
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("🌐 Webhook server started on http://0.0.0.0:8080")
    logger.info(f"📡 Bukza webhook URL: {settings.webhook_host}/webhook/bukza")


async def main():
    """Main function - polling for Telegram + webhook for Bukza"""
    logger.info("Starting bot in HYBRID mode...")
    
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
    
    # Setup bot (commands, description)
    await setup_bot(bot)
    
    # Create web app for Bukza webhooks
    app = web.Application()
    app['bot'] = bot
    app['dp'] = dp
    app.router.add_post('/webhook/bukza', handle_webhook)
    
    # Start webhook server
    await start_webhook_server(app)
    
    logger.info("🤖 Bot started with Telegram polling!")
    logger.info(f"📡 Bukza webhook: {settings.webhook_host}/webhook/bukza")
    
    try:
        # Start Telegram polling
        await dp.start_polling(bot)
    finally:
        stop_scheduler()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == '__main__':
    asyncio.run(main())
