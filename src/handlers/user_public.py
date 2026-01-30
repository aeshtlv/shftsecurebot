"""Обработчики для публичных пользователей (не админов)."""
from datetime import datetime, timedelta
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.i18n import gettext as _

from src.database import BotUser, GiftCode, Payment, Referral
from src.services.api_client import NotFoundError, api_client
from src.utils.i18n import get_i18n
from src.utils.logger import logger

router = Router(name="user_public")


def _get_months_text(months: int, locale: str) -> str:
    """Возвращает правильное склонение месяцев для русского языка."""
    if locale == "ru":
        if months == 1:
            return "1 месяц"
        elif months in (2, 3, 4):
            return f"{months} месяца"
        else:
            return f"{months} месяцев"
    else:
        # Для английского
        if months == 1:
            return "1 month"
        else:
            return f"{months} months"


def _get_user_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру главного меню пользователя."""
    from src.utils.auth import is_admin
    buttons = [
        # 1️⃣ Подключить доступ — главное действие → отдельная строка
        [
            InlineKeyboardButton(
                text=_("user_menu.connect"),
                callback_data="user:connect"
            )
        ],
        # 2️⃣ Мой доступ / Настройки — вторичные → в одной строке
        [
            InlineKeyboardButton(
                text=_("user_menu.my_access"),
                callback_data="user:my_access"
            ),
            InlineKeyboardButton(
                text=_("user_menu.settings"),
                callback_data="user:settings"
            )
        ],
        # 3️⃣ Поддержка — редко → отдельно
        [
            InlineKeyboardButton(
                text=_("user_menu.support"),
                callback_data="user:support"
            )
        ]
    ]
    # 4️⃣ Админка — только для админа, отдельно
    if is_admin(user_id):
        buttons.append([
            InlineKeyboardButton(
                text=_("user_menu.admin_panel"),
                callback_data="admin:panel",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _get_language_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка."""
    buttons = [
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Обработчик команды /start для всех пользователей."""
    user_id = message.from_user.id
    username = message.from_user.username

    # Получаем или создаем пользователя
    user = BotUser.get_or_create(user_id, username)
    locale = user.get("language", "ru")
    
    # Устанавливаем локализацию
    i18n = get_i18n()
    with i18n.use_locale(locale):
        # Инициализируем welcome_text по умолчанию
        welcome_text = _("user.welcome")
        
        # Проверяем, есть ли реферальный код
        args = message.text.split()[1:] if message.text and len(message.text.split()) > 1 else []
        
        if args:
            try:
                referrer_id = int(args[0])
                if referrer_id != user_id:
                    BotUser.set_referrer(user_id, referrer_id)
                    Referral.create(referrer_id, user_id)
                    welcome_text = _("user.welcome_with_referral")
            except (ValueError, IndexError):
                # welcome_text уже инициализирован выше
                pass
        
        await message.answer(
            welcome_text,
            reply_markup=_get_user_menu_keyboard(user_id)
        )




@router.callback_query(F.data == "admin:panel")
async def cb_admin_panel(callback: CallbackQuery) -> None:
    """Открывает админ-панель (только для админов)."""
    from src.utils.auth import is_admin
    from src.handlers.navigation import _fetch_main_menu_text
    from src.keyboards.main_menu import main_menu_keyboard

    await callback.answer()
    if not is_admin(callback.from_user.id):
        # Защита на всякий случай (middleware тоже блокирует)
        await callback.answer(_("errors.unauthorized"), show_alert=True)
        return

    menu_text = await _fetch_main_menu_text()
    await callback.message.edit_text(menu_text, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "user:menu")
async def cb_user_menu(callback: CallbackQuery) -> None:
    """Показывает главное меню пользователя."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        # Показываем приветственный текст как при /start
        welcome_text = _("user.welcome")
        await callback.message.edit_text(
            welcome_text,
            reply_markup=_get_user_menu_keyboard(user_id)
        )


@router.callback_query(F.data == "user:language")
async def cb_language(callback: CallbackQuery) -> None:
    """Обработчик выбора языка."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        buttons = [
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")
            ],
            [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:settings"
                )
            ]
        ]
        await callback.message.edit_text(
            _("user.choose_language"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )


@router.callback_query(F.data.startswith("lang:"))
async def cb_set_language(callback: CallbackQuery) -> None:
    """Устанавливает язык пользователя."""
    await callback.answer()
    language = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    BotUser.update_language(user_id, language)
    
    i18n = get_i18n()
    with i18n.use_locale(language):
        buttons = [
            [
                InlineKeyboardButton(
                    text=_("settings.language"),
                    callback_data="user:language"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("settings.referral"),
                    callback_data="user:referral"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:menu"
                )
            ]
        ]
        await callback.message.edit_text(
            _("user.language_changed"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )


@router.callback_query(F.data == "user:connect")
async def cb_connect(callback: CallbackQuery) -> None:
    """Обработчик 'Подключить доступ'."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        buttons = [
            [
                InlineKeyboardButton(
                    text=_("connect.buy_subscription"),
                    callback_data="user:buy"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("connect.trial"),
                    callback_data="user:trial"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("gift.menu_button"),
                    callback_data="user:gift"
                ),
                InlineKeyboardButton(
                    text=_("gift.activate_button"),
                    callback_data="gift:activate"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:menu"
                )
            ]
        ]
        await callback.message.edit_text(
            _("connect.title"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )


@router.callback_query(F.data == "user:my_access")
async def cb_my_access(callback: CallbackQuery) -> None:
    """Обработчик 'Мой доступ' - показывает статус подписки."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        # Показываем сообщение "Проверяем статус доступа…"
        await callback.message.edit_text(_("my_access.checking_status"))
        
        remnawave_uuid = user.get("remnawave_user_uuid")
        
        if not remnawave_uuid:
            buttons = [
                [
                    InlineKeyboardButton(
                        text=_("user_menu.connect"),
                        callback_data="user:connect"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_("user_menu.back"),
                        callback_data="user:menu"
                    )
                ]
            ]
            await callback.message.edit_text(
                _("my_access.no_access"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
            )
            return
        
        try:
            # Получаем информацию о пользователе из Remnawave
            user_data = await api_client.get_user_by_uuid(remnawave_uuid)
            info = user_data.get("response", user_data)
            
            # Получаем подписку
            short_uuid = info.get("shortUuid")
            subscription_url = ""
            if short_uuid:
                try:
                    sub_info = await api_client.get_subscription_info(short_uuid)
                    sub_data = sub_info.get("response", sub_info)
                    subscription_url = sub_data.get("subscriptionUrl", "")
                except:
                    pass
            
            # Формируем текст
            status = info.get("status", "UNKNOWN")
            expire_at = info.get("expireAt")
            traffic_used = info.get("trafficUsed", 0)
            traffic_limit = info.get("trafficLimit", 0)
            
            status_text = {
                "ACTIVE": _("my_access.status_active", locale=locale),
                "DISABLED": _("my_access.status_disabled", locale=locale),
                "LIMITED": _("my_access.status_limited", locale=locale),
                "EXPIRED": _("my_access.status_expired", locale=locale),
            }.get(status, status)
            
            expire_text = ""
            if expire_at:
                try:
                    expire_dt = datetime.fromisoformat(expire_at.replace("Z", "+00:00"))
                    expire_text = expire_dt.strftime("%d.%m.%Y %H:%M")
                except:
                    expire_text = expire_at
            
            from src.utils.formatters import format_bytes
            traffic_text = f"{format_bytes(traffic_used)} / {format_bytes(traffic_limit)}"
            
            text = _("user.subscription_info", locale=locale).format(
                status=status_text,
                expire=expire_text or _("user.no_expire", locale=locale),
                traffic=traffic_text,
                url=subscription_url or _("user.no_url", locale=locale)
            )
            
            keyboard_buttons = []
            
            if subscription_url:
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=_("user.get_config", locale=locale),
                        url=subscription_url
                    )
                ])
            
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=_("user_menu.back", locale=locale),
                    callback_data="user:menu"
                )
            ])
            
            await callback.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
                parse_mode="HTML"
            )
        except NotFoundError:
            buttons = [
                [
                    InlineKeyboardButton(
                        text=_("user_menu.connect", locale=locale),
                        callback_data="user:connect"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_("user_menu.back", locale=locale),
                        callback_data="user:menu"
                    )
                ]
            ]
            await callback.message.edit_text(
                _("my_access.no_access", locale=locale),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
            )
        except Exception as e:
            logger.exception(f"Error getting subscription info for user {user_id}, uuid {remnawave_uuid}: {e}")
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                error_text = _("my_access.no_access", locale=locale)
            else:
                error_text = _("errors.generic", locale=locale) + f"\n\nОшибка: {error_msg[:100]}"
            
            buttons = [
                [
                    InlineKeyboardButton(
                        text=_("user_menu.back", locale=locale),
                        callback_data="user:menu"
                    )
                ]
            ]
            await callback.message.edit_text(
                error_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
            )


@router.callback_query(F.data == "user:settings")
async def cb_settings(callback: CallbackQuery) -> None:
    """Обработчик 'Настройки'."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    auto_renewal = BotUser.get_auto_renewal(user_id)
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        # Определяем текст для кнопки автопродления
        auto_renewal_text = _("settings.auto_renewal_on") if auto_renewal else _("settings.auto_renewal_off")
        
        buttons = [
            [
                InlineKeyboardButton(
                    text=auto_renewal_text,
                    callback_data="user:auto_renewal"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("settings.language"),
                    callback_data="user:language"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("settings.referral"),
                    callback_data="user:referral"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("settings.documents"),
                    callback_data="user:documents"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:menu"
                )
            ]
        ]
        await callback.message.edit_text(
            _("settings.title"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )


@router.callback_query(F.data == "user:support")
async def cb_support(callback: CallbackQuery) -> None:
    """Обработчик 'Поддержка'."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        buttons = [
            [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:menu"
                )
            ]
        ]
        await callback.message.edit_text(
            _("support.title"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )


@router.callback_query(F.data == "user:documents")
async def cb_documents(callback: CallbackQuery) -> None:
    """Обработчик 'Документы'."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        buttons = [
            [
                InlineKeyboardButton(
                    text=_("documents.privacy"),
                    callback_data="user:documents:privacy"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("documents.offer"),
                    callback_data="user:documents:offer"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("documents.rules"),
                    callback_data="user:documents:rules"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:settings"
                )
            ]
        ]
        await callback.message.edit_text(
            _("documents.title"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )


@router.callback_query(F.data == "user:documents:privacy")
async def cb_documents_privacy(callback: CallbackQuery) -> None:
    """Обработчик 'Политика конфиденциальности'."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        buttons = [
            [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:documents"
                )
            ]
        ]
        await callback.message.edit_text(
            _("documents.privacy_content"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "user:documents:offer")
async def cb_documents_offer(callback: CallbackQuery) -> None:
    """Обработчик 'Публичная оферта'."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        buttons = [
            [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:documents"
                )
            ]
        ]
        await callback.message.edit_text(
            _("documents.offer_content"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "user:documents:rules")
async def cb_documents_rules(callback: CallbackQuery) -> None:
    """Обработчик 'Правила использования сервиса'."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        buttons = [
            [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:documents"
                )
            ]
        ]
        await callback.message.edit_text(
            _("documents.rules_content"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "user:subscription")
async def cb_subscription(callback: CallbackQuery) -> None:
    """Показывает информацию о подписке пользователя."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        remnawave_uuid = user.get("remnawave_user_uuid")
        
        if not remnawave_uuid:
            await callback.message.edit_text(
                _("user.no_subscription"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=_("user_menu.back", locale=locale),
                        callback_data="user:menu"
                    )
                ]])
            )
            return
        
        try:
            # Получаем информацию о пользователе из Remnawave
            user_data = await api_client.get_user_by_uuid(remnawave_uuid)
            info = user_data.get("response", user_data)
            
            # Получаем подписку
            short_uuid = info.get("shortUuid")
            if short_uuid:
                sub_info = await api_client.get_subscription_info(short_uuid)
                sub_data = sub_info.get("response", sub_info)
                subscription_url = sub_data.get("subscriptionUrl", "")
            else:
                subscription_url = ""
            
            # Формируем текст
            status = info.get("status", "UNKNOWN")
            expire_at = info.get("expireAt")
            traffic_used = info.get("trafficUsed", 0)
            traffic_limit = info.get("trafficLimit", 0)
            
            status_text = {
                "ACTIVE": _("user.status_active", locale=locale),
                "DISABLED": _("user.status_disabled", locale=locale),
                "LIMITED": _("user.status_limited", locale=locale),
                "EXPIRED": _("user.status_expired", locale=locale),
            }.get(status, status)
            
            expire_text = ""
            if expire_at:
                try:
                    expire_dt = datetime.fromisoformat(expire_at.replace("Z", "+00:00"))
                    expire_text = expire_dt.strftime("%d.%m.%Y %H:%M")
                except:
                    expire_text = expire_at
            
            from src.utils.formatters import format_bytes
            traffic_text = f"{format_bytes(traffic_used)} / {format_bytes(traffic_limit)}"
            
            text = _("user.subscription_info", locale=locale).format(
                status=status_text,
                expire=expire_text or _("user.no_expire", locale=locale),
                traffic=traffic_text,
                url=subscription_url or _("user.no_url", locale=locale)
            )
            
            keyboard_buttons = []
            
            if subscription_url:
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=_("user.get_config", locale=locale),
                        url=subscription_url
                    )
                ])
            
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=_("user_menu.back", locale=locale),
                    callback_data="user:menu"
                )
            ])
            
            await callback.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
                parse_mode="HTML"
            )
        except NotFoundError:
            await callback.message.edit_text(
                _("user.subscription_not_found", locale=locale),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=_("user_menu.back", locale=locale),
                        callback_data="user:menu"
                    )
                ]])
            )
        except Exception as e:
            logger.exception(f"Error getting subscription info for user {user_id}, uuid {remnawave_uuid}: {e}")
            error_msg = str(e)
            # Более информативное сообщение об ошибке
            if "404" in error_msg or "not found" in error_msg.lower():
                error_text = _("user.subscription_not_found", locale=locale)
            else:
                error_text = _("errors.generic", locale=locale) + f"\n\nОшибка: {error_msg[:100]}"
            
            await callback.message.edit_text(
                error_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=_("user_menu.back", locale=locale),
                        callback_data="user:menu"
                    )
                ]])
            )


