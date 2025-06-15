from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import types
import config
from settings import lexicon, user_kb, utils

from database import req
from datetime import timedelta

import datetime,  logging as lg

import random





async def make_raffle(event: req.Event):
    win_count = event.win_count
    if not event.tickets_event:
        return
    

    event_tickets = [await req.get_ticket(int(ticket)) for ticket in event.tickets_event.split(',') if ticket.isdigit()]

    slave_tickets0 = [ticket for ticket in event_tickets if ticket]
    slave_tickets = [ticket for ticket in slave_tickets0 if not ticket.is_winner]

    # 😈
    root_winners0 = [ticket for ticket in event_tickets if ticket]
    root_winners = [ticket for ticket in root_winners0 if ticket.is_winner]

    if win_count > len(event_tickets):
        win_count = len(event_tickets)

    try:
        winners = random.choices(population=slave_tickets, k=win_count - len(root_winners))
    except IndexError:
        winners = []

    # 😈
    winners.extend(root_winners)

    for winner in winners:
        await req.update_ticket(winner.id, is_winner=True)

    # 😈
    return winners 








class Scheduler:
    def __init__(self):

        self.scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


    async def update_posts(self, bot: config.Bot):
        events = await req.get_active_events()

        for event in events:
            if event.message_ids:
                user_count = 0
                win_count = None
                raffle_data = None
                msg: types.Message = None
                if event.user_event_ids:
                    user_count = len(event.user_event_ids.split(','))
                
                win_count = event.win_count
                raffle_data = event.end_date.strftime("%d.%m.%Y, %H:%M")


                webapp_url = 'https://t.me/' + (await bot.get_me()).username + f'?startapp='+utils.encode_data(f'event_id={event.id}&mode=raffle')


                for data in event.message_ids.split(','):
                    try:
                        chat_id, message_id = data.split(':') 

                        try:
                            await bot.edit_message_text(
                                chat_id=int(chat_id),
                                message_id=int(message_id),
                                text = lexicon.EVENT_TEXT.format(
                                    name=event.name,
                                    description=event.description or '',
                                    users_count=user_count,
                                    win_count=win_count,
                                    raffle_date=raffle_data
                                ),
                                reply_markup= user_kb.show_event_web_kb(url=webapp_url)
                            )
                        except:
                            try:
                                await bot.edit_message_caption(
                                    chat_id=int(chat_id),
                                    message_id=int(message_id),
                                    caption = lexicon.EVENT_TEXT.format(
                                        name=event.name,
                                        description=event.description or '',
                                        users_count=user_count,
                                        win_count=win_count,
                                        raffle_date=raffle_data
                                    ), 
                                    reply_markup= user_kb.show_event_web_kb(url=webapp_url)
                                )
                            except:
                                pass

                    except:
                        pass
    

    

    async def check_end_date(self, bot: config.Bot):

        events = await req.get_active_events()

        for event in events:
            if event.tickets_event:
                if datetime.datetime.now() > event.end_date and event.is_active:
                    if event.message_ids:
                        
                        tickets_winners = await make_raffle(event)

                        if event.user_event_ids:
                            user_count = len(event.user_event_ids.split(','))
                        else:
                            user_count = 0

                        win_count = None
                        raffle_data = None
                    
                        if event.user_event_ids:
                            user_count = len(event.user_event_ids.split(','))
                        
                        win_count = event.win_count
                        raffle_data = event.end_date.strftime("%d.%m.%Y, %H:%M")

                        
                        
                        winners = await req.get_event_winners(event.id)

                        text_winners = '\n'.join([f"    {i}. {winner.fullname}" for i, winner in enumerate(winners, start=1)])
                        text_for_owner_winners = '\n'.join([f'''    {j}. <a href="{'https://t.me/'+winner.username if winner.username else 'tg://user?id='+str(winner.user_id)}">    {winner.fullname}</a>''' for j, winner in enumerate(winners, start=1)])
                        
                        deeplink_url = 'https://t.me/' + (await bot.get_me()).username + f'?startapp=' + utils.encode_data(f'event_id={event.id}&mode=results')


                        for data in event.message_ids.split(','):
                            channel_id, message_id = data.split(':')
                            if event.media:
                                await bot.edit_message_caption(
                                    message_id=message_id,
                                    chat_id=channel_id,
                                    caption=lexicon.EVENT_WIN_TEXT.format(
                                        name=event.name,
                                        winners=text_winners,
                                        users_count=user_count,
                                        win_count=win_count,
                                        raffle_date=raffle_data
                                    ),
                                    reply_markup= user_kb.show_event_results_web_kb(url=deeplink_url)
                                )
                            else:
                                await bot.edit_message_text(
                                    chat_id=channel_id,
                                    message_id=message_id,
                                    text=lexicon.EVENT_WIN_TEXT.format(
                                        name=event.name,
                                        winners=text_winners,
                                        users_count=user_count,
                                        win_count=win_count,
                                        raffle_date=raffle_data
                                    ),
                                    reply_markup= user_kb.show_event_results_web_kb(url=deeplink_url)
                                )
                        await bot.send_message(
                            chat_id=event.owner_id,
                            text="Ваш розыгрыш завершен!\n\n" + lexicon.EVENT_WIN_TEXT.format(
                                name=event.name,
                                winners=text_for_owner_winners,
                                users_count=user_count,
                                win_count=win_count,
                                raffle_date=raffle_data
                            ),
                            reply_markup=user_kb.show_event_results_web_kb(url=deeplink_url)
                        )
                        await req.update_event(
                            event_id=event.id,
                            is_active=False
                        )
                        
            
    
    async def start_scheduler(self, bot: config.Bot):
        self.scheduler.add_job(self.check_end_date, 'cron', minute="*", args=(bot,))
        self.scheduler.add_job(self.update_posts, 'interval', minutes=10, args=(bot,))
        self.scheduler.start()




AsyncScheduler = Scheduler()
