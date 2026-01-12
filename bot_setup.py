"""Bot setup and configuration module"""
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
import logging

logger = logging.getLogger(__name__)


async def setup_bot_commands(bot: Bot):
    """
    Setup bot commands menu that appears when user types /
    This runs on every bot startup to ensure commands are always up to date
    """
    commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="bookings", description="📅 Мои записи"),
        BotCommand(command="address", description="📍 Адрес и режим работы"),
        BotCommand(command="contacts", description="📞 Контакты"),
        BotCommand(command="help", description="ℹ️ Помощь")
    ]
    
    try:
        await bot.set_my_commands(commands, BotCommandScopeDefault())
        logger.info(f"✅ Bot commands menu updated: {len(commands)} commands")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to set bot commands: {e}")
        return False


async def setup_bot_description(bot: Bot):
    """
    Setup bot description and short description
    This appears in bot info and search results
    """
    description = (
        "🎯 Официальный бот развлекательного центра «Первое место»\n\n"
        "Возможности:\n"
        "• Онлайн-запись на VR-игры\n"
        "• Уведомления о записях\n"
        "• Напоминания за 1 час до визита\n"
        "• Запрос отзывов\n"
        "• Информация о центре\n\n"
        "📍 г. Уфа, Бакалинская улица, 27\n"
        "ТКЦ ULTRA, 3 этаж"
    )
    
    short_description = "🎯 Онлайн-запись в развлекательный центр «Первое место» | г. Уфа"
    
    try:
        await bot.set_my_description(description)
        await bot.set_my_short_description(short_description)
        logger.info("✅ Bot description updated")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to set bot description: {e}")
        return False


async def setup_bot(bot: Bot):
    """
    Complete bot setup - runs on every startup
    Ensures all bot settings are up to date
    """
    logger.info("🔧 Setting up bot...")
    
    # Setup commands menu
    await setup_bot_commands(bot)
    
    # Setup bot description
    await setup_bot_description(bot)
    
    # Get bot info
    try:
        me = await bot.get_me()
        logger.info(f"✅ Bot setup complete: @{me.username} (ID: {me.id})")
    except Exception as e:
        logger.error(f"❌ Failed to get bot info: {e}")
    
    logger.info("🚀 Bot is ready!")
