import logging

import pytest

from streamstats.errors import InvalidEventError
from streamstats.parsers import parse_csv, parse_jsonl


@pytest.fixture(
    params=[
        ("csv", parse_csv),
        ("jsonl", parse_jsonl),
    ],
    ids=["csv", "jsonl"],
)
def parser_case(request):
    return request.param


def test_reads_valid_events(
    parser_case, make_event, write_events
):
    format_name, parser = parser_case

    expected = [
        make_event(),
        make_event(level="ERROR", source="database"),
    ]
    path = write_events(format_name, expected)

    assert list(parser(path)) == expected


def test_empty_file(parser_case, tmp_path):
    format_name, parser = parser_case

    path = tmp_path / f"empty.{format_name}"
    path.write_text("", encoding="utf-8")

    assert list(parser(path)) == []


def test_csv_header_only(tmp_path):
    path = tmp_path / "header.csv"
    path.write_text(
        "timestamp,level,source,message\n",
        encoding="utf-8",
    )

    assert list(parse_csv(path)) == []


def test_unicode_and_special_characters(
    parser_case, make_event, write_events
):
    format_name, parser = parser_case

    event = make_event(
        source="сервис",
        message='Ошибка, пользователь "Анна" 👋\nПовтор',
    )
    path = write_events(format_name, [event])

    assert list(parser(path)) == [event]


def test_invalid_event_stops(
    parser_case, make_event, write_events
):
    format_name, parser = parser_case

    valid = make_event()
    path = write_events(
        format_name,
        [
            valid,
            make_event(level="WRONG"),
            valid,
        ],
    )

    events = parser(path)

    assert next(events) == valid

    with pytest.raises(InvalidEventError) as caught:
        next(events)

    message = str(caught.value)
    line_number = 3 if format_name == "csv" else 2

    assert str(path) in message
    assert f"строка {line_number}" in message
    assert "WRONG" in message


def test_skip_invalid_counts_and_warns(
    parser_case, make_event, write_events, caplog
):
    format_name, parser = parser_case

    first = make_event()
    last = make_event(level="ERROR", source="database")

    path = write_events(
        format_name,
        [
            first,
            make_event(level="WRONG"),
            last,
        ],
    )
    stats = {"skipped_invalid": 0}

    with caplog.at_level(logging.WARNING):
        events = list(
            parser(
                path,
                skip_invalid=True,
                stats=stats,
            )
        )

    assert events == [first, last]
    assert stats["skipped_invalid"] == 1

    warning_found = False

    for record in caplog.records:
        if record.levelno != logging.WARNING:
            continue

        message = record.getMessage()

        if str(path) in message and "WRONG" in message:
            warning_found = True
            break

    assert warning_found


def test_invalid_timestamp_has_location(
    parser_case, make_event, write_events
):
    format_name, parser = parser_case

    path = write_events(
        format_name,
        [make_event(timestamp="not-a-date")],
    )

    with pytest.raises(InvalidEventError) as caught:
        list(parser(path))

    message = str(caught.value)
    line_number = 2 if format_name == "csv" else 1

    assert str(path) in message
    assert f"строка {line_number}" in message
    assert "not-a-date" in message


@pytest.mark.parametrize("skip_invalid", [False, True])
def test_broken_json(
    skip_invalid, make_event, write_events, caplog
):
    path = write_events("jsonl", [make_event()])
    valid_line = path.read_text(encoding="utf-8")

    path.write_text(
        valid_line + '{"level":\n' + valid_line,
        encoding="utf-8",
    )

    stats = {"skipped_invalid": 0}

    if skip_invalid:
        with caplog.at_level(logging.WARNING):
            events = list(
                parse_jsonl(
                    path,
                    skip_invalid=True,
                    stats=stats,
                )
            )

        assert events == [make_event(), make_event()]
        assert stats["skipped_invalid"] == 1
        assert str(path) in caplog.text
        assert "строка 2" in caplog.text

    else:
        with pytest.raises(InvalidEventError) as caught:
            list(parse_jsonl(path))

        assert str(path) in str(caught.value)
        assert "строка 2" in str(caught.value)


def test_broken_csv(tmp_path):
    path = tmp_path / "broken.csv"
    path.write_text(
        "timestamp,level,source,message\n"
        '2026-11-10T10:00:00+03:00,INFO,api,"unfinished',
        encoding="utf-8",
    )

    with pytest.raises(InvalidEventError) as caught:
        list(parse_csv(path))

    assert str(path) in str(caught.value)
    assert "строка" in str(caught.value)