@router.callback_query(F.data == "user:trial")
async def cb_trial(callback: CallbackQuery) -> None:
    """Обработчик пробной подписки."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        if user.get("trial_used"):
            await callback.message.edit_text(
                _("user.trial_already_used"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=_("user_menu.back"),
                        callback_data="user:menu"
                    )
                ]])
            )
            return
        
        # Пользователь сам активирует триал кнопкой
        await callback.message.edit_text(
            _("user.trial_info"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=_("user.activate_trial"),
                    callback_data="user:trial:activate"
                )
            ], [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:connect"
                )
            ]])
        )


@router.callback_query(F.data == "user:trial:activate")
async def cb_trial_activate(callback: CallbackQuery) -> None:
    """Активация пробной подписки (создаёт пользователя в Remnawave)."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        if user.get("trial_used") or user.get("remnawave_user_uuid"):
            buttons = [
                [
                    InlineKeyboardButton(text=_("user_menu.back"), callback_data="user:connect")
                ]
            ]
            await callback.message.edit_text(
                _("user.trial_already_used"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            )
            return

        from src.config import get_settings
        settings = get_settings()
        trial_days = max(1, int(settings.trial_days))

        # Генерим безопасный username для Remnawave
        base_username = (callback.from_user.username or "").lstrip("@")
        if not base_username:
            base_username = f"tg{user_id}"

        expire_at = (datetime.utcnow() + timedelta(days=trial_days)).replace(microsecond=0).isoformat() + "Z"

        # Подготавливаем сквады
        internal_squads = settings.default_internal_squads if settings.default_internal_squads else None
        
        # Логируем, что передаем
        logger.info(
            "Creating trial user for %d: external_squad=%s, internal_squads=%s (type=%s, len=%s)",
            user_id,
            settings.default_external_squad_uuid,
            internal_squads,
            type(internal_squads).__name__,
            len(internal_squads) if internal_squads else 0
        )
        
        created = None
        username_try = base_username
        for attempt in range(3):
            try:
                created = await api_client.create_user(
                    username=username_try,
                    expire_at=expire_at,
                    telegram_id=user_id,
                    description="trial",
                    external_squad_uuid=settings.default_external_squad_uuid,
                    active_internal_squads=internal_squads,
                )
                logger.info("Trial user created successfully: %s", created.get("response", {}).get("uuid", "unknown"))
                break
            except Exception as e:
                logger.warning(f"Trial activation attempt {attempt+1} failed for user {user_id}: {e}")
                # возможно конфликт username — добавим суффикс
                username_try = f"{base_username}_{attempt+1}"
                continue

        if not created:
            buttons = [
                [
                    InlineKeyboardButton(text=_("user_menu.back"), callback_data="user:connect")
                ]
            ]
            await callback.message.edit_text(
                _("user.trial_activation_failed"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            )
            return

        info = created.get("response", created)
        user_uuid = info.get("uuid")
        if user_uuid:
            BotUser.set_remnawave_uuid(user_id, user_uuid)
        BotUser.set_trial_used(user_id)
        
        # Начисляем бонус рефереру (если есть)
        from src.services.referral_service import grant_referral_bonus
        from src.services.notification_service import notify_trial_activation, notify_referral_bonus
        
        try:
            referral_data = await grant_referral_bonus(user_id)
            if referral_data:
                # Отправляем уведомление о реферальном бонусе
                await notify_referral_bonus(
                    callback.bot,
                    referral_data["referrer_id"],
                    referral_data["referrer_username"],
                    referral_data["referred_id"],
                    referral_data["referred_username"],
                    referral_data["bonus_days"],
                    referral_data["new_expire"]
                )
        except Exception as ref_exc:
            logger.warning("Failed to grant referral bonus on trial activation: %s", ref_exc)
        
        # Отправляем уведомление об активации триала
        try:
            await notify_trial_activation(
                callback.bot,
                user_id,
                callback.from_user.username,
                trial_days,
                user_uuid
            )
        except Exception as notif_exc:
            logger.warning("Failed to send trial activation notification: %s", notif_exc)

        # На всякий случай дожимаем сквады через update (если create проигнорировал)
        if settings.default_external_squad_uuid or internal_squads:
            try:
                update_payload = {}
                if settings.default_external_squad_uuid:
                    update_payload["externalSquadUuid"] = settings.default_external_squad_uuid
                if internal_squads:
                    update_payload["activeInternalSquads"] = internal_squads
                
                if update_payload:
                    await api_client.update_user(user_uuid, **update_payload)
                    logger.info(
                        "Applied squads on trial user %s: external=%s, internal=%s",
                        user_uuid,
                        settings.default_external_squad_uuid,
                        internal_squads
                    )
            except Exception as squad_exc:
                logger.warning("Failed to apply squads on trial user %s: %s", user_uuid, squad_exc)

        # Получаем ссылку на подписку
        subscription_url = ""
        short_uuid = info.get("shortUuid")
        if short_uuid:
            try:
                sub_info = await api_client.get_subscription_info(short_uuid)
                sub_data = sub_info.get("response", sub_info)
                subscription_url = sub_data.get("subscriptionUrl", "") or ""
            except Exception:
                subscription_url = ""

        buttons: list[list[InlineKeyboardButton]] = []
        if subscription_url:
            buttons.append([InlineKeyboardButton(text=_("user.get_config"), url=subscription_url)])
        buttons.append([InlineKeyboardButton(text=_("user_menu.back"), callback_data="user:connect")])

        await callback.message.edit_text(
            _("user.trial_activated").format(days=trial_days),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )


@router.callback_query(F.data == "user:auto_renewal")
async def cb_auto_renewal(callback: CallbackQuery) -> None:
    """Обработчик настройки автопродления."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        current_status = BotUser.get_auto_renewal(user_id)
        
        if current_status:
            # Выключаем автопродление
            BotUser.set_auto_renewal(user_id, False)
            status_text = _("settings.auto_renewal_disabled")
        else:
            # Включаем автопродление
            BotUser.set_auto_renewal(user_id, True)
            status_text = _("settings.auto_renewal_enabled")
        
        auto_renewal = BotUser.get_auto_renewal(user_id)
        auto_renewal_text = _("settings.auto_renewal_on") if auto_renewal else _("settings.auto_renewal_off")
        
        buttons = [
            [
                InlineKeyboardButton(
                    text=_("settings.auto_renewal_info"),
                    callback_data="user:auto_renewal:info"
                )
            ],
            [
                InlineKeyboardButton(
                    text=auto_renewal_text,
                    callback_data="user:auto_renewal"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:settings"
                )
            ]
        ]
        
        await callback.message.edit_text(
            status_text + "\n\n" + _("settings.auto_renewal_description"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )


@router.callback_query(F.data == "user:auto_renewal:info")
async def cb_auto_renewal_info(callback: CallbackQuery) -> None:
    """Показывает подробную информацию об автопродлении."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        auto_renewal = BotUser.get_auto_renewal(user_id)
        auto_renewal_text = _("settings.auto_renewal_on") if auto_renewal else _("settings.auto_renewal_off")
        
        buttons = [
            [
                InlineKeyboardButton(
                    text=auto_renewal_text,
                    callback_data="user:auto_renewal"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:settings"
                )
            ]
        ]
        
        status_text = auto_renewal_text
        await callback.message.edit_text(
            _("settings.auto_renewal_full_info").format(status=status_text),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )


@router.callback_query(F.data == "user:referral")
async def cb_referral(callback: CallbackQuery) -> None:
    """Показывает реферальную информацию."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        referrals_count = Referral.get_referrals_count(user_id)
        bonus_days = Referral.get_bonus_days(user_id)
        
        # Создаем реферальную ссылку
        try:
            bot_username = (await callback.message.bot.get_me()).username or "your_bot"
        except:
            bot_username = "your_bot"
        referral_link = f"https://t.me/{bot_username}?start={user_id}"
        
        # Узнаём сколько дней даём за реферала
        from src.config import get_settings
        settings = get_settings()
        bonus_per_referral = settings.referral_bonus_days
        
        text = _("user.referral_info", locale=locale).format(
            link=referral_link,
            count=referrals_count,
            bonus_days=bonus_days,
            bonus_per_friend=bonus_per_referral
        )
        
        keyboard = [
            [
                InlineKeyboardButton(
                    text=_("user_menu.back", locale=locale),
                    callback_data="user:settings"
                )
            ]
        ]
        
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "user:renew")
async def cb_renew(callback: CallbackQuery) -> None:
    """Обработчик 'Продлить доступ' - создает invoice для продления."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        # Используем стандартный период 1 месяц для продления
        from src.config import get_settings
        from src.services.payment_service import create_subscription_invoice
        
        settings = get_settings()
        subscription_months = 1  # По умолчанию продлеваем на 1 месяц
        
        try:
            invoice_link = await create_subscription_invoice(
                bot=callback.message.bot,
                user_id=user_id,
                subscription_months=subscription_months
            )
            
            buttons = [
                [
                    InlineKeyboardButton(
                        text=_("payment.pay_button"),
                        url=invoice_link
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_("user_menu.back"),
                        callback_data="user:menu"
                    )
                ]
            ]
            
            await callback.message.edit_text(
                _("renewal.invoice_created"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
            )
        except Exception as e:
            logger.exception("Error creating renewal invoice")
            await callback.message.edit_text(
                _("renewal.error_creating_invoice"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=_("user_menu.back"),
                        callback_data="user:menu"
                    )
                ]])
            )


