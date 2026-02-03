"""
API маршруты для Mini App.
Интегрируется с основным aiohttp сервером бота.
"""
from aiohttp import web
from datetime import datetime, timedelta
from typing import Optional

from .auth import validate_init_data, TelegramUser

# Эти импорты работают когда backend интегрирован в основной бот
# from src.config import get_settings
# from src.database import BotUser, Loyalty, Payment, GiftCode
# from src.services.api_client import api_client, NotFoundError, ApiClientError
# from src.services.loyalty_service import get_price_with_discount, process_payment_loyalty
# from src.utils.formatters import format_bytes, format_datetime
# from src.utils.logger import logger

routes = web.RouteTableDef()


def get_user_from_request(request: web.Request) -> Optional[TelegramUser]:
    """Извлекает и валидирует пользователя из запроса."""
    init_data = request.headers.get('X-Telegram-Init-Data', '')
    bot_token = request.app.get('bot_token', '')
    return validate_init_data(init_data, bot_token)


def require_auth(handler):
    """Декоратор для проверки авторизации."""
    async def wrapper(request: web.Request) -> web.Response:
        user = get_user_from_request(request)
        if not user:
            return web.json_response(
                {'error': 'Unauthorized'},
                status=401
            )
        request['tg_user'] = user
        return await handler(request)
    return wrapper


# ==================== User API ====================

@routes.get('/api/mini-app/user/profile')
@require_auth
async def get_user_profile(request: web.Request) -> web.Response:
    """Получает профиль пользователя."""
    user: TelegramUser = request['tg_user']
    
    # TODO: Раскомментировать когда интегрировано с ботом
    # from src.config import get_settings
    # from src.database import BotUser, Loyalty, GiftCode
    # from src.services.api_client import api_client, NotFoundError
    # 
    # settings = get_settings()
    # bot_user = BotUser.get_or_create(user.id, user.username)
    # loyalty_data = Loyalty.get_user_loyalty(user.id)
    # remnawave_uuid = bot_user.get('remnawave_user_uuid')
    # 
    # subscription = None
    # if remnawave_uuid:
    #     try:
    #         user_remnawave = await api_client.get_user_by_uuid(remnawave_uuid)
    #         info = user_remnawave.get('response', user_remnawave)
    #         
    #         subscription_url = ''
    #         short_uuid = info.get('shortUuid')
    #         if short_uuid:
    #             try:
    #                 sub_info = await api_client.get_subscription_info(short_uuid)
    #                 subscription_url = sub_info.get('response', {}).get('subscriptionUrl', '')
    #             except Exception:
    #                 pass
    #         
    #         subscription = {
    #             'status': info.get('status'),
    #             'expireAt': info.get('expireAt'),
    #             'trafficUsed': info.get('userTraffic', {}).get('usedTrafficBytes', 0),
    #             'trafficLimit': info.get('trafficLimitBytes', 0),
    #             'subscriptionUrl': subscription_url,
    #             'autoRenewal': BotUser.get_auto_renewal(user.id),
    #         }
    #     except NotFoundError:
    #         BotUser.set_remnawave_uuid(user.id, None)
    # 
    # return web.json_response({
    #     'telegramId': user.id,
    #     'username': user.username,
    #     'loyalty': {
    #         'points': loyalty_data['loyalty_points'],
    #         'status': loyalty_data['loyalty_status'],
    #         'totalSpent': loyalty_data['total_spent'],
    #         'joinedAt': loyalty_data['joined_at'],
    #     },
    #     'subscription': subscription,
    #     'referralLink': f"https://t.me/{settings.bot_username}?start={user.id}",
    #     'totalGiftsPurchased': len(GiftCode.get_user_gifts(user.id)),
    #     'totalGiftsReceived': len(GiftCode.get_received_gifts(user.id)),
    # })
    
    # Mock данные для разработки
    return web.json_response({
        'telegramId': user.id,
        'username': user.username,
        'loyalty': {
            'points': 850,
            'status': 'silver',
            'totalSpent': 850,
            'joinedAt': '2025-12-01',
        },
        'subscription': {
            'status': 'active',
            'expireAt': '2026-04-15T00:00:00Z',
            'trafficUsed': 45.8 * 1024 * 1024 * 1024,
            'trafficLimit': 300 * 1024 * 1024 * 1024,
            'subscriptionUrl': 'https://example.com/sub/xxx',
            'autoRenewal': True,
        },
        'referralLink': f'https://t.me/shftsecure_bot?start={user.id}',
        'totalGiftsPurchased': 2,
        'totalGiftsReceived': 1,
    })


