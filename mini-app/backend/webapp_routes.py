"""
API endpoints for Telegram Mini App.
This module provides REST API for the Mini App frontend.
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import parse_qsl

from aiohttp import web

logger = logging.getLogger(__name__)


def verify_telegram_webapp_data(init_data: str, bot_token: str) -> Optional[dict]:
    """
    Verify Telegram WebApp initData signature.
    
    Args:
        init_data: The initData string from Telegram WebApp
        bot_token: Your bot token
        
    Returns:
        Parsed user data if valid, None otherwise
    """
    try:
        # Parse the init data
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        
        # Extract and remove the hash
        received_hash = parsed.pop('hash', '')
        if not received_hash:
            return None
        
        # Create data check string
        data_check_arr = sorted(parsed.items())
        data_check_string = '\n'.join(f'{k}={v}' for k, v in data_check_arr)
        
        # Calculate secret key
        secret_key = hmac.new(
            key=b'WebAppData',
            msg=bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Verify hash
        if not hmac.compare_digest(calculated_hash, received_hash):
            logger.warning("Invalid WebApp hash")
            return None
        
        # Parse user data
        user_data = json.loads(parsed.get('user', '{}'))
        return user_data
        
    except Exception as e:
        logger.error(f"Error verifying WebApp data: {e}")
        return None


def create_webapp_routes(bot_token: str, api_client, database):
    """
    Create aiohttp routes for Mini App API.
    
    Args:
        bot_token: Telegram bot token for verification
        api_client: Remnawave API client instance
        database: Database instance
        
    Returns:
        aiohttp RouteTableDef
    """
    routes = web.RouteTableDef()
    
    async def get_user_from_request(request: web.Request) -> Optional[dict]:
        """Extract and verify user from request headers."""
        init_data = request.headers.get('X-Telegram-Init-Data', '')
        if not init_data:
            return None
        return verify_telegram_webapp_data(init_data, bot_token)
    
    @routes.get('/api/webapp/dashboard')
    async def get_dashboard(request: web.Request):
        """Get dashboard data for the user."""
        user = await get_user_from_request(request)
        if not user:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        telegram_id = user.get('id')
        if not telegram_id:
            return web.json_response({'error': 'Invalid user data'}, status=400)
        
        try:
            # Get user from database
            from src.database import BotUser, Loyalty
            
            db_user = BotUser.get_by_telegram_id(telegram_id)
            if not db_user:
                return web.json_response({'error': 'User not found'}, status=404)
            
            # Get loyalty data
            loyalty_data = Loyalty.get_user_loyalty(telegram_id)
            
            # Get subscription from Remnawave
            subscription = None
            if db_user.get('remnawave_uuid'):
                try:
                    user_info = await api_client.get_user_by_uuid(db_user['remnawave_uuid'])
                    info = user_info.get('response', user_info)
                    
                    user_traffic = info.get('userTraffic', {})
                    traffic_used = user_traffic.get('usedTrafficBytes', 0) if user_traffic else 0
                    traffic_limit = info.get('trafficLimitBytes', 0)
                    
                    subscription = {
                        'status': info.get('status', 'unknown').lower(),
                        'plan': 'Premium',
                        'endDate': info.get('expireAt'),
                        'trafficUsed': traffic_used / (1024 ** 3),  # Convert to GB
                        'trafficTotal': traffic_limit / (1024 ** 3) if traffic_limit else 0,
                        'subscriptionUrl': info.get('subscriptionUrl'),
                        'shortUuid': info.get('shortUuid'),
                    }
                except Exception as e:
                    logger.error(f"Error fetching Remnawave data: {e}")
            
            # Get referral data
            from src.database import Referral
            referral_count = len(Referral.get_referrals(telegram_id))
            
            response_data = {
                'user': {
                    'telegramId': telegram_id,
                    'username': user.get('username'),
                    'firstName': user.get('first_name', ''),
                    'lastName': user.get('last_name'),
                },
                'subscription': subscription,
                'loyalty': {
                    'level': loyalty_data.get('loyalty_status', 'bronze'),
                    'points': loyalty_data.get('loyalty_points', 0),
                    'totalSpent': loyalty_data.get('total_spent', 0),
                    'discount': _get_discount(loyalty_data.get('loyalty_status', 'bronze')),
                },
                'referral': {
                    'count': referral_count,
                    'earned': referral_count * 50,  # 50 points per referral
                    'referralLink': f"https://t.me/shftsecure_bot?start=ref{telegram_id}",
                },
            }
            
            return web.json_response(response_data)
            
        except Exception as e:
            logger.error(f"Error in get_dashboard: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    @routes.get('/api/webapp/loyalty')
    async def get_loyalty(request: web.Request):
        """Get loyalty profile data."""
        user = await get_user_from_request(request)
        if not user:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        telegram_id = user.get('id')
        
        try:
            from src.database import Loyalty
            
            loyalty_data = Loyalty.get_user_loyalty(telegram_id)
            current_status = loyalty_data.get('loyalty_status', 'bronze')
            current_points = loyalty_data.get('loyalty_points', 0)
            
            next_status_info = Loyalty.get_next_status_info(current_status)
            
            return web.json_response({
                'level': current_status,
                'points': current_points,
                'totalSpent': loyalty_data.get('total_spent', 0),
                'discount': _get_discount(current_status),
                'nextLevel': {
                    'name': next_status_info.get('next_status'),
                    'pointsRequired': next_status_info.get('points_to_next', 0) + current_points,
                    'pointsToGo': next_status_info.get('points_to_next', 0),
                    'progress': next_status_info.get('progress_percent', 100),
                } if next_status_info.get('next_status') else None,
            })
            
        except Exception as e:
            logger.error(f"Error in get_loyalty: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    @routes.get('/api/webapp/plans')
    async def get_plans(request: web.Request):
        """Get available subscription plans."""
        user = await get_user_from_request(request)
        if not user:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        telegram_id = user.get('id')
        
        try:
            from src.database import Loyalty
            from src.services.loyalty_service import DISCOUNTED_PRICES, BASE_PRICES
            
            loyalty_data = Loyalty.get_user_loyalty(telegram_id)
            current_status = loyalty_data.get('loyalty_status', 'bronze')
            prices = DISCOUNTED_PRICES.get(current_status, BASE_PRICES)
            
            plans = [
                {
                    'id': '1m',
                    'period': '1 месяц',
                    'months': 1,
                    'basePrice': 129,
                    'discountedPrice': prices.get(1, 129),
                    'traffic': '100 ГБ',
                    'trafficGb': 100,
                },
                {
                    'id': '3m',
                    'period': '3 месяца',
                    'months': 3,
                    'basePrice': 299,
                    'discountedPrice': prices.get(3, 299),
                    'traffic': '300 ГБ',
                    'trafficGb': 300,
                    'badge': 'Популярный',
                },
                {
                    'id': '6m',
                    'period': '6 месяцев',
                    'months': 6,
                    'basePrice': 549,
                    'discountedPrice': prices.get(6, 549),
                    'traffic': '600 ГБ',
                    'trafficGb': 600,
                },
                {
                    'id': '12m',
                    'period': '12 месяцев',
                    'months': 12,
                    'basePrice': 999,
                    'discountedPrice': prices.get(12, 999),
                    'traffic': '1200 ГБ',
                    'trafficGb': 1200,
                    'badge': 'Выгодный',
                },
            ]
            
            return web.json_response(plans)
            
        except Exception as e:
            logger.error(f"Error in get_plans: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    @routes.get('/api/webapp/gifts')
    async def get_gifts(request: web.Request):
        """Get user's gift codes."""
        user = await get_user_from_request(request)
        if not user:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        telegram_id = user.get('id')
        
        try:
            from src.database import GiftCode
            
            # Get purchased gifts
            purchased = GiftCode.get_user_gifts(telegram_id)
            purchased_list = [
                {
                    'id': str(g['id']),
                    'code': g['code'],
                    'status': g['status'],
                    'period': _days_to_period(g['subscription_days']),
                    'months': g['subscription_days'] // 30,
                    'createdAt': g['created_at'],
                    'activatedAt': g.get('activated_at'),
                }
                for g in purchased
            ]
            
            # Get received gifts (where user is recipient)
            # This would need a separate query
            received_list = []
            
            return web.json_response({
                'purchased': purchased_list,
                'received': received_list,
            })
            
        except Exception as e:
            logger.error(f"Error in get_gifts: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    @routes.post('/api/webapp/gifts/activate')
    async def activate_gift(request: web.Request):
        """Activate a gift code."""
        user = await get_user_from_request(request)
        if not user:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        telegram_id = user.get('id')
        
        try:
            data = await request.json()
            code = data.get('code', '').strip().upper()
            
            if not code:
                return web.json_response({'error': 'Code is required'}, status=400)
            
            from src.database import GiftCode
            
            # Try to activate
            gift = GiftCode.get_by_code(code)
            if not gift:
                return web.json_response({'error': 'Invalid code'}, status=404)
            
            if gift['status'] != 'active':
                return web.json_response({'error': 'Code already used or expired'}, status=400)
            
            # Activate the gift
            success = GiftCode.activate(code, telegram_id)
            if not success:
                return web.json_response({'error': 'Failed to activate'}, status=500)
            
            return web.json_response({'success': True})
            
        except Exception as e:
            logger.error(f"Error in activate_gift: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    @routes.get('/api/webapp/payments')
    async def get_payments(request: web.Request):
        """Get user's payment history."""
        user = await get_user_from_request(request)
        if not user:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        telegram_id = user.get('id')
        
        try:
            from src.database import Payment
            
            payments = Payment.get_user_payments(telegram_id)
            
            transactions = [
                {
                    'id': str(p['id']),
                    'date': p['created_at'],
                    'amount': p.get('amount_rub', 0) or p.get('stars', 0),
                    'currency': '₽' if p.get('amount_rub') else '⭐',
                    'type': 'gift' if 'gift' in p.get('payment_type', '').lower() else 'subscription',
                    'period': _days_to_period(p.get('subscription_days', 30)),
                    'method': _payment_method(p.get('payment_method', '')),
                    'status': 'completed' if p.get('status') == 'completed' else 'pending',
                }
                for p in payments
            ]
            
            return web.json_response(transactions)
            
        except Exception as e:
            logger.error(f"Error in get_payments: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    @routes.get('/api/webapp/subscription/config')
    async def get_subscription_config(request: web.Request):
        """Get subscription config URL."""
        user = await get_user_from_request(request)
        if not user:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        telegram_id = user.get('id')
        
        try:
            from src.database import BotUser
            
            db_user = BotUser.get_by_telegram_id(telegram_id)
            if not db_user or not db_user.get('remnawave_uuid'):
                return web.json_response({'error': 'No subscription'}, status=404)
            
            user_info = await api_client.get_user_by_uuid(db_user['remnawave_uuid'])
            info = user_info.get('response', user_info)
            
            subscription_url = info.get('subscriptionUrl', '')
            
            return web.json_response({'config': subscription_url})
            
        except Exception as e:
            logger.error(f"Error in get_subscription_config: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    return routes


# Helper functions
def _get_discount(status: str) -> int:
    """Get discount percentage for loyalty status."""
    discounts = {
        'bronze': 0,
        'silver': 5,
        'gold': 10,
        'platinum': 15,
    }
    return discounts.get(status.lower(), 0)


def _days_to_period(days: int) -> str:
    """Convert days to human-readable period."""
    if days <= 30:
        return '1 месяц'
    elif days <= 90:
        return '3 месяца'
    elif days <= 180:
        return '6 месяцев'
    else:
        return '12 месяцев'


def _payment_method(method: str) -> str:
    """Normalize payment method."""
    method_lower = method.lower()
    if 'star' in method_lower:
        return 'stars'
    elif 'sbp' in method_lower:
        return 'sbp'
    else:
        return 'card'

