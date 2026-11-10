import csv
import json

import csv

from .models import validate_event


def parse_csv(path):
    with open(path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for event in reader:
            validate_event(event)
            yield event


def parse_jsonl(path):
    with open(path, "r", encoding="utf-8") as file:
        for row in file:
            event = json.loads(row)
            validate_event(event)
            yield event