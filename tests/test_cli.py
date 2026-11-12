import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from streamstats.__main__ import app

runner = CliRunner()

VALID_CSV = (
    "timestamp,level,source,message\n"
    "2026-11-10T10:00:00+03:00,INFO,api,Started\n"
    "2026-11-10T10:01:00+03:00,ERROR,database,Failed\n"
)

MIXED_CSV = (
    "timestamp,level,source,message\n"
    "2026-11-10T10:00:00+03:00,INFO,api,Started\n"
    "2026-11-10T10:01:00+03:00,WRONG,api,Broken\n"
    "2026-11-10T10:02:00+03:00,ERROR,database,Failed\n"
)

VALID_JSONL = json.dumps(
    {
        "timestamp": "2026-11-10T10:00:00+03:00",
        "level": "INFO",
        "source": "api",
        "message": "Started",
    }
) + "\n"

UNICODE_JSONL = json.dumps(
    {
        "timestamp": "2026-11-10T10:00:00+03:00",
        "level": "WARNING",
        "source": "сервис",
        "message": "Предупреждение",
    },
    ensure_ascii=False,
) + "\n"


@pytest.fixture
def make_file(tmp_path):
    def create(name, content):
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
        return path

    return create


def test_help():
    src = Path(__file__).resolve().parents[1] / "src"

    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(src) + os.pathsep + env.get("PYTHONPATH", "")
    )
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    result = subprocess.run(
        [sys.executable, "-m", "streamstats", "--help"],
        check=False,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "analyze" in result.stdout


def test_analyze_writes_report(make_file, tmp_path):
    source = make_file("events.jsonl", VALID_JSONL)
    report_path = tmp_path / "report.json"

    result = runner.invoke(
        app,
        [
            "analyze",
            str(source),
            "--format", "jsonl",
            "--output", str(report_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert report_path.exists()

    report = json.loads(
        report_path.read_text(encoding="utf-8")
    )

    assert report["total_events"] == 1
    assert report["by_source"]["api"] == 1
    assert report["by_level"]["INFO"] == 1
    assert report["skipped_invalid"] == 0
    assert "Отчёт сохранён" in result.stdout


def test_invalid_line_exits_with_code_2(make_file, tmp_path):
    source = make_file("events.csv", MIXED_CSV)
    report_path = tmp_path / "report.json"

    result = runner.invoke(
        app,
        [
            "analyze",
            str(source),
            "--format", "csv",
            "--output", str(report_path),
        ],
    )

    assert result.exit_code == 2, result.output
    assert str(source) in result.stderr
    assert "строка 3" in result.stderr
    assert "WRONG" in result.stderr
    assert "Отчёт сохранён" not in result.stdout
    assert not report_path.exists()


def test_skip_invalid_records_skipped_lines(
    make_file, tmp_path, caplog
):
    source = make_file("events.csv", MIXED_CSV)
    report_path = tmp_path / "report.json"


    with caplog.at_level("WARNING"):
        result = runner.invoke(
            app,
            [
                "analyze",
                str(source),
                "--format", "csv",
                "--output", str(report_path),
                "--skip-invalid",
            ],
        )

    assert result.exit_code == 0, result.output
    assert "строка 3" in caplog.text
    assert "WRONG" in caplog.text
    assert any(
        record.levelname == "WARNING"
        for record in caplog.records
    )

    report = json.loads(
        report_path.read_text(encoding="utf-8")
    )

    assert report["total_events"] == 2
    assert report["skipped_invalid"] == 1
    assert report["by_level"]["INFO"] == 1
    assert report["by_level"]["ERROR"] == 1
    assert "WRONG" not in report["by_level"]


def test_multiple_files(make_file, tmp_path):
    first = make_file("one.csv", VALID_CSV)

    second = make_file(
        "two.csv",
        "timestamp,level,source,message\n"
        "2026-11-10T11:00:00+03:00,CRITICAL,auth,Expired\n",
    )

    report_path = tmp_path / "report.json"

    result = runner.invoke(
        app,
        [
            "analyze",
            str(first),
            str(second),
            "--format", "csv",
            "--output", str(report_path),
        ],
    )

    assert result.exit_code == 0, result.output

    report = json.loads(
        report_path.read_text(encoding="utf-8")
    )

    assert report["total_events"] == 3
    assert report["skipped_invalid"] == 0
    assert report["by_level"]["CRITICAL"] == 1

    assert report["by_source"] == {
        "api": 1,
        "database": 1,
        "auth": 1,
    }

    assert {
        source for source, count in report["top_5"]
    } == {"database", "auth"}


def test_unicode_report(make_file, tmp_path):
    source = make_file("events.jsonl", UNICODE_JSONL)
    report_path = tmp_path / "report.json"

    result = runner.invoke(
        app,
        [
            "analyze",
            str(source),
            "--format", "jsonl",
            "--output", str(report_path),
        ],
    )

    assert result.exit_code == 0, result.output

    raw_report = report_path.read_text(encoding="utf-8")

    assert "сервис" in raw_report

    report = json.loads(raw_report)

    assert report["by_source"]["сервис"] == 1
    assert report["by_level"]["WARNING"] == 1


def test_missing_input_is_a_configuration_error(tmp_path):
    source = tmp_path / "missing.csv"
    report_path = tmp_path / "report.json"

    result = runner.invoke(
        app,
        [
            "analyze",
            str(source),
            "--format", "csv",
            "--output", str(report_path),
        ],
    )

    assert result.exit_code == 2, result.output
    assert result.stderr
    assert not report_path.exists()


def test_unsupported_format_on_the_command_line(
    make_file, tmp_path
):
    source = make_file("events.csv", VALID_CSV)
    report_path = tmp_path / "report.json"

    result = runner.invoke(
        app,
        [
            "analyze",
            str(source),
            "--format", "xml",
            "--output", str(report_path),
        ],
    )

    assert result.exit_code == 2, result.output
    assert "xml" in result.stderr
    assert not report_path.exists()