"""
API маршруты для Mini App.
"""
from aiohttp import web
from datetime import datetime, timedelta
from typing import Optional

from .auth import validate_init_data, TelegramUser
from src.config import get_settings
from src.database import BotUser, Loyalty, Payment, GiftCode
from src.services.api_client import api_client, NotFoundError, ApiClientError
from src.services.loyalty_service import get_price_with_discount
from src.utils.logger import logger
from src.utils.datetime_utils import to_utc_iso

# Константы лояльности из класса Loyalty
LOYALTY_THRESHOLDS = Loyalty.THRESHOLDS
LOYALTY_DISCOUNTS = Loyalty.DISCOUNTS

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
            return web.json_response({'error': 'Unauthorized', 'success': False}, status=401)
        request['tg_user'] = user
        return await handler(request)
    return wrapper


# ==================== User API ====================

@routes.get('/api/profile')
@require_auth
async def get_user_profile(request: web.Request) -> web.Response:
    """Получает профиль пользователя."""
    user: TelegramUser = request['tg_user']
    settings = get_settings()
    
    try:
        bot_user = BotUser.get_or_create(user.id, user.username)
        loyalty_data = Loyalty.get_user_loyalty(user.id)
        remnawave_uuid = bot_user.get('remnawave_user_uuid')
        
        subscription = None
        if remnawave_uuid:
            try:
                user_remnawave = await api_client.get_user_by_uuid(remnawave_uuid)
                info = user_remnawave.get('response', user_remnawave)
                
                subscription_url = ''
                short_uuid = info.get('shortUuid')
                if short_uuid:
                    try:
                        sub_info = await api_client.get_subscription_info(short_uuid)
                        subscription_url = sub_info.get('response', {}).get('subscriptionUrl', '')
                    except Exception:
                        pass
                
                # Определяем статус подписки
                status = 'none'
                expire_at = info.get('expireAt')
                if expire_at:
                    try:
                        expire_dt = datetime.fromisoformat(expire_at.replace('Z', '+00:00'))
                        if expire_dt.replace(tzinfo=None) > datetime.now():
                            status = 'active'
                        else:
                            status = 'expired'
                    except Exception:
                        status = info.get('status', 'none')
                
                subscription = {
                    'status': status,
                    'expireAt': expire_at,
                    'trafficUsed': info.get('userTraffic', {}).get('usedTrafficBytes', 0),
                    'trafficLimit': info.get('trafficLimitBytes', 0),
                    'subscriptionUrl': subscription_url,
                    'autoRenewal': BotUser.get_auto_renewal(user.id),
                }
            except NotFoundError:
                logger.warning(f"Remnawave user {remnawave_uuid} not found")
                BotUser.set_remnawave_uuid(user.id, None)
            except ApiClientError as e:
                logger.error(f"Error fetching Remnawave user: {e}")
        
        purchased_gifts = GiftCode.get_user_gifts(user.id)
        received_gifts = GiftCode.get_received_gifts(user.id) if hasattr(GiftCode, 'get_received_gifts') else []
        
        # Вычисляем статус лояльности и скидку
        points = loyalty_data.get('loyalty_points', 0)
        loyalty_status = 'bronze'
        if points >= LOYALTY_THRESHOLDS['platinum']:
            loyalty_status = 'platinum'
        elif points >= LOYALTY_THRESHOLDS['gold']:
            loyalty_status = 'gold'
        elif points >= LOYALTY_THRESHOLDS['silver']:
            loyalty_status = 'silver'
        
        discount = LOYALTY_DISCOUNTS.get(loyalty_status, 0)
        
        return web.json_response({
            'success': True,
            'user': {
                'telegramId': user.id,
                'username': user.username,
                'loyalty': {
                    'points': points,
                    'status': loyalty_status,
                    'discount': discount,
                    'totalSpent': loyalty_data.get('total_spent', 0),
                },
                'subscription': subscription,
                'referralLink': f"https://t.me/{settings.bot_username}?start={user.id}",
                'totalGiftsPurchased': len(purchased_gifts),
                'totalGiftsReceived': len(received_gifts),
            }
        })
    except Exception as e:
        logger.exception("Error getting user profile")
        return web.json_response({'success': False, 'error': 'Internal error'}, status=500)


