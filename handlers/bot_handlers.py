from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import async_session_maker
from database.repository import UserRepository, BookingRepository
import logging

logger = logging.getLogger(__name__)

router = Router()


class RegistrationStates(StatesGroup):
    waiting_for_phone = State()


class FeedbackStates(StatesGroup):
    waiting_for_rating = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        
        if user and user.phone_number:
            # User already registered
            booking_repo = BookingRepository(session)
            active_bookings = await booking_repo.get_active_by_user(user.id)
            
            if active_bookings:
                bookings_text = "\n".join([
                    f"• {b.service_name} - {b.booking_datetime.strftime('%d.%m.%Y %H:%M')}"
                    for b in active_bookings
                ])
                await message.answer(
                    f"Вы уже зарегистрированы!\n\n"
                    f"Ваши предстоящие записи:\n{bookings_text}"
                )
            else:
                await message.answer("Вы уже зарегистрированы! У вас пока нет активных записей.")
        else:
            # New user - request phone number
            keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]],
                resize_keyboard=True
            )
            await message.answer(
                "Добро пожаловать! 👋\n\n"
                "Для получения уведомлений о записях, пожалуйста, поделитесь своим номером телефона.",
                reply_markup=keyboard
            )
            await state.set_state(RegistrationStates.waiting_for_phone)


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone_number(message: Message, state: FSMContext):
    """Process phone number from user"""
    phone_number = message.contact.phone_number
    
    # Normalize phone number
    if not phone_number.startswith('+'):
        phone_number = f"+{phone_number}"
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        
        if user:
            # Update existing user
            user = await user_repo.update_phone(user.id, phone_number)
        else:
            # Create new user
            user = await user_repo.create(message.from_user.id, phone_number)
        
        await message.answer(
            "✅ Регистрация завершена!\n\n"
            "Теперь вы будете получать уведомления о ваших записях:\n"
            "• Подтверждение при создании записи\n"
            "• Напоминание за 24 часа до визита\n"
            "• Запрос обратной связи после посещения"
        )
    
    await state.clear()


@router.message(FeedbackStates.waiting_for_rating)
async def process_rating(message: Message, state: FSMContext):
    """Process rating from user"""
    try:
        rating = int(message.text)
        
        if rating < 1 or rating > 5:
            await message.answer("Пожалуйста, оцените услугу числом от 1 до 5.")
            return
        
        # Get booking_id from state
        data = await state.get_data()
        booking_id = data.get("booking_id")
        
        if not booking_id:
            await message.answer("Произошла ошибка. Попробуйте позже.")
            await state.clear()
            return
        
        # Save rating
        async with async_session_maker() as session:
            booking_repo = BookingRepository(session)
            booking = await booking_repo.get_by_bukza_id(str(booking_id))
            
            if booking:
                await booking_repo.save_rating(booking.id, rating)
                
                # Send feedback to Bukza
                await bukza_client.send_feedback(booking.bukza_booking_id, rating)
        
        if rating == 5:
            # Send review links
            from config import settings
            await message.answer(
                f"Спасибо за отличную оценку! 🌟\n\n"
                f"Будем очень благодарны, если вы оставите отзыв:\n\n"
                f"📍 2ГИС: {settings.link_2gis}\n"
                f"📍 Яндекс.Карты: {settings.link_yandex_maps}"
            )
        else:
            await message.answer("Спасибо за вашу обратную связь! 🙏")
        
        await state.clear()
        
    except ValueError:
        await message.answer("Пожалуйста, отправьте число от 1 до 5.")
