"""Обработчики для управления промокодами в админ-панели."""
from datetime import datetime
from typing import Optional

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from src.database import PromoCode
from src.handlers.common import _not_admin, _send_clean_message
from src.handlers.state import PENDING_INPUT
from src.keyboards.main_menu import main_menu_keyboard
from src.keyboards.navigation import NavTarget, nav_row
from src.utils.i18n import get_i18n
from src.utils.logger import logger

router = Router(name="promocodes")


def promocodes_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура меню промокодов."""
    i18n = get_i18n()
    _ = i18n.gettext
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("promocodes.create"),
                    callback_data="promo:create"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("promocodes.list"),
                    callback_data="promo:list"
                )
            ],
            nav_row(NavTarget.MAIN_MENU),
        ]
    )


def _format_promocode_info(promo: dict, locale: str = "ru") -> str:
    """Форматирует информацию о промокоде для отображения."""
    i18n = get_i18n()
    with i18n.use_locale(locale):
        _ = i18n.gettext
        
        code = promo.get("code", "")
        discount = promo.get("discount_percent")
        bonus_days = promo.get("bonus_days")
        max_uses = promo.get("max_uses")
        current_uses = promo.get("current_uses", 0)
        expires_at = promo.get("expires_at")
        is_active = promo.get("is_active", 1)
        
        lines = [
            f"<b>Код:</b> <code>{code}</code>",
            f"<b>Статус:</b> {'✅ Активен' if is_active else '❌ Неактивен'}"
        ]
        
        if discount:
            lines.append(f"<b>Скидка:</b> {discount}%")
        if bonus_days:
            lines.append(f"<b>Бонусные дни:</b> +{bonus_days}")
        
        if max_uses:
            lines.append(f"<b>Использований:</b> {current_uses}/{max_uses}")
        else:
            lines.append(f"<b>Использований:</b> {current_uses} (без ограничений)")
        
        if expires_at:
            try:
                expires = datetime.fromisoformat(expires_at)
                expires_str = expires.strftime("%d.%m.%Y %H:%M")
                lines.append(f"<b>Истекает:</b> {expires_str}")
            except:
                lines.append(f"<b>Истекает:</b> {expires_at}")
        else:
            lines.append("<b>Истекает:</b> Без ограничений")
        
        created_at = promo.get("created_at")
        if created_at:
            try:
                created = datetime.fromisoformat(created_at)
                created_str = created.strftime("%d.%m.%Y %H:%M")
                lines.append(f"<b>Создан:</b> {created_str}")
            except:
                pass
        
        return "\n".join(lines)


# Обработчик menu:section:promocodes находится в navigation.py


@router.callback_query(F.data == "promo:list")
async def cb_promo_list(callback: CallbackQuery) -> None:
    """Показывает список всех промокодов."""
    if await _not_admin(callback):
        return
    await callback.answer()
    
    i18n = get_i18n()
    _ = i18n.gettext
    
    promocodes = PromoCode.get_all()
    
    if not promocodes:
        await _send_clean_message(
            callback,
            _("promocodes.empty_list"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[nav_row(NavTarget.MAIN_MENU)])
        )
        return
    
    # Показываем список промокодов
    text_parts = [f"<b>{_('promocodes.list_title')}</b>\n"]
    
    for promo in promocodes:
        code = promo.get("code", "")
        discount = promo.get("discount_percent")
        bonus_days = promo.get("bonus_days")
        is_active = promo.get("is_active", 1)
        current_uses = promo.get("current_uses", 0)
        max_uses = promo.get("max_uses")
        
        status = "✅" if is_active else "❌"
        promo_info = f"{status} <code>{code}</code>"
        
        if discount:
            promo_info += f" -{discount}%"
        if bonus_days:
            promo_info += f" +{bonus_days}д"
        
        if max_uses:
            promo_info += f" ({current_uses}/{max_uses})"
        else:
            promo_info += f" ({current_uses})"
        
        text_parts.append(promo_info)
    
    text = "\n".join(text_parts)
    
    # Создаем кнопки для каждого промокода
    buttons = []
    for promo in promocodes:
        code = promo.get("code", "")
        buttons.append([
            InlineKeyboardButton(
                text=f"📝 {code}",
                callback_data=f"promo:view:{code}"
            )
        ])
    
    buttons.append(nav_row(NavTarget.MAIN_MENU))
    
    await _send_clean_message(
        callback,
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("promo:view:"))
async def cb_promo_view(callback: CallbackQuery) -> None:
    """Показывает детальную информацию о промокоде."""
    if await _not_admin(callback):
        return
    await callback.answer()
    
    code = callback.data.split(":")[-1]
    promo = PromoCode.get_by_code(code)
    
    if not promo:
        i18n = get_i18n()
        _ = i18n.gettext
        await _send_clean_message(
            callback,
            _("promocodes.not_found"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[nav_row(NavTarget.MAIN_MENU)])
        )
        return
    
    i18n = get_i18n()
    _ = i18n.gettext
    
    text = f"<b>{_('promocodes.details_title')}</b>\n\n"
    text += _format_promocode_info(promo)
    
    # Кнопки управления
    is_active = promo.get("is_active", 1)
    buttons = [
        [
            InlineKeyboardButton(
                text=_("promocodes.deactivate") if is_active else _("promocodes.activate"),
                callback_data=f"promo:toggle:{code}"
            )
        ],
        [
            InlineKeyboardButton(
                text=_("promocodes.delete"),
                callback_data=f"promo:delete_confirm:{code}"
            )
        ],
        [
            InlineKeyboardButton(
                text=_("actions.back"),
                callback_data="promo:list"
            )
        ],
        nav_row(NavTarget.MAIN_MENU)
    ]
    
    await _send_clean_message(
        callback,
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("promo:toggle:"))
async def cb_promo_toggle(callback: CallbackQuery) -> None:
    """Активирует/деактивирует промокод."""
    if await _not_admin(callback):
        return
    await callback.answer()
    
    code = callback.data.split(":")[-1]
    promo = PromoCode.get_by_code(code)
    
    if not promo:
        i18n = get_i18n()
        _ = i18n.gettext
        await callback.answer(_("promocodes.not_found"), show_alert=True)
        return
    
    is_active = promo.get("is_active", 1)
    new_status = not bool(is_active)
    
    PromoCode.set_active(code, new_status)
    
    i18n = get_i18n()
    _ = i18n.gettext
    
    status_text = _("promocodes.activated") if new_status else _("promocodes.deactivated")
    await callback.answer(status_text, show_alert=True)
    
    # Обновляем отображение
    await cb_promo_view(callback)


@router.callback_query(F.data.startswith("promo:delete_confirm:"))
async def cb_promo_delete_confirm(callback: CallbackQuery) -> None:
    """Подтверждение удаления промокода."""
    if await _not_admin(callback):
        return
    await callback.answer()
    
    code = callback.data.split(":")[-1]
    
    i18n = get_i18n()
    _ = i18n.gettext
    
    text = f"<b>{_('promocodes.delete_confirm_title')}</b>\n\n"
    text += _("promocodes.delete_confirm_text").format(code=code)
    
    buttons = [
        [
            InlineKeyboardButton(
                text=_("actions.confirm"),
                callback_data=f"promo:delete:{code}"
            ),
            InlineKeyboardButton(
                text=_("actions.cancel"),
                callback_data=f"promo:view:{code}"
            )
        ],
        nav_row(NavTarget.MAIN_MENU)
    ]
    
    await _send_clean_message(
        callback,
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("promo:delete:"))
async def cb_promo_delete(callback: CallbackQuery) -> None:
    """Удаляет промокод."""
    if await _not_admin(callback):
        return
    await callback.answer()
    
    code = callback.data.split(":")[-1]
    
    success = PromoCode.delete(code)
    
    i18n = get_i18n()
    _ = i18n.gettext
    
    if success:
        await callback.answer(_("promocodes.deleted"), show_alert=True)
        await cb_promo_list(callback)
    else:
        await callback.answer(_("promocodes.delete_failed"), show_alert=True)


@router.callback_query(F.data == "promo:create")
async def cb_promo_create(callback: CallbackQuery) -> None:
    """Начинает процесс создания промокода."""
    if await _not_admin(callback):
        return
    await callback.answer()
    
    i18n = get_i18n()
    _ = i18n.gettext
    
    user_id = callback.from_user.id
    PENDING_INPUT[user_id] = {"action": "promo_create", "step": "code"}
    
    text = f"<b>{_('promocodes.create_title')}</b>\n\n"
    text += _("promocodes.enter_code")
    
    buttons = [
        [
            InlineKeyboardButton(
                text=_("actions.cancel"),
                callback_data="menu:section:promocodes"
            )
        ],
        nav_row(NavTarget.MAIN_MENU)
    ]
    
    await _send_clean_message(
        callback,
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )


@router.message(F.text.regexp(r'^[A-Za-z0-9]{3,20}$'))
async def handle_promo_create(message: Message) -> None:
    """Обработка ввода данных при создании промокода."""
    from src.utils.auth import is_admin
    if not is_admin(message.from_user.id):
        return
    
    user_id = message.from_user.id
    pending = PENDING_INPUT.get(user_id)
    
    if not pending or pending.get("action") != "promo_create":
        return
    
    i18n = get_i18n()
    _ = i18n.gettext
    
    step = pending.get("step")
    
    if step == "code":
        code = message.text.upper()
        # Проверяем, не существует ли уже такой промокод
        existing = PromoCode.get_by_code(code)
        if existing:
            await message.answer(
                _("promocodes.code_exists").format(code=code),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    nav_row(NavTarget.MAIN_MENU)
                ])
            )
            del PENDING_INPUT[user_id]
            return
        
        PENDING_INPUT[user_id] = {"action": "promo_create", "step": "type", "code": code}
        
        text = _("promocodes.choose_type")
        buttons = [
            [
                InlineKeyboardButton(
                    text=_("promocodes.type_discount"),
                    callback_data=f"promo:create_type:{code}:discount"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("promocodes.type_bonus_days"),
                    callback_data=f"promo:create_type:{code}:bonus"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("promocodes.type_both"),
                    callback_data=f"promo:create_type:{code}:both"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("actions.cancel"),
                    callback_data="menu:section:promocodes"
                )
            ],
            nav_row(NavTarget.MAIN_MENU)
        ]
        
        await message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
    
    elif step == "discount":
        try:
            discount = int(message.text)
            if discount < 0 or discount > 100:
                raise ValueError
            pending["discount_percent"] = discount
            pending["step"] = "bonus_or_finish"
            await _promo_create_next_step(message, pending)
        except ValueError:
            await message.answer(_("promocodes.invalid_discount"))
    
    elif step == "bonus_days":
        try:
            bonus_days = int(message.text)
            if bonus_days < 0:
                raise ValueError
            pending["bonus_days"] = bonus_days
            pending["step"] = "max_uses"
            await _promo_create_next_step(message, pending)
        except ValueError:
            await message.answer(_("promocodes.invalid_bonus_days"))
    
    elif step == "max_uses":
        try:
            max_uses = int(message.text) if message.text.strip() else None
            if max_uses is not None and max_uses < 1:
                raise ValueError
            pending["max_uses"] = max_uses
            pending["step"] = "expires_at"
            await _promo_create_next_step(message, pending)
        except ValueError:
            await message.answer(_("promocodes.invalid_max_uses"))
    
    elif step == "expires_at":
        expires_text = message.text.strip()
        if expires_text:
            # Парсим дату в формате DD.MM.YYYY или DD.MM.YYYY HH:MM
            try:
                if " " in expires_text:
                    expires = datetime.strptime(expires_text, "%d.%m.%Y %H:%M")
                else:
                    expires = datetime.strptime(expires_text, "%d.%m.%Y")
                    expires = expires.replace(hour=23, minute=59)
                pending["expires_at"] = expires.isoformat()
            except ValueError:
                await message.answer(_("promocodes.invalid_date"))
                return
        else:
            pending["expires_at"] = None
        
        # Создаем промокод
        await _promo_create_finish(message, pending)


async def _promo_create_next_step(message: Message, pending: dict) -> None:
    """Переход к следующему шагу создания промокода."""
    i18n = get_i18n()
    _ = i18n.gettext
    
    step = pending.get("step")
    
    if step == "bonus_or_finish":
        # Если есть скидка, спрашиваем про бонусные дни
        if pending.get("discount_percent"):
            pending["step"] = "bonus_days"
            text = _("promocodes.enter_bonus_days_optional")
            buttons = [
                [
                    InlineKeyboardButton(
                        text=_("actions.skip_step"),
                        callback_data=f"promo:skip_bonus:{pending.get('code')}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_("actions.cancel"),
                        callback_data="menu:section:promocodes"
                    )
                ],
                nav_row(NavTarget.MAIN_MENU)
            ]
        else:
            pending["step"] = "max_uses"
            text = _("promocodes.enter_max_uses_optional")
            buttons = [
                [
                    InlineKeyboardButton(
                        text=_("actions.skip_step"),
                        callback_data=f"promo:skip_max_uses:{pending.get('code')}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_("actions.cancel"),
                        callback_data="menu:section:promocodes"
                    )
                ],
                nav_row(NavTarget.MAIN_MENU)
            ]
        
        await message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
    
    elif step == "max_uses":
        pending["step"] = "expires_at"
        text = _("promocodes.enter_expires_at_optional")
        buttons = [
            [
                InlineKeyboardButton(
                    text=_("actions.skip_step"),
                    callback_data=f"promo:skip_expires:{pending.get('code')}"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("actions.cancel"),
                    callback_data="menu:section:promocodes"
                )
            ],
            nav_row(NavTarget.MAIN_MENU)
        ]
        
        await message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )


async def _promo_create_finish(message: Message, pending: dict) -> None:
    """Завершает создание промокода."""
    user_id = message.from_user.id
    
    code = pending.get("code")
    discount_percent = pending.get("discount_percent")
    bonus_days = pending.get("bonus_days")
    max_uses = pending.get("max_uses")
    expires_at = pending.get("expires_at")
    
    try:
        PromoCode.create(
            code=code,
            discount_percent=discount_percent,
            bonus_days=bonus_days,
            max_uses=max_uses,
            expires_at=expires_at
        )
        
        del PENDING_INPUT[user_id]
        
        i18n = get_i18n()
        _ = i18n.gettext
        
        text = f"<b>{_('promocodes.created')}</b>\n\n"
        promo = PromoCode.get_by_code(code)
        if promo:
            text += _format_promocode_info(promo)
        
        buttons = [
            [
                InlineKeyboardButton(
                    text=_("promocodes.view"),
                    callback_data=f"promo:view:{code}"
                )
            ],
            nav_row(NavTarget.MAIN_MENU)
        ]
        
        await message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )
        
        logger.info(f"Admin {user_id} created promo code: {code}")
        
    except Exception as e:
        logger.exception(f"Failed to create promo code: {e}")
        i18n = get_i18n()
        _ = i18n.gettext
        await message.answer(
            _("promocodes.create_failed"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[nav_row(NavTarget.MAIN_MENU)])
        )
        del PENDING_INPUT[user_id]


@router.callback_query(F.data.startswith("promo:create_type:"))
async def cb_promo_create_type(callback: CallbackQuery) -> None:
    """Обработчик выбора типа промокода."""
    if await _not_admin(callback):
        return
    await callback.answer()
    
    parts = callback.data.split(":")
    code = parts[2]
    promo_type = parts[3]
    
    user_id = callback.from_user.id
    pending = PENDING_INPUT.get(user_id, {})
    pending["code"] = code
    pending["action"] = "promo_create"
    
    i18n = get_i18n()
    _ = i18n.gettext
    
    if promo_type == "discount":
        pending["step"] = "discount"
        pending["discount_percent"] = None
        pending["bonus_days"] = None
        text = _("promocodes.enter_discount")
    elif promo_type == "bonus":
        pending["step"] = "bonus_days"
        pending["discount_percent"] = None
        pending["bonus_days"] = None
        text = _("promocodes.enter_bonus_days")
    else:  # both
        pending["step"] = "discount"
        pending["discount_percent"] = None
        pending["bonus_days"] = None
        text = _("promocodes.enter_discount")
    
    PENDING_INPUT[user_id] = pending
    
    buttons = [
        [
            InlineKeyboardButton(
                text=_("actions.cancel"),
                callback_data="menu:section:promocodes"
            )
        ],
        nav_row(NavTarget.MAIN_MENU)
    ]
    
    await _send_clean_message(
        callback,
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@router.callback_query(F.data.startswith("promo:skip_"))
async def cb_promo_skip_step(callback: CallbackQuery) -> None:
    """Пропускает опциональный шаг создания промокода."""
    if await _not_admin(callback):
        return
    await callback.answer()
    
    parts = callback.data.split(":")
    step = parts[0].replace("promo:skip_", "")
    code = parts[1]
    
    user_id = callback.from_user.id
    pending = PENDING_INPUT.get(user_id, {})
    
    if step == "bonus":
        pending["bonus_days"] = None
        pending["step"] = "max_uses"
    elif step == "max_uses":
        pending["max_uses"] = None
        pending["step"] = "expires_at"
    elif step == "expires":
        pending["expires_at"] = None
        # Завершаем создание - нужно отправить сообщение
        i18n = get_i18n()
        _ = i18n.gettext
        
        code = pending.get("code")
        discount_percent = pending.get("discount_percent")
        bonus_days = pending.get("bonus_days")
        max_uses = pending.get("max_uses")
        
        try:
            PromoCode.create(
                code=code,
                discount_percent=discount_percent,
                bonus_days=bonus_days,
                max_uses=max_uses,
                expires_at=None
            )
            
            del PENDING_INPUT[user_id]
            
            text = f"<b>{_('promocodes.created')}</b>\n\n"
            promo = PromoCode.get_by_code(code)
            if promo:
                text += _format_promocode_info(promo)
            
            buttons = [
                [
                    InlineKeyboardButton(
                        text=_("promocodes.view"),
                        callback_data=f"promo:view:{code}"
                    )
                ],
                nav_row(NavTarget.MAIN_MENU)
            ]
            
            await _send_clean_message(
                callback,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
                parse_mode="HTML"
            )
            
            logger.info(f"Admin {user_id} created promo code: {code}")
            return
        except Exception as e:
            logger.exception(f"Failed to create promo code: {e}")
            await callback.answer(_("promocodes.create_failed"), show_alert=True)
            del PENDING_INPUT[user_id]
            return
    
    PENDING_INPUT[user_id] = pending
    
    i18n = get_i18n()
    _ = i18n.gettext
    
    if step == "bonus":
        text = _("promocodes.enter_max_uses_optional")
    elif step == "max_uses":
        text = _("promocodes.enter_expires_at_optional")
    
    buttons = [
        [
            InlineKeyboardButton(
                text=_("actions.skip_step"),
                callback_data=f"promo:skip_{'max_uses' if step == 'bonus' else 'expires'}:{code}"
            )
        ],
        [
            InlineKeyboardButton(
                text=_("actions.cancel"),
                callback_data="menu:section:promocodes"
            )
        ],
        nav_row(NavTarget.MAIN_MENU)
    ]
    
    await _send_clean_message(
        callback,
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

