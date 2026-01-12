from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional
import enum


class Base(DeclarativeBase):
    pass


class BookingStatus(enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class MessageType(enum.Enum):
    BOOKING_CREATED = "booking_created"
    BOOKING_CANCELLED = "booking_cancelled"
    REMINDER = "reminder"
    FEEDBACK_REQUEST = "feedback_request"


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")
    messages: Mapped[list["Message"]] = relationship(back_populates="user")


class Booking(Base):
    __tablename__ = "bookings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    bukza_booking_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    service_name: Mapped[str] = mapped_column(String(255))
    client_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    client_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    booking_datetime: Mapped[datetime] = mapped_column(DateTime)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    status: Mapped[BookingStatus] = mapped_column(SQLEnum(BookingStatus), default=BookingStatus.ACTIVE)
    
    rating: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user: Mapped["User"] = relationship(back_populates="bookings")
    messages: Mapped[list["Message"]] = relationship(back_populates="booking")


class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    booking_id: Mapped[Optional[int]] = mapped_column(ForeignKey("bookings.id"))
    
    message_type: Mapped[MessageType] = mapped_column(SQLEnum(MessageType))
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    user: Mapped["User"] = relationship(back_populates="messages")
    booking: Mapped[Optional["Booking"]] = relationship(back_populates="messages")
