"""База данных для пользователей бота и рефералов."""
import secrets
import sqlite3
import string
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
# Используем директорию data для хранения БД (монтируется через volume в Docker)
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)  # Создаем директорию, если её нет
DB_PATH = DATA_DIR / "bot_data.db"


@contextmanager
def get_db_connection():
    """Контекстный менеджер для работы с БД."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Инициализирует базу данных."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Таблица пользователей бота
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                language TEXT DEFAULT 'ru',
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                trial_used BOOLEAN DEFAULT 0,
                referrer_id INTEGER,
                remnawave_user_uuid TEXT,
                auto_renewal BOOLEAN DEFAULT 0,
                last_renewal_notification TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES bot_users(telegram_id)
            )
        """)
        
        # Миграция: добавляем поля автопродления, если их нет
        try:
            cursor.execute("ALTER TABLE bot_users ADD COLUMN auto_renewal BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Колонка уже существует
        
        try:
            cursor.execute("ALTER TABLE bot_users ADD COLUMN last_renewal_notification TIMESTAMP")
        except sqlite3.OperationalError:
            pass  # Колонка уже существует
        
        # Миграция: добавляем поля системы лояльности
        try:
            cursor.execute("ALTER TABLE bot_users ADD COLUMN loyalty_points INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE bot_users ADD COLUMN loyalty_status TEXT DEFAULT 'bronze'")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE bot_users ADD COLUMN total_spent INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        
        # Таблица рефералов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                bonus_days INTEGER DEFAULT 0,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES bot_users(telegram_id),
                FOREIGN KEY (referred_id) REFERENCES bot_users(telegram_id),
                UNIQUE(referrer_id, referred_id)
            )
        """)
        
        # Таблица платежей (Telegram Stars и YooKassa)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                stars INTEGER,
                amount_rub INTEGER,
                status TEXT DEFAULT 'pending',
                remnawave_user_uuid TEXT,
                invoice_payload TEXT,
                subscription_days INTEGER,
                payment_method TEXT DEFAULT 'stars',
                yookassa_payment_id TEXT,
                yookassa_payment_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES bot_users(telegram_id)
            )
        """)
        
        # Миграция: добавляем новые поля для YooKassa, если их нет
        try:
            cursor.execute("ALTER TABLE payments ADD COLUMN amount_rub INTEGER")
        except sqlite3.OperationalError:
            pass  # Колонка уже существует
        
        try:
            cursor.execute("ALTER TABLE payments ADD COLUMN payment_method TEXT DEFAULT 'stars'")
        except sqlite3.OperationalError:
            pass  # Колонка уже существует
        
        try:
            cursor.execute("ALTER TABLE payments ADD COLUMN yookassa_payment_id TEXT")
        except sqlite3.OperationalError:
            pass  # Колонка уже существует
        
        try:
            cursor.execute("ALTER TABLE payments ADD COLUMN yookassa_payment_url TEXT")
        except sqlite3.OperationalError:
            pass  # Колонка уже существует
        
        # Таблица подарочных кодов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gift_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                buyer_id INTEGER NOT NULL,
                subscription_days INTEGER NOT NULL,
                stars INTEGER DEFAULT 0,
                amount_rub INTEGER DEFAULT 0,
                payment_method TEXT DEFAULT 'stars',
                status TEXT DEFAULT 'active',
                recipient_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                activated_at TIMESTAMP,
                remnawave_user_uuid TEXT,
                FOREIGN KEY (buyer_id) REFERENCES bot_users(telegram_id),
                FOREIGN KEY (recipient_id) REFERENCES bot_users(telegram_id)
            )
        """)
        
        # Индекс для быстрого поиска по коду
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_gift_codes_code ON gift_codes(code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_gift_codes_buyer ON gift_codes(buyer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_gift_codes_status ON gift_codes(status)")


class BotUser:
    """Модель пользователя бота."""
    
    @staticmethod
    def get_or_create(telegram_id: int, username: Optional[str] = None) -> dict:
        """Получает или создает пользователя."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM bot_users WHERE telegram_id = ?",
                (telegram_id,)
            )
            user = cursor.fetchone()
            
            if user:
                return dict(user)
            
            # Создаем нового пользователя
            cursor.execute("""
                INSERT INTO bot_users (telegram_id, username)
                VALUES (?, ?)
            """, (telegram_id, username))
            
            cursor.execute(
                "SELECT * FROM bot_users WHERE telegram_id = ?",
                (telegram_id,)
            )
            return dict(cursor.fetchone())
    
    @staticmethod
    def update_language(telegram_id: int, language: str):
        """Обновляет язык пользователя."""
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE bot_users SET language = ? WHERE telegram_id = ?",
                (language, telegram_id)
            )
    
    @staticmethod
    def set_trial_used(telegram_id: int):
        """Отмечает пробную подписку как использованную."""
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE bot_users SET trial_used = 1 WHERE telegram_id = ?",
                (telegram_id,)
            )
    
    @staticmethod
    def set_referrer(telegram_id: int, referrer_id: int):
        """Устанавливает реферера для пользователя."""
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE bot_users SET referrer_id = ? WHERE telegram_id = ?",
                (referrer_id, telegram_id)
            )
    
    @staticmethod
    def set_remnawave_uuid(telegram_id: int, uuid: str):
        """Сохраняет UUID пользователя в Remnawave."""
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE bot_users SET remnawave_user_uuid = ? WHERE telegram_id = ?",
                (uuid, telegram_id)
            )
    
    @staticmethod
    def set_auto_renewal(telegram_id: int, enabled: bool):
        """Включает или выключает автопродление."""
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE bot_users SET auto_renewal = ? WHERE telegram_id = ?",
                (1 if enabled else 0, telegram_id)
            )
    
    @staticmethod
    def get_auto_renewal(telegram_id: int) -> bool:
        """Получает статус автопродления."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT auto_renewal FROM bot_users WHERE telegram_id = ?",
                (telegram_id,)
            )
            row = cursor.fetchone()
            return bool(row[0]) if row and row[0] is not None else False
    
    @staticmethod
    def update_last_renewal_notification(telegram_id: int):
        """Обновляет время последнего напоминания об автопродлении."""
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE bot_users SET last_renewal_notification = ? WHERE telegram_id = ?",
                (datetime.now().isoformat(), telegram_id)
            )
    
    @staticmethod
    def get_users_with_auto_renewal():
        """Получает всех пользователей с включенным автопродлением."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT telegram_id, username, remnawave_user_uuid, auto_renewal, last_renewal_notification
                FROM bot_users
                WHERE remnawave_user_uuid IS NOT NULL AND auto_renewal = 1
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    @staticmethod
    def get_all_user_ids() -> list[int]:
        """Получает ID всех пользователей бота."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT telegram_id FROM bot_users")
            return [row[0] for row in cursor.fetchall()]
    
    @staticmethod
    def get_users_with_subscription() -> list[int]:
        """Получает ID пользователей с активной подпиской (есть remnawave_user_uuid)."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT telegram_id FROM bot_users 
                WHERE remnawave_user_uuid IS NOT NULL
            """)
            return [row[0] for row in cursor.fetchall()]
    
    @staticmethod
    def get_users_without_subscription() -> list[int]:
        """Получает ID пользователей без подписки."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT telegram_id FROM bot_users 
                WHERE remnawave_user_uuid IS NULL
            """)
            return [row[0] for row in cursor.fetchall()]
    
    @staticmethod
    def get_user_count() -> dict:
        """Получает количество пользователей по категориям."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM bot_users")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM bot_users WHERE remnawave_user_uuid IS NOT NULL")
            with_sub = cursor.fetchone()[0]
            
            return {
                'total': total,
                'with_subscription': with_sub,
                'without_subscription': total - with_sub
            }


