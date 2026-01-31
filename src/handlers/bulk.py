"""Обработчики для массовых операций."""
import asyncio

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _

from src.handlers.common import _edit_text_safe, _not_admin, _send_clean_message
from src.handlers.state import PENDING_INPUT, SEARCH_PAGE_SIZE
from src.keyboards.bulk_hosts import bulk_hosts_keyboard
from src.keyboards.bulk_users import bulk_users_keyboard
from src.services.api_client import ApiClientError, UnauthorizedError, api_client
from src.utils.logger import logger
from src.utils.notifications import send_user_notification

# Временные импорты из других модулей
# TODO: Импортировать _fetch_hosts_text из hosts.py после завершения рефакторинга
from src.handlers.hosts import _fetch_hosts_text

router = Router(name="bulk")

# Разрешенные статусы для массовых операций
ALLOWED_STATUSES = {"ACTIVE", "DISABLED", "LIMITED", "EXPIRED"}


def _parse_uuids(text: str, expected_min: int = 1) -> list[str]:
    """Парсит UUID из текста команды."""
    parts = text.split()
    if len(parts) <= expected_min:
        return []
    return parts[expected_min:]


async def _run_bulk_action(
    target: Message | CallbackQuery,
    action: str,
    uuids: list[str] | None = None,
    status: str | None = None,
    days: int | None = None,
) -> None:
    """Выполняет массовую операцию над пользователями."""
    try:
        if action == "reset":
            await api_client.bulk_reset_traffic_users(uuids or [])
        elif action == "delete":
            # Получаем информацию о пользователях перед удалением для уведомлений
            users_to_notify = []
            if uuids:
                for user_uuid in uuids:
                    try:
                        user = await api_client.get_user_by_uuid(user_uuid)
                        users_to_notify.append(user)
                    except Exception:
                        logger.debug("Failed to get user data for notification user_uuid=%s", user_uuid)
            
            await api_client.bulk_delete_users(uuids or [])
            
            # Отправляем уведомления о удалении
            try:
                bot = target.message.bot if isinstance(target, CallbackQuery) else target.bot
                for user in users_to_notify:
                    await send_user_notification(bot, "deleted", user)
            except Exception:
                logger.exception("Failed to send user deletion notifications")
        elif action == "delete_status":
            if status not in ALLOWED_STATUSES:
                await _reply(target, _("bulk.usage_delete_status"))
                return
            
            # Получаем информацию о пользователях перед удалением для уведомлений
            users_to_notify = []
            try:
                start = 0
                while True:
                    users_data = await api_client.get_users(start=start, size=SEARCH_PAGE_SIZE)
                    payload = users_data.get("response", users_data)
                    users = payload.get("users", [])
                    total = payload.get("total", len(users))
                    
                    for user in users:
                        user_info = user.get("response", user)
                        if user_info.get("status") == status and user_info.get("uuid"):
                            users_to_notify.append(user)
                    
                    start += SEARCH_PAGE_SIZE
                    if start >= total or not users:
                        break
            except Exception:
                logger.exception("Failed to get users for deletion notifications")
            
            await api_client.bulk_delete_users_by_status(status)
            
            # Отправляем уведомления о удалении
            try:
                bot = target.message.bot if isinstance(target, CallbackQuery) else target.bot
                for user in users_to_notify:
                    await send_user_notification(bot, "deleted", user)
            except Exception:
                logger.exception("Failed to send user deletion notifications")
        elif action == "revoke":
            await api_client.bulk_revoke_subscriptions(uuids or [])
        elif action == "extend":
            if days is None:
                await _reply(target, _("bulk.usage_extend"))
                return
            await api_client.bulk_extend_users(uuids or [], days)
        elif action == "extend_all":
            if days is None:
                await _reply(target, _("bulk.usage_extend_all"))
                return
            await api_client.bulk_extend_all_users(days)
        elif action == "status":
            if status not in ALLOWED_STATUSES:
                await _reply(target, _("bulk.usage_status"))
                return
            await api_client.bulk_update_users_status(uuids or [], status)
        else:
            await _reply(target, _("errors.generic"))
            return
        await _reply(target, _("bulk.done"), back=False)
    except UnauthorizedError:
        await _reply(target, _("errors.unauthorized"))
    except ApiClientError:
        logger.exception("❌ Bulk users action failed action=%s", action)
        await _reply(target, _("bulk.error"))


