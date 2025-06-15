from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import ForeignKey, String, BigInteger, Boolean, DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Table, Column


import asyncio
from datetime import datetime
from typing import List, Optional

engine = create_async_engine(
    url="sqlite+aiosqlite:///database/db.sqlite3",
    pool_size=20,
    max_overflow=0,
    pool_recycle=500,
    connect_args={"check_same_thread": False}
)


async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase, AsyncAttrs):
    pass




class User(Base):
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    fullname: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Отношения
    referrals: Mapped[str] = mapped_column(String, nullable=True)
    referrer: Mapped[int] = mapped_column(Integer, nullable=True)

    tickets_ids: Mapped[str] = mapped_column(String, nullable=True)
    event_ids: Mapped[str] = mapped_column(String, nullable=True)
    channel_ids: Mapped[str] = mapped_column(String, nullable=True) 


class Ticket(Base):
    __tablename__ = "tickets"
   
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    number: Mapped[str] = mapped_column(String(20), nullable=False)
    is_winner: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"))  # Добавлено


class Channel(Base):
    __tablename__ = "channels"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    root_event_ids: Mapped[str] = mapped_column(String, nullable=True)
    url: Mapped[str] = mapped_column(String(200))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    


class Event(Base):
    __tablename__ = "events"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    media: Mapped[Optional[str]] = mapped_column(Text)
    win_count: Mapped[int] = mapped_column(Integer)
    
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    use_captcha: Mapped[bool] = mapped_column(Boolean, default=True)
    user_event_ids: Mapped[str] = mapped_column(String, nullable=True)
    
    # Отношение к Channel
    channel_event_ids: Mapped[str] = mapped_column(String, nullable=True)

    tickets_event: Mapped[str] = mapped_column(String, nullable=True)

    message_ids: Mapped[str] = mapped_column(String, nullable=True)

    is_referral: Mapped[bool] = mapped_column(Boolean, default=False)
    ref_tickets_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)




async def create_tables():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(create_tables())