@routes.get('/api/payments')
@require_auth
async def get_user_payments(request: web.Request) -> web.Response:
    """Получает историю платежей пользователя."""
    user: TelegramUser = request['tg_user']
    
    try:
        payments = Payment.get_user_payments(user.id)
        formatted = []
        
        for p in payments:
            payment_method = p.get('payment_method', 'unknown')
            is_stars = payment_method == 'stars'
            
            # Определяем статус
            status = p.get('status', 'unknown')
            if status == 'succeeded':
                status = 'completed'
            elif status == 'pending' or status == 'waiting_for_capture':
                status = 'pending'
            elif status in ['canceled', 'failed', 'expired']:
                status = 'failed'
            
            formatted.append({
                'id': str(p.get('id')),
                'date': p.get('created_at', '')[:10] if p.get('created_at') else '',
                'amount': p.get('stars', 0) if is_stars else p.get('amount_rub', 0),
                'currency': '⭐' if is_stars else '₽',
                'type': 'gift' if str(p.get('invoice_payload', '')).startswith('gift:') else 'subscription',
                'periodDays': p.get('subscription_days', 0),
                'method': payment_method,
                'status': status,
            })
        
        return web.json_response({'success': True, 'payments': formatted})
    except Exception as e:
        logger.exception("Error getting payments")
        return web.json_response({'success': False, 'error': 'Internal error'}, status=500)


@routes.get('/api/gifts')
@require_auth
async def get_user_gifts(request: web.Request) -> web.Response:
    """Получает подарки пользователя."""
    user: TelegramUser = request['tg_user']
    
    try:
        purchased = GiftCode.get_user_gifts(user.id)
        received = GiftCode.get_received_gifts(user.id) if hasattr(GiftCode, 'get_received_gifts') else []
        
        purchased_formatted = []
        for g in purchased:
            purchased_formatted.append({
                'id': str(g.get('id')),
                'code': g.get('code', ''),
                'status': g.get('status', 'unknown'),
                'periodDays': g.get('subscription_days', 0),
                'createdAt': g.get('created_at', '')[:10] if g.get('created_at') else '',
                'activatedAt': g.get('activated_at', '')[:10] if g.get('activated_at') else None,
            })
        
        received_formatted = []
        for g in received:
            received_formatted.append({
                'id': str(g.get('id')),
                'code': g.get('code', ''),
                'periodDays': g.get('subscription_days', 0),
                'activatedAt': g.get('activated_at', '')[:10] if g.get('activated_at') else '',
            })
        
        return web.json_response({
            'success': True,
            'purchasedGifts': purchased_formatted,
            'receivedGifts': received_formatted,
        })
    except Exception as e:
        logger.exception("Error getting gifts")
        return web.json_response({'success': False, 'error': 'Internal error'}, status=500)


# ==================== Gift API ====================

@routes.post('/api/gifts/activate')
@require_auth
async def activate_gift(request: web.Request) -> web.Response:
    """Активирует подарочный код."""
    user: TelegramUser = request['tg_user']
    settings = get_settings()
    
    try:
        data = await request.json()
        code = data.get('code', '').strip().upper()
    except Exception:
        return web.json_response({'success': False, 'error': 'Invalid request'}, status=400)
    
    if not code:
        return web.json_response({'success': False, 'error': 'Введите код подарка'}, status=400)
    
    try:
        gift = GiftCode.get_by_code(code)
        if not gift:
            return web.json_response({'success': False, 'error': 'Код не найден'}, status=404)
        if gift.get('status') != 'active':
            return web.json_response({'success': False, 'error': 'Код уже использован'}, status=400)
        if gift.get('buyer_id') == user.id:
            return web.json_response({'success': False, 'error': 'Нельзя активировать свой код'}, status=400)
        
        bot_user = BotUser.get_or_create(user.id, user.username)
        existing_uuid = bot_user.get('remnawave_user_uuid')
        subscription_days = gift.get('subscription_days', 30)
        
        if existing_uuid:
            # Продлеваем существующую подписку
            user_remnawave = await api_client.get_user_by_uuid(existing_uuid)
            info = user_remnawave.get('response', user_remnawave)
            current_expire = info.get('expireAt')
            
            new_expire = datetime.utcnow() + timedelta(days=subscription_days)
            if current_expire:
                try:
                    expire_dt = datetime.fromisoformat(current_expire.replace('Z', '+00:00'))
                    if expire_dt.replace(tzinfo=None) > datetime.utcnow():
                        new_expire = expire_dt.replace(tzinfo=None) + timedelta(days=subscription_days)
                except Exception:
                    pass
            
            expire_str = to_utc_iso(new_expire)
            await api_client.update_user(existing_uuid, expireAt=expire_str)
            GiftCode.activate(code, user.id, existing_uuid)
            
            return web.json_response({
                'success': True,
                'expireDate': new_expire.strftime('%d.%m.%Y'),
            })
        else:
            # Создаём нового пользователя
            base_username = (user.username or '').lstrip('@') or f'user{user.id}'
            expire_date = to_utc_iso(datetime.utcnow() + timedelta(days=subscription_days))
            
            internal_squads = settings.default_internal_squads if settings.default_internal_squads else None
            
            result = await api_client.create_user(
                username=base_username,
                expire_at=expire_date,
                telegram_id=user.id,
                external_squad_uuid=settings.default_external_squad_uuid,
                active_internal_squads=internal_squads,
            )
            
            result_data = result.get('response', result) if result else {}
            if result_data and result_data.get('uuid'):
                new_uuid = result_data['uuid']
                BotUser.set_remnawave_uuid(user.id, new_uuid)
                GiftCode.activate(code, user.id, new_uuid)
                
                expire_formatted = (datetime.now() + timedelta(days=subscription_days)).strftime('%d.%m.%Y')
                return web.json_response({
                    'success': True,
                    'expireDate': expire_formatted,
                })
            else:
                return web.json_response({'success': False, 'error': 'Ошибка создания подписки'}, status=500)
                
    except ApiClientError as e:
        logger.error(f"API error activating gift: {e}")
        return web.json_response({'success': False, 'error': 'Ошибка API'}, status=500)
    except Exception as e:
        logger.exception("Error activating gift")
        return web.json_response({'success': False, 'error': 'Внутренняя ошибка'}, status=500)


