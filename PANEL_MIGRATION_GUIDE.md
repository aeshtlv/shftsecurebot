# 🚚 Миграция на новую панель Remnawave

## 📋 Сценарий

Вы создаёте **новую панель Remnawave** на новом сервере с новым доменом, и нужно:
1. ✅ Перенести всех пользователей
2. ✅ Сохранить их подписки и сроки
3. ✅ Выдать новые конфиги через бота
4. ✅ Минимизировать простой для пользователей

---

## ⚠️ Важно понимать

### Что хранится в боте:
```
bot_users:
  telegram_id: 123456789
  username: "user123"
  remnawave_user_uuid: "abc-123-def-456"  ← UUID из старой панели
  loyalty_points: 500
  trial_used: true
```

### Что хранится в панели Remnawave:
```
users:
  uuid: "abc-123-def-456"  ← Этот UUID создаёт панель
  username: "user123"
  telegram_id: 123456789
  expire_at: "2026-03-01T00:00:00Z"
  subscriptionUrl: "https://panel.old-domain.com/api/sub/SHORT_UUID"
```

**Проблема:** При создании **новой панели** у пользователей будут **новые UUID**, и бот потеряет связь со старыми данными!

---

## 🎯 Стратегии миграции

### Вариант A: Автоматическая миграция (Рекомендуется)

**Плюсы:**
- ✅ Минимум ручной работы
- ✅ Пользователи получают конфиги автоматически
- ✅ Бот сам обновляет UUID

**Минусы:**
- ⚠️ Требует экспорта/импорта пользователей
- ⚠️ Нужен скрипт для обновления UUID в базе бота

---

### Вариант B: Ручная миграция (Простая)

**Плюсы:**
- ✅ Не требует скриптов
- ✅ Легко контролировать

**Минусы:**
- ❌ Пользователи должны заново "купить" подписку (можно дать бесплатно)
- ❌ Потеря истории лояльности (если не мигрировать БД)

---

## 📝 Вариант A: Автоматическая миграция

### Шаг 1: Экспорт пользователей из старой панели

**Через API старой панели:**

```bash
#!/bin/bash
# export_users.sh

OLD_PANEL="https://panel.old-domain.com"
API_TOKEN="your_old_api_token"

curl -X GET "$OLD_PANEL/api/users?start=0&size=1000" \
  -H "Authorization: Bearer $API_TOKEN" \
  -o users_export.json

echo "✅ Exported users to users_export.json"
```

**Результат:** Файл `users_export.json` со всеми пользователями.

---

### Шаг 2: Импорт пользователей в новую панель

**Создайте скрипт импорта:**

```python
#!/usr/bin/env python3
# import_users.py

import json
import httpx
from datetime import datetime

OLD_PANEL = "https://panel.old-domain.com"
NEW_PANEL = "https://panel.new-domain.com"
NEW_API_TOKEN = "your_new_api_token"

# Загружаем экспортированных пользователей
with open("users_export.json", "r") as f:
    data = json.load(f)
    users = data.get("response", {}).get("items", [])

print(f"📦 Found {len(users)} users to migrate")

# Маппинг старых UUID → новых UUID
uuid_mapping = {}

client = httpx.Client(
    base_url=NEW_PANEL,
    headers={"Authorization": f"Bearer {NEW_API_TOKEN}"},
    timeout=30.0
)

for user in users:
    old_uuid = user["uuid"]
    username = user["username"]
    telegram_id = user.get("telegramId")
    expire_at = user["expireAt"]
    traffic_limit = user.get("trafficLimitBytes")
    description = user.get("description", "")
    
    # Создаём пользователя в новой панели
    try:
        payload = {
            "username": username,
            "expireAt": expire_at,
            "trafficLimitBytes": traffic_limit,
            "description": description,
        }
        
        if telegram_id:
            payload["telegramId"] = telegram_id
        
        # Добавляем дефолтные squads (замените на свои)
        payload["externalSquadUuid"] = "your-external-squad-uuid"
        payload["activeInternalSquads"] = ["squad-1-uuid", "squad-2-uuid"]
        
        response = client.post("/api/users", json=payload)
        response.raise_for_status()
        
        new_user = response.json().get("response", response.json())
        new_uuid = new_user["uuid"]
        
        uuid_mapping[old_uuid] = new_uuid
        print(f"✅ Migrated: {username} ({old_uuid} → {new_uuid})")
        
    except Exception as e:
        print(f"❌ Failed to migrate {username}: {e}")

# Сохраняем маппинг UUID
with open("uuid_mapping.json", "w") as f:
    json.dump(uuid_mapping, f, indent=2)

print(f"\n✅ Migration complete! Migrated {len(uuid_mapping)} users")
print(f"📄 UUID mapping saved to uuid_mapping.json")
```