@routes.get('/api/mini-app/user/payments')
@require_auth
async def get_user_payments(request: web.Request) -> web.Response:
    """Получает историю платежей пользователя."""
    user: TelegramUser = request['tg_user']
    
    # TODO: Раскомментировать когда интегрировано с ботом
    # from src.database import Payment
    # from src.utils.formatters import format_datetime
    # 
    # payments = Payment.get_user_payments(user.id)
    # formatted = []
    # for p in payments:
    #     formatted.append({
    #         'id': p['id'],
    #         'date': format_datetime(p['created_at']),
    #         'amount': p['amount_rub'] if p['payment_method'] != 'stars' else p['stars'],
    #         'currency': '₽' if p['payment_method'] != 'stars' else '⭐',
    #         'type': 'gift' if p['invoice_payload'].startswith('gift:') else 'subscription',
    #         'periodDays': p['subscription_days'],
    #         'method': p['payment_method'],
    #         'status': p['status'],
    #     })
    # return web.json_response({'payments': formatted})
    
    # Mock данные
    return web.json_response({
        'payments': [
            {
                'id': 1,
                'date': '30 янв 2026',
                'amount': 284,
                'currency': '₽',
                'type': 'subscription',
                'periodDays': 90,
                'method': 'sbp',
                'status': 'completed',
            },
            {
                'id': 2,
                'date': '25 янв 2026',
                'amount': 123,
                'currency': '₽',
                'type': 'gift',
                'periodDays': 30,
                'method': 'card',
                'status': 'completed',
            },
        ]
    })


@routes.get('/api/mini-app/user/gifts')
@require_auth
async def get_user_gifts(request: web.Request) -> web.Response:
    """Получает подарки пользователя."""
    user: TelegramUser = request['tg_user']
    
    # TODO: Раскомментировать когда интегрировано с ботом
    # from src.database import GiftCode
    # from src.utils.formatters import format_datetime
    # 
    # purchased = GiftCode.get_user_gifts(user.id)
    # received = GiftCode.get_received_gifts(user.id)
    # 
    # return web.json_response({
    #     'purchasedGifts': [...],
    #     'receivedGifts': [...],
    # })
    
    # Mock данные
    return web.json_response({
        'purchasedGifts': [
            {
                'id': 1,
                'code': 'GIFT-ABC123-XYZ',
                'status': 'active',
                'periodDays': 30,
                'createdAt': '15 янв 2026',
            },
            {
                'id': 2,
                'code': 'GIFT-DEF456-QRS',
                'status': 'used',
                'periodDays': 90,
                'createdAt': '20 дек 2025',
                'activatedAt': '25 дек 2025',
            },
        ],
        'receivedGifts': [
            {
                'id': 1,
                'code': 'GIFT-GHI789-TUV',
                'periodDays': 30,
                'fromUserId': 123456789,
                'activatedAt': '10 янв 2026',
            },
        ],
    })


# ==================== Gift API ====================

