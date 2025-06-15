from aiogram import BaseMiddleware, types
from aiogram.types import TelegramObject, ChatMemberMember, ChatMemberAdministrator, ChatMemberOwner

from typing import Any, Union, Callable, Dict, Awaitable
import asyncio

import config
from settings import user_kb







class AlbumMiddleware(BaseMiddleware):
    def __init__(self, latency: Union[int, float] = 0.9):
        # Initialize latency and album_data dictionary
        self.latency = latency
        self.album_data = {}

    def collect_album_messages(self, event: types.Message):
        """
        Collect messages of the same media group.
        """
        # Check if media_group_id exists in album_data
        if event.media_group_id not in self.album_data:
             # Create a new entry for the media group
            self.album_data[event.media_group_id] = {"messages": []}

        # Append the new message to the media group
        self.album_data[event.media_group_id]["messages"].append(event)

        # Return the total number of messages in the current media group
        return len(self.album_data[event.media_group_id]["messages"])

    async def __call__(self, handler, event: types.Message, data: Dict[str, Any]) -> Any:
        """
        Main middleware logic.
        """
        # If the event has no media_group_id, pass it to the handler immediately
        if not event.media_group_id:
            return await handler(event, data)
 
        # Collect messages of the same media group
        total_before = self.collect_album_messages(event)
 
        # Wait for a specified latency period
        await asyncio.sleep(self.latency)
 
        # Check the total number of messages after the latency
        total_after = len(self.album_data[event.media_group_id]["messages"])
 
        # If new messages were added during the latency, exit
        if total_before != total_after:
            return
 
        # Sort the album messages by message_id and add to data
        album_messages = self.album_data[event.media_group_id]["messages"]
        album_messages.sort(key=lambda x: x.message_id)
        data["album"] = album_messages
 
        # Remove the media group from tracking to free up memory
        del self.album_data[event.media_group_id]
        # Call the original event handler
        return await handler(event, data)







class ChannelSubscriptionWare(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        u_status = await event.bot.get_chat_member(chat_id=int(config.CHANNEL_ID),
                                                   user_id=event.from_user.id)
        if isinstance(u_status, ChatMemberMember) or isinstance(u_status, ChatMemberAdministrator) \
                or isinstance(u_status, ChatMemberOwner):
            return await handler(event, data)
        
        if isinstance(event, types.CallbackQuery):
            event: types.CallbackQuery
            await event.answer('Вы не подписаны на канал @MishkinMishkinOmsk', show_alert=True)
            # try:
            #     await event.message.edit_text(
            #                             text=f'Привет, <i>{event.from_user.full_name}</i>. '
            #                                     f'Этот бот позволит тебе посещать мероприятия с QR-кодом!'
            #                                     "\n\n<b>Ты не подписался на канал!</b>",
            #                             reply_markup=user_kb.subscribe_kb())
            # except:
            #     await event.message.edit_text(
            #                             text=f'Привет, <i>{event.from_user.full_name}</i>! '
            #                                     f'Этот бот позволит тебе посещать мероприятия с QR-кодом!'
            #                                     "\n\n<b>Ты не подписался на канал!</b>",
            #                             reply_markup=user_kb.subscribe_kb())
        else:
            await event.answer(
                                text=f'Привет, <i>{event.from_user.full_name}</i>! '
                                        f'Этот бот позволит тебе посещать мероприятия с QR-кодом!'
                                        "\n\n<b>Ты не подписался на канал!</b>",
                                reply_markup=user_kb.subscribe_kb())