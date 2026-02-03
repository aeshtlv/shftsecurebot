#!/usr/bin/env python3
"""
Полная диагностика системы лояльности и API
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from src.database import BotUser, Loyalty
from src.config import get_settings

USER_ID = 8274493133

print("=" * 60)
print("ПОЛНАЯ ДИАГНОСТИКА СИСТЕМЫ ЛОЯЛЬНОСТИ")
print("=" * 60)

# 1. Проверяем данные в БД
print("\n1️⃣  ДАННЫЕ В БАЗЕ ДАННЫХ")
print("-" * 60)
user = BotUser.get_or_create(USER_ID, None)
print(f"telegram_id: {user.get('telegram_id')}")
print(f"username: {user.get('username')}")
print(f"loyalty_points (RAW): {user.get('loyalty_points')}")
print(f"loyalty_status (RAW): {user.get('loyalty_status')}")
print(f"total_spent (RAW): {user.get('total_spent')}")
print(f"remnawave_user_uuid: {user.get('remnawave_user_uuid')}")

# 2. Проверяем метод Loyalty.get_user_loyalty()
print("\n2️⃣  МЕТОД Loyalty.get_user_loyalty()")
print("-" * 60)
loyalty_data = Loyalty.get_user_loyalty(USER_ID)
print(f"Тип данных: {type(loyalty_data)}")
print(f"Содержимое: {loyalty_data}")
print(f"points: {loyalty_data.get('points')}")
print(f"status: {loyalty_data.get('status')}")
print(f"total_spent: {loyalty_data.get('total_spent')}")

# 3. Проверяем константы
print("\n3️⃣  КОНСТАНТЫ ЛОЯЛЬНОСТИ")
print("-" * 60)
from src.webapp.routes import LOYALTY_THRESHOLDS, LOYALTY_DISCOUNTS
print(f"LOYALTY_THRESHOLDS: {LOYALTY_THRESHOLDS}")
print(f"LOYALTY_DISCOUNTS: {LOYALTY_DISCOUNTS}")

# 4. Симулируем логику API
print("\n4️⃣  СИМУЛЯЦИЯ ЛОГИКИ API")
print("-" * 60)
points = loyalty_data.get('points', 0)
loyalty_status = loyalty_data.get('status', 'bronze')
discount = LOYALTY_DISCOUNTS.get(loyalty_status, 0)

print(f"points из loyalty_data: {points}")
print(f"status из loyalty_data: {loyalty_status}")
print(f"discount для статуса '{loyalty_status}': {discount}")

# 5. Проверяем формат ответа API
print("\n5️⃣  ФОРМАТ ОТВЕТА API")
print("-" * 60)
api_response = {
    'success': True,
    'user': {
        'telegramId': USER_ID,
        'username': user.get('username'),
        'loyalty': {
            'points': points,
            'status': loyalty_status,
            'discount': discount,
            'totalSpent': loyalty_data.get('total_spent', 0),
        },
    }
}
print(f"API Response loyalty block:")
import json
print(json.dumps(api_response['user']['loyalty'], indent=2))

# 6. Проверяем настройки
print("\n6️⃣  НАСТРОЙКИ БОТА")
print("-" * 60)
settings = get_settings()
print(f"WEBAPP_ENABLED: {settings.webapp_enabled if hasattr(settings, 'webapp_enabled') else 'N/A'}")
print(f"WEBAPP_PORT: {settings.webapp_port if hasattr(settings, 'webapp_port') else 'N/A'}")

print("\n" + "=" * 60)
print("✅ ДИАГНОСТИКА ЗАВЕРШЕНА")
print("=" * 60)

# Если points == 0, но в БД есть данные - проблема в коде
if user.get('loyalty_points', 0) > 0 and points == 0:
    print("\n🚨 ПРОБЛЕМА ОБНАРУЖЕНА!")
    print(f"В БД: {user.get('loyalty_points')} баллов")
    print(f"API отдаёт: {points} баллов")
    print("Проблема в методе Loyalty.get_user_loyalty() или в API")
elif points > 0:
    print(f"\n✅ ВСЁ РАБОТАЕТ ПРАВИЛЬНО! Баллов: {points}, Статус: {loyalty_status}")
else:
    print(f"\n⚠️  В БД тоже 0 баллов. Нужно начислить вручную.")

