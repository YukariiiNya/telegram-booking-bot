from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
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


class MessageStates(StatesGroup):
    waiting_for_message = State()


def get_main_menu_keyboard():
    """Get main menu keyboard with beautiful layout"""
    # Web App button for booking
    booking_url = "https://1emesto.ru/"
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎯 Записаться", web_app=WebAppInfo(url=booking_url)), KeyboardButton(text="📅 Мои записи")],
            [KeyboardButton(text="📍 Адрес"), KeyboardButton(text="📞 Контакты")],
            [KeyboardButton(text="💬 Написать нам"), KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )
    return keyboard


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
    from config import settings
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        
        if user and user.phone_number:
            # User already registered - show menu with Web App button
            booking_url = "https://1emesto.ru/"
            
            inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎯 Записаться онлайн", web_app=WebAppInfo(url=booking_url))]
            ])
            
            await message.answer(
                "🎯 Добро пожаловать в «Первое место»!\n\n"
                "Развлекательный центр в ТКЦ ULTRA, Уфа\n\n"
                "Нажмите кнопку ниже для онлайн-записи или выберите действие в меню:",
                reply_markup=get_main_menu_keyboard()
            )
            await message.answer(
                "👇 Быстрая запись:",
                reply_markup=inline_keyboard
            )
        else:
            # New user - request phone number
            keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]],
                resize_keyboard=True
            )
            await message.answer(
                "🎯 Добро пожаловать в «Первое место»!\n\n"
                "Развлекательный центр в ТКЦ ULTRA, Уфа\n\n"
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
            "• Запрос обратной связи после посещения",
            reply_markup=get_main_menu_keyboard()
        )
    
    await state.clear()


# Button handlers
@router.message(F.text == "📅 Мои записи")
async def button_bookings(message: Message):
    """Handle 'Мои записи' button"""
    await cmd_bookings(message)


@router.message(F.text == "💬 Написать нам")
async def button_contact(message: Message, state: FSMContext):
    """Handle 'Написать нам' button"""
    await cmd_contact(message, state)


@router.message(F.text == "ℹ️ Помощь")
async def button_help(message: Message):
    """Handle 'Помощь' button"""
    await cmd_help(message)


@router.message(F.text == "📍 Адрес")
async def button_address(message: Message):
    """Handle 'Адрес' button"""
    await cmd_address(message)


@router.message(F.text == "📞 Контакты")
async def button_contacts(message: Message):
    """Handle 'Контакты' button"""
    await cmd_contacts(message)


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