**Запустите:**
```bash
python3 import_users.py
```

**Результат:** Файл `uuid_mapping.json` с маппингом старых UUID на новые.

---

### Шаг 3: Обновление UUID в базе данных бота

**Создайте скрипт обновления:**

```python
#!/usr/bin/env python3
# update_bot_database.py

import json
import sqlite3

DB_PATH = "data/bot_data.db"  # Путь к базе бота

# Загружаем маппинг UUID
with open("uuid_mapping.json", "r") as f:
    uuid_mapping = json.load(f)

print(f"📦 Loaded {len(uuid_mapping)} UUID mappings")

# Подключаемся к базе данных
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

updated = 0
not_found = 0

for old_uuid, new_uuid in uuid_mapping.items():
    # Обновляем UUID в таблице bot_users
    cursor.execute(
        "UPDATE bot_users SET remnawave_user_uuid = ? WHERE remnawave_user_uuid = ?",
        (new_uuid, old_uuid)
    )
    
    if cursor.rowcount > 0:
        updated += 1
        print(f"✅ Updated: {old_uuid} → {new_uuid}")
    else:
        not_found += 1
        print(f"⚠️ Not found in bot DB: {old_uuid}")

conn.commit()
conn.close()

print(f"\n✅ Database update complete!")
print(f"   Updated: {updated}")
print(f"   Not found: {not_found}")
```

**На сервере:**
```bash
# 1. Копируем файлы на сервер
scp uuid_mapping.json update_bot_database.py root@SERVER_IP:/opt/shftsecurebot/

# 2. Подключаемся к серверу
ssh root@SERVER_IP

# 3. Переходим в директорию бота
cd /opt/shftsecurebot

# 4. Останавливаем бота (чтобы не было конфликтов с БД)
docker compose down

# 5. Делаем бэкап базы данных
cp data/bot_data.db data/bot_data.db.backup

# 6. Запускаем скрипт обновления
python3 update_bot_database.py

# 7. Обновляем .env (API_BASE_URL на новую панель)
nano .env
# Измените: API_BASE_URL=https://panel.new-domain.com

# 8. Запускаем бота
docker compose up -d --build
```

---

### Шаг 4: Массовое уведомление пользователей

**Отправьте всем уведомление о новых конфигах:**

```python
# Добавьте в src/handlers/admin.py

@router.message(Command("migrate_notify"))
async def migrate_notify(message: Message):
    """Уведомить всех пользователей о миграции на новую панель."""
    if message.from_user.id not in get_settings().admins:
        return
    
    # Получаем всех пользователей с активной подпиской
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT telegram_id, username 
        FROM bot_users 
        WHERE remnawave_user_uuid IS NOT NULL
    """)
    users = cursor.fetchall()
    conn.close()
    
    notification_text = (
        "🔔 <b>Важное обновление!</b>\n\n"
        "Мы перенесли нашу инфраструктуру на новые, более быстрые серверы!\n\n"
        "📥 <b>Получите новый конфиг:</b>\n"
        "1. Нажмите /start\n"
        "2. Выберите «🔐 Мой доступ»\n"
        "3. Нажмите «📥 Получить конфиг»\n\n"
        "⚡️ Все ваши данные, подписки и бонусы сохранены!\n\n"
        "Приятного пользования! 🚀"
    )
    
    success = 0
    failed = 0
    
    for user in users:
        user_id = user['telegram_id']
        try:
            await message.bot.send_message(user_id, notification_text, parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.05)  # Задержка 50ms между сообщениями
        except Exception as e:
            failed += 1
            logger.warning(f"Failed to notify user {user_id}: {e}")
    
    await message.reply(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"Отправлено: {success}\n"
        f"Ошибки: {failed}",
        parse_mode="HTML"
    )
```

