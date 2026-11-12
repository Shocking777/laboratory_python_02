from datetime import datetime
from typing import Any

from .errors import InvalidEventError, InvalidTimestampError

Event = dict[str, Any]

def validate_event(event: Event) -> None:
    """
    Проверяет обязательные поля и значения одного события.

    Args:
        event: Словарь одного события.

    Returns:
        None.
    """
    if not isinstance(event, dict):
        raise InvalidEventError("Событие должно быть словарём")

    required_fields = ("timestamp", "level", "source", "message")

    for field in required_fields:
        if field not in event:
            raise InvalidEventError(f"Отсутствует обязательное поле: {field}")

    level = event["level"]

    if not isinstance(level, str):
        raise InvalidEventError("Поле level должно быть строкой")

    allowed_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

    if level not in allowed_levels:
        raise InvalidEventError(f"Недопустимый уровень события: {level}")

    timestamp = event["timestamp"]

    if not isinstance(timestamp, str):
        raise InvalidTimestampError("Поле timestamp должно быть строкой")

    try:
        datetime.fromisoformat(timestamp)
    except ValueError as error:
        raise InvalidTimestampError(f"Некорректная временная метка: {timestamp}") from error

    source = event["source"]

    if not isinstance(source, str):
        raise InvalidEventError("Поле source должно быть строкой")

    if not source:
        raise InvalidEventError("Поле source не может быть пустым")

    if not isinstance(event["message"], str):
        raise InvalidEventError("Поле message должно быть строкой")