class Referral:
    """Модель реферальной программы."""
    
    @staticmethod
    def create(referrer_id: int, referred_id: int, bonus_days: int = 0):
        """Создает реферальную запись."""
        with get_db_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO referrals (referrer_id, referred_id, bonus_days)
                    VALUES (?, ?, ?)
                """, (referrer_id, referred_id, bonus_days))
                return True
            except sqlite3.IntegrityError:
                # Уже существует
                return False
    
    @staticmethod
    def get_referrals_count(referrer_id: int) -> int:
        """Получает количество рефералов."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM referrals WHERE referrer_id = ?",
                (referrer_id,)
            )
            return cursor.fetchone()[0]
    
    @staticmethod
    def get_bonus_days(referrer_id: int) -> int:
        """Получает общее количество бонусных дней от рефералов."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT SUM(bonus_days) FROM referrals WHERE referrer_id = ?",
                (referrer_id,)
            )
            result = cursor.fetchone()[0]
            return result if result else 0
    
    @staticmethod
    def grant_bonus(referrer_id: int, referred_id: int, bonus_days: int) -> bool:
        """Начисляет бонусные дни за реферала (обновляет запись)."""
        with get_db_connection() as conn:
            conn.execute("""
                UPDATE referrals 
                SET bonus_days = bonus_days + ?
                WHERE referrer_id = ? AND referred_id = ?
            """, (bonus_days, referrer_id, referred_id))
            return conn.total_changes > 0
    
    @staticmethod
    def update_bonus_days(referrer_id: int, referred_id: int, bonus_days: int):
        """Обновляет количество бонусных дней за реферала."""
        with get_db_connection() as conn:
            conn.execute("""
                UPDATE referrals 
                SET bonus_days = ?
                WHERE referrer_id = ? AND referred_id = ?
            """, (bonus_days, referrer_id, referred_id))


class Payment:
    """Модель платежа."""
    
    @staticmethod
    def create(
        user_id: int, 
        stars: int = 0,
        amount_rub: int = 0,
        invoice_payload: str = "",
        subscription_days: int = 0,
        remnawave_user_uuid: Optional[str] = None,
        payment_method: str = "stars",
        yookassa_payment_id: Optional[str] = None,
        yookassa_payment_url: Optional[str] = None
    ) -> int:
        """Создает запись о платеже."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO payments (user_id, stars, amount_rub, remnawave_user_uuid, invoice_payload, 
                                     subscription_days, payment_method, yookassa_payment_id, yookassa_payment_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, stars, amount_rub, remnawave_user_uuid, invoice_payload, subscription_days, 
                  payment_method, yookassa_payment_id, yookassa_payment_url))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_payload(invoice_payload: str) -> Optional[dict]:
        """Получает платеж по invoice payload."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM payments WHERE invoice_payload = ?", (invoice_payload,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def update_status(payment_id: int, status: str, remnawave_uuid: Optional[str] = None):
        """Обновляет статус платежа."""
        with get_db_connection() as conn:
            completed_at = datetime.now().isoformat() if status == "completed" else None
            if remnawave_uuid:
                conn.execute("""
                    UPDATE payments 
                    SET status = ?, completed_at = ?, remnawave_user_uuid = ?
                    WHERE id = ?
                """, (status, completed_at, remnawave_uuid, payment_id))
            else:
                conn.execute("""
                    UPDATE payments 
                    SET status = ?, completed_at = ?
                    WHERE id = ?
                """, (status, completed_at, payment_id))
    
    @staticmethod
    def get(payment_id: int) -> Optional[dict]:
        """Получает платеж по ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_by_yookassa_id(yookassa_payment_id: str) -> Optional[dict]:
        """Получает платеж по YooKassa payment ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM payments WHERE yookassa_payment_id = ?", (yookassa_payment_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def update_yookassa_payment(payment_id: int, yookassa_payment_id: str, yookassa_payment_url: str):
        """Обновляет информацию о платеже YooKassa."""
        with get_db_connection() as conn:
            conn.execute("""
                UPDATE payments 
                SET yookassa_payment_id = ?, yookassa_payment_url = ?
                WHERE id = ?
            """, (yookassa_payment_id, yookassa_payment_url, payment_id))
    
    @staticmethod
    def get_user_payments(user_id: int, limit: int = 20) -> list:
        """Получает историю платежей пользователя."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, stars, amount_rub, status, subscription_days, 
                       payment_method, created_at, completed_at
                FROM payments 
                WHERE user_id = ? AND status = 'completed'
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_user_stats(user_id: int) -> dict:
        """Получает статистику платежей пользователя."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_payments,
                    SUM(CASE WHEN amount_rub > 0 THEN amount_rub ELSE 0 END) as total_rub,
                    SUM(CASE WHEN stars > 0 THEN stars ELSE 0 END) as total_stars,
                    SUM(subscription_days) as total_days
                FROM payments 
                WHERE user_id = ? AND status = 'completed'
            """, (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'total_payments': row['total_payments'] or 0,
                    'total_rub': row['total_rub'] or 0,
                    'total_stars': row['total_stars'] or 0,
                    'total_days': row['total_days'] or 0
                }
            return {'total_payments': 0, 'total_rub': 0, 'total_stars': 0, 'total_days': 0}


