from aiohttp import web
from datetime import datetime
from database import async_session_maker
from database.repository import UserRepository, BookingRepository, MessageRepository
from database.models import BookingStatus, MessageType
from services.scheduler import schedule_reminder, schedule_feedback_request, cancel_scheduled_tasks
from aiogram import Bot
from aiogram.types import Update, InlineKeyboardMarkup, InlineKeyboardButton
import logging

logger = logging.getLogger(__name__)


async def handle_telegram_webhook(request: web.Request) -> web.Response:
    """Handle webhook from Telegram"""
    bot = request.app['bot']
    dp = request.app['dp']
    
    try:
        data = await request.json()
        logger.info(f"Received Telegram update: {data}")
        
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
        
        return web.Response(status=200)
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {e}", exc_info=True)
        return web.Response(status=500)


async def send_reminder(booking_id: int, bot: Bot):
    """Send reminder to user"""
    async with async_session_maker() as session:
        booking_repo = BookingRepository(session)
        booking = await booking_repo.get_by_bukza_id(str(booking_id))
        
        if not booking or booking.status != BookingStatus.ACTIVE:
            logger.info(f"Skipping reminder for booking {booking_id} - not active")
            return
        
        message_repo = MessageRepository(session)
        user_repo = UserRepository(session)
        
        user = await session.get(booking.user)
        if not user:
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗺 Открыть в 2ГИС", url="https://2gis.ru/ufa/firm/70000001092498553")]
        ])
        
        try:
            await bot.send_message(
                user.telegram_id,
                f"⏰ Напоминание!\n\n"
                f"Через 1 час ваша запись:\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 {booking.service_name}\n"
                f"🕐 {booking.booking_datetime.strftime('%H:%M')}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📍 ТКЦ ULTRA, Бакалинская 27\n"
                f"3 этаж, вход со стороны парковки\n\n"
                f"Ждём вас! 🎮",
                reply_markup=keyboard
            )
            await message_repo.create(user.id, MessageType.REMINDER, booking.id)
            logger.info(f"Reminder sent for booking {booking_id}")
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")


async def send_feedback_request(booking_id: int, bot: Bot):
    """Send feedback request to user"""
    async with async_session_maker() as session:
        booking_repo = BookingRepository(session)
        booking = await booking_repo.get_by_bukza_id(str(booking_id))
        
        if not booking:
            return
        
        message_repo = MessageRepository(session)
        user = await session.get(booking.user)
        
        if not user:
            return
        
        try:
            await bot.send_message(
                user.telegram_id,
                f"Спасибо, что посетили нас! 💐\n\n"
                f"Пожалуйста, оцените услугу '{booking.service_name}' от 1 до 5:"
            )
            await message_repo.create(user.id, MessageType.FEEDBACK_REQUEST, booking.id)
            logger.info(f"Feedback request sent for booking {booking_id}")
        except Exception as e:
            logger.error(f"Failed to send feedback request: {e}")


