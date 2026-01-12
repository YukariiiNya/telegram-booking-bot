from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Booking, Message, BookingStatus, MessageType
from typing import Optional
from datetime import datetime


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_phone(self, phone_number: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.phone_number == phone_number)
        )
        return result.scalar_one_or_none()
    
    async def create(self, telegram_id: int, phone_number: Optional[str] = None) -> User:
        user = User(telegram_id=telegram_id, phone_number=phone_number)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def update_phone(self, user_id: int, phone_number: str) -> User:
        await self.session.execute(
            update(User).where(User.id == user_id).values(phone_number=phone_number)
        )
        await self.session.commit()
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one()


class BookingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_bukza_id(self, bukza_booking_id: str) -> Optional[Booking]:
        result = await self.session.execute(
            select(Booking).where(Booking.bukza_booking_id == bukza_booking_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_by_user(self, user_id: int) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(Booking.user_id == user_id)
            .where(Booking.status == BookingStatus.ACTIVE)
            .order_by(Booking.booking_datetime)
        )
        return list(result.scalars().all())
    
    async def get_all_by_user(self, user_id: int) -> list[Booking]:
        """Get all bookings for user, ordered by date descending"""
        result = await self.session.execute(
            select(Booking)
            .where(Booking.user_id == user_id)
            .order_by(Booking.booking_datetime.desc())
        )
        return list(result.scalars().all())
    
    async def create(
        self,
        bukza_booking_id: str,
        service_name: str,
        booking_datetime: datetime,
        duration_minutes: int,
        user_id: Optional[int] = None,
        client_name: Optional[str] = None,
        client_phone: Optional[str] = None
    ) -> Booking:
        booking = Booking(
            bukza_booking_id=bukza_booking_id,
            user_id=user_id,
            service_name=service_name,
            client_name=client_name,
            client_phone=client_phone,
            booking_datetime=booking_datetime,
            duration_minutes=duration_minutes
        )
        self.session.add(booking)
        await self.session.commit()
        await self.session.refresh(booking)
        return booking
    
    async def link_to_user(self, booking_id: int, user_id: int) -> bool:
        """Link booking to user"""
        await self.session.execute(
            update(Booking).where(Booking.id == booking_id).values(user_id=user_id)
        )
        await self.session.commit()
        return True
    
    async def get_unlinked_by_code(self, bukza_booking_id: str) -> Optional[Booking]:
        """Get booking by code that is not linked to any user"""
        result = await self.session.execute(
            select(Booking).where(
                Booking.bukza_booking_id == bukza_booking_id,
                Booking.user_id == None
            )
        )
        return result.scalar_one_or_none()
    
    async def update_status(self, booking_id: int, status: BookingStatus):
        await self.session.execute(
            update(Booking).where(Booking.id == booking_id).values(status=status)
        )
        await self.session.commit()
    
    async def save_rating(self, booking_id: int, rating: int):
        await self.session.execute(
            update(Booking).where(Booking.id == booking_id).values(rating=rating)
        )
        await self.session.commit()


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        user_id: int,
        message_type: MessageType,
        booking_id: Optional[int] = None
    ) -> Message:
        message = Message(
            user_id=user_id,
            booking_id=booking_id,
            message_type=message_type
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message
