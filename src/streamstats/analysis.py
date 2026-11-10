from collections import Counter


def analyze_events(events):
    total_events = 0

    by_level = Counter({
        "DEBUG": 0,
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0,
        "CRITICAL": 0,
    })

    by_source = Counter()

    for event in events:
        total_events += 1

        level = event["level"]
        source = event["source"]

        by_level[level] += 1
        by_source[source] += 1

    return {
        "total_events": total_events,
        "by_level": dict(by_level),
        "by_source": dict(by_source),
    }