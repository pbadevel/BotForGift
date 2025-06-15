from database.models import User, Ticket, Channel, Event, async_session
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from typing import Optional, List
import asyncio
import random
import string

from datetime import datetime, timedelta



async def add_user(
    user_id: int,
    username: Optional[str] = None,
    **kwargs
) -> Optional[User]:
    """
    Добавляет нового пользователя в базу данных.
    
    Args:
        user_id: Уникальный ID пользователя (обязательный)
        username: Имя пользователя (опционально)
        referrer_id: ID пригласившего пользователя (опционально)
        
    Returns:
        User: Объект пользователя или None при ошибке
    """
    try:
        async with async_session() as session:
            # Проверка существования реферера
            
            # Создание объекта пользователя
            new_user = User(
                user_id=user_id,
                username=username,
                created_at=datetime.now(),
                **kwargs
            )
            
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            
            return new_user
            
    except IntegrityError as e:
        # await session.rollback()
        # print(f"Ошибка целостности: {e}")
        # Если пользователь уже существует, можно вернуть существующего
        existing_user = await session.get(User, user_id)
        return existing_user
        
    except SQLAlchemyError as e:
        # await session.rollback()
        print(f"Ошибка базы данных: {e}")
        return None
        
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return None



async def get_user(user_id: int) -> Optional[User]:
    async with async_session() as session:
        result = await session.execute(
            select(User)
            .where(User.user_id == user_id) 
        )
        return result.scalars().one()
    
async def get_users() -> List[User]:
    async with async_session() as session:
        result = await session.execute(
            select(User) 
        )
        return result.scalars().all()
    



async def update_user(user_id: int, **data) -> Optional[User]:
    try:
        async with async_session() as session:
            user = await session.get(User, user_id)
            if not user:
                return None
                
            for key, value in data.items():
                setattr(user, key, value)
                
            await session.commit()
            await session.refresh(user)
            return user
    except SQLAlchemyError as e:
        print(f"Error updating user: {e}")
        # await session.rollback()
        return None



async def add_ticket(
    user_id: int,
    event_id: int,  # Добавьте этот параметр
    number: str,
    **kwargs
) -> Optional[Ticket]:
    try:
        async with async_session() as session:
            ticket = Ticket(
                user_id=user_id,
                event_id=event_id,  # Укажите event_id
                number=number,
                **kwargs
            )
            session.add(ticket)
            await session.commit()
            return ticket
    except Exception as e:
        print(f"Error adding ticket: {e}")
        # await session.rollback()
        return None
    
















async def generate_ticket_number(event_id: int, user_id: int) -> Optional[Ticket]:
    """
    Генерирует уникальный номер билета для указанного события и пользователя.
    Формат: XXXXXXgenerate
    """
    try:
        async with async_session() as session:
            # Получаем событие с жадной загрузкой билетов
            event = await session.execute(
                select(Event)
                .where(Event.id == event_id)
            )

            if not event.scalars().first():
                print(f"Событие с ID {event_id} не найдено")
                return None

            # Генерируем уникальный номер
            new_number = generate_ticket()
            tickets = [i.number for i in await get_tickets()]
            
            while True:
                if new_number not in tickets:
                    break
                new_number = generate_ticket()
            
            # Создаем билет
            ticket = Ticket(
                number=new_number,
                user_id=user_id,
                event_id=event_id,
                created_at=datetime.now()
            )
            
            session.add(ticket)
            await session.commit()

            return ticket

    except SQLAlchemyError as e:
        print(f"Ошибка генерации билета: {e}")
        # await session.rollback()
        return None




def generate_ticket():
    characters = string.ascii_uppercase + string.digits
    new_number = ''.join(random.choice(characters) for _ in range(6))
    
    return new_number            






async def get_ticket(ticket_id: int) -> Optional[Ticket]:
    try:
        async with async_session() as session:
            return await session.get(Ticket, ticket_id)
    except SQLAlchemyError as e:
        print(f"Error getting ticket: {e}")
        return None

async def update_ticket(id: int, **data) -> Optional[Ticket]:
    try:
        async with async_session() as session:
            ticket = await session.get(Ticket, id)
            if not ticket:
                return None
                
            for key, value in data.items():
                setattr(ticket, key, value)
                
            await session.commit()
            await session.refresh(ticket)
            return ticket
    except SQLAlchemyError as e:
        print(f"Error updating user: {e}")
        # await session.rollback()
        return None



async def get_tickets() -> List[Ticket]:
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Ticket)
                )
            return result.scalars().all()
        
    except SQLAlchemyError as e:
        print(f"Error getting ticket: {e}")
        return None




async def get_user_tickets(user_id: int) -> List[Ticket]:
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Ticket)
                .where(Ticket.user_id == user_id)
                )
            return result.scalars().all()
    except SQLAlchemyError as e:
        print(f"Error getting tickets: {e}")
        return []