# ==================== Payment API ====================

@routes.post('/api/payments/create')
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
        return web.json_response({'success': False, 'error': 'Invalid request'}, status=400)
    
    if not months or not method:
        return web.json_response({'success': False, 'error': 'Укажите все параметры'}, status=400)
    
    if months not in [1, 3, 6, 12]:
        return web.json_response({'success': False, 'error': 'Неверный период подписки'}, status=400)
    
    if method not in ['stars', 'sbp', 'card']:
        return web.json_response({'success': False, 'error': 'Неверный способ оплаты'}, status=400)
    
    try:
        bot = request.app.get('bot')
        
        if is_gift:
            from src.services.payment_service import create_gift_invoice
            from src.services.yookassa_service import create_yookassa_gift_payment
            
            if method == 'stars':
                if not bot:
                    return web.json_response({'success': False, 'error': 'Бот недоступен'}, status=500)
                invoice_link = await create_gift_invoice(bot, user.id, months)
                return web.json_response({
                    'success': True,
                    'paymentUrl': invoice_link,
                    'method': 'stars',
                })
            else:
                payment_data = await create_yookassa_gift_payment(user.id, months, method)
                return web.json_response({
                    'success': True,
                    'paymentId': str(payment_data.get('payment_db_id')),
                    'paymentUrl': payment_data.get('payment_url'),
                    'method': method,
                })
        else:
            from src.services.payment_service import create_subscription_invoice
            from src.services.yookassa_service import create_yookassa_payment
            
            if method == 'stars':
                if not bot:
                    return web.json_response({'success': False, 'error': 'Бот недоступен'}, status=500)
                invoice_link = await create_subscription_invoice(bot, user.id, months)
                return web.json_response({
                    'success': True,
                    'paymentUrl': invoice_link,
                    'method': 'stars',
                })
            else:
                payment_data = await create_yookassa_payment(user.id, months, method)
                return web.json_response({
                    'success': True,
                    'paymentId': str(payment_data.get('payment_db_id')),
                    'paymentUrl': payment_data.get('payment_url'),
                    'method': method,
                })
                
    except ValueError as e:
        return web.json_response({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        logger.exception("Error creating payment")
        return web.json_response({'success': False, 'error': 'Внутренняя ошибка'}, status=500)


@routes.get('/api/payments/{payment_id}/status')
@require_auth
async def check_payment_status(request: web.Request) -> web.Response:
    """Проверяет статус платежа YooKassa."""
    user: TelegramUser = request['tg_user']
    
    try:
        payment_id = int(request.match_info['payment_id'])
    except ValueError:
        return web.json_response({'success': False, 'error': 'Неверный ID платежа'}, status=400)
    
    try:
        payment = Payment.get(payment_id)
        if not payment:
            return web.json_response({'success': False, 'error': 'Платёж не найден'}, status=404)
        if payment.get('user_id') != user.id:
            return web.json_response({'success': False, 'error': 'Нет доступа'}, status=403)
        
        if payment.get('status') == 'completed':
            return web.json_response({
                'success': True,
                'status': 'completed',
            })
        
        yookassa_payment_id = payment.get('yookassa_payment_id')
        if not yookassa_payment_id:
            return web.json_response({'success': False, 'error': 'Не YooKassa платёж'}, status=400)
        
        from src.services.yookassa_service import check_yookassa_payment_status
        
        yookassa_status = await check_yookassa_payment_status(yookassa_payment_id)
        status = yookassa_status.get('status')
        
        if status == 'succeeded' and yookassa_status.get('paid'):
            # Обрабатываем успешный платёж
            invoice_payload = payment.get('invoice_payload', '')
            
            if invoice_payload.startswith('gift:'):
                from src.services.yookassa_service import process_yookassa_gift_payment
                bot = request.app.get('bot')
                result = await process_yookassa_gift_payment(yookassa_payment_id, bot)
                
                if result.get('success'):
                    return web.json_response({
                        'success': True,
                        'status': 'completed',
                    })
                else:
                    return web.json_response({
                        'success': False,
                        'status': 'failed',
                    }, status=500)
            else:
                from src.services.yookassa_service import process_yookassa_payment
                bot = request.app.get('bot')
                result = await process_yookassa_payment(yookassa_payment_id, bot)
                
                if result.get('success'):
                    return web.json_response({
                        'success': True,
                        'status': 'completed',
                    })
                else:
                    return web.json_response({
                        'success': False,
                        'status': 'failed',
                    }, status=500)
        elif status == 'canceled':
            return web.json_response({
                'success': True,
                'status': 'failed',
            })
        else:
            return web.json_response({
                'success': True,
                'status': 'pending',
            })
            
    except Exception as e:
        logger.exception("Error checking payment status")
        return web.json_response({'success': False, 'error': 'Внутренняя ошибка'}, status=500)


# ==================== Webhook API ====================

@routes.get('/webhook/yookassa')
async def yookassa_webhook_health(request: web.Request) -> web.Response:
    """Проверка доступности вебхука (для YooKassa)."""
    return web.json_response({'status': 'ok', 'service': 'shftsecure webhook'})


@routes.post('/webhook/yookassa')
async def yookassa_webhook(request: web.Request) -> web.Response:
    """Обрабатывает вебхуки от YooKassa."""
    try:
        data = await request.json()
        logger.info(f"YooKassa webhook received: {data.get('event')}")
        
        event = data.get('event')
        if event != 'payment.succeeded':
            logger.info(f"Ignoring YooKassa event: {event}")
            return web.json_response({'status': 'ok'})
        
        payment_object = data.get('object', {})
        payment_id = payment_object.get('id')
        
        if not payment_id:
            logger.error("YooKassa webhook: missing payment ID")
            return web.json_response({'error': 'Missing payment ID'}, status=400)
        
        # Получаем платёж из БД
        payment = Payment.get_by_yookassa_id(payment_id)
        if not payment:
            logger.error(f"YooKassa webhook: payment not found {payment_id}")
            return web.json_response({'error': 'Payment not found'}, status=404)
        
        # Проверяем статус
        if payment.get('status') == 'completed':
            logger.info(f"YooKassa webhook: payment {payment_id} already completed")
            return web.json_response({'status': 'ok'})
        
        # Обрабатываем платёж
        bot = request.app.get('bot')
        invoice_payload = payment.get('invoice_payload', '')
        
        if invoice_payload.startswith('yookassa_gift:'):
            # Подарочный платёж
            from src.services.yookassa_service import process_yookassa_gift_payment
            result = await process_yookassa_gift_payment(payment_id, bot)
        else:
            # Обычный платёж за подписку
            from src.services.yookassa_service import process_yookassa_payment
            result = await process_yookassa_payment(payment_id, bot)
        
        if result.get('success'):
            logger.info(f"YooKassa webhook: payment {payment_id} processed successfully")
            return web.json_response({'status': 'ok'})
        else:
            logger.error(f"YooKassa webhook: failed to process payment {payment_id}")
            return web.json_response({'error': result.get('error', 'Processing failed')}, status=500)
        
    except Exception as e:
        logger.exception("Error processing YooKassa webhook")
        return web.json_response({'error': 'Internal error'}, status=500)


# ==================== Setup ====================

def setup_routes(app: web.Application, bot_token: str, bot_instance=None):
    """
    Настраивает маршруты Mini App.
    
    Args:
        app: aiohttp Application
        bot_token: Токен бота для валидации initData
        bot_instance: Экземпляр aiogram Bot
    """
    app['bot_token'] = bot_token
    if bot_instance:
        app['bot'] = bot_instance
    app.add_routes(routes)
