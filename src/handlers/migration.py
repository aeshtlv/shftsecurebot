"""Команды для миграции на новую панель."""
import asyncio
from datetime import datetime, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _

from src.config import get_settings
from src.database import BotUser, get_db_connection
from src.handlers.common import _not_admin, _send_clean_message
from src.services.api_client import api_client
from src.utils.logger import logger

router = Router(name="migration")


@router.message(Command("migrate_notify"))
async def cmd_migrate_notify(message: Message) -> None:
    """
    Отправить массовое уведомление пользователям о миграции на новую панель.
    
    Usage: /migrate_notify
    """
    if await _not_admin(message):
        return
    
    # Получаем всех пользователей с UUID
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT telegram_id, username 
        FROM bot_users 
        WHERE remnawave_user_uuid IS NOT NULL
    """)
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        await _send_clean_message(message, "❌ Нет пользователей с активной подпиской")
        return
    
    # Подтверждение
    confirm_text = (
        f"⚠️ <b>Массовая рассылка</b>\n\n"
        f"Будет отправлено уведомлений: <b>{len(users)}</b>\n\n"
        f"Отправить? (yes/no)"
    )
    
    await _send_clean_message(message, confirm_text, parse_mode="HTML")
    
    # TODO: Добавить FSM для подтверждения
    # Пока требует ввода команды /migrate_notify_confirm
    

@router.message(Command("migrate_notify_confirm"))
async def cmd_migrate_notify_confirm(message: Message) -> None:
    """
    Подтверждение отправки массового уведомления.
    
    Usage: /migrate_notify_confirm
    """
    if await _not_admin(message):
        return
    
    # Получаем всех пользователей с UUID
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
    
    status_msg = await _send_clean_message(
        message, 
        f"📤 Начинаю рассылку для {len(users)} пользователей...",
        parse_mode="HTML"
    )
    
    success = 0
    failed = 0
    
    for i, user in enumerate(users, 1):
        user_id = user['telegram_id']
        username = user['username'] or f"user_{user_id}"
        
        try:
            await message.bot.send_message(user_id, notification_text, parse_mode="HTML")
            success += 1
            logger.info(f"✅ Sent migration notification to {username} ({user_id})")
            
            # Обновляем статус каждые 10 пользователей
            if i % 10 == 0:
                await status_msg.edit_text(
                    f"📤 Отправлено: {success}/{len(users)}\n"
                    f"❌ Ошибок: {failed}",
                    parse_mode="HTML"
                )
            
            # Задержка между сообщениями (Telegram: max 30 msg/sec)
            await asyncio.sleep(0.05)  # 50ms
            
        except Exception as e:
            failed += 1
            logger.warning(f"❌ Failed to notify user {username} ({user_id}): {e}")
    
    # Финальный отчет
    final_text = (
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"Отправлено: <b>{success}</b>\n"
        f"Ошибки: <b>{failed}</b>\n"
        f"Всего: <b>{len(users)}</b>"
    )
    
    await status_msg.edit_text(final_text, parse_mode="HTML")


@router.message(Command("grant_migration"))
async def cmd_grant_migration(message: Message) -> None:
    """
    Выдать бесплатную подписку всем пользователям после миграции.
    
    Usage: /grant_migration [days]
    Default: 30 days
    """
    if await _not_admin(message):
        return
    
    # Парсим количество дней
    parts = message.text.split(maxsplit=1)
    days = 30
    if len(parts) > 1:
        try:
            days = int(parts[1])
        except ValueError:
            await _send_clean_message(message, "❌ Неверный формат. Использование: /grant_migration [days]")
            return
    
    # Получаем всех пользователей
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id, username FROM bot_users")
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        await _send_clean_message(message, "❌ Нет пользователей в базе данных")
        return
    
    # Подтверждение
    confirm_text = (
        f"⚠️ <b>Массовая выдача подписок</b>\n\n"
        f"Будет выдано подписок: <b>{len(users)}</b>\n"
        f"Срок: <b>{days} дней</b>\n\n"
        f"Это создаст/продлит подписку для всех пользователей!\n\n"
        f"Для подтверждения введите команду:\n"
        f"/grant_migration_confirm {days}"
    )
    
    await _send_clean_message(message, confirm_text, parse_mode="HTML")


@router.message(Command("grant_migration_confirm"))
async def cmd_grant_migration_confirm(message: Message) -> None:
    """
    Подтверждение выдачи бесплатных подписок.
    
    Usage: /grant_migration_confirm [days]
    """
    if await _not_admin(message):
        return
    
    # Парсим количество дней
    parts = message.text.split(maxsplit=1)
    days = 30
    if len(parts) > 1:
        try:
            days = int(parts[1])
        except ValueError:
            await _send_clean_message(message, "❌ Неверный формат. Использование: /grant_migration_confirm [days]")
            return
    
    # Получаем всех пользователей
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id, username FROM bot_users")
    users = cursor.fetchall()
    conn.close()
    
    settings = get_settings()
    expire_date = (datetime.utcnow() + timedelta(days=days)).isoformat() + "Z"
    
    status_msg = await _send_clean_message(
        message, 
        f"⚙️ Начинаю выдачу подписок для {len(users)} пользователей...",
        parse_mode="HTML"
    )
    
    granted = 0
    failed = 0
    
    for i, user in enumerate(users, 1):
        user_id = user['telegram_id']
        username = user['username'] or f"user_{user_id}"
        
        try:
            # Проверяем, есть ли уже UUID
            bot_user = BotUser.get_or_create(user_id, username)
            existing_uuid = bot_user.get('remnawave_user_uuid')
            
            if existing_uuid:
                # Продлеваем существующего пользователя
                try:
                    await api_client.update_user(existing_uuid, expireAt=expire_date)
                    granted += 1
                    logger.info(f"✅ Extended {username} ({user_id}) to {expire_date}")
                except Exception as e:
                    # Если пользователь не найден, создаём нового
                    logger.warning(f"User {existing_uuid} not found in new panel, creating new...")
                    raise e
            else:
                # Создаём нового пользователя
                user_data = await api_client.create_user(
                    username=username,
                    expire_at=expire_date,
                    telegram_id=user_id,
                    external_squad_uuid=settings.default_external_squad_uuid,
                    active_internal_squads=settings.default_internal_squads if settings.default_internal_squads else None,
                )
                
                user_info = user_data.get("response", user_data)
                user_uuid = user_info.get("uuid")
                
                if user_uuid:
                    BotUser.set_remnawave_uuid(user_id, user_uuid)
                    granted += 1
                    logger.info(f"✅ Granted {days} days to {username} ({user_id})")
                else:
                    failed += 1
                    logger.error(f"❌ No UUID returned for {username}")
            
            # Обновляем статус каждые 5 пользователей
            if i % 5 == 0:
                await status_msg.edit_text(
                    f"⚙️ Обработано: {i}/{len(users)}\n"
                    f"✅ Выдано: {granted}\n"
                    f"❌ Ошибок: {failed}",
                    parse_mode="HTML"
                )
            
            # Небольшая задержка между запросами к API
            await asyncio.sleep(0.2)  # 200ms
            
        except Exception as e:
            failed += 1
            logger.error(f"❌ Failed to grant to {username} ({user_id}): {e}")
    
    # Финальный отчет
    final_text = (
        f"✅ <b>Выдача подписок завершена!</b>\n\n"
        f"Выдано: <b>{granted}</b>\n"
        f"Ошибки: <b>{failed}</b>\n"
        f"Всего: <b>{len(users)}</b>\n"
        f"Срок: <b>{days} дней</b>\n\n"
        f"Теперь отправьте уведомления:\n"
        f"/migrate_notify_confirm"
    )
    
    await status_msg.edit_text(final_text, parse_mode="HTML")

