"""Сервис уведомлений администраторам."""
from datetime import datetime
from typing import Optional

from aiogram import Bot

from src.config import get_settings
from src.utils.logger import logger


async def send_admin_notification(
    bot: Bot,
    text: str,
    parse_mode: str = "HTML"
) -> bool:
    """
    Отправляет уведомление в админский канал/группу.
    
    Args:
        bot: Экземпляр бота
        text: Текст уведомления
        parse_mode: Режим парсинга (HTML/Markdown)
    
    Returns:
        True если отправлено, False если не настроено или ошибка
    """
    settings = get_settings()
    chat_id = settings.notifications_chat_id
    topic_id = settings.notifications_topic_id
    
    if not chat_id:
        logger.debug("Notifications disabled: NOTIFICATIONS_CHAT_ID not set")
        return False
    
    try:
        # Если указан topic_id, отправляем в топик (для групп с темами)
        kwargs = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
        if topic_id:
            kwargs["message_thread_id"] = topic_id
        
        await bot.send_message(**kwargs)
        logger.debug("Admin notification sent to chat_id=%s topic_id=%s", chat_id, topic_id)
        return True
        
    except Exception as e:
        # Не критичная ошибка - просто не настроен чат для уведомлений
        logger.warning("Failed to send admin notification: %s", str(e))
        return False


async def notify_trial_activation(
    bot: Bot,
    user_id: int,
    username: Optional[str],
    trial_days: int,
    remnawave_uuid: str
) -> None:
    """Уведомление об активации пробной подписки."""
    user_mention = f"@{username}" if username else f"User {user_id}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    text = (
        f"🎁 <b>Активирована пробная подписка</b>\n\n"
        f"👤 Пользователь: {user_mention}\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n"
        f"⏰ Срок: <b>{trial_days} дней</b>\n"
        f"🔗 UUID: <code>{remnawave_uuid}</code>\n"
        f"📅 Время: {timestamp}"
    )
    
    await send_admin_notification(bot, text)


async def notify_payment_success(
    bot: Bot,
    user_id: int,
    username: Optional[str],
    subscription_months: int,
    stars: int,
    remnawave_uuid: str,
    expire_date: str
) -> None:
    """Уведомление об успешной оплате."""
    user_mention = f"@{username}" if username else f"User {user_id}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Уведомление админам
    admin_text = (
        f"💰 <b>Новая покупка</b>\n\n"
        f"👤 Пользователь: {user_mention}\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n"
        f"⭐ Сумма: <b>{stars} Stars</b>\n"
        f"📅 Период: <b>{subscription_months} мес.</b>\n"
        f"🔗 UUID: <code>{remnawave_uuid}</code>\n"
        f"⏳ Истекает: <code>{expire_date}</code>\n"
        f"📅 Время: {timestamp}"
    )
    
    await send_admin_notification(bot, admin_text)
    
    # Уведомление пользователю
    try:
        user_text = (
            f"✅ <b>Оплата успешна!</b>\n\n"
            f"Ваша подписка активирована.\n\n"
            f"📅 Период: <b>{subscription_months} мес.</b>\n"
            f"⏳ Действует до: <code>{expire_date}</code>\n\n"
            f"Приятного пользования! 🚀"
        )
        await bot.send_message(user_id, user_text, parse_mode="HTML")
        logger.info(f"Payment success notification sent to user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to send payment notification to user {user_id}: {e}")


async def notify_yookassa_payment_success(
    bot: Bot,
    user_id: int,
    username: Optional[str],
    subscription_months: int,
    amount_rub: float,
    remnawave_uuid: str,
    expire_date: str
) -> None:
    """Уведомление об успешной оплате через YooKassa."""
    user_mention = f"@{username}" if username else f"User {user_id}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Уведомление админам
    admin_text = (
        f"💰 <b>Новая покупка (YooKassa)</b>\n\n"
        f"👤 Пользователь: {user_mention}\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n"
        f"💳 Сумма: <b>{amount_rub}₽</b>\n"
        f"📅 Период: <b>{subscription_months} мес.</b>\n"
        f"🔗 UUID: <code>{remnawave_uuid}</code>\n"
        f"⏳ Истекает: <code>{expire_date}</code>\n"
        f"📅 Время: {timestamp}"
    )
    
    await send_admin_notification(bot, admin_text)
    
    # Уведомление пользователю
    try:
        user_text = (
            f"✅ <b>Оплата получена!</b>\n\n"
            f"Ваша подписка успешно активирована.\n\n"
            f"💳 Сумма: <b>{amount_rub}₽</b>\n"
            f"📅 Период: <b>{subscription_months} мес.</b>\n"
            f"⏳ Действует до: <code>{expire_date}</code>\n\n"
            f"Приятного пользования! 🚀"
        )
        await bot.send_message(user_id, user_text, parse_mode="HTML")
        logger.info(f"YooKassa payment success notification sent to user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to send YooKassa payment notification to user {user_id}: {e}")


async def notify_referral_bonus(
    bot: Bot,
    referrer_id: int,
    referrer_username: Optional[str],
    referred_id: int,
    referred_username: Optional[str],
    bonus_days: int,
    new_expire: str
) -> None:
    """Уведомление о начислении реферального бонуса."""
    referrer_mention = f"@{referrer_username}" if referrer_username else f"User {referrer_id}"
    referred_mention = f"@{referred_username}" if referred_username else f"User {referred_id}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    text = (
        f"👥 <b>Реферальный бонус начислен</b>\n\n"
        f"👤 Реферер: {referrer_mention}\n"
        f"🆔 ID: <code>{referrer_id}</code>\n"
        f"🎁 Бонус: <b>+{bonus_days} дней</b>\n"
        f"⏳ Новая дата истечения: <code>{new_expire}</code>\n\n"
        f"👥 Приглашённый: {referred_mention}\n"
        f"🆔 ID: <code>{referred_id}</code>\n"
        f"📅 Время: {timestamp}"
    )
    
    await send_admin_notification(bot, text)