@router.callback_query(F.data == "user:resume")
async def cb_resume(callback: CallbackQuery) -> None:
    """Обработчик 'Возобновить доступ' после окончания подписки."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        from src.config import get_settings
        settings = get_settings()
        
        # Перенаправляем на покупку подписки
        buttons = [
            [
                InlineKeyboardButton(
                    text=_("payment.subscription_1month"),
                    callback_data="buy:1"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:menu"
                )
            ]
        ]
        
        await callback.message.edit_text(
            _("renewal.resume_access"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )


@router.callback_query(F.data == "user:buy")
async def cb_buy(callback: CallbackQuery) -> None:
    """Обработчик покупки подписки."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        # Получаем актуальные цены из настроек
        from src.config import get_settings
        settings = get_settings()
        
        # Клавиатура с вариантами подписки и ценами
        buttons = [
            [
                InlineKeyboardButton(
                    text=_("payment.subscription_1month"),
                    callback_data="buy:1"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("payment.subscription_3months"),
                    callback_data="buy:3"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("payment.subscription_6months"),
                    callback_data="buy:6"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("payment.subscription_12months"),
                    callback_data="buy:12"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:connect"
                )
            ]
        ]
        
        await callback.message.edit_text(
            _("payment.choose_subscription"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )


@router.callback_query(F.data.startswith("buy:"))
async def cb_buy_subscription(callback: CallbackQuery) -> None:
    """Обрабатывает покупку подписки - показывает ввод промокода или создает invoice."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    try:
        parts = callback.data.split(":")
        subscription_months = int(parts[1])
        action = parts[2] if len(parts) > 2 else None
        
        # Показываем меню выбора способа оплаты
            # Показываем меню выбора способа оплаты
            i18n = get_i18n()
            with i18n.use_locale(locale):
                months_text = _get_months_text(subscription_months, locale)
                
                buttons = [
                    [
                        InlineKeyboardButton(
                            text=_("payment.payment_method_stars"),
                            callback_data=f"payment:{subscription_months}:stars"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=_("payment.payment_method_sbp"),
                            callback_data=f"payment:{subscription_months}:sbp"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=_("payment.payment_method_card"),
                            callback_data=f"payment:{subscription_months}:card"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=_("user_menu.back"),
                            callback_data="user:buy"
                        )
                    ]
                ]
                
                # Безопасное редактирование - если сообщение фото, удаляем и отправляем новое
                try:
                    await callback.message.edit_text(
                        _("payment.choose_payment_method"),
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                    )
                except Exception:
                    # Если не удалось отредактировать (например, это фото), удаляем и отправляем новое
                    try:
                        await callback.message.delete()
                    except Exception:
                        pass
                    await callback.message.answer(
                        _("payment.choose_payment_method"),
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                    )
    except ValueError as e:
        logger.exception("Invalid subscription months")
        i18n = get_i18n()
        with i18n.use_locale(locale):
            error_markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=_("user_menu.back", locale=locale),
                    callback_data="user:buy"
                )
            ]])
            try:
                await callback.message.edit_text(
                    _("payment.error_creating_invoice", locale=locale),
                    reply_markup=error_markup
                )
            except Exception:
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                await callback.message.answer(
                    _("payment.error_creating_invoice", locale=locale),
                    reply_markup=error_markup
                )
    except Exception as e:
        logger.exception("Failed to create invoice")
        i18n = get_i18n()
        with i18n.use_locale(locale):
            error_markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:buy"
                )
            ]])
            try:
                await callback.message.edit_text(
                    _("payment.error_creating_invoice"),
                    reply_markup=error_markup
                )
            except Exception:
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                await callback.message.answer(
                    _("payment.error_creating_invoice"),
                    reply_markup=error_markup
                )


@router.callback_query(F.data.startswith("payment:"))
async def cb_choose_payment_method(callback: CallbackQuery) -> None:
    """Обработчик выбора способа оплаты после выбора тарифа."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    try:
        # Формат: payment:months:method
        # Примеры: payment:1:stars, payment:3:sbp, payment:6:card
        parts = callback.data.split(":")
        if len(parts) != 3:
            return
        
        subscription_months = int(parts[1])
        payment_method = parts[2]  # stars, sbp, card
        
        i18n = get_i18n()
        with i18n.use_locale(locale):
            if payment_method == "stars":
                # Для Telegram Stars сразу создаем invoice
                from src.services.payment_service import create_subscription_invoice
                
                invoice_link = await create_subscription_invoice(
                    bot=callback.message.bot,
                    user_id=user_id,
                    subscription_months=subscription_months
                )
                
                buttons = [
                    [
                        InlineKeyboardButton(
                            text=_("payment.pay_button"),
                            url=invoice_link
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=_("user_menu.back"),
                            callback_data="user:buy"
                        )
                    ]
                ]
                
                try:
                    await callback.message.edit_text(
                        _("payment.invoice_created"),
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                    )
                except Exception:
                    try:
                        await callback.message.delete()
                    except Exception:
                        pass
                    await callback.message.answer(
                        _("payment.invoice_created"),
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                    )
            elif payment_method in ("sbp", "card"):
                # Создаем платеж через YooKassa
                from src.services.yookassa_service import create_yookassa_payment
                
                payment_data = await create_yookassa_payment(
                    user_id=user_id,
                    subscription_months=subscription_months,
                    payment_method=payment_method
                )
                
                payment_url = payment_data["payment_url"]
                payment_db_id = payment_data["payment_db_id"]
                amount = payment_data["amount"]
                qr_data = payment_data.get("qr_data", payment_url)
                
                # Генерируем QR-код
                from src.services.yookassa_service import generate_qr_code_image
                qr_image = generate_qr_code_image(qr_data)
                qr_file = BufferedInputFile(qr_image.read(), filename="qr_code.png")
                
                # Формируем текст сообщения в зависимости от метода оплаты
                yookassa_payment_id = payment_data.get("payment_id", "")
                if payment_method == "sbp":
                    payment_text = _("payment.yookassa_invoice_created_with_qr").format(
                        months_text=_get_months_text(subscription_months, locale),
                        amount=amount,
                        payment_id=yookassa_payment_id[:12] if yookassa_payment_id else ""
                    )
                else:  # card
                    payment_text = _("payment.yookassa_invoice_created_card").format(
                        months_text=_get_months_text(subscription_months, locale),
                        amount=amount,
                        payment_id=yookassa_payment_id[:12] if yookassa_payment_id else ""
                    )
                
                buttons = [
                    [
                        InlineKeyboardButton(
                            text=_("payment.pay_button"),
                            url=payment_url
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=_("payment.check_status"),
                            callback_data=f"check_payment:{payment_db_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=_("user_menu.back"),
                            callback_data=f"buy:{subscription_months}"
                        )
                    ]
                ]
                
                # Отправляем фото с QR-кодом и текстом
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                await callback.message.answer_photo(
                    photo=qr_file,
                    caption=payment_text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                )
    except (ValueError, IndexError) as e:
        logger.exception("Invalid payment method callback")
        i18n = get_i18n()
        with i18n.use_locale(locale):
            error_markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:buy"
                )
            ]])
            try:
                await callback.message.edit_text(
                    _("payment.error_creating_invoice"),
                    reply_markup=error_markup
                )
            except Exception:
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                await callback.message.answer(
                    _("payment.error_creating_invoice"),
                    reply_markup=error_markup
                )
    except Exception as e:
        logger.exception("Failed to process payment method selection")
        i18n = get_i18n()
        with i18n.use_locale(locale):
            error_markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:buy"
                )
            ]])
            try:
                await callback.message.edit_text(
                    _("payment.error_creating_invoice"),
                    reply_markup=error_markup
                )
            except Exception:
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                await callback.message.answer(
                    _("payment.error_creating_invoice"),
                    reply_markup=error_markup
                )