**Использование:**
```
/migrate_notify
```

---

## 📝 Вариант B: Ручная миграция (упрощённая)

Если не хотите писать скрипты, можно сделать проще:

### Шаг 1: Создайте новую панель

1. Установите Remnawave на новом сервере
2. Настройте ноды и squads
3. Получите новый API токен

---

### Шаг 2: Обновите .env бота

```bash
# На сервере бота
cd /opt/shftsecurebot
nano .env

# Измените:
API_BASE_URL=https://panel.new-domain.com
API_TOKEN=your_new_api_token

# Сохраните и перезапустите
docker compose down
docker compose up -d --build
```

---

### Шаг 3: Сбросьте UUID у всех пользователей

**На сервере бота:**

```bash
# Останавливаем бота
docker compose down

# Делаем бэкап БД
cp data/bot_data.db data/bot_data.db.backup

# Сбрасываем UUID (пользователи заново получат доступ)
sqlite3 data/bot_data.db "UPDATE bot_users SET remnawave_user_uuid = NULL;"

# НЕ СБРАСЫВАЕМ trial_used и loyalty_points - они сохранятся!

# Запускаем бота
docker compose up -d --build
```

---

### Шаг 4: Выдайте бесплатную подписку всем

**Создайте команду для админа:**

```python
# src/handlers/admin.py

@router.message(Command("grant_migration"))
async def grant_migration(message: Message):
    """Выдать 30 дней всем пользователям после миграции."""
    if message.from_user.id not in get_settings().admins:
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id, username FROM bot_users")
    users = cursor.fetchall()
    conn.close()
    
    settings = get_settings()
    granted = 0
    failed = 0
    
    for user in users:
        user_id = user['telegram_id']
        username = user['username'] or f"user_{user_id}"
        
        try:
            # Создаём/продлеваем пользователя на 30 дней
            expire_date = (datetime.now() + timedelta(days=30)).isoformat() + "Z"
            
            user_data = await api_client.create_user(
                username=username,
                expire_at=expire_date,
                telegram_id=user_id,
                external_squad_uuid=settings.default_external_squad_uuid,
                active_internal_squads=settings.default_internal_squads,
            )
            
            user_uuid = user_data.get("response", {}).get("uuid")
            BotUser.set_remnawave_uuid(user_id, user_uuid)
            
            granted += 1
            logger.info(f"✅ Granted 30 days to {username} (ID: {user_id})")
            
        except Exception as e:
            failed += 1
            logger.error(f"❌ Failed to grant to {username}: {e}")
    
    await message.reply(
        f"✅ <b>Миграция завершена!</b>\n\n"
        f"Выдано 30 дней: {granted}\n"
        f"Ошибки: {failed}",
        parse_mode="HTML"
    )
```

**Использование:**
```
/grant_migration
```

Это создаст **новых пользователей** в новой панели и выдаст всем 30 дней бесплатно.

---

### Шаг 5: Уведомите пользователей

```python
# Используйте команду /migrate_notify из Варианта A
```

---

## 🔄 Сравнение вариантов

| Критерий | Вариант A (Автомат) | Вариант B (Ручной) |
|----------|---------------------|-------------------|
| **Сложность** | Высокая (скрипты) | Низкая |
| **Время работы** | 2-4 часа | 30 минут |
| **Сохранение данных** | Все данные (даты, UUID) | Только loyalty/trial |
| **Простой для пользователей** | Минимальный | Требует переподключения |
| **Риск ошибок** | Средний | Низкий |
| **Подходит для** | >100 пользователей | <100 пользователей |

---

## ✅ Чеклист миграции

### Подготовка
- [ ] Создана новая панель Remnawave
- [ ] Настроены ноды и squads
- [ ] Получен новый API токен
- [ ] Сделан бэкап базы данных бота
- [ ] Сделан бэкап конфигов Caddy/Docker

