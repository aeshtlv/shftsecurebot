# shftsecurebot — Telegram‑бот для shftsecure (покупка подписок + админ‑панель)

shftsecurebot превращает Remnawave‑панель в **user‑facing витрину** для **shftsecure**: пользователь покупает подписку → получает конфиг‑ссылку, а администратор управляет инфраструктурой Remnawave в привычном интерфейсе бота.

## Возможности

- **Пользователям**:
  - **Покупка подписок** через Telegram Stars (1 / 3 / 6 / 12 месяцев)
  - **Выбор способа оплаты** (Telegram Stars, СБП, Банковская карта)
  - **Пробная подписка** (кнопка "Активировать")
  - **Промокоды** (скидка/бонусные дни)
  - **Реферальная программа**
  - **Моя подписка**: статус, срок, трафик, ссылка на конфиг
  - **RU/EN интерфейс**
- **Админам**:
  - Управление пользователями/нодами/хостами
  - Ресурсы (шаблоны/сниппеты/токены)
  - Биллинг/статистика

## Быстрый старт (Docker)

### Требования

- Docker + Docker Compose
- Telegram Bot Token от [@BotFather](https://t.me/BotFather)
- Доступ к Remnawave API (`API_BASE_URL`, `API_TOKEN`)

### Установка

```bash
git clone https://github.com/aeshtlv/shftsecurebot.git
cd shftsecurebot
cp env.sample .env
nano .env
docker network create remnawave-network || true
docker compose up -d --build
docker compose logs -f bot
```

> `docker-compose.yml` автоматически читает `.env` через `env_file`, ничего дополнительно пробрасывать не нужно.

## Конфигурация (.env)

Все переменные перечислены в `env.sample`.

Ключевые:

- **`BOT_TOKEN`**: токен бота
- **`API_BASE_URL`**: базовый URL панели (например `https://panel.example.com`)
- **`API_TOKEN`**: токен доступа
- **`ADMINS`**: Telegram ID админов через запятую
- **`SUBSCRIPTION_STARS_*`**: цены (Stars)
- **`DEFAULT_INTERNAL_SQUADS` / `DEFAULT_EXTERNAL_SQUAD_UUID`**: squads для новых пользователей (важно для корректного конфига)

`DEFAULT_INTERNAL_SQUADS` поддерживает форматы:
- `uuid1,uuid2`
- `["uuid1","uuid2"]`

## Разработка

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или: .venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp env.sample .env
python -m src.main
```

## Структура проекта

```
shftsecurebot/
├── src/                    # Исходный код бота
│   ├── handlers/          # Обработчики команд и callback'ов
│   ├── keyboards/         # Клавиатуры для интерфейса
│   ├── services/          # Сервисы (API, платежи, уведомления)
│   └── utils/             # Утилиты (логирование, локализация)
├── locales/               # Файлы локализации (ru/en)
├── docker-compose.yml     # Docker Compose конфигурация
├── Dockerfile            # Docker образ
├── requirements.txt      # Python зависимости
└── env.sample           # Пример файла конфигурации
```

## Troubleshooting

- **Не меняются цены/сквады**: убедись, что правишь именно `.env` рядом с `docker-compose.yml`, затем `docker compose up -d --build`.
- **Временные ошибки Telegram (Bad Gateway/Connection reset)**: это сетевое; при частых проблемах нужен прокси на сервере.
- **Бот не подключается к API**: проверь, что `API_BASE_URL` и `API_TOKEN` корректны, и оба контейнера в одной Docker сети.

## Поддержка

Issues: https://github.com/aeshtlv/shftsecurebot/issues

## Лицензия

MIT — см. `LICENSE`.
