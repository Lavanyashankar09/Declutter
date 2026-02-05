"""
Calendar Generator Module
Takes Claude's processed calendar events and saves as jCal (RFC 7265) format.
"""

import json
import os
from datetime import datetime

from .llm_processor import ProcessedResult


class CalendarGenerator:
    """Generates jCal format calendar from processed events."""

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir
        self.calendar_dir = os.path.join(output_dir, "calendar")

    def generate(self, result: ProcessedResult) -> str:
        """Generate jCal JSON file from calendar events."""

        # Create output directory
        os.makedirs(self.calendar_dir, exist_ok=True)

        # Build jCal structure (RFC 7265)
        jcal = self._build_jcal(result.calendar_events)

        # Save to file
        filepath = os.path.join(self.calendar_dir, "events.json")
        with open(filepath, "w") as f:
            json.dump(jcal, f, indent=2)

        print(f"Created: {filepath} ({len(result.calendar_events)} events)")
        return filepath

    def _build_jcal(self, events: list) -> list:
        """
        Build jCal structure per RFC 7265.

        jCal format:
        ["vcalendar", [properties], [components]]

        Each component:
        ["vevent", [properties], [sub-components]]

        Each property:
        ["propname", {params}, "type", value]
        """

        # Calendar properties
        cal_props = [
            ["version", {}, "text", "2.0"],
            ["prodid", {}, "text", "-//Desktop Declutter Agent//EN"],
            ["calscale", {}, "text", "GREGORIAN"],
        ]

        # Build event components
        components = []
        for i, event in enumerate(events):
            vevent = self._build_vevent(event, i)
            components.append(vevent)

        return ["vcalendar", cal_props, components]

    def _build_vevent(self, event: dict, index: int) -> list:
        """Build a single vevent component in jCal format."""

        date_str = event.get("date", "")
        time_str = event.get("time")
        title = event.get("title", "Untitled")
        description = event.get("description", "")
        source = event.get("source_file", "")

        # Build datetime
        if time_str:
            dt_str = f"{date_str}T{time_str}:00"
            dt_type = "date-time"
        else:
            dt_str = date_str
            dt_type = "date"

        # Generate UID
        uid = f"event-{index}-{date_str}@desktop-declutter"

        # Build properties
        props = [
            ["uid", {}, "text", uid],
            ["summary", {}, "text", title],
            ["dtstart", {}, dt_type, dt_str],
        ]

        if description:
            props.append(["description", {}, "text", description])

        if source:
            props.append(["x-source-file", {}, "text", source])

        # Created timestamp
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        props.append(["dtstamp", {}, "date-time", now])

        return ["vevent", props, []]


def test_generator():
    """Test the calendar generator."""
    from .file_parser import FileParser
    from .llm_processor import LLMProcessor

    # Parse and process
    parser = FileParser("./desktop")
    files = parser.parse_all_files()

    processor = LLMProcessor()
    result = processor.process_all(files)

    # Generate calendar
    generator = CalendarGenerator("./output")
    filepath = generator.generate(result)

    print("\n" + "=" * 60)
    print("CALENDAR GENERATION COMPLETE")
    print("=" * 60)

    # Show sample
    with open(filepath) as f:
        jcal = json.load(f)

    events = jcal[2]  # components array
    print(f"Total events: {len(events)}")
    print("\nSample events:")
    for event in events[:3]:
        props = {p[0]: p[3] for p in event[1]}
        print(f"  {props.get('dtstart', '?')}: {props.get('summary', '?')}")


if __name__ == "__main__":
    test_generator()
