#!/bin/bash
# Скрипт деплоя Mini App на сервер
# Использование: ./deploy.sh

set -e

echo "🚀 Деплой SHFT Secure Mini App"
echo "================================"

# 1. Сборка фронтенда
echo "📦 Сборка фронтенда..."
cd frontend
npm ci --silent
npm run build
cd ..

# 2. Проверка Caddyfile
echo "✅ Проверка конфигурации Caddy..."
docker run --rm -v "$(pwd)/Caddyfile:/etc/caddy/Caddyfile:ro" caddy:2-alpine caddy validate --config /etc/caddy/Caddyfile

# 3. Запуск/перезапуск Caddy
echo "🔄 Запуск Caddy..."
docker compose up -d caddy

# 4. Проверка статуса
echo ""
echo "✅ Деплой завершён!"
echo ""
echo "📱 Mini App доступен по адресу:"
echo "   https://app.shftsecure.one"
echo ""
echo "📊 Логи Caddy:"
echo "   docker compose logs -f caddy"

