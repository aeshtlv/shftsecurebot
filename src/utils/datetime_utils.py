"""Утилиты для работы с датой и временем."""
from datetime import datetime, timezone


def to_utc_iso(dt: datetime) -> str:
    """
    Преобразует datetime в ISO 8601 формат с Z (UTC).
    
    Примеры:
        >>> to_utc_iso(datetime(2026, 3, 25, 8, 21, 28))
        '2026-03-25T08:21:28Z'
    
    Args:
        dt: datetime объект
        
    Returns:
        Строка в формате ISO 8601 с 'Z'
    """
    # Убираем микросекунды и timezone info для чистого ISO формата
    clean_dt = dt.replace(microsecond=0, tzinfo=None)
    return clean_dt.isoformat() + 'Z'


def utcnow_iso() -> str:
    """
    Возвращает текущее UTC время в ISO 8601 формате с Z.
    
    Returns:
        Строка вида '2026-03-25T08:21:28Z'
    """
    return to_utc_iso(datetime.utcnow())

