from aiogram.types import TelegramObject, ChatMemberMember, ChatMemberAdministrator, ChatMemberOwner
from aiogram import Bot

from typing import List


from database import req
from database.models import Ticket, Channel
from settings import request_utils, utils

import config

from datetime import datetime, timedelta

import hashlib
import hmac
from operator import itemgetter
from urllib.parse import parse_qsl






async def get_json_subscriptions(bot: Bot, user_tg_id: int, channels: List[Channel]):
    result = {
        "allSubscribed": False,
        "details": []
    }

    for channel in channels:
        if channel.is_active:
            
            if not request_utils.check_subscription(user_tg_id, channel.id, config.BOT_TOKEN):
                image = request_utils.get_channel_image(
                            bot_token=config.BOT_TOKEN,
                            channel_id=channel.id
                        )
                if image:
                    if len(image) == 2:
                        image = utils.bytes_to_data_url(image[0])
                    else:
                        image = '/friends.webp'
                else:
                    image = '/friends.webp'

                result['details'].append(
                    {
                        "channelId": channel.id,
                        "image_data": image,
                        "channelName": channel.name,
                        "channelUrl": channel.url,
                        "isSubscribed": False
                    }
                )
            
    if len(result['details']) == 0:
        result['allSubscribed'] = True

    return result




async def user_tickets_not_in_event(user: req.User, event: req.Event):

    if not user.tickets_ids:
        return True
    
    if not event.tickets_event:
        return True

    
    user_tickets_nums = [i.number for i in await req.get_user_tickets(user.user_id) if i]
    event_tickets = []
    
    for ticket_id in event.tickets_event.split(','):
        if not ticket_id == '':
            try:
                event_tickets.append(
                    (await req.get_ticket(int(ticket_id))).number
                )
            except:
                pass

    for user_ticket in user_tickets_nums:
        if user_ticket in event_tickets:
            return False
        
    return True











async def _get_tickets(user: req.User, event: req.Event):
    tickets = []
    user_tickets = user.tickets_ids.split(',') if user.tickets_ids else []
    for ticket_id in user_tickets:
        if not ticket_id == '' and ticket_id.isdigit():
            try:
                ticket = await req.get_ticket(int(ticket_id))

                if ticket.event_id == event.id:
                    tickets.append({
                        "id": ticket.id,
                        "number": ticket.number,
                        "createdAt": ticket.created_at.strftime("%d.%m.%Y, %H:%M")
                        })
            except Exception as e:
               
               pass 
                # return {
                #     'ok': False,
                #     'err': str(e)
                # }
        
    return tickets


async def get_json_user_tickets(user_id: int, event_id: int):
    user = await req.get_user(user_id=user_id)
    event = await req.get_event(event_id=event_id)

    
    return {
            "tickets": await _get_tickets(user=user, event=event)
        } 



async def get_json_event_time(eventId: int):
    print(eventId)
    event = await req.get_event(int(eventId))
    
    event_date = event.end_date

    date = event_date - datetime.now()
    
    
    return {
     
            "days": 0,
            "hours": 0,
            "minutes": 0,
            "seconds": date.days*24*60*60 + date.seconds,
            "users_to_invite": event.ref_tickets_count
            
        }



async def get_json_event(eventId: int):
    print(eventId)
    event = await req.get_event(int(eventId))
    
    return { 
        "users_to_invite":event.ref_tickets_count,
        "use_captcha": event.use_captcha
        }


async def get_json_event_winners(eventId: int):
    print(eventId)
    event_winners = await req.get_event_winners(int(eventId))
    # print(event_winners)
    result = []
    
    for i, winner in enumerate(event_winners):
        try:
            image_url = request_utils.get_channel_image(
                bot_token=config.BOT_TOKEN, channel_id=winner.user_id)
            if image_url:
                if len(image_url) == 2:
                    image_url = utils.bytes_to_data_url(image_url[0])
            else:
                image_url = '/friends.webp'
        except:
            image_url =  '/friends.webp'
        tickets = [await req.get_ticket(int(ticket_id)) for ticket_id in winner.tickets_ids.split(',') if ticket_id!='' and (not ticket_id.startswith("<database"))]
        
        result.append(
            {
                'id':i,
                'ticket': tickets[0].number,
                'name':winner.fullname,
                'image_url': image_url
            }
        )

    # print('res', result)

    return result




    


async def get_json_user(userId, event_id):
    user = await req.get_user(user_id=userId)
    event = await req.get_event(event_id=event_id)


    return {
        "id": user.user_id,
        "referralLink": config.BOT_URL + f'?startapp='+utils.encode_data(f'event_id={event.id}&mode=ref&referrer_id={userId}'),
        # "referralLink": f"{config.BOT_URL}?start={userId}-{event_id}", # t.me/<bot_username>?start=<parameter>
        "tickets": await _get_tickets(user=user, event=event)
        }




async def get_captcha_json():
    captcha_img, captcha_ans = await utils.generate_captcha()
    wrong2 = [await utils.generate_random_string(5) for _ in (0,1)]
    wrong2.append(captcha_ans)
    
    asnwers = wrong2
    
    image_data = utils.pillow_image_to_data_url(captcha_img)

    return {
        "image": image_data,
        "answers": asnwers,
        "right": captcha_ans
    }




async def get_json_event_channels(eventId):
    event = await req.get_event(eventId)

    channels_event: list[req.Channel] = []


    for channel_id in event.channel_event_ids.split(','):
        if not channel_id == '':
            channels_event.append(await req.get_channel(int(channel_id)))

    channels = []

    for channel in channels_event:
        if channel.is_active:
                channels.append(
                    {
                        "channelId": channel.id,
                        "image_data": "",
                        "channelName": channel.name,
                        "channelUrl": channel.url,
                        "isSubscribed": True
                    }
                )

    return {
        "channels": channels
        }








def check_webapp_signature(token: str, init_data: str) -> bool:
    """
    Check incoming WebApp init data signature

    Source: https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app

    :param token:
    :param init_data:
    :return:
    """
    try:
        parsed_data = dict(parse_qsl(init_data))
    except ValueError:
        # Init data is not a valid query string
        return False
    if "hash" not in parsed_data:
        # Hash is not present in init data
        return False

    hash_ = parsed_data.pop('hash')
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items(), key=itemgetter(0))
    )
    secret_key = hmac.new(
        key=b"WebAppData", msg=token.encode(), digestmod=hashlib.sha256
    )
    calculated_hash = hmac.new(
        key=secret_key.digest(), msg=data_check_string.encode(), digestmod=hashlib.sha256
    ).hexdigest()
    return calculated_hash == hash_