# 🔍 Mini App Debugging Guide

## Проверка #1: Проблема найдена и исправлена

### ❌ **Что было не так:**
В файлах `main.tsx` и `client.ts` были **неправильные импорты TypeScript деклараций**:

```typescript
import './types/telegram.d.ts';  // ❌ ОШИБКА!
```

Файлы `.d.ts` (TypeScript декларации) **нельзя импортировать** в runtime коде - они используются только на этапе компиляции!

### ✅ **Что исправлено:**
1. Удалён импорт из `mini-app/frontend/src/main.tsx`
2. Удалён импорт из `mini-app/frontend/src/api/client.ts`
3. Пересобран фронтенд без ошибок
4. Изменения закоммичены: `89970ed`

## Проверка на сервере

### 1. Обновить код на сервере:
```bash
cd /opt/shftsecurebot
git pull
```

### 2. Перезапустить Caddy:
```bash
cd /opt/shftsecurebot/caddy
docker compose restart
```

### 3. Проверить, что файлы обновились:
```bash
ls -lah /srv/mini-app/
cat /srv/mini-app/index.html
```

Должно быть в index.html:
```html
<script type="module" crossorigin src="/assets/index-C9KrP05x.js"></script>
```

### 4. Проверить логи бота:
```bash
cd /opt/shftsecurebot
docker compose logs bot --tail=50
```

Должно быть:
```
🌐 Mini App API server started on http://0.0.0.0:8080
```

### 5. Проверить, что API отвечает:
```bash
curl -v http://localhost:8080/api/profile \
  -H "X-Telegram-Init-Data: test"
```

Должно вернуть либо 401 (нормально - нужна авторизация), либо данные.

### 6. Очистить кеш Telegram:
1. **Закрыть Telegram полностью** (не просто свернуть!)
2. На Android: Settings → Data and Storage → Storage Usage → Clear Cache
3. На iOS: Settings → Data and Storage → Clear Cache
4. Открыть Telegram заново
5. Открыть Mini App

## Возможные проблемы

### Проблема: Mini App всё ещё не загружается

**Причина 1:** Старый dist не обновился на сервере
```bash
cd /opt/shftsecurebot
git status
git log --oneline -3
```

Должен быть коммит `89970ed Fix: Remove invalid .d.ts imports`

**Причина 2:** WEBAPP_ENABLED=false в .env
```bash
cd /opt/shftsecurebot
grep WEBAPP_ENABLED .env
```

Должно быть: `WEBAPP_ENABLED=true`

**Причина 3:** Caddy не проксирует запросы
```bash
cd /opt/shftsecurebot/caddy
docker compose logs --tail=20
```

Проверить, что запросы к `/api/*` проксируются на `localhost:8080`

**Причина 4:** Бот не запустил API сервер
```bash
cd /opt/shftsecurebot
docker compose logs bot | grep -i "mini app\|webapp\|8080"
```

Должно быть: `🌐 Mini App API server started on http://0.0.0.0:8080`

## Тестовый HTML для локальной проверки

Создай файл `test.html` и открой в браузере:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Mini App Test</title>
    <script>
        // Эмуляция Telegram WebApp
        window.Telegram = {
            WebApp: {
                initData: '',
                initDataUnsafe: { user: { id: 123456, first_name: 'Test' } },
                ready: () => console.log('✅ Telegram.WebApp.ready()'),
                expand: () => console.log('✅ Telegram.WebApp.expand()'),
                setHeaderColor: () => {},
                setBackgroundColor: () => {},
                HapticFeedback: {
                    impactOccurred: () => {},
                    notificationOccurred: () => {}
                }
            }
        };
    </script>
</head>
<body>
    <h1>Testing Mini App Load</h1>
    <div id="root"></div>
    <script type="module" src="http://localhost:3000/src/main.tsx"></script>
</body>
</html>
```

Запусти:
```bash
cd /path/to/mini-app/frontend
npm run dev
```

Открой `test.html` - должно загрузиться приложение без ошибок в консоли.

## Проверка в Chrome DevTools

1. Открой Mini App в Telegram Web
2. Нажми F12 → Console
3. Проверь ошибки:
   - ❌ `Cannot find module './types/telegram.d.ts'` - старая версия!
   - ✅ Нет ошибок - исправлено!

## Структура файлов (должна быть такая)

```
mini-app/frontend/
├── dist/
│   ├── assets/
│   │   ├── index-BrtEFORk.css
│   │   └── index-C9KrP05x.js
│   └── index.html
├── src/
│   ├── api/
│   │   ├── client.ts          ✅ БЕЗ импорта .d.ts
│   │   └── types.ts
│   ├── components/
│   │   ├── Dashboard.tsx
│   │   ├── Shop.tsx
│   │   └── ...
│   ├── types/
│   │   └── telegram.d.ts      ℹ️ Только для TypeScript
│   └── main.tsx               ✅ БЕЗ импорта .d.ts
└── package.json
```

## После всех проверок

Если Mini App всё ещё не работает, покажи:
1. Вывод `git log --oneline -3` на сервере
2. Вывод `docker compose logs bot --tail=50`
3. Вывод `docker compose logs -f` из папки `caddy/`
4. Скриншот ошибки из DevTools (F12 → Console)