@router.callback_query(F.data.startswith("yookassa_pay:"))
async def cb_yookassa_pay(callback: CallbackQuery) -> None:
    """Создает платеж YooKassa без промокода."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    try:
        # Формат: yookassa_pay:months:method
        parts = callback.data.split(":")
        subscription_months = int(parts[1])
        payment_method = parts[2]
        
        i18n = get_i18n()
        with i18n.use_locale(locale):
            try:
                from src.services.yookassa_service import create_yookassa_payment
                
                payment_data = await create_yookassa_payment(
                    user_id=user_id,
                    subscription_months=subscription_months,
                    payment_method=payment_method
                )
                
                payment_url = payment_data["payment_url"]
                payment_db_id = payment_data["payment_db_id"]
                amount = payment_data["amount"]
                qr_data = payment_data.get("qr_data", payment_url)
                yookassa_payment_id = payment_data.get("payment_id", "")
                
                # Для СБП показываем QR-код, для карты тоже (из URL)
                from src.services.yookassa_service import generate_qr_code_image
                qr_image = generate_qr_code_image(qr_data)
                qr_file = BufferedInputFile(qr_image.read(), filename="qr_code.png")
                
                # Формируем текст сообщения в зависимости от метода оплаты
                if payment_method == "sbp":
                    payment_text = _("payment.yookassa_invoice_created_with_qr").format(
                        months_text=_get_months_text(subscription_months, locale),
                        amount=amount,
                        payment_id=yookassa_payment_id[:12] if yookassa_payment_id else ""
                    )
                else:  # card
                    payment_text = _("payment.yookassa_invoice_created_card").format(
                        months_text=_get_months_text(subscription_months, locale),
                        amount=amount,
                        payment_id=yookassa_payment_id[:12] if yookassa_payment_id else ""
                    )
                
                buttons = [
                    [
                        InlineKeyboardButton(
                            text=_("payment.pay_button"),
                            url=payment_url
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=_("payment.check_status"),
                            callback_data=f"check_payment:{payment_db_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=_("user_menu.back"),
                            callback_data=f"buy:{subscription_months}"
                        )
                    ]
                ]
                
                # Отправляем фото с QR-кодом и текстом
                await callback.message.delete()  # Удаляем предыдущее сообщение
                await callback.message.answer_photo(
                    photo=qr_file,
                    caption=payment_text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                )
            except Exception as e:
                logger.exception("Failed to create YooKassa payment")
                await callback.message.edit_text(
                    _("payment.error_creating_invoice"),
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(
                            text=_("user_menu.back"),
                            callback_data=f"buy:{subscription_months}"
                        )
                    ]])
                )
    except (ValueError, IndexError) as e:
        logger.exception("Invalid yookassa_pay callback")
        i18n = get_i18n()
        with i18n.use_locale(locale):
            await callback.message.edit_text(
                _("payment.error_creating_invoice"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=_("user_menu.back"),
                        callback_data="user:buy"
                    )
                ]])
            )
    except Exception as e:
        logger.exception("Failed to process yookassa_pay")
        i18n = get_i18n()
        with i18n.use_locale(locale):
            await callback.message.edit_text(
                _("payment.error_creating_invoice"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=_("user_menu.back"),
                        callback_data="user:buy"
                    )
                ]])
            )


async def _safe_edit_or_send(callback: CallbackQuery, text: str, reply_markup=None):
    """Безопасно редактирует сообщение или отправляет новое, если редактирование невозможно."""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        # Если не удалось отредактировать (например, это фото), удаляем и отправляем новое
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(text, reply_markup=reply_markup)


@router.callback_query(F.data.startswith("check_payment:"))
async def cb_check_payment_status(callback: CallbackQuery) -> None:
    """Проверяет статус платежа YooKassa."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    try:
        # Формат: check_payment:payment_db_id
        parts = callback.data.split(":")
        payment_db_id = int(parts[1])
        
        # Получаем платеж из БД
        payment = Payment.get(payment_db_id)
        if not payment:
            i18n = get_i18n()
            with i18n.use_locale(locale):
                await _safe_edit_or_send(
                    callback,
                    _("payment.payment_not_found"),
                    InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(
                            text=_("user_menu.back"),
                            callback_data="user:buy"
                        )
                    ]])
                )
            return
        
        # Проверяем, что платеж принадлежит пользователю
        if payment["user_id"] != user_id:
            i18n = get_i18n()
            with i18n.use_locale(locale):
                await _safe_edit_or_send(
                    callback,
                    _("payment.unauthorized_payment"),
                    InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(
                            text=_("user_menu.back"),
                            callback_data="user:buy"
                        )
                    ]])
                )
            return
        
        # Если платеж уже обработан
        if payment["status"] == "completed":
            i18n = get_i18n()
            with i18n.use_locale(locale):
                buttons = []
                if payment.get("remnawave_user_uuid"):
                    buttons.append([InlineKeyboardButton(
                        text=_("user_menu.my_access"),
                        callback_data="user:my_access"
                    )])
                else:
                    buttons.append([InlineKeyboardButton(
                        text=_("user_menu.back"),
                        callback_data="user:buy"
                    )])
                
                await _safe_edit_or_send(
                    callback,
                    _("payment.already_completed"),
                    InlineKeyboardMarkup(inline_keyboard=buttons)
                )
            return
        
        # Проверяем статус в YooKassa
        yookassa_payment_id = payment.get("yookassa_payment_id")
        if not yookassa_payment_id:
            i18n = get_i18n()
            with i18n.use_locale(locale):
                await _safe_edit_or_send(
                    callback,
                    _("payment.payment_not_found"),
                    InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(
                            text=_("user_menu.back"),
                            callback_data="user:buy"
                        )
                    ]])
                )
            return
        
        from src.services.yookassa_service import check_yookassa_payment_status, process_yookassa_payment
        
        try:
            yookassa_status = await check_yookassa_payment_status(yookassa_payment_id)
            status = yookassa_status["status"]
            paid = yookassa_status.get("paid", False)
            
            i18n = get_i18n()
            with i18n.use_locale(locale):
                if status == "succeeded" and paid:
                    # Платеж успешен - обрабатываем его
                    result = await process_yookassa_payment(yookassa_payment_id, callback.message.bot)
                    
                    if result.get("success"):
                        buttons = []
                        if result.get("subscription_url"):
                            buttons.append([InlineKeyboardButton(
                                text=_("user.get_config"),
                                url=result["subscription_url"]
                            )])
                        buttons.append([InlineKeyboardButton(
                            text=_("user_menu.my_access"),
                            callback_data="user:my_access"
                        )])
                        
                        await _safe_edit_or_send(
                            callback,
                            _("payment.success").format(
                                expire_date=result.get("expire_date", "")[:10] if result.get("expire_date") else _("payment.unknown")
                            ),
                            InlineKeyboardMarkup(inline_keyboard=buttons)
                        )
                    else:
                        await _safe_edit_or_send(
                            callback,
                            _("payment.error_processing"),
                            InlineKeyboardMarkup(inline_keyboard=[[
                                InlineKeyboardButton(
                                    text=_("payment.check_status"),
                                    callback_data=f"check_payment:{payment_db_id}"
                                ),
                                InlineKeyboardButton(
                                    text=_("user_menu.back"),
                                    callback_data="user:buy"
                                )
                            ]])
                        )
                elif status == "pending" or status == "waiting_for_capture":
                    # Платеж в обработке
                    buttons = []
                    if payment.get("yookassa_payment_url"):
                        buttons.append([InlineKeyboardButton(
                            text=_("payment.pay_button"),
                            url=payment["yookassa_payment_url"]
                        )])
                    buttons.append([
                        InlineKeyboardButton(
                            text=_("payment.check_status"),
                            callback_data=f"check_payment:{payment_db_id}"
                        ),
                        InlineKeyboardButton(
                            text=_("user_menu.back"),
                            callback_data="user:buy"
                        )
                    ])
                    
                    await _safe_edit_or_send(
                        callback,
                        _("payment.pending_status").format(status=_("payment.status_pending")),
                        InlineKeyboardMarkup(inline_keyboard=buttons)
                    )
                elif status == "canceled":
                    # Платеж отменен
                    await _safe_edit_or_send(
                        callback,
                        _("payment.canceled_status"),
                        InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(
                                text=_("user_menu.back"),
                                callback_data="user:buy"
                            )
                        ]])
                    )
                else:
                    # Неизвестный статус
                    buttons = []
                    if payment.get("yookassa_payment_url"):
                        buttons.append([InlineKeyboardButton(
                            text=_("payment.pay_button"),
                            url=payment["yookassa_payment_url"]
                        )])
                    buttons.append([
                        InlineKeyboardButton(
                            text=_("payment.check_status"),
                            callback_data=f"check_payment:{payment_db_id}"
                        ),
                        InlineKeyboardButton(
                            text=_("user_menu.back"),
                            callback_data="user:buy"
                        )
                    ])
                    
                    await _safe_edit_or_send(
                        callback,
                        _("payment.unknown_status").format(status=status),
                        InlineKeyboardMarkup(inline_keyboard=buttons)
                    )
        except Exception as e:
            logger.exception("Failed to check YooKassa payment status")
            i18n = get_i18n()
            with i18n.use_locale(locale):
                buttons = []
                if payment.get("yookassa_payment_url"):
                    buttons.append([InlineKeyboardButton(
                        text=_("payment.pay_button"),
                        url=payment["yookassa_payment_url"]
                    )])
                buttons.append([
                    InlineKeyboardButton(
                        text=_("payment.check_status"),
                        callback_data=f"check_payment:{payment_db_id}"
                    ),
                    InlineKeyboardButton(
                        text=_("user_menu.back"),
                        callback_data="user:buy"
                    )
                ])
                
                await _safe_edit_or_send(
                    callback,
                    _("payment.error_checking_status"),
                    InlineKeyboardMarkup(inline_keyboard=buttons)
                )
    except (ValueError, IndexError) as e:
        logger.exception("Invalid check_payment callback")
        i18n = get_i18n()
        with i18n.use_locale(locale):
            await _safe_edit_or_send(
                callback,
                _("payment.error_processing"),
                InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=_("user_menu.back"),
                        callback_data="user:buy"
                    )
                ]])
            )
    except Exception as e:
        logger.exception("Failed to check payment status")
        i18n = get_i18n()
        with i18n.use_locale(locale):
            await _safe_edit_or_send(
                callback,
                _("payment.error_processing"),
                InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=_("user_menu.back"),
                        callback_data="user:buy"
                    )
                ]])
            )