class GiftCode:
    """Модель подарочного кода."""
    
    @staticmethod
    def generate_code() -> str:
        """Генерирует уникальный подарочный код формата GIFT-XXXX-XXXX."""
        chars = string.ascii_uppercase + string.digits
        # Исключаем похожие символы (0, O, I, L, 1)
        chars = chars.replace('0', '').replace('O', '').replace('I', '').replace('L', '').replace('1', '')
        part1 = ''.join(secrets.choice(chars) for _ in range(4))
        part2 = ''.join(secrets.choice(chars) for _ in range(4))
        return f"GIFT-{part1}-{part2}"
    
    @staticmethod
    def create(
        buyer_id: int,
        subscription_days: int,
        stars: int = 0,
        amount_rub: int = 0,
        payment_method: str = "stars"
    ) -> Optional[dict]:
        """Создает подарочный код после успешной оплаты."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Генерируем уникальный код
            for _ in range(10):  # Максимум 10 попыток
                code = GiftCode.generate_code()
                try:
                    cursor.execute("""
                        INSERT INTO gift_codes (code, buyer_id, subscription_days, stars, amount_rub, payment_method)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (code, buyer_id, subscription_days, stars, amount_rub, payment_method))
                    
                    cursor.execute("SELECT * FROM gift_codes WHERE id = ?", (cursor.lastrowid,))
                    return dict(cursor.fetchone())
                except sqlite3.IntegrityError:
                    continue  # Код уже существует, генерируем новый
            
            return None  # Не удалось создать код
    
    @staticmethod
    def get_by_code(code: str) -> Optional[dict]:
        """Получает подарочный код по коду."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Нормализуем код (убираем пробелы, приводим к верхнему регистру)
            normalized_code = code.strip().upper()
            cursor.execute("SELECT * FROM gift_codes WHERE code = ?", (normalized_code,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def activate(code: str, recipient_id: int, remnawave_uuid: str) -> bool:
        """Активирует подарочный код для получателя."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            normalized_code = code.strip().upper()
            
            # Проверяем, что код существует и активен
            cursor.execute(
                "SELECT id, status FROM gift_codes WHERE code = ?",
                (normalized_code,)
            )
            row = cursor.fetchone()
            
            if not row:
                return False
            
            if row['status'] != 'active':
                return False
            
            # Активируем код
            cursor.execute("""
                UPDATE gift_codes 
                SET status = 'used', recipient_id = ?, activated_at = ?, remnawave_user_uuid = ?
                WHERE code = ?
            """, (recipient_id, datetime.now().isoformat(), remnawave_uuid, normalized_code))
            
            return cursor.rowcount > 0
    
    @staticmethod
    def get_user_gifts(buyer_id: int) -> list:
        """Получает все подарочные коды, купленные пользователем."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM gift_codes WHERE buyer_id = ? ORDER BY created_at DESC",
                (buyer_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_active_gifts(buyer_id: int) -> list:
        """Получает активные (неиспользованные) подарочные коды пользователя."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM gift_codes WHERE buyer_id = ? AND status = 'active' ORDER BY created_at DESC",
                (buyer_id,)
            )
            return [dict(row) for row in cursor.fetchall()]


