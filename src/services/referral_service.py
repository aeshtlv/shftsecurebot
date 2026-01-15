"""Сервис реферальной программы."""
from datetime import datetime, timedelta

from src.config import get_settings
from src.database import BotUser, Referral
from src.services.api_client import api_client
from src.utils.logger import logger


async def grant_referral_bonus(referred_user_id: int) -> dict | None:
    """
    Начисляет бонусные дни рефереру за активацию реферала.
    
    Args:
        referred_user_id: ID пользователя, который активировал триал/оплатил подписку
    
    Returns:
        dict с данными о начислении бонуса, если успешно, иначе None
    """
    settings = get_settings()
    bonus_days = settings.referral_bonus_days
    
    # Получаем информацию о пользователе
    referred_user = BotUser.get_or_create(referred_user_id, None)
    referrer_id = referred_user.get("referrer_id")
    
    if not referrer_id:
        logger.info("🔍 Referral bonus check: User %s has no referrer_id", referred_user_id)
        return None
    
    logger.info("🔍 Referral bonus check: User %s has referrer_id=%s", referred_user_id, referrer_id)
    
    # Проверяем, не начислен ли уже бонус этому конкретному рефералу
    # (бонус начисляется только один раз — при первой активации триала/оплате)
    from src.database import get_db_connection
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT bonus_days FROM referrals 
            WHERE referrer_id = ? AND referred_id = ?
        """, (referrer_id, referred_user_id))
        row = cursor.fetchone()
        
        if not row:
            logger.warning(
                "⚠️ Referral bonus: No referral record found in database for referrer=%s referred=%s. "
                "Make sure the referral relationship was created when the user clicked the referral link.",
                referrer_id, referred_user_id
            )
            return None
        
        if row[0] > 0:
            logger.info("✅ Referral bonus already granted for referrer=%s referred=%s (bonus_days=%s)", 
                       referrer_id, referred_user_id, row[0])
            return None
    
    # Получаем UUID реферера в Remnawave
    referrer_user = BotUser.get_or_create(referrer_id, None)
    referrer_uuid = referrer_user.get("remnawave_user_uuid")
    
    if not referrer_uuid:
        logger.warning(
            "Referrer %s has no Remnawave account, cannot grant bonus",
            referrer_id
        )
        return None
    
    try:
        # Получаем текущую подписку реферера
        user_data = await api_client.get_user_by_uuid(referrer_uuid)
        user_info = user_data.get("response", user_data)
        current_expire = user_info.get("expireAt")
        
        if not current_expire:
            logger.warning(
                "Referrer %s has no expireAt, cannot extend subscription",
                referrer_id
            )
            return None
        
        # Продлеваем подписку на bonus_days
        current_dt = datetime.fromisoformat(current_expire.replace("Z", "+00:00"))
        new_expire = current_dt + timedelta(days=bonus_days)
        new_expire_iso = new_expire.replace(microsecond=0).isoformat() + "Z"
        
        # Обновляем expireAt в Remnawave
        await api_client.update_user(referrer_uuid, expireAt=new_expire_iso)
        
        # Записываем в БД
        Referral.update_bonus_days(referrer_id, referred_user_id, bonus_days)
        
        logger.info(
            "✅ Referral bonus granted: referrer=%s referred=%s bonus_days=%s new_expire=%s",
            referrer_id,
            referred_user_id,
            bonus_days,
            new_expire_iso
        )
        
        # Возвращаем данные для уведомлений
        return {
            "referrer_id": referrer_id,
            "referrer_username": referrer_user.get("username"),
            "referred_id": referred_user_id,
            "referred_username": referred_user.get("username"),
            "bonus_days": bonus_days,
            "new_expire": new_expire_iso
        }
        
    except Exception as e:
        logger.exception(
            "Failed to grant referral bonus for referrer %s: %s",
            referrer_id,
            e
        )
        return None