# ==================== ПОДАРОЧНЫЕ ПОДПИСКИ ====================

@router.callback_query(F.data == "user:gift")
async def cb_gift_menu(callback: CallbackQuery) -> None:
    """Меню подарочных подписок."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        buttons = [
            [
                InlineKeyboardButton(
                    text=_("gift.menu_button"),
                    callback_data="gift:buy"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("gift.activate_button"),
                    callback_data="gift:activate"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("gift.my_gifts"),
                    callback_data="gift:my"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:connect"
                )
            ]
        ]
        
        await _safe_edit_or_send(
            callback,
            _("gift.title"),
            InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "gift:buy")
async def cb_gift_buy(callback: CallbackQuery) -> None:
    """Выбор срока подарочной подписки."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        from src.config import settings
        
        buttons = [
            [
                InlineKeyboardButton(
                    text=f"{_('payment.subscription_1month')} — {settings.subscription_rub_1month} ₽",
                    callback_data="gift:period:1"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{_('payment.subscription_3months')} — {settings.subscription_rub_3months} ₽",
                    callback_data="gift:period:3"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{_('payment.subscription_6months')} — {settings.subscription_rub_6months} ₽",
                    callback_data="gift:period:6"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{_('payment.subscription_12months')} — {settings.subscription_rub_12months} ₽",
                    callback_data="gift:period:12"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:gift"
                )
            ]
        ]
        
        await _safe_edit_or_send(
            callback,
            _("gift.choose_period"),
            InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("gift:period:"))
