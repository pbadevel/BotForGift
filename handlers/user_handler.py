from aiogram import Router, F, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.enums import MessageEntityType, ParseMode
from html import escape

from aiogram.fsm.context import FSMContext

import logging as lg
from datetime import datetime, timedelta

from settings import user_kb, lexicon, UserStates, request_utils, utils
from database.req import add_user
from database import req
import config

from config import ADMIN_IDS
from aiogram.utils.deep_linking import decode_payload











router = Router()



@router.message(CommandStart())
async def start_bot(message: types.Message, command: CommandObject, state: FSMContext):
    
    if command.args:
        try:
            referrer_id, eventId = command.args.split('-')
            referrer = await req.get_user(int(referrer_id))

            if referrer_id == str(message.from_user.id):
                await message.answer('Вы не можете пригласить самого себя!')
                return
            
            users_referrers_ids=[]
            pre_users_referrers_ids = [i.referrals for i in await req.get_users() if i.referrals]
            
            for user_referrers_ids in pre_users_referrers_ids:
                for user_referrer_id in user_referrers_ids.split(','):
                    if user_referrer_id!='':
                        users_referrers_ids.append(user_referrer_id)


            if referrer.referrals:
                if str(message.from_user.id) in users_referrers_ids:
                    await message.answer('Вы уже были приглашены пользователем!')
                    return
            
            event = await req.get_event(int(eventId)) 
            event_channels = event.channel_event_ids.split(',')
            c = 0
            if '' in event_channels:
                c-=1
            
            for channel_id in event_channels:
                if channel_id != '':
                    res = request_utils.check_subscription(int(message.from_user.id), int(channel_id), config.BOT_TOKEN)
                    lg.info(f'{int(message.from_user.id), channel_id, config.BOT_TOKEN, res}')
                    if res:
                        c+=1
            lg.info(f"CHECK CHANNEL REF {c}, {len(event_channels)}")
            if not c == len(event_channels):
                await message.answer('Вы не подписанны на все каналы! Подпишитесь и снова перейдите по реферальной сслыке', reply_markup= user_kb.show_private_chat_web_app(event.id, event.end_date))
                return
            
            if referrer.referrals:
                await req.update_user(
                    user_id=int(referrer_id),
                    referrals=referrer.referrals + ',' + str(message.from_user.id) 
                )
            else:
                await req.update_user(
                    user_id=int(referrer_id),
                    referrals=str(message.from_user.id) 
                )

            if event.ref_tickets_count > 0:
                for i in range(event.ref_tickets_count):
                    ticket1 = await req.generate_ticket_number(user_id=int(referrer_id), event_id=int(eventId))

                    if not event.tickets_event:
                        event.tickets_event = ''
                    
                    if not referrer.tickets_ids:
                        referrer.tickets_ids = ''

                    await req.update_event(
                        event_id=int(eventId),
                        tickets_event=event.tickets_event+str(ticket1.id)+',' # +str(ticket2.id)+','
                    )

                    await req.update_user(
                        user_id=referrer.user_id,
                        tickets_ids=referrer.tickets_ids+str(ticket1.id)+',' # +str(ticket2.id)+','
                        )

            await add_user(
                user_id=message.from_user.id,
                username=message.from_user.username,
                fullname=message.from_user.full_name,
                referrer=referrer.user_id
            )



            await message.bot.send_message(chat_id=referrer_id, text=f'Вы получили {event.ref_tickets_count} тикета за приглашенного пользователя на событие: {event.name} !')

            await message.answer(
                lexicon.START_TEXT, 
                reply_markup=user_kb.main_reply()
            )

            return

        except:
            pass


        return
    try:
        await add_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            fullname=message.from_user.full_name
        )
    except Exception:
        lg.warning(f'FAILED TO ADD USER IN START u_id:{message.from_user.id}')
    


    # print(message)

    await message.answer(
        lexicon.START_TEXT, 
        reply_markup=user_kb.main_reply()
    )


    


