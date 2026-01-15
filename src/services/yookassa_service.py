"""Сервис для работы с платежами через YooKassa."""
import io
from datetime import datetime, timedelta
from typing import Optional

import qrcode
from yookassa import Configuration, Payment as YooKassaPayment

from src.config import get_settings
from src.database import Payment
from src.utils.logger import logger


def init_yookassa():
    """Инициализирует YooKassa с настройками из конфига."""
    settings = get_settings()
    if not settings.yookassa_shop_id or not settings.yookassa_secret_key:
        logger.warning("YooKassa credentials not configured")
        return False
    
    Configuration.account_id = settings.yookassa_shop_id
    Configuration.secret_key = settings.yookassa_secret_key
    return True


async def create_yookassa_payment(
    user_id: int,
    subscription_months: int,
    payment_method: str,  # "sbp" или "card"
    promo_code: Optional[str] = None
) -> dict:
    """Создает платеж через YooKassa.
    
    Args:
        user_id: ID пользователя Telegram
        subscription_months: Количество месяцев подписки (1, 3, 6, 12)
        payment_method: Способ оплаты ("sbp" или "card")
        promo_code: Промокод для скидки (опционально)
    
    Returns:
        Словарь с payment_id, payment_url и payment_db_id
    """
    if not init_yookassa():
        raise ValueError("YooKassa not configured")
    
    settings = get_settings()
    
    # Получаем цену в рублях
    rub_prices = {
        1: settings.subscription_rub_1month,
        3: settings.subscription_rub_3months,
        6: settings.subscription_rub_6months,
        12: settings.subscription_rub_12months,
    }
    
    if subscription_months not in rub_prices:
        raise ValueError(f"Invalid subscription months: {subscription_months}")
    
    base_amount = rub_prices[subscription_months]
    
    # Применяем промокод (если есть)
    discount_percent = 0
    if promo_code:
        from src.database import PromoCode
        promo = PromoCode.get(promo_code)
        if promo:
            discount_percent = promo.get("discount_percent", 0) or 0
    
    # Вычисляем сумму с учетом скидки
    amount_float = base_amount * (1 - discount_percent / 100)
    amount = max(1.0, amount_float)  # Минимум 1 рубль
    
    subscription_days = subscription_months * 30
    
    # Описание подписки
    locale_map = {
        1: ("1 месяц", "1 month"),
        3: ("3 месяца", "3 months"),
        6: ("6 месяцев", "6 months"),
        12: ("12 месяцев", "12 months"),
    }
    description_ru, description_en = locale_map[subscription_months]
    description = f"Подписка shftsecure {description_ru} | shftsecure subscription {description_en}"
    
    # Создаем запись о платеже в БД
    payment_db_id = Payment.create(
        user_id=user_id,
        amount_rub=amount,
        invoice_payload=f"yookassa:{user_id}:{subscription_months}:{payment_method}:{promo_code or ''}",
        subscription_days=subscription_days,
        promo_code=promo_code,
        payment_method=payment_method
    )
    
    # Настройки платежа в зависимости от метода
    # Для СБП используем qr, чтобы получить QR-код напрямую
    # Для карты используем redirect
    if payment_method == "sbp":
        confirmation_type = "qr"
    else:
        confirmation_type = "redirect"
    
    try:
        # YooKassa требует сумму как строку с двумя знаками после запятой
        # Убеждаемся, что сумма не меньше минимальной (1 рубль)
        if amount < 1.0:
            raise ValueError(f"Amount too small: {amount} RUB. Minimum is 1 RUB")
        
        # Форматируем сумму с двумя знаками после запятой
        amount_str = f"{float(amount):.2f}"
        
        # Формируем параметры платежа
        payment_params = {
            "amount": {
                "value": amount_str,
                "currency": "RUB"
            },
            "confirmation": {
                "type": confirmation_type,
                "return_url": "https://t.me/shftsecurebot"  # Возврат в бота после оплаты
            },
            "capture": True,
            "description": description,
            "metadata": {
                "user_id": str(user_id),
                "subscription_months": str(subscription_months),
                "payment_db_id": str(payment_db_id),
                "promo_code": promo_code or ""
            }
        }
        
        # Указываем payment_method_data для обоих методов
        # По документации YooKassa для СБП нужно явно указывать type: "sbp"
        if payment_method == "sbp":
            payment_params["payment_method_data"] = {"type": "sbp"}
        elif payment_method == "card":
            payment_params["payment_method_data"] = {"type": "bank_card"}
        
        logger.info(
            "Creating YooKassa payment: amount=%s RUB, method=%s, months=%s, user_id=%s, confirmation_type=%s",
            amount_str, payment_method, subscription_months, user_id, confirmation_type
        )
        
        # Создаем платеж в YooKassa
        payment = YooKassaPayment.create(payment_params)
        
        yookassa_payment_id = payment.id
        confirmation_type_returned = getattr(payment.confirmation, 'type', 'unknown') if payment.confirmation else None
        
        # Получаем URL в зависимости от типа confirmation
        yookassa_payment_url = None
        if payment.confirmation:
            if hasattr(payment.confirmation, 'confirmation_url'):
                # Для redirect типа
                yookassa_payment_url = payment.confirmation.confirmation_url
            elif hasattr(payment.confirmation, 'confirmation_data'):
                # Для qr типа - URL может быть в confirmation_data или формируем из payment_id
                confirmation_data = payment.confirmation.confirmation_data
                if hasattr(confirmation_data, 'qr_data'):
                    # QR-код уже есть в данных
                    pass
                # Формируем URL для кнопки "Оплатить"
                yookassa_payment_url = f"https://yoomoney.ru/checkout/payments/v2/contract/sbp?orderId={yookassa_payment_id}"
        
        # Логируем полный ответ для отладки
        logger.debug(
            "YooKassa payment response: id=%s, status=%s, confirmation_type=%s, has_confirmation_data=%s",
            yookassa_payment_id,
            getattr(payment, 'status', 'unknown'),
            confirmation_type_returned,
            hasattr(payment.confirmation, 'confirmation_data') if payment.confirmation else False
        )
        
        # Для СБП с confirmation.type = "qr" пытаемся извлечь данные QR-кода
        qr_data = None
        if payment_method == "sbp" and payment.confirmation:
            # Пытаемся извлечь данные QR-кода из confirmation_data
            try:
                if hasattr(payment.confirmation, 'confirmation_data'):
                    confirmation_data = payment.confirmation.confirmation_data
                    # Проверяем различные варианты хранения QR-кода
                    if hasattr(confirmation_data, 'qr_data'):
                        qr_data = confirmation_data.qr_data
                        logger.info("Extracted QR data from confirmation_data.qr_data for SBP")
                    elif hasattr(confirmation_data, 'qr_code'):
                        qr_data = confirmation_data.qr_code
                        logger.info("Extracted QR code from confirmation_data.qr_code for SBP")
                    elif isinstance(confirmation_data, dict):
                        qr_data = confirmation_data.get('qr_data') or confirmation_data.get('qr_code')
                        if qr_data:
                            logger.info("Extracted QR data from confirmation_data dict for SBP")
                
                # Если не нашли в confirmation_data, проверяем напрямую в confirmation
                if not qr_data:
                    if hasattr(payment.confirmation, 'qr_data'):
                        qr_data = payment.confirmation.qr_data
                        logger.info("Extracted QR data from confirmation.qr_data for SBP")
                    elif hasattr(payment.confirmation, 'qr_code'):
                        qr_data = payment.confirmation.qr_code
                        logger.info("Extracted QR code from confirmation.qr_code for SBP")
                
                # Логируем структуру для отладки, если QR не найден
                if not qr_data:
                    logger.warning(
                        "QR data not found in confirmation for SBP. Confirmation type: %s",
                        getattr(payment.confirmation, 'type', 'unknown')
                    )
                    if hasattr(payment.confirmation, '__dict__'):
                        logger.debug("Confirmation attributes: %s", list(payment.confirmation.__dict__.keys()))
            except Exception as e:
                logger.exception("Failed to extract QR data from confirmation: %s", e)
        
        # Если QR-код не найден для СБП, используем fallback - URL страницы YooKassa
        if payment_method == "sbp":
            if not qr_data:
                # Fallback: используем специальный URL для страницы с QR-кодом
                sbp_url = f"https://yoomoney.ru/checkout/payments/v2/contract/sbp?orderId={yookassa_payment_id}"
                qr_data = sbp_url
                yookassa_payment_url = sbp_url
                logger.info("Using SBP URL as QR fallback: %s", sbp_url)
            else:
                # Если получили QR-код, используем оригинальный confirmation_url для кнопки
                if not yookassa_payment_url:
                    yookassa_payment_url = f"https://yoomoney.ru/checkout/payments/v2/contract/sbp?orderId={yookassa_payment_id}"
                logger.info("Using extracted QR data for SBP payment")
        elif payment_method == "card":
            if not yookassa_payment_url:
                raise ValueError("YooKassa did not return confirmation_url")
            # Для карты используем обычный URL и генерируем QR из него
            qr_data = yookassa_payment_url
        else:
            if not yookassa_payment_url:
                raise ValueError("YooKassa did not return confirmation_url")
            # Для других методов используем URL платежа
            qr_data = yookassa_payment_url
        
        logger.info(
            "YooKassa payment URL: %s (method=%s)",
            yookassa_payment_url[:80] + "..." if len(yookassa_payment_url) > 80 else yookassa_payment_url,
            payment_method
        )
        
        # Обновляем запись в БД с информацией о платеже YooKassa
        Payment.update_yookassa_payment(
            payment_db_id,
            yookassa_payment_id,
            yookassa_payment_url or ""
        )
        
        logger.info(
            "YooKassa payment created: user_id=%s, payment_id=%s, amount=%s RUB, method=%s, has_qr=%s",
            user_id, yookassa_payment_id, amount, payment_method, qr_data is not None
        )
        
        return {
            "payment_id": yookassa_payment_id,
            "payment_url": yookassa_payment_url,
            "payment_db_id": payment_db_id,
            "amount": amount,
            "qr_data": qr_data or yookassa_payment_url  # Используем URL как fallback для QR
        }
    except Exception as e:
        # Логируем детали ошибки для отладки
        error_details = str(e)
        error_type = type(e).__name__
        
        # Пытаемся получить детали ответа от YooKassa
        response_text = None
        error_code = None
        error_description = None
        
        if hasattr(e, 'response'):
            if hasattr(e.response, 'text'):
                response_text = e.response.text
            elif hasattr(e.response, 'content'):
                try:
                    response_text = e.response.content.decode('utf-8')
                except:
                    response_text = str(e.response.content)
        
        if response_text:
            logger.error(
                "YooKassa API error response: %s", response_text
            )
            error_details = f"{error_details}\nAPI Response: {response_text}"
        
        logger.error(
            "Failed to create YooKassa payment for user %s: %s (%s)\nAmount: %s RUB, Method: %s, Payment DB ID: %s",
            user_id, error_details, error_type, amount, payment_method, payment_db_id
        )
        logger.exception("Full traceback:")
        
        # Обновляем статус платежа на failed
        Payment.update_status(payment_db_id, "failed")
        raise


