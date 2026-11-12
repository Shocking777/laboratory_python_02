import csv
import json
from pathlib import Path
from typing import Any

Report = dict[str, Any]

def report(data: Report, output: str | Path) -> None:
    """
    Сохраняет готовую статистику в JSON-файл.

    Args:
        data: Словарь статистики событий.
        output: Путь к выходному JSON-файлу.

    Returns:
        None.
    """
    with open(output,"w",encoding="utf-8") as file:
        json.dump(data,file,ensure_ascii=False,indent=4,sort_keys=True)


def report_csv(data: Report, output: str | Path) -> None:
    """
    Сохраняет готовую статистику в CSV-файл.

    Args:
        data: Словарь статистики событий.
        output: Путь к выходному CSV-файлу.

    Returns:
        None.

    """
    with open(output, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)

        writer.writerow(["section", "name", "value"])

        writer.writerow(["summary", "total_events", data["total_events"]])
        writer.writerow(["summary", "skipped_invalid", data["skipped_invalid"]])
        writer.writerow(["summary", "first_timestamp", data["mn"]])
        writer.writerow(["summary", "last_timestamp", data["mx"]])

        for level, count in data["by_level"].items():
            writer.writerow(["by_level", level, count])

        for source, count in data["by_source"].items():
            writer.writerow(["by_source", source, count])

        for source, count in data["by_error"].items():
            writer.writerow(["by_error", source, count])

        for source, count in data["top_5"]:
            writer.writerow(["top_5", source, count])