@router.message(Command("bookings"))
async def cmd_bookings(message: Message):
    """Show user's booking history"""
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        
        if not user:
            await message.answer(
                "Вы не зарегистрированы. Используйте /start для регистрации.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        booking_repo = BookingRepository(session)
        bookings = await booking_repo.get_all_by_user(user.id)
        
        if not bookings:
            await message.answer(
                "У вас пока нет записей.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Group bookings by status
        active = [b for b in bookings if b.status.value == 'ACTIVE']
        completed = [b for b in bookings if b.status.value == 'COMPLETED']
        cancelled = [b for b in bookings if b.status.value == 'CANCELLED']
        
        response = "📅 Ваши записи:\n\n"
        
        if active:
            response += "🟢 Активные:\n"
            for b in active:
                response += f"• {b.service_name}\n  {b.booking_datetime.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        if completed:
            response += "✅ Завершённые:\n"
            for b in completed[:5]:  # Last 5
                rating_text = f" (⭐ {b.rating})" if b.rating else ""
                response += f"• {b.service_name}{rating_text}\n  {b.booking_datetime.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        if cancelled:
            response += "❌ Отменённые:\n"
            for b in cancelled[:3]:  # Last 3
                response += f"• {b.service_name}\n  {b.booking_datetime.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        await message.answer(response, reply_markup=get_main_menu_keyboard())


@router.message(Command("contact"))
async def cmd_contact(message: Message, state: FSMContext):
    """Allow user to send a message to support"""
    await message.answer(
        "💬 Напишите ваше сообщение, и мы обязательно ответим!\n\n"
        "Отправьте текст сообщения:"
    )
    await state.set_state(MessageStates.waiting_for_message)


@router.message(MessageStates.waiting_for_message)
async def process_contact_message(message: Message, state: FSMContext):
    """Forward user message to support channel"""
    from config import settings
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        
        phone = user.phone_number if user else "не указан"
        username = message.from_user.username or "нет username"
        
        # Forward to support channel (you need to set SUPPORT_CHANNEL_ID in config)
        support_text = (
            f"📨 Новое сообщение от клиента\n\n"
            f"👤 Пользователь: @{username}\n"
            f"📱 Телефон: {phone}\n"
            f"💬 Сообщение:\n{message.text}"
        )
        
        try:
            # Send to support channel if configured
            if hasattr(settings, 'support_channel_id') and settings.support_channel_id:
                await message.bot.send_message(settings.support_channel_id, support_text)
            
            await message.answer(
                "✅ Ваше сообщение отправлено!\n\n"
                "Мы свяжемся с вами в ближайшее время.",
                reply_markup=get_main_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Failed to send message to support: {e}")
            await message.answer(
                "Произошла ошибка при отправке сообщения.\n"
                "Пожалуйста, свяжитесь с нами напрямую.",
                reply_markup=get_main_menu_keyboard()
            )
    
    await state.clear()


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Show help information"""
    await message.answer(
        "ℹ️ Помощь\n\n"
        "Используйте кнопки меню:\n\n"
        "🎯 Записаться - онлайн-запись на услуги\n"
        "📅 Мои записи - история бронирований\n"
        "📍 Адрес - как нас найти\n"
        "📞 Контакты - связаться с нами\n"
        "💬 Написать нам - сообщение в поддержку\n"
        "ℹ️ Помощь - эта справка\n\n"
        "Автоматические уведомления:\n"
        "• При создании записи\n"
        "• Напоминание за 24 часа\n"
        "• Запрос отзыва после посещения",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("address"))
async def cmd_address(message: Message):
    """Show company address"""
    from config import settings
    
    address_text = settings.company_address.replace('\\n', '\n')
    
    await message.answer(
        f"📍 Наш адрес:\n\n"
        f"{address_text}\n\n"
        f"🕐 Режим работы:\n"
        f"{settings.company_hours}\n\n"
        f"🗺 Мы на картах:\n"
        f"• 2ГИС: {settings.link_2gis}\n"
        f"• Яндекс.Карты: {settings.link_yandex_maps}\n\n"
        f"🚇 Как добраться:\n"
        f"Остановка «ТЦ Мега» или «ТКЦ ULTRA»",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("contacts"))
async def cmd_contacts(message: Message):
    """Show contact information"""
    from config import settings
    
    await message.answer(
        f"📞 Контакты:\n\n"
        f"☎️ Телефон: {settings.company_phone}\n"
        f"📱 WhatsApp: {settings.company_phone}\n"
        f"📧 Email: {settings.company_email}\n"
        f"🌐 Сайт: {settings.company_website}\n"
        f"📱 Instagram: {settings.company_instagram}\n\n"
        f"💬 Или напишите нам прямо здесь через кнопку\n"
        f"«Написать нам» - мы ответим в течение часа!\n\n"
        f"Ждём вас в «Первое место»! 🎯",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("book"))
async def cmd_book(message: Message):
    """Show booking link"""
    from config import settings
    
    booking_url = settings.bukza_booking_url or settings.bukza_api_url.replace('/api', '')
    
    await message.answer(
        "🎯 Онлайн-запись в «Первое место»\n\n"
        "Выберите удобное время и активность:\n"
        "• VR-игры\n"
        "• Аренда зала\n"
        "• Корпоративы\n"
        "• Детские праздники\n\n"
        f"👉 Записаться: {booking_url}\n\n"
        "После записи вы получите уведомление в этом боте!",
        reply_markup=get_main_menu_keyboard()
    )
