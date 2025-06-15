import random
import base64
from PIL import Image, ImageDraw, ImageFont
from aiogram import types, Bot

import io







default_color_red = 228
default_color_green = 150
default_color_blue = 150

async def generate_random_string(length):
    random_string = ""
    for i in range(0,length):
        random_string = random_string + random.choice('1234567890ABCDEFGHIJKLMNOPQRSTUVQXYZ')
    return random_string

async def draw_random_ellipse(draw):
    a = random.randrange(10, 300, 1)
    b = random.randrange(10, 275, 1)
    c = a + random.randrange(10, 90, 1)
    d = b + random.randrange(10, 90, 1)
    draw.ellipse((a,b,c,d), fill=(default_color_red + random.randrange(-100,100,1), 
                                  default_color_green + random.randrange(-100,100,1), 
                                  default_color_blue + random.randrange(-100,100,1), 255), 
                                  outline = "black")

async def generate_captcha():
    '''
    Generate a captcha
    :return: A tuple (image, captcha string encoded in the image)
    '''
    captcha_string = await generate_random_string(5)

    captcha_image = Image.new("RGBA", (400, 200), (default_color_red,default_color_green,default_color_blue))
    draw = ImageDraw.Draw(captcha_image, "RGBA")
    for i in range(1,20):
        await draw_random_ellipse(draw)

    fontStyle = ImageFont.truetype("Aaargh.ttf", 48)     # font must be in the same folder as the .py file. 

    # Arbitrary starting co-ordinates for the text we will write
    x = 10 + random.randrange(0, 100, 1)
    y = 79 + random.randrange(-10, 10, 1)
    for letter in captcha_string:
        draw.text((x, y), letter, (0,0,0),font=fontStyle)    # Write in black
        x = x + 35
        y = y +  random.randrange(-10, 10, 1)
    
    return (captcha_image, captcha_string)  # return a heterogeneous tuple



def bytes_to_data_url(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """
    Конвертирует байты изображения в Data URL
    :param image_bytes: Бинарные данные изображения
    :param mime_type: MIME-тип изображения (например, image/jpeg, image/png)
    :return: Data URL строка
    """
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"



def pillow_image_to_data_url(img):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return 'data:image/jpeg;base64,' + base64.b64encode(buffered.getvalue()).decode("utf-8")


def base64_string_to_pillow_image(base64_str):
    return Image.open(io.BytesIO(base64.decodebytes(bytes(base64_str, "utf-8"))))


def encode_data(string: str) -> str:
    """
    Кодирует словарь в base64 строку, безопасную для URL
    """
    # Преобразуем словарь в JSON-строку
    
    # Кодируем в bytes
    data_bytes = string.encode('utf-8')
    
    # Кодируем в base64 и делаем безопасным для URL
    encoded = base64.urlsafe_b64encode(data_bytes).decode('utf-8')
    
    return encoded





