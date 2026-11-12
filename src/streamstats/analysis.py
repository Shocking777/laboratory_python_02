from collections import Counter
from collections.abc import Iterable, Iterator
from datetime import datetime
from typing import Any

from .errors import CLIConfigError

Event = dict[str, Any]
Report = dict[str, Any]

def analyze_events(events: Iterable[Event]) -> Report:
    """
    Подсчитывает статистику событий за один проход.

    Args:
        events: Последовательность словарей событий.

    Returns:
        Словарь с общим количеством событий, счётчиками по уровням
        и источникам, счётчиками ошибок, топ-5 источников ошибок
        и минимальной и максимальной временными метками.
    """
    total_events = 0

    by_level = Counter({
        "DEBUG": 0,
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0,
        "CRITICAL": 0,
    })

    by_source = Counter()

    by_error = Counter()

    mx = None
    mn = None


    for event in events:
        total_events += 1

        level = event["level"]
        source = event["source"]
        date = datetime.fromisoformat(event["timestamp"])

        by_level[level] += 1
        by_source[source] += 1

        if level in ("ERROR", "CRITICAL"):
            by_error[source] += 1

        if mx is None or date > mx:
            mx = date

        if mn is None or date < mn:
            mn = date

    top_5 = by_error.most_common(5)


    return {
        "total_events": total_events,
        "by_level": dict(by_level),
        "by_source": dict(by_source),
        "by_error": dict(by_error),
        "top_5": top_5,
        "mn": mn.isoformat() if mn is not None else None,
        "mx": mx.isoformat() if mx is not None else None,
    }

def filter_events(events: Iterable[Event],
level: str | None = None,
source: str | None = None,
from_time: datetime | None = None,
to_time: datetime | None = None) -> Iterator[Event]:
    """
    Лениво фильтрует события по уровню, источнику и времени.

    Args:
        events: Поток событий, представленных словарями.
        level: Уровень событий для отбора.
        source: Источник событий для отбора.
        from_time: Начало диапазона времени включительно.
        to_time: Конец диапазона времени включительно.

    Yields:
        Словари событий, соответствующих всем заданным условиям.
    """
    for boundary in (from_time, to_time):
        if boundary is not None and boundary.tzinfo is None:
            raise CLIConfigError(
                "Укажи часовой пояс в границе времени, например +03:00"
            )

    if (
        from_time is not None
        and to_time is not None
        and from_time > to_time
    ):
        raise CLIConfigError(
            "--from-time не может быть позже --to-time"
        )

    for event in events:
        if level is not None and event["level"] != level:
            continue

        if source is not None and event["source"] != source:
            continue

        if from_time is not None or to_time is not None:
            timestamp = datetime.fromisoformat(event["timestamp"])

            if timestamp.tzinfo is None:
                raise CLIConfigError(
                    "Для фильтра по времени события должны "
                    "содержать часовой пояс"
                )

            if from_time is not None and timestamp < from_time:
                continue

            if to_time is not None and timestamp > to_time:
                continue

        yield event