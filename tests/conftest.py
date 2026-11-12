import csv
import json
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import pytest

Event = dict[str, Any]

@pytest.fixture
def make_event() -> Callable[..., Event]:
    """
    Создаёт событие с возможностью заменить поля.

    Returns:
        Функция, создающая словарь события
        с возможностью заменить указанные поля.

    """
    def create(**changes: Any) -> Event:
        """
    Создаёт тестовое событие с указанными изменениями полей.

    Args:
        **changes: Именованные поля для замены стандартных значений.

    Returns:
        Словарь одного тестового события.
        """
        event = {
            "timestamp": "2026-11-10T10:00:00+03:00",
            "level": "INFO",
            "source": "api",
            "message": "Сервис запущен",
        }
        event.update(changes)
        return event

    return create


@pytest.fixture
def write_events(tmp_path: Path) -> Callable[..., Path]:
    """
    Записывает события во временный CSV или JSONL.

    Args:
        tmp_path: Путь к временной папке, предоставленной pytest.

    Returns:
        Функция, записывающая события в файл и возвращающая путь к нему.
    """

    def write(
            format_name: str,
            events: Iterable[Event],
            name: str = "events",
    ) -> Path:
        """
        Записывает тестовые события во временный файл.

        Args:
            format_name: Формат файла.
            events: Последовательность словарей событий для записи.
            name: Имя файла без расширения.

        Returns:
            Путь к созданному файлу в виде объекта Path.
        """
        path = tmp_path / f"{name}.{format_name}"

        with path.open("w", encoding="utf-8", newline="") as file:
            if format_name == "csv":
                writer = csv.DictWriter(
                    file,
                    fieldnames=[
                        "timestamp",
                        "level",
                        "source",
                        "message",
                    ],
                )
                writer.writeheader()
                writer.writerows(events)

            else:
                for event in events:
                    file.write(
                        json.dumps(event, ensure_ascii=False) + "\n"
                    )

        return path

    return write