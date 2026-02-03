"""
Авторизация Mini App через Telegram initData.
"""
import hashlib
import hmac
import json
from urllib.parse import unquote
from typing import Optional
from dataclasses import dataclass


@dataclass
class TelegramUser:
    """Данные пользователя из Telegram initData."""
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: bool = False


def validate_init_data(init_data: str, bot_token: str) -> Optional[TelegramUser]:
    """
    Проверяет подлинность initData от Telegram Mini App.
    
    Args:
        init_data: Строка initData из Telegram WebApp
        bot_token: Токен бота
        
    Returns:
        TelegramUser если данные валидны, None если нет
    """
    if not init_data:
        return None

    try:
        # Парсим данные
        parsed = {}
        for pair in init_data.split('&'):
            if '=' in pair:
                key, value = pair.split('=', 1)
                parsed[key] = unquote(value)

        # Получаем hash для проверки
        check_hash = parsed.pop('hash', None)
        if not check_hash:
            return None

        # Формируем строку для проверки
        data_check_string = '\n'.join(
            f'{k}={v}' for k, v in sorted(parsed.items())
        )

        # Вычисляем секретный ключ
        secret_key = hmac.new(
            b'WebAppData',
            bot_token.encode(),
            hashlib.sha256
        ).digest()

        # Вычисляем hash
        computed_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        # Сравниваем
        if computed_hash != check_hash:
            return None

        # Парсим данные пользователя
        user_data = json.loads(parsed.get('user', '{}'))
        if not user_data.get('id'):
            return None

        return TelegramUser(
            id=user_data['id'],
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name'),
            username=user_data.get('username'),
            language_code=user_data.get('language_code'),
            is_premium=user_data.get('is_premium', False),
        )

    except Exception:
        return None

