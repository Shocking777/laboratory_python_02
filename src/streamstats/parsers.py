import csv
import json
import logging
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

from .errors import InvalidEventError, UnsupportedFormatError
from .models import validate_event

Event = dict[str, Any]
Stats = dict[str, int]

logger = logging.getLogger(__name__)

def parse_csv(path: str | Path,
skip_invalid: bool = False,
stats: Stats | None = None,
delimiter: str = ",") -> Iterator[Event]:
    """
    Читает CSV-файл с заголовком и проверяет его.

    Args:
        path: Путь к входному CSV-файлу.
        skip_invalid: Флаг пропуска событий с неверными полями.
        stats: Общий словарь со счётчиком skipped_invalid.
        delimiter: Символ разделителя полей. По умолчанию — запятая.

    Yields:
        Словари корректных событий.

    """
    with open(path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(
            file,
            delimiter=delimiter,
            strict=True,
        )

        try:
            for event in reader:
                try:
                    validate_event(event)

                except InvalidEventError as error:
                    message = f"{path}: строка {reader.line_num}: {error}"

                    if skip_invalid:
                        logger.warning(message)

                        if stats is not None:
                            stats["skipped_invalid"] += 1

                        continue

                    raise InvalidEventError(message) from error

                yield event

        except csv.Error as error:
            raise InvalidEventError(
                f"{path}: строка {reader.line_num}: {error}"
            ) from error

def parse_tsv(path: str | Path,
skip_invalid: bool = False,
stats: Stats | None = None) -> Iterator[Event]:
    """
    Читает TSV-файл

    Args:
        path: Путь к входному TSV-файлу.
        skip_invalid: Флаг пропуска событий с неверными полями.
        stats: Общий словарь со счётчиком skipped_invalid.

    Yields:
        Словари корректных событий.

    """
    yield from parse_csv(
        path,
        skip_invalid=skip_invalid,
        stats=stats,
        delimiter="\t",
    )

def parse_jsonl(path: str | Path,
skip_invalid: bool = False,
stats: Stats | None = None) -> Iterator[Event]:
    """
    Читает JSONL-файл и проверяет его.

    Args:
        path: Путь к входному JSON-файлу.
        skip_invalid: Флаг пропуска событий с неверными полями.
        stats: Общий словарь со счётчиком skipped_invalid.

    Yields:
        Словари корректных событий.

    """
    with open(path, "r", encoding="utf-8") as file:
        for line_number, row in enumerate(file, start=1):
            try:
                event = json.loads(row)
                validate_event(event)

            except (json.JSONDecodeError, InvalidEventError) as error:
                message = f"{path}: строка {line_number}: {error}"

                if skip_invalid:
                    logger.warning(message)

                    if stats is not None:
                        stats["skipped_invalid"] += 1

                    continue

                raise InvalidEventError(message) from error

            yield event


PARSERS = {
    "csv": parse_csv,
    "jsonl": parse_jsonl,
}

Parser = Callable[..., Iterator[Event]]

def register_parser(format_name: str, parser: Parser) -> None:
    """
    Регистрирует функцию парсера для указанного формата.

    Args:
        format_name: Название формата
        parser: Функция чтения событий этого формата.

    Returns:
        None.

    """
    PARSERS[format_name] = parser


def get_parser(format_name: str) -> Parser:
    """
    Получает зарегистрированный парсер по названию формата.

    Args:
        format_name: Название входного формата.

    Returns:
        Функция парсера для указанного формата.

    """
    try:
        return PARSERS[format_name]
    except KeyError as error:
        raise UnsupportedFormatError(
            f"Неподдерживаемый формат: {format_name}"
        ) from error

register_parser("tsv", parse_tsv)