@router.callback_query(F.data == 'backMain')
async def backmain(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer('')

    try: await state.clear()
    except: pass
    
    try:
        await cb.message.edit_text(
            lexicon.START_TEXT, 
            reply_markup=user_kb.main_reply()
        )
    except:
        await cb.message.answer(
            lexicon.START_TEXT, 
            reply_markup=user_kb.main_reply()
        )






@router.message(F.text == "Розыгрыши")
async def raffle(message: types.Message):
    user = await req.get_user(message.from_user.id)

    if user:
        user_raffles = user.event_ids
        if user_raffles:
            await message.answer('<b>Вот ваши розыгрыши:</b>',
                                reply_markup=await user_kb.create_user_raffles(user_raffles.split(',')))


        elif user_raffles == None or user_raffles == '':
            await message.answer('<b>У вас нет розыгрышей!</b>', reply_markup=user_kb.back_to_menu())



@router.callback_query(F.data.startswith('user_event_'))
async def user_event(cb: types.CallbackQuery):

    await cb.answer('')

    action = cb.data.split('_')[-2]
    event_id = int(cb.data.split('_')[-1])


    if action == 'show':
        event = await req.get_event(event_id)
        if event and event.is_active:
            user_count = 0
            win_count = None
            raffle_data = None

            if event.user_event_ids:
                user_count = len(event.user_event_ids.split(','))
            
            win_count = event.win_count
            raffle_data = event.end_date.strftime("%d.%m.%Y, %H:%M")

            if event.media:
                await cb.message.answer_photo(
                    photo=event.media,
                    caption=lexicon.EVENT_TEXT.format(
                    name=event.name,
                    description=event.description or '',
                    users_count=user_count,
                    win_count=win_count,
                    raffle_date=raffle_data
                    ),
                    reply_markup=await user_kb.show_event_kb(event.id, use_captha=event.use_captcha, is_active=event.is_active)
                )
            else:
                await cb.message.answer(text=lexicon.EVENT_TEXT.format(
                    name=event.name,
                    description=event.description or '',
                    users_count=user_count,
                    win_count=win_count,
                    raffle_date=raffle_data
                ),
                    reply_markup=await user_kb.show_event_kb(event.id, use_captha=event.use_captcha, is_active=event.is_active)
                )
        elif event and (not event.is_active):
            user_count = 0
            win_count = None
            raffle_data = None

            if event.user_event_ids:
                user_count = len(event.user_event_ids.split(','))
            
            win_count = event.win_count
            raffle_data = event.end_date.strftime("%d.%m.%Y, %H:%M")

            winners = await req.get_event_winners(event.id)

            text_for_owner_winners = '\n'.join([f'''<a href="{'https://t.me/'+winner.username if winner.username else 'tg://user?id='+str(winner.user_id)}">    {winner.fullname}</a>''' for winner in winners])
                
            deeplink_url = 'https://t.me/' + (await cb.bot.get_me()).username + f'?startapp='+ utils.encode_data(f'event_id={event.id}&mode=results')

            if event.media:
                await cb.message.answer_photo(
                    photo=event.media,
                    caption=lexicon.EVENT_WIN_TEXT.format(
                        name=event.name,
                        winners=text_for_owner_winners,
                        users_count=user_count,
                        win_count=win_count,
                        raffle_date=raffle_data
                    ),
                    reply_markup= user_kb.show_private_event_results_web_kb(url=deeplink_url, event_id=event.id)
                )
            else:
                await cb.message.answer(
                    text=lexicon.EVENT_WIN_TEXT.format(
                        name=event.name,
                        winners=text_for_owner_winners,
                        users_count=user_count,
                        win_count=win_count,
                        raffle_date=raffle_data
                    ),
                    reply_markup= user_kb.show_private_event_results_web_kb(url=deeplink_url, event_id=event.id)
                )
        else:
            await cb.message.answer('Что-то пошло не так...', reply_markup=user_kb.back_to_menu())
























@router.callback_query(F.data.startswith('edit_event_'))
async def edit_event(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer('')

    action = cb.data.split('_')[-2]
    event_id = int(cb.data.split('_')[-1])

    await state.update_data(
        event_id=event_id,
        action = action
    )    


    if action == 'name':
        await cb.message.answer(
            text='Введите новое наименование розыгрыша:',
            reply_markup=user_kb.back_to_menu()
        )
        
        await state.set_state(UserStates.EditEventState.inp)
    
    elif action == 'media':
        await cb.message.answer(
            text='Пришлите новую фотку для розыгрыша:',
            reply_markup=user_kb.back_to_menu()
        )
        await state.set_state(UserStates.EditEventState.photo)

    
    elif action == 'description':
        await cb.message.answer(
            text='Введите новое описание розыгрыша:',
            reply_markup=user_kb.back_to_menu()
        )
        await state.set_state(UserStates.EditEventState.inp)
    
    elif action == 'wins':
        await cb.message.answer(
            text='Введите новое кол-во призовых мест розыгрыша:',
            reply_markup=user_kb.back_to_menu()
        )
        await state.set_state(UserStates.EditEventState.inp)
    
    elif action == 'channels':
        user_channels = (await req.get_user(cb.from_user.id)).channel_ids
        if not user_channels or user_channels == '':
            user_channels = []
        else:
            user_channels = user_channels.split(',')
        
        await cb.message.answer(
            text='Выберите канал,\n\n<b>ВНИМАНИЕ: Бот должен иметь права администатора в вашем Канале/Чате чтобы проверять наличие пользователя</b>',
            reply_markup=await user_kb.show_user_channels(user_channels, event_id)
        )
    
    elif action == 'date':
        await cb.message.answer(
            text=f'Введите новую дату окончания розыгрыша:\n\nФормат: <b>{datetime.now().strftime("%d.%m.%Y %H:%M")}</b>',
            reply_markup=user_kb.back_to_menu()
        )
        await state.set_state(UserStates.EditEventState.inp)
    



@router.message(UserStates.EditEventState.inp)
async def edit_input(message: types.Message, state: FSMContext):
    data = await state.get_data()

    if 'event_id' not in data.keys() or 'action' not in data.keys():
        await message.answer('Данные устарели!', reply_markup=user_kb.back_to_menu())

    action = data['action']
    event_id = int(data['event_id'])

    formatted_text = apply_html_formatting(
        text=message.text or "", 
        entities=message.entities or []
    )


    if action == 'name':
        await req.update_event(
            event_id=event_id,
            name=formatted_text
        )
        
        await message.answer('Данные обновлены!', reply_markup=user_kb.back_to_event(event_id))

    elif action == 'description':
        await req.update_event(
            event_id=event_id,
            description=formatted_text
        )
    
        await message.answer('Данные обновлены!', reply_markup=user_kb.back_to_event(event_id))
    
    elif action == 'wins':
        await req.update_event(
            event_id=event_id,
            win_count=message.text
        )
    
        await message.answer('Данные обновлены!', reply_markup=user_kb.back_to_event(event_id))
    
    elif action == 'date':
        try:
            time = datetime.strptime(message.text, '%d.%m.%Y %H:%M')
        except:
            await message.answer(f'Неверный формат!\n\n Пример: {datetime.now().strftime("%d.%m.%Y %H:%M")}\n\nВведите еще раз:',
                                 reply_markup=user_kb.back_to_event(event_id))
            return
        

        await req.update_event(
            event_id=event_id,
            end_date=time
        )
    
        await message.answer('Данные обновлены!', reply_markup=user_kb.back_to_event(event_id))
    

    await state.clear()




@router.message(UserStates.EditEventState.photo)
async def handle_edit_photo(message: types.Message, state: FSMContext):
    if message.photo:
        data = await state.get_data()
        event_id = int(data['event_id'])

        photo_id = message.photo[-1].file_id

        await req.update_event(
            event_id=event_id,
            media=photo_id
        )

        await message.answer('Данные обновлены!', reply_markup=user_kb.back_to_event(event_id))
        await state.clear()
    else:
        await message.answer('Пришлите только одно фото!', reply_markup=user_kb.back_to_event(event_id))


@router.callback_query(F.data.startswith('channel_disable_'))
async def change_event_channel(cb: types.CallbackQuery, state: FSMContext):
    data = cb.data.split('_')

    event_id = int(data[-2])
    channel_id = data[-1]

    event = await req.get_event(event_id)
    channel = await req.get_channel(int(channel_id))
    user_channels = (await req.get_user(cb.from_user.id)).channel_ids
    if not user_channels or user_channels == '':
        user_channels = []
    else:
        user_channels = user_channels.split(',')

    if event.channel_event_ids:
        event_channels = event.channel_event_ids.split(',')
        event_channels.remove(channel_id)
        event_channels = ','.join(event_channels)

        channel_events = channel.root_event_ids.split(',')
        channel_events.remove(str(event_id))
        channel_events = ','.join(channel_events)

        
        await req.update_event(event_id=event_id, channel_event_ids=event_channels)
        await req.update_channel(channel_id=int(channel_id), 
                                 root_event_ids=channel_events
                                 )

    try:
        await cb.message.edit_text(
            text='Выберите канал,\n\n<b>ВНИМАНИЕ: Бот должен иметь права администатора в вашем Канале/Чате чтобы проверять наличие пользователя</b>',
            reply_markup=await user_kb.show_user_channels(user_channels, event_id)
        )
    except:
        await cb.message.edit_text('Успешно обновленно!', reply_markup=user_kb.back_to_event(event_id))



@router.callback_query(F.data.startswith('channel_enable_'))
async def change_event_channel(cb: types.CallbackQuery, state: FSMContext):
    data = cb.data.split('_')

    event_id = int(data[-2])
    channel_id = data[-1]

    event = await req.get_event(event_id)
    channel = await req.get_channel(int(channel_id))
    user_channels = (await req.get_user(cb.from_user.id)).channel_ids
    if not user_channels or user_channels == '':
        user_channels = []
    else:
        user_channels = user_channels.split(',')

    if event.channel_event_ids:
        event_channels = event.channel_event_ids + ',' + channel_id
    else:
        event_channels = channel_id

    if channel.root_event_ids:
        channel_root_event_ids = channel.root_event_ids + ',' + str(event_id)
    else:
        channel_root_event_ids = str(event_id)


    await req.update_event(event_id=event_id, channel_event_ids=event_channels)
    await req.update_channel(channel_id=int(channel_id), 
                                root_event_ids=channel_root_event_ids
                                )
    try:
        await cb.message.edit_text(
            text='Выберите канал,\n\n<b>ВНИМАНИЕ: Бот должен иметь права администатора в вашем Канале/Чате чтобы проверять наличие пользователя</b>',
            reply_markup=await user_kb.show_user_channels(user_channels, event_id)
        )
    except:
        await cb.message.edit_text('Успешно обновленно!', reply_markup=user_kb.back_to_event(event_id))




@router.callback_query(F.data.startswith('captcha_disable_'))
async def disable_captcha(cb: types.CallbackQuery):
    
    event = await req.get_event(int(cb.data.split('_')[-1]) )

    await req.update_event(
        event_id=event.id,
        use_captcha = False
    )

    await cb.message.edit_text('Успешно обновленно!', reply_markup=user_kb.back_to_event(event.id))





@router.callback_query(F.data.startswith('captcha_enable_'))
async def disable_captcha(cb: types.CallbackQuery):
    
    event = await req.get_event(int(cb.data.split('_')[-1]) )

    await req.update_event(
        event_id=event.id,
        use_captcha = True
    )

    await cb.message.edit_text('Успешно обновленно!', reply_markup=user_kb.back_to_event(event.id))






@router.callback_query(F.data.startswith('activeEvent_disable_'))
async def disable_captcha(cb: types.CallbackQuery):
    
    event = await req.get_event(int(cb.data.split('_')[-1]) )

    await req.update_event(
        event_id=event.id,
        is_active = False
    )

    await cb.message.edit_text('Успешно обновленно!', reply_markup=user_kb.back_to_event(event.id))





@router.callback_query(F.data.startswith('activeEvent_enable_'))
async def disable_captcha(cb: types.CallbackQuery):
    
    event = await req.get_event(int(cb.data.split('_')[-1]) )

    await req.update_event(
        event_id=event.id,
        is_active = True
    )

    await cb.message.edit_text('Успешно обновленно!', reply_markup=user_kb.back_to_event(event.id))











@router.callback_query(F.data.startswith('send_'))
async def send_post(cb: types.CallbackQuery):
    event_id = cb.data.split('_')[-1]
    
    try:
        await cb.message.edit_text('Вы уверены что хотите разослать розыгрыш по всем каналам/чатам?',
                               reply_markup=user_kb.confirm_send(event_id))
    except:
        await cb.message.answer('Вы уверены что хотите разослать розыгрыш по всем каналам/чатам?',
                               reply_markup=user_kb.confirm_send(event_id))
    


@router.callback_query(F.data.startswith('decline_'))
async def handle_decline(cb: types.CallbackQuery):
    await cb.message.edit_text(
        text='Успешно отменено',
        reply_markup=user_kb.back_to_menu()
    )



@router.callback_query(F.data.startswith('confirm_send_'))
async def confirm_sending(cb: types.CallbackQuery, bot: config.Bot):
    await cb.answer()
    event_id = cb.data.split('_')[-1]
    
    event = await req.get_event(int(event_id))

    if not event.channel_event_ids or event.channel_event_ids == '':
        await cb.message.answer('Нету активных каналов!', reply_markup=user_kb.back_to_event(event_id))
        return
    


    message_idss = []

    
    for channel_id in event.channel_event_ids.split(','):
        
        event = await req.get_event(int(event_id))

        user_count = 0
        win_count = None
        raffle_data = None
        msg: types.Message = None
        if event.user_event_ids:
            user_count = len(event.user_event_ids.split(','))
        
        win_count = event.win_count
        raffle_data = event.end_date.strftime("%d.%m.%Y, %H:%M")


        webapp_url = 'https://t.me/' + (await bot.get_me()).username + f'?startapp='+utils.encode_data(f'event_id={event.id}&mode=raffle')


        if event.media:
            msg = await bot.send_photo(
                chat_id=channel_id,
                photo=event.media,
                caption=lexicon.EVENT_TEXT.format(
                name=event.name,
                description=event.description or '',
                users_count=user_count,
                win_count=win_count,
                raffle_date=raffle_data
                ),
                reply_markup= user_kb.show_event_web_kb(url=webapp_url)
            )
        else:
            msg = await bot.send_message(
                chat_id=channel_id,
                text=lexicon.EVENT_TEXT.format(
                name=event.name,
                description=event.description or '',
                users_count=user_count,
                win_count=win_count,
                raffle_date=raffle_data
                ),
                reply_markup= user_kb.show_event_web_kb(url=webapp_url)
            )
        if msg:

            message_idss.append(
                {'channel_id': channel_id, 'msg_id': str(msg.message_id)}
            )
            # event_message_ids = event.message_ids
            # if not event.message_ids or event.message_ids  == '':
            #     event_message_ids = channel_id+":"+str(msg.message_id)
            # else:
            #     try:
            #         if event_message_ids:
            #             event_message_ids = ','.join(list(set(event_message_ids.split(',').append(channel_id+":"+str(msg.message_id)))))
            #     except:
            #         lg.error(f"EVENT {event.id}, MESSAGES = {event_message_ids}, MESSAGE = {msg.message_id}, CHANNEL = {channel_id}")
            lg.info(f"EVENT {event.id}, MESSAGES = {message_idss}")
    
    
    event_messages_ids = []
    for item in message_idss:
        event_messages_ids.append(item['channel_id'] + ":" + item['msg_id'])

    event_messages_ids = list(set(event_messages_ids))

    await req.update_event(
        event_id=int(event_id),
        message_ids=','.join(event_messages_ids)
    )

    await cb.message.edit_text('Успешно разослано по всем каналам!', reply_markup=user_kb.back_to_event(event_id))


@router.callback_query(F.data.startswith('confirm_delete_'))
async def confirm_sending(cb: types.CallbackQuery, bot: config.Bot):
    await cb.answer()
    event_id = cb.data.split('_')[-1]

    event = await req.get_event(int(event_id))

    if not event:
        await cb.message.answer('Розыгрыш не был найден, попробуйте еще раз',reply_marukup=user_kb.back_to_menu())
        return
    
    if event.message_ids:
        for data in event.message_ids.split(','):
            try:
                chat_id, message_id = data.split(':') 

                await cb.bot.delete_message(
                    chat_id=chat_id,
                    message_id=message_id
                )
            except:
                pass

    # await req.delete_event(int(event_id))
    await req.update_event(
        event_id=event.id,
        deleted = True,
        is_active = False
    )
    user = await req.get_user(cb.from_user.id)
    
    # rm event id from channels
    event_channels = event.channel_event_ids.split(',')
    for channel_id in event_channels:
        try:
            channel = await req.get_channel(int(channel_id))
            chnl_event_ids = channel.root_event_ids.split(',')
            chnl_event_ids.remove(event_id)
            await req.update_channel(
                channel_id=channel.id,
                root_event_ids=','.join(chnl_event_ids)
            )
        except:
            pass

    # rm event id from user events
    new_user_events = user.event_ids.split(',')
    new_user_events.remove(event_id)

    await req.update_user(
        user_id=user.user_id,
        event_ids=','.join(new_user_events)
    )

    await cb.message.edit_text(
        text='Розыгрыш успешно удален',
        reply_markup=user_kb.back_to_menu()
    )







def apply_html_formatting(text: str, entities: list[types.MessageEntity]) -> str:
    """
    Преобразует сущности сообщения в HTML-теги.
    """
    # Экранируем спецсимволы в тексте
    escaped_text = escape(text)
    
    # Сортируем сущности по убыванию offset, чтобы не сломать индексы
    sorted_entities = sorted(entities, key=lambda e: -e.offset)
    
    # Применяем форматирование
    for entity in sorted_entities:
        start = entity.offset
        end = entity.offset + entity.length
        fragment = escaped_text[start:end]
        
        match entity.type:
            case MessageEntityType.BOLD:
                replacement = f"<b>{fragment}</b>"
            case MessageEntityType.ITALIC:
                replacement = f"<i>{fragment}</i>"
            case MessageEntityType.CODE:
                replacement = f"<code>{fragment}</code>"
            case MessageEntityType.PRE:
                replacement = f"<pre>{fragment}</pre>"
            case MessageEntityType.UNDERLINE:
                replacement = f"<u>{fragment}</u>"
            case MessageEntityType.STRIKETHROUGH:
                replacement = f"<s>{fragment}</s>"
            case MessageEntityType.TEXT_LINK:
                replacement = f'<a href="{entity.url}">{fragment}</a>'
            case MessageEntityType.CUSTOM_EMOJI:
                replacement = f'<tg-emoji emoji-id="{entity.custom_emoji_id}">{fragment}</tg-emoji>'
            case _:
                replacement = fragment
        
        escaped_text = escaped_text[:start] + replacement + escaped_text[end:]
    
    return escaped_text





""" CHANNEL ADD """


@router.message(F.chat_shared)
async def handle_chat_selection(message: types.Message, bot: config.Bot):
    chat_shared = message.chat_shared  # Получаем объект ChatShared из сообщения
    try:
        chat = await bot.get_chat(chat_id=chat_shared.chat_id)
    except:
        await message.answer('Бота нет в данном чате/канале, сначала добавьте его и предоставьте права администратора!', 
                             reply_markup=user_kb.back_to_menu())
        return
    

    chat_username= chat.username
    chat_title = chat.title

    print(chat_username)
    if not chat_username:
        await message.answer('Невозможно добавить канал/чат без username!',reply_markup=user_kb.back_to_menu())
        return
    
    user = await req.get_user(message.from_user.id)
    
    list_user_channels = user.channel_ids

    if not user.channel_ids:
        list_user_channels = []
    else:
        list_user_channels = list_user_channels.split(",")

    if str(chat_shared.chat_id) in list_user_channels:
        await message.answer('Канал уже добавлен!',reply_markup=user_kb.back_to_menu())
        return
        

    if chat_shared.request_id == 1:
        # Логика для добавления группы
        chat_id = chat_shared.chat_id

        await req.add_channel(
            channel_id=chat_id,
            name=chat_title,
            url='https://t.me/' + chat_username
        )

        if user.channel_ids:
            await req.update_user(
                    user_id=message.from_user.id,
                    channel_ids=user.channel_ids + ',' + str(chat_id)
                )
        else:
            await req.update_user(
                    user_id=message.from_user.id,
                    channel_ids=str(chat_id)
                )

        await message.answer(f"Выбрана группа: {chat_title} \nID: {chat_id}",reply_markup=user_kb.back_to_menu())

    elif chat_shared.request_id == 2:
        # Логика для добавления канала
        chat_id = chat_shared.chat_id

        await req.add_channel(
            channel_id=chat_id,
            name=chat_title,
            url='https://t.me/' + chat_username
        )
        if user.channel_ids:
            await req.update_user(
                user_id=message.from_user.id,
                channel_ids=user.channel_ids + ',' + str(chat_id)
            )
        else:
            await req.update_user(
                    user_id=message.from_user.id,
                    channel_ids=str(chat_id)
              )

        await message.answer(f"Выбран канал: {chat_title} \nID: {chat_id}",reply_markup=user_kb.back_to_menu())



"""  Channel DELETE  """




@router.message(F.text == 'Удалить Канал|Группу')
async def delete_channel(message: types.Message):
    user = await req.get_user(message.from_user.id)
    
    if not user.channel_ids:
        await message.answer('У вас нет каналов, добавьте их')
        return

    await message.answer(
        text='Выбери канал для удаления:', 
        reply_markup= await user_kb.select_channel_delete(user)
        )


@router.callback_query(F.data.startswith('ChannelDelete_'))
async def select_channel(cb: types.CallbackQuery):
    channel = await req.get_channel(int(cb.data.split('_')[-1]))

    try:

        await cb.message.edit_text(
            text=f'Выбран: {channel.name}\n\nУдалить?', 
            reply_markup=user_kb.confirm_del_channel(channel_id=channel.id)
        )
    except:
        await cb.message.answer(
            text=f'Выбран: {channel.name}\n\nУдалить?', 
            reply_markup=user_kb.confirm_del_channel(channel_id=channel.id)
        )






@router.callback_query(F.data.startswith('ChannelDelConf_'))
async def confirm_del_channel(cb: types.CallbackQuery):

    channel = await req.get_channel(int(cb.data.split('_')[-1]))
    
    if not channel:
        await cb.message.answer('Нет такого канала, ошибка.')
        return
    

    user = await req.get_user(cb.from_user.id)

    user_channels_ids = user.channel_ids.split(',')
    for channel_id in user_channels_ids:
        lg.info(f'channel_id: {channel_id}')
        
        if channel_id == str(channel.id):
            user_channels_ids.remove(str(channel.id))
            break
        
    await req.update_user(
        user_id=user.user_id,
        channel_ids=','.join(user_channels_ids)
    )


    for event in await req.get_events():
        if event.channel_event_ids:
        
            event_channels = event.channel_event_ids.split(',')

            for channel_event_id in event_channels:
                if channel_event_id != '':
                    if channel_event_id == str(channel.id):
                        event_channels.remove(str(channel.id))
                        break
            
            await req.update_event(
                event_id=event.id,
                channel_event_ids = ','.join(event_channels)
            )
    try:
        await cb.message.edit_text(
            text=f'Успешно удалено', 
            reply_markup=user_kb.back_to_menu()
        )
                
    except:
        await cb.message.answer(
            text=f'Успешно удалено', 
            reply_markup=user_kb.back_to_menu()
        )




'''  NEW EVENT  '''


@router.message(F.text == 'Новый розыгрыш')
async def new_event(message: types.Message, state: FSMContext):
    # Создаем событие

    await message.answer('Введите название розыгрыша:', 
                         reply_markup=user_kb.back_to_menu())
    await state.set_state(UserStates.AddEvent.name)


@router.message(UserStates.AddEvent.name)
async def new_event(message: types.Message, state: FSMContext):

    await state.update_data(name=message.text)
    
    await message.answer('Введите описание розыгрыша:', 
                         reply_markup=user_kb.back_to_menu())
    await state.set_state(UserStates.AddEvent.description)


@router.message(UserStates.AddEvent.description)
async def set_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    
    await message.answer(
        'Использовать реферальную систему?\nВведите кол-во тикетов за приглашенного пользователя:\n\n<b>Введите 0 чтобы не использовать реф. систему</b>',
        reply_markup=user_kb.back_to_menu()
    )
    await state.set_state(UserStates.AddEvent.tickets_for_ref_count)



@router.message(UserStates.AddEvent.tickets_for_ref_count)
async def set_channels(message: types.Message, state: FSMContext):
    try:
        # Проверяем корректность ввода ID каналов
        count_ref_tickets = int(message.text)

        await state.update_data(ref_tickets_count=count_ref_tickets)
        
        await message.answer(
            'Введите количество победителей:',
            reply_markup=user_kb.back_to_menu()
        )
        await state.set_state(UserStates.AddEvent.win_count)
        
    except ValueError:
        await message.answer('❌ Ошибка! Введите числовое значение')

@router.callback_query(F.data == 'ReferralSkip')
async def set_channels(message: types.Message, state: FSMContext):
      
    await message.edit_text(
        'Введите количество победителей:',
        reply_markup=user_kb.back_to_menu()
    )
    await state.set_state(UserStates.AddEvent.win_count)



@router.message(UserStates.AddEvent.win_count)
async def set_win_count(message: types.Message, state: FSMContext):
    if message.text.isdigit() and int(message.text) > 0:
        await state.update_data(win_count=int(message.text))
        
        await message.answer(
            f'Введите дату окончания розыгрыша (ДД.ММ.ГГГГ ЧЧ:ММ):\n\nАктуальное время в боте: {datetime.now().strftime("%d.%m.%Y %H:%M")} MSK',
            reply_markup=user_kb.back_to_menu()
        )
        await state.set_state(UserStates.AddEvent.end_date)
    else:
        await message.answer('❌ Введите корректное число больше 0')


@router.message(UserStates.AddEvent.end_date)
async def set_end_date(message: types.Message, state: FSMContext):
    try:
        # Парсим дату из сообщения
        date_obj = datetime.strptime(message.text, '%d.%m.%Y %H:%M')
        
        # Проверяем что дата в будущем
        if date_obj <= datetime.now():
            raise ValueError
        
        await state.update_data(end_date=date_obj)
        
        # Получаем все данные из состояния
        data = await state.get_data()
        
        event = await req.create_event(
            name=data['name'],
            win_count=data['win_count'],
            owner_id=message.from_user.id,
            description=data['description'],
            end_date = date_obj,
            ref_tickets_count=data['ref_tickets_count']
        )

        if not event:
            await message.answer('Ошибка создания! Попробуйте снова...', reply_markup=user_kb.back_to_menu())
            return
        

        user = await req.get_user(message.from_user.id)

        if not user.event_ids: 
            await req.update_user(
                user_id=message.from_user.id,
                event_ids=str(event.id) + ','
            )
        else:
            await req.update_user(
                user_id=message.from_user.id,
                event_ids=user.event_ids+str(event.id) + ','
            )


        await message.answer(
            '🎉 Розыгрыш успешно создан!',
            reply_markup=user_kb.back_to_menu()
        )
        await state.clear()
        
    except ValueError:
        await message.answer(f'❌ Неверный формат даты или дата в прошлом! Используйте формат ДД.ММ.ГГГГ ЧЧ:ММ по MSK\n\nАктуальное время в боте: {datetime.now().strftime("%d.%m.%Y %H:%M")}')






@router.callback_query(F.data.startswith('event_'))
async def handler_event_ation(cb: types.CallbackQuery):
    action = cb.data.split('_')[-2]
    event_id = int(cb.data.split('_')[-1])


    if action == 'delete':
        try:
            await cb.message.edit_text(
            text='Вы действительно хотите <b>УДАЛИТЬ</b> ваш розыгрыш?',
            reply_markup=user_kb.confirm_delete_event(event_id)
            )
        except:
            await cb.message.answer(
            text='Вы действительно хотите <b>УДАЛИТЬ</b> ваш розыгрыш?',
            reply_markup=user_kb.confirm_delete_event(event_id)
        )