async def handle_webhook(request: web.Request) -> web.Response:
    """Handle webhook from Bukza"""
    from config import settings
    
    bot = request.app['bot']
    
    try:
        query_params = request.rel_url.query
        message_type = query_params.get("message", "")
        phone_from_url = query_params.get("phone", "")
        
        data = await request.json()
        logger.info(f"Received webhook - message: {message_type}, phone_url: {phone_from_url}, data: {data}")
        
        bukza_booking_id = data.get("code")
        # Get name from URL param first, then from JSON
        name_from_url = query_params.get("name", "").strip()
        client_name = name_from_url or data.get("name") or "Не указано"
        # Fix empty or placeholder names
        if client_name in ["-", "", "Не указано", None]:
            client_name = "Гость"
        service_name = data.get("resource")
        start_time_str = data.get("start")
        end_time_str = data.get("end")
        total_sum = data.get("total_sum", "0")
        
        # Get phone from URL param first, then from JSON
        phone_number = phone_from_url or data.get("phone") or data.get("client_phone") or ""
        
        # Check in fields array if phone not found
        if not phone_number or phone_number == "{client_phone}":
            fields = data.get("fields", [])
            for field in fields:
                field_name = field.get("name", "").lower()
                if "телефон" in field_name or "phone" in field_name:
                    phone_number = field.get("value", "")
                    break
        
        # Normalize phone number - remove all non-digits except leading +
        phone_normalized = ""
        if phone_number:
            # Keep only digits
            digits = ''.join(c for c in phone_number if c.isdigit())
            if digits:
                # Convert to +7 format
                if digits.startswith('8') and len(digits) == 11:
                    phone_normalized = '+7' + digits[1:]
                elif digits.startswith('7') and len(digits) == 11:
                    phone_normalized = '+' + digits
                elif len(digits) == 10:
                    phone_normalized = '+7' + digits
                else:
                    phone_normalized = '+' + digits
        
        logger.info(f"Phone: {phone_number} -> Normalized: {phone_normalized}, name: {client_name}")
        
        if not all([bukza_booking_id, service_name, start_time_str]):
            logger.error("Missing required fields in webhook")
            return web.Response(status=400, text="Missing required fields")
        
        booking_datetime = datetime.strptime(start_time_str, "%d.%m.%Y %H:%M")
        end_datetime = datetime.strptime(end_time_str, "%d.%m.%Y %H:%M")
        duration_minutes = int((end_datetime - booking_datetime).total_seconds() / 60)
        
        hours = duration_minutes // 60
        mins = duration_minutes % 60
        if hours > 0 and mins > 0:
            duration_text = f"{hours} ч {mins} мин"
        elif hours > 0:
            duration_text = f"{hours} ч"
        else:
            duration_text = f"{mins} мин"
        
        package_info = ""
        if "Пакет S" in service_name or duration_minutes == 105:
            package_info = "📦 Пакет S (1 час арены + 45 мин чаепитие)"
        elif "Пакет M" in service_name or duration_minutes == 120:
            package_info = "📦 Пакет M (2 часа аренды клуба)"
        elif "Пакет L" in service_name or duration_minutes == 180:
            package_info = "📦 Пакет L (3 часа аренды клуба)"
        elif "VR Арена" in service_name:
            package_info = "🎮 VR Арена - командный шутер"
        elif "VR Зоны" in service_name:
            package_info = "🎮 VR Зоны - более 50 игр"
        elif "Лаунж" in service_name:
            package_info = "☕ Лаунж-зона"
        
        async with async_session_maker() as session:
            user_repo = UserRepository(session)
            booking_repo = BookingRepository(session)
            message_repo = MessageRepository(session)
            
            # Try to find user by normalized phone
            user = None
            if phone_normalized:
                user = await user_repo.get_by_phone(phone_normalized)
                logger.info(f"Looking for user with phone {phone_normalized}: {'Found' if user else 'Not found'}")
            
            if message_type == "newrega":
                # Save booking to database (with or without user)
                existing_booking = await booking_repo.get_by_bukza_id(str(bukza_booking_id))
                if not existing_booking:
                    booking = await booking_repo.create(
                        bukza_booking_id=str(bukza_booking_id),
                        service_name=service_name,
                        booking_datetime=booking_datetime,
                        duration_minutes=duration_minutes,
                        user_id=user.id if user else None,
                        client_name=client_name,
                        client_phone=phone_normalized if phone_normalized else None
                    )
                    logger.info(f"Booking {bukza_booking_id} saved to database")
                else:
                    booking = existing_booking
                
                # Send to admin channel
                logger.info(f"support_channel_id = {settings.support_channel_id}")
                if settings.support_channel_id:
                    channel_msg = f"📥 НОВАЯ ЗАЯВКА\n\n"
                    channel_msg += f"👤 Имя: {client_name}\n"
                    channel_msg += f"📱 Телефон: {phone_normalized if phone_normalized else 'Не указан'}\n"
                    channel_msg += f"🎯 Услуга: {service_name}\n"
                    if package_info:
                        channel_msg += f"{package_info}\n"
                    channel_msg += f"📅 Дата: {booking_datetime.strftime('%d.%m.%Y')}\n"
                    channel_msg += f"🕐 Время: {booking_datetime.strftime('%H:%M')}\n"
                    channel_msg += f"⏱ Длительность: {duration_text}\n"
                    channel_msg += f"💰 Сумма: {total_sum} ₽\n"
                    channel_msg += f"🔖 Код: {bukza_booking_id}\n"
                    channel_msg += f"✅ В боте: Да\n" if user else f"❌ В боте: Нет\n"
                    
                    try:
                        await bot.send_message(int(settings.support_channel_id), channel_msg)
                        logger.info(f"Sent to channel {settings.support_channel_id}")
                    except Exception as e:
                        logger.error(f"Failed to send to channel: {e}")
                
                if user:
                    # Link booking to user if not already linked
                    if not booking.user_id:
                        await booking_repo.link_to_user(booking.id, user.id)
                    
                    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🗺 Открыть в 2ГИС", url="https://2gis.ru/ufa/firm/70000001092498553")],
                        [InlineKeyboardButton(text="❌ Отменить запись", callback_data=f"cancel_booking:{bukza_booking_id}")]
                    ])
                    
                    package_line = f"\n{package_info}" if package_info else ""
                    
                    try:
                        await bot.send_message(
                            user.telegram_id,
                            f"🎉 Отлично! Запись подтверждена!\n\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"🎯 {service_name}{package_line}\n"
                            f"📅 {booking_datetime.strftime('%d.%m.%Y')} в {booking_datetime.strftime('%H:%M')}\n"
                            f"⏱ {duration_text}\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"📍 Как нас найти:\n"
                            f"ТКЦ ULTRA, ул. Бакалинская 27\n"
                            f"3 этаж, вход со стороны парковки\n\n"
                            f"🔔 Напомним за 1 час до визита!\n\n"
                            f"До встречи! 🎮",
                            reply_markup=cancel_keyboard
                        )
                        await message_repo.create(user.id, MessageType.BOOKING_CREATED, booking.id)
                    except Exception as e:
                        logger.error(f"Failed to send booking notification: {e}")
                    
                    await schedule_reminder(booking.id, booking_datetime, lambda bid: send_reminder(bid, bot))
                    await schedule_feedback_request(booking.id, booking_datetime, duration_minutes, lambda bid: send_feedback_request(bid, bot))
                else:
                    logger.info(f"User with phone {phone_normalized} not registered yet")
            
            elif message_type == "cancel":
                if settings.support_channel_id:
                    try:
                        await bot.send_message(
                            int(settings.support_channel_id),
                            f"❌ ОТМЕНА ЗАЯВКИ\n\n"
                            f"👤 Имя: {client_name}\n"
                            f"📱 Телефон: {phone_number}\n"
                            f"🎯 Услуга: {service_name}\n"
                            f"📅 Дата: {booking_datetime.strftime('%d.%m.%Y')}\n"
                            f"🕐 Время: {booking_datetime.strftime('%H:%M')}\n"
                            f"🔖 Код: {bukza_booking_id}"
                        )
                    except Exception as e:
                        logger.error(f"Failed to send cancellation to channel: {e}")
                
                booking = await booking_repo.get_by_bukza_id(str(bukza_booking_id))
                
                if booking:
                    await booking_repo.update_status(booking.id, BookingStatus.CANCELLED)
                    await cancel_scheduled_tasks(booking.id)
                    
                    if user:
                        try:
                            await bot.send_message(
                                user.telegram_id,
                                f"❌ Запись отменена\n\n"
                                f"🎯 Услуга: {service_name}\n"
                                f"📅 Дата: {booking_datetime.strftime('%d.%m.%Y')}\n"
                                f"🕐 Время: {booking_datetime.strftime('%H:%M')}\n"
                                f"⏱ Длительность: {duration_text}\n\n"
                                f"Будем рады видеть вас снова! 🎮"
                            )
                            await message_repo.create(user.id, MessageType.BOOKING_CANCELLED, booking.id)
                        except Exception as e:
                            logger.error(f"Failed to send cancellation notification: {e}")
        
        return web.Response(status=200, text="OK")
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return web.Response(status=500, text="Internal server error")