async def _reply(target: Message | CallbackQuery, text: str, back: bool = False) -> None:
    """Отправляет ответ на массовую операцию."""
    markup = bulk_users_keyboard() if back else None
    if isinstance(target, CallbackQuery):
        await _edit_text_safe(target.message, text, reply_markup=markup)
    else:
        await _send_clean_message(target, text, reply_markup=markup)


async def _handle_bulk_users_input(message: Message, ctx: dict) -> None:
    """Обрабатывает ввод для массовых операций над пользователями."""
    action = ctx.get("action", "")
    text = (message.text or "").strip()
    user_id = message.from_user.id

    def _reask(prompt_key: str) -> None:
        PENDING_INPUT[user_id] = ctx
        asyncio.create_task(_send_clean_message(message, _(prompt_key), reply_markup=bulk_users_keyboard()))

    if action == "bulk_users_extend_active":
        try:
            days = int(text)
            if days <= 0:
                _reask("bulk.prompt_extend_active")
                return
        except ValueError:
            _reask("bulk.prompt_extend_active")
            return

        try:
            # Получаем всех активных пользователей с пагинацией
            active_uuids: list[str] = []
            start = 0
            while True:
                users_data = await api_client.get_users(start=start, size=SEARCH_PAGE_SIZE)
                payload = users_data.get("response", users_data)
                users = payload.get("users", [])
                total = payload.get("total", len(users))

                # Фильтруем активных пользователей
                for user in users:
                    user_info = user.get("response", user)
                    if user_info.get("status") == "ACTIVE" and user_info.get("uuid"):
                        active_uuids.append(user_info.get("uuid"))

                start += SEARCH_PAGE_SIZE
                if start >= total or not users:
                    break

            if not active_uuids:
                await _send_clean_message(message, _("bulk.no_active_users"), reply_markup=bulk_users_keyboard())
                PENDING_INPUT.pop(user_id, None)
                return

            # Продлеваем активным
            await api_client.bulk_extend_users(active_uuids, days)
            result_text = _("bulk.done_extend_active").format(count=len(active_uuids), days=days)
            await _send_clean_message(message, result_text, reply_markup=bulk_users_keyboard())
            PENDING_INPUT.pop(user_id, None)
        except UnauthorizedError:
            await _send_clean_message(message, _("errors.unauthorized"), reply_markup=bulk_users_keyboard())
            PENDING_INPUT.pop(user_id, None)
        except ApiClientError:
            logger.exception("❌ Bulk extend active users failed")
            await _send_clean_message(message, _("bulk.error"), reply_markup=bulk_users_keyboard())
            PENDING_INPUT.pop(user_id, None)
        return

    await _send_clean_message(message, _("errors.generic"), reply_markup=bulk_users_keyboard())


@router.callback_query(F.data == "menu:bulk_users")
async def cb_bulk_users(callback: CallbackQuery) -> None:
    """Обработчик кнопки 'Массовые операции (пользователи)' в меню."""
    if await _not_admin(callback):
        return
    await callback.answer()
    await _edit_text_safe(callback.message, _("bulk.overview"), reply_markup=bulk_users_keyboard())


