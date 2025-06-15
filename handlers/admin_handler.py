from aiogram import Router, F, Bot, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from middlewares.filters import AdminProtect
from settings import UserStates, admin_kb, lexicon
from database import req
from middlewares.MiddleWares import AlbumMiddleware

from config import ADMIN_IDS


from datetime import timedelta, datetime
import logging as lg





router=Router()
router.message.middleware(AlbumMiddleware())





@router.message(Command("apanel"), AdminProtect())
async def admin_panel(message: types.Message, bot: Bot):
    await message.answer("Приветсвенное сообщение для администратора", reply_markup=admin_kb.admin_start())






@router.callback_query(F.data.startswith('admin_'))
async def main_admin(cb: types.CallbackQuery, state: FSMContext):
    action = cb.data.split('_')[-1]

    if action == 'raffles':
        await cb.message.edit_text('🔍 Введите ключевые слова в названии розыгрша: ', reply_markup= admin_kb.admin_back())
        await state.set_state(UserStates.FindEvent.event_name)
    elif action == 'back':
        try: await state.clear()
        except: pass

        try:
            await cb.message.edit_text("Приветсвенное сообщение для администратора", reply_markup=admin_kb.admin_start())
        except:
            await cb.message.answer("Приветсвенное сообщение для администратора", reply_markup=admin_kb.admin_start())
    else:
        await cb.message.answer('Что-то не так...', reply_markup= admin_kb.admin_back())


@router.message(UserStates.FindEvent.event_name)
async def handle_event_name(message: types.Message, state: FSMContext):
    event_name = message.text

    if len(event_name) < 4:
        await message.answer('Введите слово, в котором больше 3х букв', reply_markup=admin_kb.admin_back())
        return

    events = await req.find_events_by_name(event_name)
    lg.info(events)
    lg.info([i.name for i in events])

    if len(events) == 0:
        await message.answer('Ничего не найдено, попробуйте еще раз:', reply_markup=admin_kb.admin_back())
        return
    
    await state.clear()
        
    try:
        await message.edit_text("Выберите розыгрыш", reply_markup=admin_kb.available_events(events))
    except:
        await message.answer("Выберите розыгрыш", reply_markup=admin_kb.available_events(events))


@router.callback_query(F.data.startswith('adminShow_'))
async def show_admin_event(cb: types.CallbackQuery, state: FSMContext):
    event_id = int(cb.data.split('_')[-1])

    await state.update_data(event_id=event_id)

    try:
        await cb.message.edit_text('Розыгрыш выбран, введите "счастливые" тикеты:\n\nПример1: ABC123\nПример2: ABC123,BBB456', reply_markup=admin_kb.admin_back())
    except:
        await cb.message.answer('Розыгрыш выбран, введите "счастливые" тикеты:\n\nПример1: ABC123\nПример2: ABC123,BBB456', reply_markup=admin_kb.admin_back())

    await state.set_state(UserStates.SetWinners.winners)


@router.message(UserStates.SetWinners.winners)
async def get_winners_from_admin(message: types.Message, state: FSMContext):
    olddata = await state.get_data()
    if 'event_id' not in olddata.keys():
        await message.answer('Данные устарели, попробуйте заново', 
                                reply_markup=admin_kb.admin_back())
        await state.clear()
        return

    current_winners = olddata['winners'] if 'winners' in olddata.keys() else ''

    event = await req.get_event(int(olddata['event_id']))
    if not event.tickets_event:
        await message.answer('В данном розыгрыше еще никто не учавствовал...')
        await state.clear()
        return
    
    if len(event.tickets_event.split(',')) < len(message.text.split(',')):
        await message.answer(f'В данном розыгрыше {len(event.tickets_event.split(','))} победителей!')
        await state.clear()
        return
    

    await state.update_data(winners = current_winners + message.text)


    data = await state.get_data()

    text = lexicon.ADMIN_ADD_TICKETS_TEXT.format(tickets = '\n'.join(data['winners'].split(',')))

    try:
        await message.edit_text(text=text, reply_markup=admin_kb.confirm_winners())
    except:
        await message.answer(text=text, reply_markup=admin_kb.confirm_winners())
        


@router.callback_query(F.data == 'confirmWinners')
async def confirm_winners(cb: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if (not 'winners' in data.keys()) or (not 'event_id' in data.keys()):
        await cb.message.answer('Данные устарели, попробуйте заново', 
                                reply_markup=admin_kb.admin_back())
        await state.clear()
        return
    
    event = await req.get_event(int(data['event_id']))
    root_tickets: list = data['winners'].split(',')
    len_root_tickets = len(root_tickets)


    

    for ticket_id in event.tickets_event.split(','):
        if ticket_id != '':
            ticket = await req.get_ticket(int(ticket_id))
            if ticket:
                if ticket.number in root_tickets:
                    await req.update_ticket(
                        id=ticket.id,
                        is_winner=True
                    )
                    root_tickets.remove(ticket.number)

    unhided_tickets = '' if len(root_tickets) == 0 else "\nНе найденные тикеты:\n"+'\n'.join(root_tickets)
    
    
    await cb.message.answer(
            text=f"Успешно обработанно: <b>{len_root_tickets-len(root_tickets)} шт.</b>\n"+\
            f'Не найденных тикетов: <b>{len(root_tickets)} шт.</b>\n'\
                +unhided_tickets,
            
            reply_markup= admin_kb.admin_back()
    )



    