@routes.post('/api/mini-app/gift/activate')
@require_auth
async def activate_gift(request: web.Request) -> web.Response:
    """Активирует подарочный код."""
    user: TelegramUser = request['tg_user']
    
    try:
        data = await request.json()
        code = data.get('code', '').strip().upper()
    except Exception:
        return web.json_response({'error': 'Invalid request'}, status=400)
    
    if not code:
        return web.json_response({'error': 'Code is required'}, status=400)
    
    # TODO: Раскомментировать когда интегрировано с ботом
    # from src.database import GiftCode, BotUser
    # from src.services.api_client import api_client
    # from src.config import get_settings
    # 
    # gift = GiftCode.get_by_code(code)
    # if not gift:
    #     return web.json_response({'error': 'Code not found'}, status=404)
    # if gift['status'] != 'active':
    #     return web.json_response({'error': 'Code already used'}, status=400)
    # if gift['buyer_id'] == user.id:
    #     return web.json_response({'error': 'Cannot activate own code'}, status=400)
    # 
    # ... логика активации ...
    # 
    # return web.json_response({
    #     'success': True,
    #     'expireDate': expire_date,
    # })
    
    # Mock ответ
    if code == 'GIFT-TEST-CODE':
        return web.json_response({
            'success': True,
            'expireDate': '2026-05-15',
        })
    else:
        return web.json_response({'error': 'Invalid code'}, status=400)


# ==================== Payment API ====================

@routes.post('/api/mini-app/payment/create')
@require_auth
async def create_payment(request: web.Request) -> web.Response:
    """Создаёт платёж."""
    user: TelegramUser = request['tg_user']
    
    try:
        data = await request.json()
        months = data.get('months')
        method = data.get('method')
        is_gift = data.get('isGift', False)
    except Exception:
        return web.json_response({'error': 'Invalid request'}, status=400)
    
    if not months or not method:
        return web.json_response({'error': 'Missing parameters'}, status=400)
    
    if months not in [1, 3, 6, 12]:
        return web.json_response({'error': 'Invalid subscription period'}, status=400)
    
    if method not in ['stars', 'sbp', 'card']:
        return web.json_response({'error': 'Invalid payment method'}, status=400)
    
    # TODO: Раскомментировать когда интегрировано с ботом
    # from src.services.payment_service import create_subscription_invoice, create_gift_invoice
    # from src.services.yookassa_service import create_yookassa_payment, create_yookassa_gift_payment
    # 
    # if is_gift:
    #     if method == 'stars':
    #         invoice_link = await create_gift_invoice(request.app['bot'], user.id, months)
    #         return web.json_response({
    #             'success': True,
    #             'paymentUrl': invoice_link,
    #             'method': 'stars',
    #         })
    #     else:
    #         payment_data = await create_yookassa_gift_payment(user.id, months, method)
    #         return web.json_response({
    #             'success': True,
    #             'paymentUrl': payment_data['payment_url'],
    #             'method': method,
    #             'paymentDbId': payment_data['payment_db_id'],
    #         })
    # else:
    #     ... аналогично для обычной подписки ...
    
    # Mock ответ
    return web.json_response({
        'success': True,
        'paymentUrl': 'https://example.com/pay/xxx',
        'method': method,
        'paymentDbId': 123 if method != 'stars' else None,
    })


@routes.get('/api/mini-app/payment/check_status/{payment_id}')
@require_auth
async def check_payment_status(request: web.Request) -> web.Response:
    """Проверяет статус платежа YooKassa."""
    user: TelegramUser = request['tg_user']
    payment_id = int(request.match_info['payment_id'])
    
    # TODO: Раскомментировать когда интегрировано с ботом
    # from src.database import Payment
    # from src.services.yookassa_service import check_yookassa_payment_status, process_yookassa_payment
    # 
    # payment = Payment.get(payment_id)
    # if not payment:
    #     return web.json_response({'error': 'Payment not found'}, status=404)
    # if payment['user_id'] != user.id:
    #     return web.json_response({'error': 'Unauthorized'}, status=403)
    # 
    # ... проверка статуса ...
    
    # Mock ответ
    return web.json_response({
        'status': 'completed',
        'message': 'Payment successful',
    })


# ==================== Setup ====================

def setup_routes(app: web.Application, bot_token: str, bot_instance=None):
    """
    Настраивает маршруты Mini App в aiohttp приложении.
    
    Args:
        app: aiohttp Application
        bot_token: Токен бота для валидации initData
        bot_instance: Экземпляр aiogram Bot (опционально, для создания платежей)
    """
    app['bot_token'] = bot_token
    if bot_instance:
        app['bot'] = bot_instance
    app.add_routes(routes)

