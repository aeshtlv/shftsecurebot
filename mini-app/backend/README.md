# Mini App Backend

API endpoints для Telegram Mini App.

## Интеграция с ботом

Добавьте в `src/main.py` или создайте отдельный веб-сервер:

```python
from aiohttp import web
from mini_app.backend.webapp_routes import create_webapp_routes

# В функции main() или отдельном модуле:
async def setup_webapp_server(bot_token: str, api_client, database):
    """Запуск веб-сервера для Mini App API."""
    
    # Создаём routes
    routes = create_webapp_routes(bot_token, api_client, database)
    
    # Создаём приложение
    app = web.Application()
    app.add_routes(routes)
    
    # Настраиваем CORS для Mini App
    import aiohttp_cors
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods=["GET", "POST", "OPTIONS"],
        )
    })
    
    for route in list(app.router.routes()):
        cors.add(route)
    
    # Запускаем сервер
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    return runner
```

## API Endpoints

### GET /api/webapp/dashboard
Главная страница - информация о пользователе, подписке, лояльности.

**Headers:**
- `X-Telegram-Init-Data`: initData из Telegram WebApp

**Response:**
```json
{
  "user": {
    "telegramId": 123456789,
    "username": "user",
    "firstName": "Имя"
  },
  "subscription": {
    "status": "active",
    "endDate": "2026-04-15T00:00:00Z",
    "trafficUsed": 45.8,
    "trafficTotal": 300
  },
  "loyalty": {
    "level": "silver",
    "points": 320,
    "discount": 5
  },
  "referral": {
    "count": 3,
    "earned": 150
  }
}
```

### GET /api/webapp/loyalty
Профиль лояльности.

### GET /api/webapp/plans
Список тарифов с учётом скидки пользователя.

### GET /api/webapp/gifts
Подарочные коды пользователя.

### POST /api/webapp/gifts/activate
Активация подарочного кода.

**Body:**
```json
{
  "code": "SHFT-XXXX-XXXX-XXXX"
}
```

### GET /api/webapp/payments
История платежей.

### GET /api/webapp/subscription/config
Получение URL конфигурации подписки.

## Безопасность

Все запросы верифицируются через `X-Telegram-Init-Data` header.
Используется HMAC-SHA256 для проверки подписи данных от Telegram.

## Зависимости

```
aiohttp>=3.9.0
aiohttp-cors>=0.7.0
```

