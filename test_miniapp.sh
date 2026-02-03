#!/bin/bash
# Полный тест Mini App

echo "=== Mini App Health Check ==="
echo ""

# 1. Активация платежа
echo "1. Активация платежа пользователя..."
docker compose exec -T bot python3 << 'EOF'
import asyncio
from datetime import datetime, timedelta
from src.database import BotUser, Payment, Loyalty
from src.services.api_client import api_client
from src.config import get_settings
from src.utils.datetime_utils import to_utc_iso

async def activate():
    user_id = 8025502815
    days = 50
    
    settings = get_settings()
    bot_user = BotUser.get_or_create(user_id, "aeshatilov")
    uuid = bot_user.get('remnawave_user_uuid')
    
    if uuid:
        print(f"User already has UUID: {uuid}")
        user_data = await api_client.get_user_by_uuid(uuid)
        info = user_data.get('response', user_data)
        print(f"Current expire: {info.get('expireAt')}")
        return True
    
    expire_date = to_utc_iso(datetime.utcnow() + timedelta(days=days))
    result = await api_client.create_user(
        username="aeshatilov",
        expire_at=expire_date,
        telegram_id=user_id,
        external_squad_uuid=settings.default_external_squad_uuid,
        active_internal_squads=settings.default_internal_squads,
    )
    
    uuid = result.get('response', {}).get('uuid')
    if uuid:
        BotUser.set_remnawave_uuid(user_id, uuid)
        Loyalty.add_points(user_id, 129)
        print(f"✅ Created: {uuid}, Expires: {expire_date}")
        return True
    return False

asyncio.run(activate())
EOF

echo ""
echo "2. Проверка API эндпоинтов..."

# Test profile
echo -n "   /api/profile: "
curl -s https://app.shftsecure.one/api/profile -o /dev/null && echo "✅" || echo "❌"

# Test webhook
echo -n "   /webhook/yookassa: "
curl -s https://app.shftsecure.one/webhook/yookassa -o /dev/null && echo "✅" || echo "❌"

echo ""
echo "3. Проверка данных пользователя..."
docker compose exec -T bot python3 << 'EOF'
from src.database import BotUser, Loyalty, Payment
import asyncio
from src.services.api_client import api_client

user = BotUser.get_or_create(8025502815, None)
uuid = user.get('remnawave_user_uuid')

print(f"   UUID: {uuid}")
print(f"   Loyalty: {user.get('loyalty_points')} points")
print(f"   Spent: {user.get('total_spent')} RUB")

if uuid:
    async def check():
        data = await api_client.get_user_by_uuid(uuid)
        info = data.get('response', data)
        print(f"   ✅ Subscription: {info.get('status')}")
        print(f"   ✅ Expires: {info.get('expireAt')}")
    asyncio.run(check())
else:
    print("   ❌ No subscription")

payments = Payment.get_user_payments(8025502815)
print(f"   Payments: {len(payments)} total")
EOF

echo ""
echo "4. Проверка портов..."
netstat -tlnp | grep 8080 > /dev/null && echo "   ✅ Port 8080 listening" || echo "   ❌ Port 8080 not listening"
netstat -tlnp | grep 443 > /dev/null && echo "   ✅ Port 443 listening" || echo "   ❌ Port 443 not listening"

echo ""
echo "=== Проверка завершена ==="
echo "Теперь откройте Mini App и проверьте:"
echo "  1. Dashboard - подписка отображается"
echo "  2. Кнопки (Конфиг, QR, Пригласить) работают"  
echo "  3. Shop - оплата открывается"
echo "  4. History - платежи видны"
echo "  5. Loyalty - баллы и скидки корректные"