### Вариант A (Автоматический)
- [ ] Экспортированы пользователи из старой панели
- [ ] Импортированы пользователи в новую панель
- [ ] Создан маппинг UUID (uuid_mapping.json)
- [ ] Обновлены UUID в базе данных бота
- [ ] Обновлён .env (API_BASE_URL, API_TOKEN)
- [ ] Обновлён Caddyfile (если меняется домен)
- [ ] Перезапущен бот и Caddy
- [ ] Отправлены уведомления пользователям

### Вариант B (Ручной)
- [ ] Сброшены UUID в базе данных бота
- [ ] Обновлён .env (API_BASE_URL, API_TOKEN)
- [ ] Выданы бесплатные подписки всем (/grant_migration)
- [ ] Отправлены уведомления пользователям (/migrate_notify)
- [ ] Протестировано получение конфигов

### Проверка
- [ ] Бот запустился без ошибок
- [ ] API новой панели доступен
- [ ] Тестовый пользователь получил конфиг
- [ ] Конфиг работает (подключение VPN)
- [ ] Mini App отображает правильные данные
- [ ] Логи бота без критических ошибок

---

## ⚠️ Возможные проблемы

### 1. UUID не обновились в БД бота

**Симптом:** Пользователи видят "Подписка не найдена"

**Решение:**
```bash
# Проверьте маппинг
cat uuid_mapping.json

# Проверьте БД
sqlite3 data/bot_data.db "SELECT telegram_id, remnawave_user_uuid FROM bot_users LIMIT 10;"

# Запустите update_bot_database.py заново
```

---

### 2. Панель не создаёт пользователей

**Симптом:** Ошибка "API error 400" при создании пользователя

**Решение:**
- Проверьте, что squads существуют в новой панели
- Убедитесь, что API токен валиден
- Проверьте формат `expireAt` (должен быть ISO 8601)

---

### 3. Пользователи не получают уведомления

**Симптом:** "Failed to send notification: bot was blocked"

**Решение:**
- Это нормально — некоторые пользователи заблокировали бота
- Остальные получат уведомление при следующем входе

---

## 🚀 После миграции

### 1. Мониторинг логов

```bash
# Логи бота
docker logs shftsecurebot-bot-1 -f

# Логи Caddy
docker logs caddy -f
```

---

### 2. Проверка метрик

```bash
# Количество пользователей с UUID
sqlite3 data/bot_data.db "SELECT COUNT(*) FROM bot_users WHERE remnawave_user_uuid IS NOT NULL;"

# Количество активных подписок
curl -X GET "https://panel.new-domain.com/api/users?start=0&size=1" \
  -H "Authorization: Bearer $API_TOKEN" | jq '.response.totalCount'
```

---

### 3. Деактивация старой панели

**Только после того, как все пользователи перешли на новую!**

```bash
# На старом сервере
docker compose down

# Или настройте редирект
# В Caddyfile старой панели:
panel.old-domain.com {
    redir https://panel.new-domain.com{uri} permanent
}
```

---

## 📞 Поддержка

Если возникли проблемы:

1. **Проверьте логи:** `docker logs shftsecurebot-bot-1`
2. **Проверьте БД:** `sqlite3 data/bot_data.db "SELECT * FROM bot_users LIMIT 5;"`
3. **Откатите изменения:**
   ```bash
   docker compose down
   cp data/bot_data.db.backup data/bot_data.db
   # Верните старый .env
   docker compose up -d
   ```

---

## 🎯 Рекомендации

1. **Выберите время с минимальной нагрузкой** (ночь/раннее утро)
2. **Протестируйте на тестовом пользователе** перед массовой миграцией
3. **Сделайте бэкапы всего** (БД, .env, конфиги)
4. **Держите старую панель работающей** первые 24-48 часов
5. **Мониторьте логи и метрики** после миграции

---

**Готово!** 🎉

Теперь у вас есть полная инструкция по миграции на новую панель Remnawave.

Если нужна помощь — обращайтесь! 😊

