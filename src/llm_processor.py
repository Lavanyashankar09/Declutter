"""
LLM Processor Module
Sends all parsed content to Claude and gets structured output.
"""

import json
import os
from dataclasses import dataclass

from anthropic import Anthropic

from .file_parser import ParsedFile


@dataclass
class ProcessedResult:
    """Result from Claude processing."""

    topics: list[str]
    calendar_events: list[dict]
    notes: list[dict]  # notes organized by topic (Claude decides topics)


class LLMProcessor:
    """Processes all content using Claude API."""

    PROMPT = """You are organizing a messy desktop folder into a structured knowledge system.

Below are contents from multiple files. READ EACH FILE CAREFULLY and extract ALL meaningful information.

## STEP 1: DEEPLY ANALYZE EACH FILE

For EVERY file, look for:
- Main content and summaries
- Comments (# comments, // comments, /* comments */, <!-- comments -->)
- TODOs, FIXMEs, action items, tasks
- Dates, meetings, deadlines, appointments
- Ideas, tips, notes, references
- Hidden info in code comments or file metadata

Don't skip anything valuable. A code file might have important TODOs in comments.
A log file might have human notes. A CSV might have a notes column. READ EVERYTHING.

## STEP 2: DISCOVER TOPICS (STRICT LIMIT: 5-7 TOPICS ONLY)

CRITICAL: You MUST create EXACTLY 5-7 topics. NO MORE THAN 7. NO EXCEPTIONS.
If you find more than 7 natural categories, MERGE related ones together.

Merge strategy:
- "technical" + "development" + "infrastructure" → pick ONE name
- "tasks" + "work" → merge into ONE
- "ideas" + "projects" → merge into ONE

YOU decide the topic names - whatever fits the actual content best.
Examples: "work", "technical", "personal", "ideas", "learning", "meetings", etc.

BEFORE returning JSON, COUNT your topics. If more than 7, GO BACK AND MERGE.

## STEP 3: EXTRACT AND CLASSIFY

For each piece of information:

CALENDAR EVENT (has specific date/time):
- Meetings: "Team sync on Feb 14 at 2pm"
- Deadlines: "Project due March 10"
- Appointments: "Dentist Feb 20 10:30am"
- Conferences: "Tech Summit March 15-17"
→ Extract: date (YYYY-MM-DD), time (HH:MM or null), title, description, source_file

NOTE (everything else):
- Ideas, thoughts, reflections
- Technical tips, references
- Action items, tasks, TODOs
- Book/article recommendations
- Personal reminders
→ Extract: topic, content, tags, source_file

## STEP 4: RETURN JSON ONLY

{
  "topics": ["topic1", "topic2", ...],
  "calendar_events": [
    {"date": "2025-02-14", "time": "14:30", "title": "Team sync", "description": "Weekly standup", "source_file": "meeting_notes.md"}
  ],
  "notes": [
    {"topic": "technical", "content": "Use PgBouncer for connection pooling", "tags": ["database", "optimization"], "source_file": "notes.md"}
  ]
}

CRITICAL RULES:
- Return ONLY valid JSON, no extra text before or after
- Every item MUST have source_file
- Extract ALL calendar events - convert dates like "Feb 14" to "2025-02-14"
- Extract ALL meaningful content - don't summarize too much, keep useful details
- For multi-line content, preserve the key information

=== FILE CONTENTS ===

"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required")
        self.client = Anthropic(api_key=self.api_key)

    def process_all(self, parsed_files: list[ParsedFile]) -> ProcessedResult:
        """Process all parsed files with Claude."""

        # First, process images with Claude Vision
        image_descriptions = {}
        image_files = [pf for pf in parsed_files if pf.file_type == "image"]

        if image_files:
            print(f"Processing {len(image_files)} images with Claude Vision...")
            for pf in image_files:
                desc = self.process_image(pf)
                image_descriptions[pf.filename] = desc.get(
                    "description", "No description"
                )
                print(f"  → {pf.filename}: {desc.get('description', '')[:50]}...")

        # Build the full prompt with all file contents
        prompt = self.PROMPT

        for pf in parsed_files:
            if pf.file_type == "image":
                # Include image description from Vision analysis
                prompt += f"\n--- FILE: {pf.filename} ---\n"
                prompt += (
                    f"[IMAGE] {image_descriptions.get(pf.filename, 'Image file')}\n"
                )
            else:
                prompt += f"\n--- FILE: {pf.filename} ---\n"
                prompt += pf.content + "\n"

        print(f"Sending {len(parsed_files)} files to Claude...")
        print(f"Total prompt size: {len(prompt):,} characters")

        # Call Claude API
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse response
        response_text = response.content[0].text
        print(f"Response received: {len(response_text):,} characters")

        # Extract JSON from response
        try:
            # Find JSON in response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response was: {response_text[:500]}...")
            raise

        return ProcessedResult(
            topics=data.get("topics", []),
            calendar_events=data.get("calendar_events", []),
            notes=data.get("notes", []),
        )

    def process_image(self, parsed_file: ParsedFile) -> dict:
        """Process an image file with Claude Vision."""

        if not parsed_file.image_base64:
            return {"description": "No image data"}

        # Extract base64 data
        base64_data = parsed_file.image_base64.split(",")[1]
        media_type = parsed_file.image_base64.split(";")[0].split(":")[1]

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Briefly describe this image in 1-2 sentences. Is it a photo, screenshot, document, or something else?",
                        },
                    ],
                }
            ],
        )

        return {"description": response.content[0].text}


def test_processor():
    """Test the LLM processor."""
    from .file_parser import FileParser

    # Parse files
    parser = FileParser("./desktop")
    files = parser.parse_all_files()

    print("=" * 60)
    print("LLM PROCESSOR TEST")
    print("=" * 60)

    # Process with Claude
    processor = LLMProcessor()
    result = processor.process_all(files)

    print(f"\nTopics discovered: {result.topics}")
    print(f"Calendar events: {len(result.calendar_events)}")
    print(f"Notes: {len(result.notes)}")

    # Show sample
    print("\n--- Sample Calendar Events ---")
    for event in result.calendar_events[:3]:
        print(f"  {event['date']} {event.get('time', '')}: {event['title']}")

    print("\n--- Notes by Topic ---")
    # Group notes by topic
    by_topic = {}
    for note in result.notes:
        topic = note.get("topic", "uncategorized")
        by_topic.setdefault(topic, []).append(note)

    for topic, notes in by_topic.items():
        print(f"\n  [{topic}] - {len(notes)} notes")
        for note in notes[:2]:
            print(f"    • {note['content'][:60]}...")


if __name__ == "__main__":
    test_processor()