class Loyalty:
    """Система лояльности."""
    
    # Пороги для статусов (в баллах, 1 балл = 1 рубль)
    # Быстрый старт: Silver после 1 покупки 3мес+, Gold после 1 года, Platinum после 2.5 лет
    THRESHOLDS = {
        'bronze': 0,
        'silver': 250,
        'gold': 1000,
        'platinum': 2500
    }
    
    # Скидки для каждого статуса и периода (в рублях)
    # Базовые цены: 1мес=129, 3мес=299, 6мес=549, 12мес=999
    DISCOUNTS = {
        'bronze': {30: 0, 90: 0, 180: 0, 365: 0},
        'silver': {30: 10, 90: 20, 180: 30, 365: 50},      # ~5%
        'gold': {30: 14, 90: 30, 180: 60, 365: 100},       # ~10%
        'platinum': {30: 20, 90: 50, 180: 90, 365: 150}    # ~15%
    }
    
    # Названия статусов с эмодзи
    STATUS_NAMES = {
        'bronze': '🥉 Bronze',
        'silver': '🥈 Silver',
        'gold': '🥇 Gold',
        'platinum': '💎 Platinum'
    }
    
    @staticmethod
    def get_user_loyalty(telegram_id: int) -> dict:
        """Получает данные лояльности пользователя."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT loyalty_points, loyalty_status, total_spent FROM bot_users WHERE telegram_id = ?",
                (telegram_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'points': row['loyalty_points'] or 0,
                    'status': row['loyalty_status'] or 'bronze',
                    'total_spent': row['total_spent'] or 0
                }
            return {'points': 0, 'status': 'bronze', 'total_spent': 0}
    
    @staticmethod
    def add_points(telegram_id: int, amount_rub: int) -> dict:
        """Добавляет баллы за покупку и обновляет статус."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Получаем текущие данные
            cursor.execute(
                "SELECT loyalty_points, total_spent FROM bot_users WHERE telegram_id = ?",
                (telegram_id,)
            )
            row = cursor.fetchone()
            current_points = (row['loyalty_points'] or 0) if row else 0
            total_spent = (row['total_spent'] or 0) if row else 0
            
            # Добавляем баллы (1 рубль = 1 балл)
            new_points = current_points + amount_rub
            new_total_spent = total_spent + amount_rub
            
            # Определяем новый статус
            new_status = 'bronze'
            for status, threshold in sorted(Loyalty.THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
                if new_points >= threshold:
                    new_status = status
                    break
            
            # Обновляем в БД
            cursor.execute("""
                UPDATE bot_users 
                SET loyalty_points = ?, loyalty_status = ?, total_spent = ?
                WHERE telegram_id = ?
            """, (new_points, new_status, new_total_spent, telegram_id))
            conn.commit()
            
            return {
                'points': new_points,
                'status': new_status,
                'total_spent': new_total_spent,
                'previous_status': row['loyalty_status'] if row and row['loyalty_status'] else 'bronze'
            }
    
    @staticmethod
    def get_discount(telegram_id: int, days: int) -> int:
        """Получает скидку в рублях для пользователя на указанный период."""
        loyalty = Loyalty.get_user_loyalty(telegram_id)
        status = loyalty['status']
        
        # Находим ближайший подходящий период
        available_days = sorted(Loyalty.DISCOUNTS[status].keys())
        discount_days = days
        for d in available_days:
            if d >= days:
                discount_days = d
                break
        else:
            discount_days = available_days[-1]
        
        return Loyalty.DISCOUNTS[status].get(discount_days, 0)
    
    @staticmethod
    def get_discounted_price(base_price: int, telegram_id: int, days: int) -> tuple[int, int]:
        """Возвращает цену со скидкой и размер скидки."""
        discount = Loyalty.get_discount(telegram_id, days)
        discounted_price = max(base_price - discount, 0)
        return discounted_price, discount
    
    @staticmethod
    def get_next_status_info(telegram_id: int) -> dict | None:
        """Получает информацию о следующем статусе."""
        loyalty = Loyalty.get_user_loyalty(telegram_id)
        current_status = loyalty['status']
        current_points = loyalty['points']
        
        statuses = ['bronze', 'silver', 'gold', 'platinum']
        current_idx = statuses.index(current_status)
        
        if current_idx >= len(statuses) - 1:
            return None  # Уже максимальный статус
        
        next_status = statuses[current_idx + 1]
        points_needed = Loyalty.THRESHOLDS[next_status] - current_points
        
        return {
            'next_status': next_status,
            'next_status_name': Loyalty.STATUS_NAMES[next_status],
            'points_needed': points_needed
        }
    
    @staticmethod
    def get_status_name(status: str) -> str:
        """Возвращает название статуса с эмодзи."""
        return Loyalty.STATUS_NAMES.get(status, '🥉 Bronze')