async def cb_gift_period(callback: CallbackQuery) -> None:
    """Выбор способа оплаты для подарка."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    try:
        months = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        return
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        from src.config import settings
        
        # Получаем цены
        rub_prices = {
            1: settings.subscription_rub_1month,
            3: settings.subscription_rub_3months,
            6: settings.subscription_rub_6months,
            12: settings.subscription_rub_12months,
        }
        stars_prices = {
            1: settings.subscription_stars_1month,
            3: settings.subscription_stars_3months,
            6: settings.subscription_stars_6months,
            12: settings.subscription_stars_12months,
        }
        
        rub_price = rub_prices.get(months, 0)
        stars_price = stars_prices.get(months, 0)
        
        buttons = [
            [
                InlineKeyboardButton(
                    text=f"⭐ {stars_price} Stars",
                    callback_data=f"gift:pay:{months}:stars"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"🏦 СБП — {rub_price} ₽",
                    callback_data=f"gift:pay:{months}:sbp"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"💳 Карта — {rub_price} ₽",
                    callback_data=f"gift:pay:{months}:card"
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="gift:buy"
                )
            ]
        ]
        
        await _safe_edit_or_send(
            callback,
            _("gift.choose_payment_method"),
            InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("gift:pay:"))
async def cb_gift_pay(callback: CallbackQuery) -> None:
    """Обработка оплаты подарочной подписки."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    try:
        parts = callback.data.split(":")
        months = int(parts[2])
        payment_method = parts[3]
    except (ValueError, IndexError):
        return
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        from src.config import settings
        
        subscription_days = months * 30
        
        if payment_method == "stars":
            # Для Stars используем процесс похожий на обычную оплату
            from src.services.payment_service import get_stars_amount
            
            stars = get_stars_amount(months)
            
            # Создаем invoice для подарка
            from src.services.payment_service import create_gift_invoice
            
            try:
                invoice_link = await create_gift_invoice(
                    bot=callback.message.bot,
                    user_id=user_id,
                    subscription_months=months
                )
                
                buttons = [
                    [
                        InlineKeyboardButton(
                            text=_("payment.pay_button"),
                            url=invoice_link
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=_("user_menu.back"),
                            callback_data=f"gift:period:{months}"
                        )
                    ]
                ]
                
                await _safe_edit_or_send(
                    callback,
                    _("payment.invoice_created"),
                    InlineKeyboardMarkup(inline_keyboard=buttons),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.exception("Failed to create gift invoice")
                await _safe_edit_or_send(
                    callback,
                    _("gift.error_creating"),
                    InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(
                            text=_("user_menu.back"),
                            callback_data="gift:buy"
                        )
                    ]]),
                    parse_mode="HTML"
                )
        
        elif payment_method in ("sbp", "card"):
            # Создаем платеж через YooKassa для подарка
            from src.services.yookassa_service import create_yookassa_gift_payment, generate_qr_code_image
            
            try:
                payment_data = await create_yookassa_gift_payment(
                    user_id=user_id,
                    subscription_months=months,
                    payment_method=payment_method
                )
                
                payment_url = payment_data["payment_url"]
                payment_db_id = payment_data["payment_db_id"]
                amount = payment_data["amount"]
                qr_data = payment_data.get("qr_data", payment_url)
                yookassa_payment_id = payment_data.get("payment_id", "")
                
                # Генерируем QR-код
                qr_image = generate_qr_code_image(qr_data)
                qr_file = BufferedInputFile(qr_image.read(), filename="qr_code.png")
                
                if payment_method == "sbp":
                    payment_text = _("payment.yookassa_invoice_created_with_qr").format(
                        months_text=_get_months_text(months, locale),
                        amount=amount,
                        payment_id=yookassa_payment_id[:12] if yookassa_payment_id else ""
                    )
                else:
                    payment_text = _("payment.yookassa_invoice_created_card").format(
                        months_text=_get_months_text(months, locale),
                        amount=amount,
                        payment_id=yookassa_payment_id[:12] if yookassa_payment_id else ""
                    )
                
                buttons = [
                    [
                        InlineKeyboardButton(
                            text=_("payment.pay_button"),
                            url=payment_url
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=_("payment.check_status"),
                            callback_data=f"check_gift_payment:{payment_db_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=_("user_menu.back"),
                            callback_data=f"gift:period:{months}"
                        )
                    ]
                ]
                
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                await callback.message.answer_photo(
                    photo=qr_file,
                    caption=payment_text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                )
            except Exception as e:
                logger.exception("Failed to create YooKassa gift payment")
                await _safe_edit_or_send(
                    callback,
                    _("gift.error_creating"),
                    InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(
                            text=_("user_menu.back"),
                            callback_data="gift:buy"
                        )
                    ]]),
                    parse_mode="HTML"
                )


