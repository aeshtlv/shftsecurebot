# Удаление промокодов

Необходимо вручную удалить из `src/handlers/user_public.py`:

1. Функцию `cb_promo_input` (строки ~917-944)
2. Функцию `handle_promo_code` (строки ~947-1130)
3. Функцию `cb_apply_promo` (строки ~1133-1189)
4. Все упоминания `promo_code` в других функциях
5. Все кнопки "Ввести промокод" и "Пропустить промокод"
6. Упростить `cb_buy_subscription` - убрать логику промокодов

Также нужно:
- Удалить `promo_code=None` из вызовов `create_subscription_invoice` и `create_yookassa_payment`
- Упростить логику в `cb_buy_subscription` - сразу создавать invoice без промокодов
- Убрать все кнопки промокодов из интерфейса

