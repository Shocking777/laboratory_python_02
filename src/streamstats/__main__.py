from .analysis import analyze_events
from .parsers import parse_csv, parse_jsonl


def main():
    csv_events = parse_csv("streamstats/events.csv")
    jsonl_events = parse_jsonl("streamstats/events.jsonl")

    print("CSV:", analyze_events(csv_events))
    print("JSONL:", analyze_events(jsonl_events))


if __name__ == "__main__":
    main()