@router.callback_query(F.data == "gift:my")
async def cb_gift_my(callback: CallbackQuery) -> None:
    """Показать мои подарочные коды."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        gifts = GiftCode.get_user_gifts(user_id)
        
        if not gifts:
            text = _("gift.my_gifts_empty")
        else:
            text = f"<b>{_('gift.my_gifts_title')}</b>\n\n"
            for gift in gifts:
                days = gift["subscription_days"]
                created = gift["created_at"][:10] if gift["created_at"] else ""
                
                if gift["status"] == "active":
                    text += _("gift.gift_item_active").format(
                        code=gift["code"],
                        days=days,
                        created=created
                    ) + "\n\n"
                else:
                    activated = gift["activated_at"][:10] if gift["activated_at"] else ""
                    text += _("gift.gift_item_used").format(
                        code=gift["code"],
                        days=days,
                        activated=activated
                    ) + "\n\n"
        
        buttons = [
            [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:gift"
                )
            ]
        ]
        
        await _safe_edit_or_send(
            callback,
            text,
            InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "gift:activate")
async def cb_gift_activate(callback: CallbackQuery) -> None:
    """Начало активации подарочного кода."""
    await callback.answer()
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id, callback.from_user.username)
    locale = user.get("language", "ru")
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        from aiogram.fsm.context import FSMContext
        from aiogram.fsm.state import State, StatesGroup
        
        # Устанавливаем состояние ожидания кода
        # Для простоты используем callback_data с ожиданием сообщения
        buttons = [
            [
                InlineKeyboardButton(
                    text=_("user_menu.back"),
                    callback_data="user:gift"
                )
            ]
        ]
        
        await _safe_edit_or_send(
            callback,
            _("gift.activate_title"),
            InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML"
        )
        
        # Сохраняем состояние ожидания кода
        from src.handlers.state import set_user_state, GIFT_ACTIVATE_STATE
        set_user_state(user_id, GIFT_ACTIVATE_STATE)


@router.message(F.text.regexp(r"^GIFT-[A-Z0-9]{4}-[A-Z0-9]{4}$"))
async def msg_activate_gift_code(message: Message) -> None:
    """Обработка ввода подарочного кода."""
    user_id = message.from_user.id
    user = BotUser.get_or_create(user_id, message.from_user.username)
    locale = user.get("language", "ru")
    
    code = message.text.strip().upper()
    
    i18n = get_i18n()
    with i18n.use_locale(locale):
        # Проверяем код
        gift = GiftCode.get_by_code(code)
        
        if not gift:
            await message.answer(
                _("gift.code_not_found"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=_("user_menu.back"),
                        callback_data="user:gift"
                    )
                ]]),
                parse_mode="HTML"
            )
            return
        
        if gift["status"] != "active":
            await message.answer(
                _("gift.code_already_used"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=_("user_menu.back"),
                        callback_data="user:gift"
                    )
                ]]),
                parse_mode="HTML"
            )
            return
        
        # Проверяем, что пользователь не активирует свой собственный код
        if gift["buyer_id"] == user_id:
            await message.answer(
                _("gift.cannot_activate_own"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=_("user_menu.back"),
                        callback_data="user:gift"
                    )
                ]]),
                parse_mode="HTML"
            )
            return
        
        # Активируем подписку для получателя
        try:
            subscription_days = gift["subscription_days"]
            username = user.get("username") or f"user_{user_id}"
            
            # Проверяем, есть ли уже подписка у пользователя
            existing_uuid = user.get("remnawave_user_uuid")
            
            if existing_uuid:
                # Продлеваем существующую подписку
                try:
                    existing_user = await api_client.get_user(existing_uuid)
                    if existing_user:
                        from datetime import datetime, timedelta
                        current_expire = existing_user.get("expireAt")
                        if current_expire:
                            expire_dt = datetime.fromisoformat(current_expire.replace("Z", "+00:00"))
                            if expire_dt > datetime.now(expire_dt.tzinfo):
                                new_expire = expire_dt + timedelta(days=subscription_days)
                            else:
                                new_expire = datetime.now() + timedelta(days=subscription_days)
                        else:
                            new_expire = datetime.now() + timedelta(days=subscription_days)
                        
                        expire_str = new_expire.replace(microsecond=0).isoformat().replace("+00:00", "Z")
                        if not expire_str.endswith("Z"):
                            expire_str += "Z"
                        
                        await api_client.update_user(existing_uuid, expire_at=expire_str)
                        
                        # Отмечаем код как использованный
                        GiftCode.activate(code, user_id, existing_uuid)
                        
                        await message.answer(
                            _("gift.activation_success").format(expire_date=expire_str[:10]),
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                                InlineKeyboardButton(
                                    text=_("user_menu.my_access"),
                                    callback_data="user:my_access"
                                )
                            ]]),
                            parse_mode="HTML"
                        )
                        return
                except Exception as e:
                    logger.exception("Failed to extend subscription via gift")
            
            # Создаем нового пользователя в Remnawave
            from datetime import datetime, timedelta
            expire_date = (datetime.now() + timedelta(days=subscription_days)).replace(microsecond=0).isoformat() + "Z"
            
            result = await api_client.create_user(
                username=f"gift_{user_id}_{int(datetime.now().timestamp())}",
                expire_at=expire_date,
                telegram_id=user_id
            )
            
            if result and result.get("uuid"):
                new_uuid = result["uuid"]
                BotUser.set_remnawave_uuid(user_id, new_uuid)
                GiftCode.activate(code, user_id, new_uuid)
                
                await message.answer(
                    _("gift.activation_success").format(expire_date=expire_date[:10]),
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(
                            text=_("user_menu.my_access"),
                            callback_data="user:my_access"
                        )
                    ]]),
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    _("gift.activation_failed"),
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(
                            text=_("user_menu.back"),
                            callback_data="user:gift"
                        )
                    ]]),
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.exception("Failed to activate gift code")
            await message.answer(
                _("gift.activation_failed"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=_("user_menu.back"),
                        callback_data="user:gift"
                    )
                ]]),
                parse_mode="HTML"
            )
