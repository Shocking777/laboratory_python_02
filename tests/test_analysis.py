from itertools import chain

import pytest

from streamstats.analysis import analyze_events
from streamstats.errors import InvalidEventError
from streamstats.parsers import parse_csv, parse_jsonl


def test_empty_events():
    report = analyze_events(iter(()))

    assert report["total_events"] == 0
    assert report["by_source"] == {}
    assert report["by_error"] == {}
    assert report["top_5"] == []
    assert report["mn"] is None
    assert report["mx"] is None
    assert all(count == 0 for count in report["by_level"].values())


def test_levels_and_sources(make_event):
    events = [
        make_event(level="INFO", source="api"),
        make_event(level="ERROR", source="database"),
        make_event(level="CRITICAL", source="database"),
        make_event(level="DEBUG", source="api"),
        make_event(level="WARNING", source="auth"),
    ]

    report = analyze_events(iter(events))

    assert report["total_events"] == 5
    assert report["by_level"] == {
        "DEBUG": 1,
        "INFO": 1,
        "WARNING": 1,
        "ERROR": 1,
        "CRITICAL": 1,
    }
    assert report["by_source"] == {
        "api": 2,
        "database": 2,
        "auth": 1,
    }
    assert report["by_error"] == {"database": 2}


def test_first_and_last_timestamp(make_event):
    events = [
        make_event(timestamp="2026-11-10T10:00:00+03:00"),
        make_event(timestamp="2026-11-12T10:00:00+03:00"),
        make_event(timestamp="2026-11-09T10:00:00+03:00"),
    ]

    report = analyze_events(iter(events))

    assert report["mn"] == "2026-11-09T10:00:00+03:00"
    assert report["mx"] == "2026-11-12T10:00:00+03:00"


def test_timestamps_with_different_offsets(make_event):
    events = [
        make_event(timestamp="2026-11-10T10:00:00+03:00"),
        make_event(timestamp="2026-11-10T08:00:00+00:00"),
    ]

    report = analyze_events(iter(events))

    assert report["mn"] == "2026-11-10T10:00:00+03:00"
    assert report["mx"] == "2026-11-10T08:00:00+00:00"


def test_top_error_sources_ignore_other_levels(make_event):
    events = []

    for index, count in enumerate((6, 5, 4, 3, 2, 1), start=1):
        for number in range(count):
            level = "ERROR" if number % 2 == 0 else "CRITICAL"
            events.append(
                make_event(level=level, source=f"source-{index}")
            )


    events.extend(
        make_event(level="INFO", source="noisy")
        for _ in range(30)
    )

    report = analyze_events(iter(events))

    assert report["top_5"] == [
        ("source-1", 6),
        ("source-2", 5),
        ("source-3", 4),
        ("source-4", 3),
        ("source-5", 2),
    ]
    assert "noisy" not in report["by_error"]


def test_unicode(make_event):
    events = [
        make_event(level="WARNING", source="сервис"),
        make_event(level="ERROR", source="база данных"),
    ]

    report = analyze_events(iter(events))

    assert report["by_source"]["сервис"] == 1
    assert report["by_source"]["база данных"] == 1
    assert report["by_error"] == {"база данных": 1}


@pytest.mark.parametrize(
    ("format_name", "parser"),
    [
        ("csv", parse_csv),
        ("jsonl", parse_jsonl),
    ],
)
def test_multiple_files(format_name, parser, make_event, write_events):
    first = write_events(
        format_name,
        [make_event(level="INFO", source="api")],
        name="first",
    )
    second = write_events(
        format_name,
        [
            make_event(level="ERROR", source="database"),
            make_event(level="CRITICAL", source="api"),
        ],
        name="second",
    )

    events = chain(parser(first), parser(second))
    report = analyze_events(events)

    assert report["total_events"] == 3
    assert report["by_source"] == {"api": 2, "database": 1}
    assert report["by_error"] == {"database": 1, "api": 1}


@pytest.mark.parametrize(
    ("format_name", "parser"),
    [
        ("csv", parse_csv),
        ("jsonl", parse_jsonl),
    ],
)
def test_invalid_event_stops_analysis(
    format_name, parser, make_event, write_events
):
    path = write_events(
        format_name,
        [make_event(), make_event(level="WRONG")],
    )

    with pytest.raises(InvalidEventError, match="WRONG"):
        analyze_events(parser(path))


@pytest.mark.parametrize(
    ("format_name", "parser"),
    [
        ("csv", parse_csv),
        ("jsonl", parse_jsonl),
    ],
)
def test_invalid_event_is_skipped(
    format_name, parser, make_event, write_events
):
    path = write_events(
        format_name,
        [
            make_event(level="INFO"),
            make_event(level="WRONG"),
            make_event(level="ERROR", source="database"),
        ],
    )
    stats = {"skipped_invalid": 0}

    events = parser(path, skip_invalid=True, stats=stats)
    report = analyze_events(events)

    assert report["total_events"] == 2
    assert stats["skipped_invalid"] == 1
    assert report["by_level"]["INFO"] == 1
    assert report["by_level"]["ERROR"] == 1
    assert "WRONG" not in report["by_level"]
    assert report["by_error"] == {"database": 1}