async def add_channel(channel_id:int, name: str, url: str, root_event_ids: str = None) -> Optional[Channel]:
    try:
        async with async_session() as session:
            channel = Channel(
                id=channel_id, 
                name=name, 
                url=url,
                root_event_ids=root_event_ids
            )

            session.add(channel)
            await session.commit()
            await session.refresh(channel)
            return channel
        
    except IntegrityError as e:
        # await session.rollback()
        print(f"Channel already exists: {e}")
        return None
    except SQLAlchemyError as e:
        print(f"Error adding channel: {e}")
        # await session.rollback()
        return None
    



async def get_channel(id: int) -> Optional[Channel]:
    try:
        async with async_session() as session:
            return await session.get(Channel, id)
    except SQLAlchemyError as e:
        print(f"Error getting channel: {e}")
        return None

async def get_all_channels() -> List[Channel]:
    try:
        async with async_session() as session:
            result = await session.execute(select(Channel))
            return result.scalars().all()
    except SQLAlchemyError as e:
        print(f"Error getting channels: {e}")
        return []

async def update_channel(channel_id: int, **data) -> Optional[Channel]:
    try:
        async with async_session() as session:
            channel = await session.get(Channel, channel_id)
            if not channel:
                return None

            for key, value in data.items():
                setattr(channel, key, value)
                
            await session.commit()
            await session.refresh(channel)
            return channel
    except SQLAlchemyError as e:
        print(f"Error updating channel: {e}")
        # await session.rollback()
        return None

async def create_event(
    name: str,
    description: Optional[str] = None,
    **kwargs
) -> Optional[Event]:
    try:
        async with async_session() as session:
            event = Event(
                name=name,
                description=description,
                **kwargs
            )
                            
            session.add(event)
            await session.commit()
            await session.refresh(event)
            return event
    except SQLAlchemyError as e:
        print(f"Error creating event: {e}")
        # await session.rollback()
        return None



async def find_events_by_name(event_name):
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Event)
                .where(Event.name.contains(event_name))
                
            )
            return result.scalars().all()
    except SQLAlchemyError as e:
        print(f"Error getting active events: {e}")
        return []


async def get_active_events() -> List[Event]:
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Event)
                .where(Event.is_active == True)
                
            )
            return result.scalars().all()
    except SQLAlchemyError as e:
        print(f"Error getting active events: {e}")
        return []


async def get_event_winners(event_id: int) -> List[User]:
    async with async_session() as session:
        result = []
        user_ids = []

        event_ = await session.execute(
            select(Event)
            .where(
                Event.id == event_id
            )
        )
        event = event_.scalars().first()

        if not event.tickets_event:
            return []
        
        
        for ticket in event.tickets_event.split(','):
            if not ticket == '':    
                t = await get_ticket(int(ticket))
                if t:
                    
                    if t.is_winner and (t.user_id not in user_ids):
                        user = await get_user(t.user_id)
                        result.append(user)
                        user_ids.append(user.user_id)


        return result


async def get_event(event_id: int) -> Optional[Event]:
    try:
        async with async_session() as session:
             result = await session.execute(
                select(Event)
                .where(Event.id == event_id)
        
            )
        return result.scalars().first()
    except SQLAlchemyError as e:
        print(f"Error getting event: {e}")
        return None
    

async def get_events() -> Optional[List[Event]]:
    try:
        async with async_session() as session:
             result = await session.execute(
                select(Event)
            )
        return result.scalars().all()
    except SQLAlchemyError as e:
        print(f"Error getting event: {e}")
        return None



async def update_event_status(event_id: int, is_active: bool) -> Optional[Event]:
    try:
        async with async_session() as session:
            event = await session.get(Event, event_id)
            if not event:
                return None
                
            event.is_active = is_active
            await session.commit()
            await session.refresh(event)
            return event
    except SQLAlchemyError as e:
        print(f"Error updating event status: {e}")
        # await session.rollback()
        return None



async def update_event(event_id: int, **kw) -> Optional[Event]:
    try:
        async with async_session() as session:
            event = await session.get(Event, event_id)
            if not event:
                return None
                
            for key, value in kw.items():
                setattr(event, key, value)
                
            await session.commit()
            await session.refresh(event)
            return event
    except SQLAlchemyError as e:
        print(f"Error updating event status: {e}")
        # await session.rollback()
        return None



async def delete_event(event_id: int) -> bool:
    """
    Удаляет событие и все связанные с ним данные (билеты, связи с каналами)
    
    Args:
        event_id: ID события для удаления
        
    Returns:
        bool: True если удаление успешно, False в случае ошибки
    """
    try:
        async with async_session() as session:
            # Получаем событие со всеми связями
            q = await session.execute(
                select(Event)
                .where(Event.id == event_id)
            )
            
            event = q.scalars().first()

            if not event:
                print(f"Событие с ID {event_id} не найдено")
                return False


            # Удаляем само событие
            await session.delete(event)
            await session.commit()
            return True

    except SQLAlchemyError as e:
        print(f"Ошибка при удалении события: {e}")
        # await session.rollback()
        return False
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return False


