from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from environs import Env

import os

os.environ.clear()

env = Env()
env.read_env()
# print(env.path())
# admins=env('ADMIN_IDS')
# print('admins:', admins)
ADMIN_IDS: list[int] = list(map(int, env('ADMIN_IDS').split(',')))

BOT_TOKEN = env('BOT_TOKEN')

BOT_URL = env('BOT_URL')

SERVER_IP = env('SERVER_IP')

HOST_URL = env('HOST_URL')



bot=Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='html', link_preview_is_disabled=True))
dp=Dispatcher()
