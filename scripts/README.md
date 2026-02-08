# 🛠️ Migration Scripts

Набор скриптов для миграции на новую панель Remnawave.

---

## 📋 Скрипты

### 1. `export_users.sh` — Экспорт пользователей

Экспортирует всех пользователей из старой панели в JSON файл.

**Использование:**

```bash
export OLD_API_TOKEN="your_old_api_token"
export OLD_PANEL_URL="https://panel.old-domain.com"
./export_users.sh
```

**Результат:** `users_export.json`

---

### 2. `import_users.py` — Импорт пользователей

Импортирует пользователей в новую панель и создаёт маппинг UUID.

**Требования:**
```bash
pip install httpx
```

**Использование:**

```bash
export NEW_PANEL_URL="https://panel.new-domain.com"
export NEW_API_TOKEN="your_new_api_token"
export EXTERNAL_SQUAD_UUID="your-squad-uuid"
export INTERNAL_SQUAD_UUIDS="uuid1,uuid2"

python3 import_users.py users_export.json
```

**Результат:** `uuid_mapping.json`

---

### 3. `update_bot_database.py` — Обновление БД бота

Обновляет UUID в базе данных бота на основе маппинга.

**Использование:**

```bash
# На сервере бота
python3 update_bot_database.py uuid_mapping.json data/bot_data.db
```

**Результат:** Обновлённая БД + бэкап

---

## 🚀 Быстрый старт (полная миграция)

### Шаг 1: Экспорт (на локальной машине)

```bash
cd scripts

export OLD_API_TOKEN="your_old_token"
export OLD_PANEL_URL="https://panel.old-domain.com"

chmod +x export_users.sh
./export_users.sh
```

---

### Шаг 2: Импорт (на локальной машине)

```bash
# Установите зависимости
pip install httpx

# Настройте переменные
export NEW_PANEL_URL="https://panel.new-domain.com"
export NEW_API_TOKEN="your_new_token"
export EXTERNAL_SQUAD_UUID="your-squad-uuid"
export INTERNAL_SQUAD_UUIDS="uuid1,uuid2"  # Опционально

# Запустите импорт
python3 import_users.py users_export.json
```

**Результат:** 
- Пользователи созданы в новой панели
- Файл `uuid_mapping.json` с маппингом старых UUID → новых UUID

---

### Шаг 3: Обновление БД (на сервере бота)

```bash
# Копируем маппинг на сервер
scp uuid_mapping.json root@SERVER_IP:/opt/shftsecurebot/scripts/

# Подключаемся к серверу
ssh root@SERVER_IP

# Переходим в директорию бота
cd /opt/shftsecurebot

# Останавливаем бота
docker compose down

# Запускаем обновление БД
python3 scripts/update_bot_database.py scripts/uuid_mapping.json data/bot_data.db
```

---

### Шаг 4: Обновление конфигурации (на сервере бота)

```bash
# Редактируем .env
nano .env

# Изменяем:
# API_BASE_URL=https://panel.new-domain.com
# API_TOKEN=your_new_api_token

# Сохраняем (Ctrl+O, Enter, Ctrl+X)

# Перезапускаем бота
docker compose up -d --build
```

---

### Шаг 5: Проверка (на сервере бота)

```bash
# Смотрим логи
docker logs shftsecurebot-bot-1 --tail 50

# Проверяем, что бот запустился без ошибок
# Должно быть: "Bot started successfully"
```

---

### Шаг 6: Уведомление пользователей

В Telegram боте (от имени админа):

```
/migrate_notify
```

Это отправит всем пользователям уведомление о необходимости получить новый конфиг.

---

## 🔍 Проверка результатов

### Проверить количество пользователей в новой панели:

```bash
curl -X GET "https://panel.new-domain.com/api/users?start=0&size=1" \
  -H "Authorization: Bearer $NEW_API_TOKEN" | jq '.response.totalCount'
```

### Проверить UUID в БД бота:

```bash
sqlite3 data/bot_data.db "SELECT COUNT(*) FROM bot_users WHERE remnawave_user_uuid IS NOT NULL;"
```

### Проверить маппинг:

```bash
cat uuid_mapping.json | jq 'length'
```

---

## ⚠️ Устранение проблем

### Проблема: "Module not found: httpx"

**Решение:**
```bash
pip install httpx
```

---

### Проблема: "API error 400" при импорте

**Причины:**
- Неверный формат даты `expireAt`
- Несуществующий squad UUID
- Пользователь уже существует

**Решение:**
- Проверьте, что squads существуют в новой панели
- Проверьте формат даты в `users_export.json`

---

### Проблема: "Database is locked"

**Причина:** Бот запущен и использует БД

**Решение:**
```bash
docker compose down
python3 update_bot_database.py ...
docker compose up -d
```

---

### Проблема: Пользователи не видят подписку

**Причина:** UUID в БД не обновились

**Решение:**
```bash
# Проверьте логи
docker logs shftsecurebot-bot-1 --tail 100

# Проверьте UUID в БД
sqlite3 data/bot_data.db \
  "SELECT telegram_id, username, remnawave_user_uuid FROM bot_users LIMIT 5;"

# Запустите update_bot_database.py заново
```

---

## 📊 Статистика миграции

После миграции можно получить статистику:

```bash
# Пользователи в БД бота
sqlite3 data/bot_data.db "SELECT 
    COUNT(*) as total,
    COUNT(remnawave_user_uuid) as with_uuid,
    COUNT(*) - COUNT(remnawave_user_uuid) as without_uuid
FROM bot_users;"

# Пользователи в новой панели
curl -X GET "https://panel.new-domain.com/api/users?start=0&size=1" \
  -H "Authorization: Bearer $NEW_API_TOKEN" \
  | jq '.response.totalCount'
```

---

## 🎯 Best Practices

1. **Делайте бэкапы** перед каждым шагом
2. **Тестируйте на 1-2 пользователях** перед полной миграцией
3. **Сохраняйте старую панель работающей** первые 24-48 часов
4. **Мониторьте логи** после миграции
5. **Держите маппинг UUID** на случай отката

---

## 📞 Поддержка

Если что-то пошло не так:

1. Проверьте логи: `docker logs shftsecurebot-bot-1`
2. Проверьте БД: `sqlite3 data/bot_data.db "SELECT * FROM bot_users LIMIT 5;"`
3. Восстановите бэкап: `cp data/bot_data.db.backup data/bot_data.db`
4. См. полную инструкцию: `PANEL_MIGRATION_GUIDE.md`

---

**Удачной миграции!** 🚀

