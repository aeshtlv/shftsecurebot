# 🔧 Mini App Not Loading - Full Diagnostic Checklist

## ✅ Шаг 1: Проверка на сервере

### 1.1 Обновить код
```bash
cd /opt/shftsecurebot
git pull
```

Должно показать:
```
c4beb1b Update Support advantages without emoji (fix loading issue)
```

### 1.2 Проверить dist файлы
```bash
cat /srv/mini-app/index.html
```

Должно быть:
```html
<script type="module" crossorigin src="/assets/index-Bs_9sKc6.js"></script>
<link rel="stylesheet" crossorigin href="/assets/index-BrtEFORk.css">
```

### 1.3 Проверить что файлы существуют
```bash
ls -lh /srv/mini-app/assets/
```

Должно быть:
- `index-Bs_9sKc6.js` (~238 KB)
- `index-BrtEFORk.css` (~21 KB)

### 1.4 Перезапустить Caddy
```bash
cd /opt/shftsecurebot/caddy
docker compose restart
docker compose logs --tail=20
```

Не должно быть ошибок.

---

## ✅ Шаг 2: Проверка бота

### 2.1 Проверить что Mini App API запущен
```bash
cd /opt/shftsecurebot
docker compose logs bot --tail=50 | grep -i "mini app\|webapp\|8080"
```

Должно быть:
```
🌐 Mini App API server started on http://0.0.0.0:8080
```

### 2.2 Проверить переменные окружения
```bash
cd /opt/shftsecurebot
grep WEBAPP .env
```

Должно быть:
```
WEBAPP_ENABLED=true
WEBAPP_PORT=8080
```

### 2.3 Проверить что API отвечает
```bash
curl -v http://localhost:8080/api/profile 2>&1 | head -20
```

Должно вернуть **401** (это нормально!) или JSON с данными.  
Если **404** - значит Caddy не проксирует запросы.

---

## ✅ Шаг 3: Проверка Caddy

### 3.1 Проверить конфигурацию
```bash
cat /opt/shftsecurebot/caddy/Caddyfile
```

Должно быть:
```
app.shftsecure.one {
    # Вебхуки (доступны публично)
    handle /webhook/* {
        reverse_proxy localhost:8080
    }
    
    # API проксируем на бота (порт 8080) - СНАЧАЛА!
    handle /api/* {
        reverse_proxy localhost:8080
    }
    
    # Frontend (статика из mini-app/frontend/dist)
    handle {
        root * /srv/mini-app
        try_files {path} /index.html
        file_server
    }
    ...
}
```

### 3.2 Проверить что Caddy видит файлы
```bash
docker compose -f /opt/shftsecurebot/caddy/docker-compose.yml exec caddy ls -lh /srv/mini-app/
```

Должно показать `index.html` и папку `assets/`.

### 3.3 Проверить логи Caddy
```bash
cd /opt/shftsecurebot/caddy
docker compose logs --tail=50 | grep -i error
```

Не должно быть ошибок 404 или 500.

---

## ✅ Шаг 4: Тест в браузере

### 4.1 Открыть Mini App через Telegram Web
1. Открыть https://web.telegram.org/
2. Найти бота @shftsecurebot
3. Нажать кнопку для открытия Mini App
4. Открыть DevTools (F12) → Console
5. Проверить ошибки

### 4.2 Частые ошибки:

**❌ "Failed to fetch" / "NetworkError"**
- Проблема с API или Caddy
- Проверить шаг 2 и 3

**❌ "Cannot find module" / "404 Not Found"**
- Файлы dist не обновились на сервере
- Проверить шаг 1.2 и 1.3

**❌ "Unexpected token '<'" / "<!DOCTYPE"**
- Caddy отдаёт index.html вместо JS файла
- Проверить Caddyfile (шаг 3.1)

**❌ Белый экран, без ошибок**
- Проблема с React или инициализацией
- Проверить console.log в DevTools

---

## ✅ Шаг 5: Очистка кеша Telegram

### На Android:
1. Telegram → Settings → Data and Storage
2. Storage Usage → Clear Cache
3. Закрыть Telegram полностью (свайп из недавних)
4. Открыть заново

### На iOS:
1. Settings → Data and Storage → Clear Cache
2. Закрыть Telegram (дважды нажать Home, свайп вверх)
3. Открыть заново

### На Desktop:
1. Settings → Advanced → Manage local storage
2. Clear All
3. Закрыть Telegram
4. Открыть заново

---

## ✅ Шаг 6: Проверка исходного кода

### 6.1 Проверить что нет неправильных импортов
```bash
cd /opt/shftsecurebot
grep -r "import.*\.d\.ts" mini-app/frontend/src/
```

Должно быть **пусто** (ничего не найдено).

### 6.2 Проверить Support.tsx
```bash
cat mini-app/frontend/src/components/Support.tsx | head -10
```

Должно быть:
```typescript
import { MessageCircle, Mail, ChevronRight, Shield, Zap } from 'lucide-react';
```

**НЕ** должно быть `Clock` в импортах!

---

## 🆘 Если ничего не помогло

### Полный перезапуск всего:

```bash
cd /opt/shftsecurebot

# 1. Остановить всё
docker compose down
cd caddy
docker compose down
cd ..

# 2. Обновить код
git pull

# 3. Проверить что файлы на месте
ls -lh /srv/mini-app/index.html
ls -lh /srv/mini-app/assets/

# 4. Запустить бота
docker compose up -d --build

# 5. Дождаться запуска (30 сек)
sleep 30
docker compose logs bot --tail=20

# 6. Запустить Caddy
cd caddy
docker compose up -d
docker compose logs --tail=20
cd ..

# 7. Проверить что всё работает
curl http://localhost:8080/api/profile -H "X-Telegram-Init-Data: test"
```

Должно вернуть либо 401, либо JSON.

---

## 📝 Отправь результаты

После проверки отправь мне:

1. Вывод `git log --oneline -3` на сервере
2. Вывод `cat /srv/mini-app/index.html | grep index-`
3. Вывод `docker compose logs bot --tail=20 | grep -i webapp`
4. Скриншот консоли браузера (F12 → Console) при открытии Mini App
5. Описание что именно ты видишь (белый экран? ошибка? ничего не происходит?)

Это поможет точно понять где проблема! 🔍