@router.callback_query(F.data.startswith("bulk:users:"))
async def cb_bulk_users_actions(callback: CallbackQuery) -> None:
    """Обработчик действий массовых операций над пользователями."""
    if await _not_admin(callback):
        return
    await callback.answer()
    parts = callback.data.split(":")
    action = parts[2] if len(parts) > 2 else None
    try:
        if action == "reset":
            await api_client.bulk_reset_traffic_all_users()
            await _edit_text_safe(callback.message, _("bulk.done"), reply_markup=bulk_users_keyboard())
        elif action == "delete" and len(parts) > 3:
            status = parts[3]
            
            # Получаем информацию о пользователях перед удалением для уведомлений
            users_to_notify = []
            try:
                start = 0
                while True:
                    users_data = await api_client.get_users(start=start, size=SEARCH_PAGE_SIZE)
                    payload = users_data.get("response", users_data)
                    users = payload.get("users", [])
                    total = payload.get("total", len(users))
                    
                    for user in users:
                        user_info = user.get("response", user)
                        if user_info.get("status") == status and user_info.get("uuid"):
                            users_to_notify.append(user)
                    
                    start += SEARCH_PAGE_SIZE
                    if start >= total or not users:
                        break
            except Exception:
                logger.exception("Failed to get users for deletion notifications")
            
            await api_client.bulk_delete_users_by_status(status)
            
            # Отправляем уведомления о удалении
            try:
                bot = callback.message.bot
                for user in users_to_notify:
                    await send_user_notification(bot, "deleted", user)
            except Exception:
                logger.exception("Failed to send user deletion notifications")
            
            await _edit_text_safe(callback.message, _("bulk.done"), reply_markup=bulk_users_keyboard())
        elif action == "extend_all" and len(parts) > 3:
            try:
                days = int(parts[3])
            except ValueError:
                await callback.answer(_("errors.generic"), show_alert=True)
                return
            await api_client.bulk_extend_all_users(days)
            await _edit_text_safe(callback.message, _("bulk.done"), reply_markup=bulk_users_keyboard())
        elif action == "extend_active":
            # Запрашиваем количество дней
            PENDING_INPUT[callback.from_user.id] = {"action": "bulk_users_extend_active"}
            await _edit_text_safe(callback.message, _("bulk.prompt_extend_active"), reply_markup=bulk_users_keyboard())
        else:
            await callback.answer(_("errors.generic"), show_alert=True)
            return
    except UnauthorizedError:
        await _edit_text_safe(callback.message, _("errors.unauthorized"), reply_markup=bulk_users_keyboard())
    except ApiClientError:
        logger.exception("❌ Bulk users action failed action=%s", action)
        await _edit_text_safe(callback.message, _("bulk.error"), reply_markup=bulk_users_keyboard())


@router.callback_query(F.data == "menu:bulk_hosts")
async def cb_bulk_hosts(callback: CallbackQuery) -> None:
    """Обработчик кнопки 'Массовые операции (хосты)' в меню."""
    if await _not_admin(callback):
        return
    await callback.answer()
    await _edit_text_safe(callback.message, _("bulk_hosts.overview"), reply_markup=bulk_hosts_keyboard())


@router.callback_query(F.data.startswith("bulk:hosts:"))
async def cb_bulk_hosts_actions(callback: CallbackQuery) -> None:
    """Обработчик действий массовых операций над хостами."""
    if await _not_admin(callback):
        return
    await callback.answer()
    action = callback.data.split(":")[-1]
    if action == "list":
        text = await _fetch_hosts_text()
        await _edit_text_safe(callback.message, text, reply_markup=bulk_hosts_keyboard())
        return
    try:
        if action == "enable_all":
            hosts_data = await api_client.get_hosts()
            hosts = hosts_data.get("response", [])
            uuids = [h.get("uuid") for h in hosts if h.get("uuid")]
            if uuids:
                await api_client.bulk_enable_hosts(uuids)
            await _edit_text_safe(callback.message, _("bulk_hosts.done"), reply_markup=bulk_hosts_keyboard())
        elif action == "disable_all":
            hosts_data = await api_client.get_hosts()
            hosts = hosts_data.get("response", [])
            uuids = [h.get("uuid") for h in hosts if h.get("uuid")]
            if uuids:
                await api_client.bulk_disable_hosts(uuids)
            await _edit_text_safe(callback.message, _("bulk_hosts.done"), reply_markup=bulk_hosts_keyboard())
        elif action == "delete_disabled":
            hosts_data = await api_client.get_hosts()
            hosts = hosts_data.get("response", [])
            uuids = [h.get("uuid") for h in hosts if h.get("uuid") and h.get("isDisabled")]
            if uuids:
                await api_client.bulk_delete_hosts(uuids)
            await _edit_text_safe(callback.message, _("bulk_hosts.done"), reply_markup=bulk_hosts_keyboard())
        else:
            await callback.answer(_("errors.generic"), show_alert=True)
            return
    except UnauthorizedError:
        await _edit_text_safe(callback.message, _("errors.unauthorized"), reply_markup=bulk_hosts_keyboard())
    except ApiClientError:
        logger.exception("❌ Bulk hosts action failed action=%s", action)
        await _edit_text_safe(callback.message, _("bulk_hosts.error"), reply_markup=bulk_hosts_keyboard())


# ============================================================
# РАССЫЛКА СООБЩЕНИЙ
# ============================================================

from src.database import BotUser
from src.handlers.state import (
    BROADCAST_DATA,
    BROADCAST_MESSAGE_STATE,
    clear_user_state,
    get_user_state,
    set_user_state,
)


