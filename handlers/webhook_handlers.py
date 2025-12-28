from aiohttp import web
from datetime import datetime
from database import async_session_maker
from database.repository import UserRepository, BookingRepository, MessageRepository
from database.models import BookingStatus, MessageType
from services.scheduler import schedule_reminder, schedule_feedback_request, cancel_scheduled_tasks
from aiogram import Bot
import logging

logger = logging.getLogger(__name__)


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
        
        try:
            await bot.send_message(
                user.telegram_id,
                f"⏰ Напоминание о записи!\n\n"
                f"Услуга: {booking.service_name}\n"
                f"Дата и время: {booking.booking_datetime.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Ждём вас! 😊"
            )
            await message_repo.create(user.id, MessageType.REMINDER, booking.id)
            logger.info(f"Reminder sent for booking {booking_id}")
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")


async def send_feedback_request(booking_id: int, bot: Bot):
    """Send feedback request to user"""
    from aiogram.fsm.context import FSMContext
    from handlers.bot_handlers import FeedbackStates
    
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
            # Store booking_id in user's state
            from aiogram.fsm.storage.memory import MemoryStorage
            storage = MemoryStorage()
            state = FSMContext(storage=storage, key=f"user_{user.telegram_id}")
            await state.set_state(FeedbackStates.waiting_for_rating)
            await state.update_data(booking_id=booking_id)
            
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
    bot = request.app['bot']
    
    try:
        # Get query parameters from URL
        query_params = request.rel_url.query
        message_type = query_params.get("message", "")
        phone_number = query_params.get("phone", "")
        
        # Get JSON body
        data = await request.json()
        logger.info(f"Received webhook - message: {message_type}, phone: {phone_number}, data: {data}")
        
        # Extract booking data from Bukza format
        bukza_booking_id = data.get("code")  # "C6UDS3"
        client_name = data.get("name")  # "Алина"
        service_name = data.get("resource")  # "VR Арена"
        start_time_str = data.get("start")  # "27.12.2025 12:00"
        end_time_str = data.get("end")  # "27.12.2025 13:00"
        
        if not all([bukza_booking_id, phone_number, service_name, start_time_str]):
            logger.error("Missing required fields in webhook")
            return web.Response(status=400, text="Missing required fields")
        
        # Parse datetime from Bukza format "27.12.2025 12:00"
        booking_datetime = datetime.strptime(start_time_str, "%d.%m.%Y %H:%M")
        end_datetime = datetime.strptime(end_time_str, "%d.%m.%Y %H:%M")
        duration_minutes = int((end_datetime - booking_datetime).total_seconds() / 60)
        
        # Normalize phone number
        if not phone_number.startswith('+'):
            phone_number = f"+{phone_number}"
        
        async with async_session_maker() as session:
            user_repo = UserRepository(session)
            booking_repo = BookingRepository(session)
            message_repo = MessageRepository(session)
            
            # Find user by phone
            user = await user_repo.get_by_phone(phone_number)
            
            if message_type == "newrega":
                # New booking created
                if user:
                    # Create booking
                    booking = await booking_repo.create(
                        bukza_booking_id=str(bukza_booking_id),
                        user_id=user.id,
                        service_name=service_name,
                        booking_datetime=booking_datetime,
                        duration_minutes=duration_minutes
                    )
                    
                    # Send notification
                    try:
                        await bot.send_message(
                            user.telegram_id,
                            f"✅ Запись создана!\n\n"
                            f"Услуга: {service_name}\n"
                            f"Дата и время: {booking_datetime.strftime('%d.%m.%Y %H:%M')}\n"
                            f"Длительность: {duration_minutes} мин\n\n"
                            f"Ждём вас! 😊"
                        )
                        await message_repo.create(user.id, MessageType.BOOKING_CREATED, booking.id)
                    except Exception as e:
                        logger.error(f"Failed to send booking notification: {e}")
                    
                    # Schedule reminder and feedback
                    await schedule_reminder(booking.id, booking_datetime, lambda bid: send_reminder(bid, bot))
                    await schedule_feedback_request(
                        booking.id,
                        booking_datetime,
                        duration_minutes,
                        lambda bid: send_feedback_request(bid, bot)
                    )
                else:
                    # User not registered - just save booking for later
                    logger.info(f"User with phone {phone_number} not registered yet")
            
            elif message_type == "cancel":
                # Booking cancelled
                booking = await booking_repo.get_by_bukza_id(str(bukza_booking_id))
                
                if booking:
                    await booking_repo.update_status(booking.id, BookingStatus.CANCELLED)
                    await cancel_scheduled_tasks(booking.id)
                    
                    if user:
                        try:
                            await bot.send_message(
                                user.telegram_id,
                                f"❌ Запись отменена\n\n"
                                f"Услуга: {service_name}\n"
                                f"Дата и время: {booking_datetime.strftime('%d.%m.%Y %H:%M')}"
                            )
                            await message_repo.create(user.id, MessageType.BOOKING_CANCELLED, booking.id)
                        except Exception as e:
                            logger.error(f"Failed to send cancellation notification: {e}")
        
        return web.Response(status=200, text="OK")
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return web.Response(status=500, text="Internal server error")
