import requests
import base64
from typing import Optional, Tuple



def check_subscription(user_id: int, channel_id: str, bot_token: str) -> bool:
    url = f"https://api.telegram.org/bot{bot_token}/getChatMember"
    params = {
        "chat_id": channel_id,
        "user_id": user_id
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if not data['ok']:
        if data['error_code'] == 400:
            return False
        raise Exception(data['description'])
    
    status = data['result']['status']
    print(status)
    return status in ['member', 'administrator', 'creator']






def get_channel_image(bot_token: str, channel_id: str, size: str = 'small') -> Optional[Tuple[bytes, str]]:
    """
    Получает изображение канала/чата Telegram
    :param bot_token: Токен вашего бота
    :param channel_id: ID канала (например @channelname или -1001234567890)
    :param size: Размер изображения ('small' или 'big')
    :return: Кортеж (бинарные данные изображения, MIME-тип) или None
    """
    # 1. Получаем информацию о чате
    chat_info_url = f"https://api.telegram.org/bot{bot_token}/getChat"
    params = {"chat_id": channel_id}
    
    try:
        response = requests.get(chat_info_url, params=params, timeout=10)
        response.raise_for_status()
        chat_data = response.json()
        
        if not chat_data['ok']:
            print(f"Ошибка: {chat_data.get('description')}")
            return None
            
        # 2. Проверяем наличие фото
        if 'photo' not in chat_data['result']:
            print("У канала нет изображения")
            return None
            
        # 3. Получаем file_id для выбранного размера
        photo_data = chat_data['result']['photo']
        file_id = photo_data[f'{size}_file_id']

        # 4. Получаем путь к файлу
        file_info_url = f"https://api.telegram.org/bot{bot_token}/getFile"
        file_response = requests.get(file_info_url, params={'file_id': file_id})
        file_response.raise_for_status()
        file_data = file_response.json()
        
        if not file_data['ok']:
            print(f"Ошибка получения файла: {file_data.get('description')}")
            return None
            
        file_path = file_data['result']['file_path']

        # 5. Скачиваем изображение
        image_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        image_response = requests.get(image_url, timeout=10)
        image_response.raise_for_status()
        
        return image_response.content, image_response.headers['Content-Type']

    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети: {str(e)}")
    except KeyError as e:
        print(f"Некорректный ответ API: отсутствует ключ {str(e)}")
    except Exception as e:
        print(f"Неожиданная ошибка: {str(e)}")
        
    return None