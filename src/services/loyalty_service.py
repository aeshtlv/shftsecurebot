"""
Сервис системы лояльности.
Управляет статусами, баллами и скидками пользователей.
"""

from src.database import Loyalty, BotUser
from src.utils.i18n import get_i18n


# Базовые цены в рублях
BASE_PRICES = {
    30: 129,    # 1 месяц
    90: 299,    # 3 месяца
    180: 549,   # 6 месяцев
    360: 999,   # 12 месяцев (12 * 30 = 360)
    365: 999    # 12 месяцев (365 дней - для совместимости)
}

# Количество Stars для каждого периода (1 Star ≈ 1.85₽)
STARS_PRICES = {
    30: 70,     # 129₽ / 1.85 ≈ 70 Stars
    90: 162,    # 299₽ / 1.85 ≈ 162 Stars
    180: 297,   # 549₽ / 1.85 ≈ 297 Stars
    360: 540,   # 999₽ / 1.85 ≈ 540 Stars (12 * 30 = 360)
    365: 540    # 999₽ / 1.85 ≈ 540 Stars (365 дней - для совместимости)
}


def get_price_with_discount(telegram_id: int, days: int) -> dict:
    """
    Получает цену с учётом скидки лояльности.
    
    Returns:
        dict с ключами:
        - base_price: базовая цена в рублях
        - discounted_price: цена со скидкой в рублях
        - discount: размер скидки в рублях
        - stars_base: базовая цена в Stars
        - stars_discounted: цена со скидкой в Stars
    """
    base_price = BASE_PRICES.get(days, 129)
    stars_base = STARS_PRICES.get(days, 70)
    
    discounted_price, discount = Loyalty.get_discounted_price(base_price, telegram_id, days)
    
    # Пересчитываем Stars с учётом скидки
    if discount > 0:
        discount_ratio = discounted_price / base_price
        stars_discounted = int(stars_base * discount_ratio)
    else:
        stars_discounted = stars_base
    
    return {
        'base_price': base_price,
        'discounted_price': discounted_price,
        'discount': discount,
        'stars_base': stars_base,
        'stars_discounted': stars_discounted
    }


def process_payment_loyalty(telegram_id: int, amount_rub: int) -> dict | None:
    """
    Обрабатывает платёж для системы лояльности.
    Начисляет баллы и проверяет повышение статуса.
    
    Returns:
        dict с информацией об изменении статуса или None
    """
    result = Loyalty.add_points(telegram_id, amount_rub)
    
    # Проверяем, был ли повышен статус
    if result['status'] != result['previous_status']:
        return {
            'status_upgraded': True,
            'old_status': result['previous_status'],
            'new_status': result['status'],
            'new_status_name': Loyalty.get_status_name(result['status']),
            'points': result['points']
        }
    
    return None


def get_loyalty_profile(telegram_id: int) -> dict:
    """
    Получает полный профиль лояльности пользователя.
    """
    loyalty = Loyalty.get_user_loyalty(telegram_id)
    next_info = Loyalty.get_next_status_info(telegram_id)
    
    # Получаем примеры скидок для текущего статуса
    status = loyalty['status']
    discounts_examples = []
    for days, base_price in sorted(BASE_PRICES.items()):
        discount = Loyalty.DISCOUNTS[status].get(days, 0)
        if discount > 0:
            discounts_examples.append({
                'days': days,
                'base_price': base_price,
                'discount': discount,
                'final_price': base_price - discount
            })
    
    return {
        'status': status,
        'status_name': Loyalty.get_status_name(status),
        'points': loyalty['points'],
        'total_spent': loyalty['total_spent'],
        'next_status_info': next_info,
        'current_discounts': discounts_examples
    }


def format_loyalty_profile_message(telegram_id: int, lang: str = 'ru') -> str:
    """
    Форматирует сообщение с профилем лояльности.
    """
    i18n = get_i18n()
    profile = get_loyalty_profile(telegram_id)
    
    # Формируем текст о текущих скидках
    discounts_text = ""
    if profile['current_discounts']:
        discounts_text = "\n"
        for d in profile['current_discounts']:
            period_name = i18n.t(f'period_{d["days"]}d', locale=lang)
            discounts_text += f"   • {period_name}: <s>{d['base_price']}₽</s> → <b>{d['final_price']}₽</b> (-{d['discount']}₽)\n"
    
    # Формируем текст о следующем статусе
    next_status_text = ""
    if profile['next_status_info']:
        next_status_text = i18n.t(
            'loyalty_next_status',
            locale=lang,
            next_status=profile['next_status_info']['next_status_name'],
            points_needed=profile['next_status_info']['points_needed']
        )
    else:
        next_status_text = i18n.t('loyalty_max_status', locale=lang)
    
    # Собираем полное сообщение
    message = i18n.t(
        'loyalty_profile',
        locale=lang,
        status_name=profile['status_name'],
        points=profile['points'],
        total_spent=profile['total_spent'],
        discounts=discounts_text,
        next_status=next_status_text
    )
    
    return message


def get_price_display(telegram_id: int, days: int, lang: str = 'ru') -> str:
    """
    Возвращает отформатированную строку с ценой (со скидкой, если есть).
    """
    price_info = get_price_with_discount(telegram_id, days)
    
    if price_info['discount'] > 0:
        # Есть скидка - показываем зачёркнутую цену и новую
        return f"<s>{price_info['base_price']}₽</s> {price_info['discounted_price']}₽"
    else:
        return f"{price_info['base_price']}₽"


def get_stars_display(telegram_id: int, days: int, lang: str = 'ru') -> str:
    """
    Возвращает отформатированную строку с ценой в Stars (со скидкой, если есть).
    """
    price_info = get_price_with_discount(telegram_id, days)
    
    if price_info['discount'] > 0:
        return f"<s>{price_info['stars_base']}⭐</s> {price_info['stars_discounted']}⭐"
    else:
        return f"{price_info['stars_base']}⭐"