def _broadcast_menu_keyboard(user_counts: dict) -> InlineKeyboardMarkup:
    """Клавиатура выбора получателей рассылки."""
    from src.keyboards.navigation import NavTarget, nav_row
    
    buttons = [
        [InlineKeyboardButton(
            text=_("broadcast.target_all").format(count=user_counts['total']),
            callback_data="broadcast:target:all"
        )],
        [InlineKeyboardButton(
            text=_("broadcast.target_active").format(count=user_counts['with_subscription']),
            callback_data="broadcast:target:active"
        )],
        [InlineKeyboardButton(
            text=_("broadcast.target_inactive").format(count=user_counts['without_subscription']),
            callback_data="broadcast:target:inactive"
        )],
        nav_row(NavTarget.MAIN),
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения рассылки."""
    buttons = [
        [
            InlineKeyboardButton(text=_("broadcast.btn_confirm"), callback_data="broadcast:confirm"),
            InlineKeyboardButton(text=_("broadcast.btn_cancel"), callback_data="broadcast:cancel"),
        ],
        [InlineKeyboardButton(text=_("broadcast.btn_back"), callback_data="menu:broadcast")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "menu:broadcast")
async def cb_broadcast_menu(callback: CallbackQuery) -> None:
    """Меню рассылки."""
    if await _not_admin(callback):
        return
    await callback.answer()
    
    # Очищаем предыдущие данные рассылки
    admin_id = callback.from_user.id
    BROADCAST_DATA.pop(admin_id, None)
    clear_user_state(admin_id)
    
    user_counts = BotUser.get_user_count()
    text = f"<b>{_('broadcast.title')}</b>\n\n{_('broadcast.select_target')}"
    await _edit_text_safe(callback.message, text, reply_markup=_broadcast_menu_keyboard(user_counts), parse_mode="HTML")


@router.callback_query(F.data.startswith("broadcast:target:"))
async def cb_broadcast_target(callback: CallbackQuery) -> None:
    """Выбор целевой аудитории рассылки."""
    if await _not_admin(callback):
        return
    await callback.answer()
    
    admin_id = callback.from_user.id
    target_type = callback.data.split(":")[-1]
    
    # Сохраняем тип аудитории
    BROADCAST_DATA[admin_id] = {
        'target_type': target_type,
        'message_text': None,
        'photo_id': None,
    }
    
    # Устанавливаем состояние ожидания сообщения
    set_user_state(admin_id, BROADCAST_MESSAGE_STATE)
    
    text = _("broadcast.enter_message")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("broadcast.btn_cancel"), callback_data="broadcast:cancel")]
    ])
    await _edit_text_safe(callback.message, text, reply_markup=keyboard, parse_mode="HTML")


@router.message(F.text == "/cancel")
async def msg_cancel_broadcast(message: Message) -> None:
    """Отмена рассылки по команде /cancel."""
    admin_id = message.from_user.id
    state = get_user_state(admin_id)
    
    if state == BROADCAST_MESSAGE_STATE:
        clear_user_state(admin_id)
        BROADCAST_DATA.pop(admin_id, None)
        
        user_counts = BotUser.get_user_count()
        await message.answer(
            _("broadcast.cancelled"),
            reply_markup=_broadcast_menu_keyboard(user_counts),
            parse_mode="HTML"
        )


@router.message(F.photo)
async def msg_broadcast_photo(message: Message) -> None:
    """Получение фото для рассылки."""
    admin_id = message.from_user.id
    state = get_user_state(admin_id)
    
    if state != BROADCAST_MESSAGE_STATE:
        return
    
    if admin_id not in BROADCAST_DATA:
        return
    
    # Сохраняем фото и подпись
    BROADCAST_DATA[admin_id]['photo_id'] = message.photo[-1].file_id
    BROADCAST_DATA[admin_id]['message_text'] = message.caption or ""
    
    # Показываем превью
    await _show_broadcast_preview(message, admin_id)


@router.message(F.text)
async def msg_broadcast_text(message: Message) -> None:
    """Получение текста для рассылки."""
    admin_id = message.from_user.id
    state = get_user_state(admin_id)
    
    if state != BROADCAST_MESSAGE_STATE:
        return
    
    if admin_id not in BROADCAST_DATA:
        return
    
    # Игнорируем команды
    if message.text.startswith('/'):
        return
    
    # Сохраняем текст
    BROADCAST_DATA[admin_id]['message_text'] = message.text
    
    # Показываем превью
    await _show_broadcast_preview(message, admin_id)


async def _show_broadcast_preview(message: Message, admin_id: int) -> None:
    """Показывает превью рассылки."""
    data = BROADCAST_DATA.get(admin_id, {})
    target_type = data.get('target_type', 'all')
    
    # Получаем название аудитории
    target_names = {
        'all': _("broadcast.target_all_name"),
        'active': _("broadcast.target_active_name"),
        'inactive': _("broadcast.target_inactive_name"),
    }
    target_name = target_names.get(target_type, target_type)
    
    # Получаем количество получателей
    if target_type == 'all':
        recipients = BotUser.get_all_user_ids()
    elif target_type == 'active':
        recipients = BotUser.get_users_with_subscription()
    else:
        recipients = BotUser.get_users_without_subscription()
    
    count = len(recipients)
    
    preview_text = f"<b>{_('broadcast.preview_title')}</b>\n\n"
    preview_text += f"{_('broadcast.preview_target').format(target=target_name)}\n"
    preview_text += f"{_('broadcast.preview_count').format(count=count)}\n\n"
    preview_text += f"<b>📝 Сообщение:</b>\n"
    preview_text += "━━━━━━━━━━━━━━━━━━━━\n"
    preview_text += data.get('message_text', '') or "<i>Без текста</i>"
    preview_text += "\n━━━━━━━━━━━━━━━━━━━━\n\n"
    preview_text += _("broadcast.confirm_send")
    
    if data.get('photo_id'):
        await message.answer_photo(
            photo=data['photo_id'],
            caption=preview_text,
            reply_markup=_broadcast_confirm_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            preview_text,
            reply_markup=_broadcast_confirm_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "broadcast:cancel")
async def cb_broadcast_cancel(callback: CallbackQuery) -> None:
    """Отмена рассылки."""
    if await _not_admin(callback):
        return
    await callback.answer()
    
    admin_id = callback.from_user.id
    clear_user_state(admin_id)
    BROADCAST_DATA.pop(admin_id, None)
    
    user_counts = BotUser.get_user_count()
    await _edit_text_safe(
        callback.message,
        _("broadcast.cancelled"),
        reply_markup=_broadcast_menu_keyboard(user_counts),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "broadcast:confirm")
async def cb_broadcast_confirm(callback: CallbackQuery) -> None:
    """Подтверждение и запуск рассылки."""
    if await _not_admin(callback):
        return
    await callback.answer()
    
    admin_id = callback.from_user.id
    data = BROADCAST_DATA.get(admin_id, {})
    
    if not data or not data.get('message_text'):
        await callback.answer(_("broadcast.no_message"), show_alert=True)
        return
    
    target_type = data.get('target_type', 'all')
    message_text = data.get('message_text', '')
    photo_id = data.get('photo_id')
    
    # Получаем список получателей
    if target_type == 'all':
        recipients = BotUser.get_all_user_ids()
    elif target_type == 'active':
        recipients = BotUser.get_users_with_subscription()
    else:
        recipients = BotUser.get_users_without_subscription()
    
    total = len(recipients)
    sent = 0
    errors = 0
    
    # Очищаем состояние
    clear_user_state(admin_id)
    BROADCAST_DATA.pop(admin_id, None)
    
    # Обновляем сообщение на статус отправки
    status_msg = await callback.message.edit_text(
        _("broadcast.sending").format(sent=0, total=total),
        parse_mode="HTML"
    )
    
    bot = callback.message.bot
    
    # Отправляем сообщения с задержкой
    for i, user_id in enumerate(recipients):
        try:
            if photo_id:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=photo_id,
                    caption=message_text,
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text=message_text,
                    parse_mode="HTML"
                )
            sent += 1
        except Exception as e:
            errors += 1
            logger.debug(f"Broadcast error for user {user_id}: {e}")
        
        # Обновляем статус каждые 10 сообщений
        if (i + 1) % 10 == 0:
            try:
                await status_msg.edit_text(
                    _("broadcast.sending").format(sent=sent, total=total),
                    parse_mode="HTML"
                )
            except Exception:
                pass
        
        # Задержка между сообщениями (20 сообщений в секунду максимум)
        await asyncio.sleep(0.05)
    
    # Итоговый результат
    from src.keyboards.main_menu import main_menu_keyboard
    
    result_text = _("broadcast.completed").format(
        sent=sent,
        errors=errors,
        total=total
    )
    
    try:
        await status_msg.edit_text(result_text, reply_markup=main_menu_keyboard(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(result_text, reply_markup=main_menu_keyboard(), parse_mode="HTML")

