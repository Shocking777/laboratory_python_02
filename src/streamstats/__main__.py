from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer

from .analysis import analyze_events, filter_events
from .errors import StreamStatsError
from .parsers import get_parser
from .report import report, report_csv

app = typer.Typer()


class EventLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ReportFormat(str, Enum):
    json = "json"
    csv = "csv"


@app.callback()
def main():
    """
    Предоставляет интерфейс командной строки для анализа событий.

    Returns:
        None.
    """


@app.command()
def analyze(
    inputs: Annotated[
        list[Path],
        typer.Argument(exists=True, dir_okay=False),
    ],
    format: Annotated[
        str,
        typer.Option("--format", help="Формат входных файлов"),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", help="Путь выходного отчёта"),
    ],
    skip_invalid: Annotated[
        bool,
        typer.Option("--skip-invalid", help="Пропускать неверные строки"),
    ] = False,
    level: Annotated[
        EventLevel | None,
        typer.Option("--level", help="Оставить события указанного уровня"),
    ] = None,
    source: Annotated[
        str | None,
        typer.Option("--source", help="Оставить события указанного источника"),
    ] = None,
    from_time: Annotated[
        datetime | None,
        typer.Option(
            "--from-time",
            formats=["%Y-%m-%dT%H:%M:%S%z"],
            help="Начало диапазона включительно",
        ),
    ] = None,
    to_time: Annotated[
        datetime | None,
        typer.Option(
            "--to-time",
            formats=["%Y-%m-%dT%H:%M:%S%z"],
            help="Конец диапазона включительно",
        ),
    ] = None,
    report_format: Annotated[
        ReportFormat,
        typer.Option("--report-format", help="Формат выходного отчёта"),
    ] = ReportFormat.json,
):
    """
    Потоково анализирует события и сохраняет отчет.

    Args:
        inputs: Пути к входным файлам.
        format: Название зарегистрированного входного формата.
        output: Путь, куда сохранить отчёт.
        skip_invalid: Флаг пропуска неверных записей.
        level: Уровень событий для фильтрации.
        source: Источник событий для фильтрации.
        from_time: Начало диапазона включительно.
        to_time: Конец диапазона включительно.
        report_format: Формат выходного отчёта

    Returns:
        None.

    """
    stats = {"skipped_invalid": 0}

    try:
        parser = get_parser(format)

        events = (
            event
            for path in inputs
            for event in parser(
                path,
                skip_invalid=skip_invalid,
                stats=stats,
            )
        )

        filtered = filter_events(
            events,
            level=level.value if level is not None else None,
            source=source,
            from_time=from_time,
            to_time=to_time,
        )

        data = analyze_events(filtered)

        data = {
            "total_events": data["total_events"],
            "skipped_invalid": stats["skipped_invalid"],
            **{
                key: value
                for key, value in data.items()
                if key != "total_events"
            },
        }

        if report_format == ReportFormat.csv:
            report_csv(data, output)
        else:
            report(data, output)

    except StreamStatsError as error:
        typer.echo(f"Ошибка: {error}", err=True)
        raise typer.Exit(code=2) from error

    typer.echo(f"Отчёт сохранён: {output}")


if __name__ == "__main__":
    app()