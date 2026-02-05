"""
Random code snippets I keep reusing.
Cleaning this up is a TODO for... someday.
"""

# TODO: turn this into a proper CLI tool
# TODO: add type hints throughout

import json
import csv
from datetime import datetime

# Quick date parser I use all the time
# REMINDER: daylight saving time switch on March 9 2025 - check if this breaks anything
def parse_flexible_date(date_str):
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

# CSV to JSON converter
# NOTE: used this for the data migration last month
# TODO: handle encoding issues (got bitten by UTF-8 BOM last time)
def csv_to_json(csv_path, json_path):
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        data = list(reader)
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)

# HACK: quick retry wrapper, should use tenacity library instead
# TODO: add exponential backoff
# TODO: make max_retries configurable
def retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed: {e}")

# Birthday reminder: get a gift for Jake's birthday party on March 2, 2025
# He's into mechanical keyboards and board games
