# Mini App Backend

Backend API для Telegram Mini App. Интегрируется с основным ботом.

## Структура

```
backend/
├── __init__.py
├── auth.py      # Валидация Telegram initData
├── routes.py    # API endpoints
└── README.md
```

## API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/mini-app/user/profile` | Профиль пользователя |
| GET | `/api/mini-app/user/payments` | История платежей |
| GET | `/api/mini-app/user/gifts` | Подарки пользователя |
| POST | `/api/mini-app/gift/activate` | Активация подарочного кода |
| POST | `/api/mini-app/payment/create` | Создание платежа |
| GET | `/api/mini-app/payment/check_status/{id}` | Статус платежа YooKassa |

## Авторизация

Все запросы должны содержать заголовок:
```
X-Telegram-Init-Data: <initData from Telegram.WebApp.initData>
```

Backend валидирует подпись initData с использованием bot_token.

## Интеграция с ботом

### 1. Добавь импорт в `src/main.py`:

```python
from mini_app.backend.routes import setup_routes
```

### 2. Настрой aiohttp сервер:

```python
from aiohttp import web

async def start_webapp_server(bot: Bot, settings):
    app = web.Application()
    
    # Настраиваем Mini App API
    setup_routes(app, settings.bot_token, bot)
    
    # Запускаем сервер
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    return runner
```

### 3. Запусти сервер при старте бота:

```python
async def on_startup(dispatcher):
    settings = get_settings()
    webapp_runner = await start_webapp_server(dispatcher.bot, settings)
    # Сохрани runner для graceful shutdown
```

### 4. Настрой reverse proxy (Caddy/Nginx):

```caddyfile
app.shftsecure.one {
    # Frontend (статика)
    root * /path/to/mini-app/frontend/dist
    file_server
    try_files {path} /index.html
    
    # Backend API
    handle /api/* {
        reverse_proxy localhost:8080
    }
}
```

## Разработка

Для локальной разработки backend возвращает mock данные.
Раскомментируй реальные вызовы в `routes.py` после интеграции.

## Переменные окружения

Frontend использует:
- `VITE_API_URL` — базовый URL API (по умолчанию `/api/mini-app`)