async def check_yookassa_payment_status(payment_id: str) -> dict:
    """Проверяет статус платежа в YooKassa.
    
    Args:
        payment_id: ID платежа в YooKassa
    
    Returns:
        Словарь с информацией о платеже
    """
    if not init_yookassa():
        raise ValueError("YooKassa not configured")
    
    try:
        payment = YooKassaPayment.find_one(payment_id)
        
        return {
            "id": payment.id,
            "status": payment.status,  # pending, waiting_for_capture, succeeded, canceled
            "paid": payment.paid,
            "amount": payment.amount.value if payment.amount else None,
            "metadata": payment.metadata or {}
        }
    except Exception as e:
        logger.exception("Failed to check YooKassa payment status: %s", e)
        raise


async def process_yookassa_payment(
    payment_id: str,
    bot=None
) -> dict:
    """Обрабатывает успешный платеж YooKassa.
    
    Args:
        payment_id: ID платежа в YooKassa
        bot: Экземпляр бота для уведомлений
    
    Returns:
        Словарь с результатом обработки
    """
    # Находим платеж в БД
    payment = Payment.get_by_yookassa_id(payment_id)
    if not payment:
        logger.error(f"Payment not found for YooKassa ID: {payment_id}")
        return {"success": False, "error": "Payment not found"}
    
    if payment["status"] == "completed":
        logger.warning(f"Payment {payment['id']} already completed")
        return {
            "success": True,
            "user_uuid": payment["remnawave_user_uuid"],
            "already_completed": True
        }
    
    # Проверяем статус в YooKassa
    try:
        yookassa_status = await check_yookassa_payment_status(payment_id)
    except Exception as e:
        logger.exception("Failed to check YooKassa payment status")
        return {"success": False, "error": str(e)}
    
    if yookassa_status["status"] != "succeeded" or not yookassa_status["paid"]:
        return {
            "success": False,
            "error": f"Payment not completed. Status: {yookassa_status['status']}"
        }
    
    # Парсим invoice_payload для получения данных
    invoice_payload = payment["invoice_payload"]
    parts = invoice_payload.split(":")
    if len(parts) < 4:
        logger.error(f"Invalid invoice_payload format: {invoice_payload}")
        return {"success": False, "error": "Invalid payload format"}
    
    user_id = int(parts[1])
    subscription_months = int(parts[2])
    subscription_days = payment["subscription_days"]
    promo_code = payment.get("promo_code")
    
    # Используем логику из payment_service для создания/обновления пользователя
    # Но адаптируем под YooKassa - создаем временный payload
    temp_payload = f"{user_id}:{subscription_months}:0:{promo_code or ''}"
    
    # Временно обновляем invoice_payload для совместимости с process_successful_payment
    from src.database import get_db_connection
    original_payload = payment["invoice_payload"]
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE payments SET invoice_payload = ? WHERE id = ?",
            (temp_payload, payment["id"])
        )
    
    try:
        from src.services.payment_service import process_successful_payment
        
        result = await process_successful_payment(
            user_id=user_id,
            invoice_payload=temp_payload,
            total_amount=0,  # Для YooKassa не используется
            bot=bot
        )
        
        # Восстанавливаем оригинальный payload
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE payments SET invoice_payload = ? WHERE id = ?",
                (original_payload, payment["id"])
            )
        
        if result.get("success"):
            # Обновляем статус платежа
            Payment.update_status(payment["id"], "completed", result.get("user_uuid"))
            return result
        else:
            Payment.update_status(payment["id"], "failed")
            return result
    except Exception as e:
        logger.exception("Failed to process YooKassa payment")
        # Восстанавливаем оригинальный payload даже при ошибке
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE payments SET invoice_payload = ? WHERE id = ?",
                (original_payload, payment["id"])
            )
        Payment.update_status(payment["id"], "failed")
        return {"success": False, "error": str(e)}


def generate_qr_code_image(data: str) -> io.BytesIO:
    """Генерирует QR-код из данных и возвращает как BytesIO.
    
    Args:
        data: Данные для QR-кода (обычно URL или строка для СБП)
    
    Returns:
        BytesIO объект с изображением QR-кода
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Сохраняем в BytesIO
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes

