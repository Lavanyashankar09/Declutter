"""
Smart Extractor Module
Pre-processes large/machine-generated files to extract only meaningful content
before sending to Claude.

This module handles:
- api-test-9-25.log: Scans for human comments in 10,001 lines
- api_responses_sample.json: Skips (machine-generated)
- system_logs.txt: Extracts only warnings/errors/human comments
- dependencies_audit.csv: Extracts only "notes" column
"""

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExtractedContent:
    """Result of smart extraction."""

    filename: str
    meaningful_content: str
    original_size: int  # in bytes
    extracted_size: int  # in bytes
    items_found: int
    should_skip: bool = False
    skip_reason: str = ""


class SmartExtractor:
    """Extracts only meaningful content from problematic files."""

    # Patterns that indicate human-written content in logs
    HUMAN_PATTERNS = [
        r"#\s*(NOTE|TODO|FIXME|REMINDER|XXX)",  # Comment markers
        r"need to",
        r"don\'t forget",
        r"remember to",
        r"should (be|have|fix|check|update)",
        r"follow up",
        r"ask \w+",
        r"check with",
        r"waiting on",
        r"blocked by",
    ]

    def __init__(self):
        self.human_pattern = re.compile("|".join(self.HUMAN_PATTERNS), re.IGNORECASE)

    def extract_from_log(self, filepath: str) -> ExtractedContent:
        """
        Extract human comments from a large log file.
        Scans ALL lines but only keeps meaningful ones.
        """
        path = Path(filepath)
        original_size = path.stat().st_size

        meaningful_lines = []
        line_count = 0

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                line_count += 1

                # Check if line contains human content
                if self.human_pattern.search(line):
                    meaningful_lines.append(f"Line {line_num}: {line.strip()}")

        if meaningful_lines:
            content = f"=== Human Comments Found in {path.name} ===\n"
            content += f"(Scanned {line_count:,} lines, found {len(meaningful_lines)} with human content)\n\n"
            content += "\n".join(meaningful_lines)
        else:
            content = f"=== {path.name} ===\n"
            content += f"(Scanned {line_count:,} lines, no human comments found)\n"
            content += "This appears to be pure machine-generated logs."

        return ExtractedContent(
            filename=path.name,
            meaningful_content=content,
            original_size=original_size,
            extracted_size=len(content.encode("utf-8")),
            items_found=len(meaningful_lines),
        )

    def extract_from_csv_notes(self, filepath: str) -> ExtractedContent:
        """
        Extract only the 'notes' column from a CSV file.
        Scans ALL rows but only keeps notes.
        """
        path = Path(filepath)
        original_size = path.stat().st_size

        notes = []
        row_count = 0

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []

            # Find notes-like columns
            note_columns = [
                h
                for h in headers
                if h.lower() in ["notes", "note", "comments", "comment", "description"]
            ]

            for row in reader:
                row_count += 1
                for col in note_columns:
                    value = row.get(col, "").strip()
                    if value:
                        # Include some context (first column value usually)
                        context = row.get(headers[0], "") if headers else ""
                        notes.append(f"- [{context}] {value}")

        if notes:
            content = f"=== Notes from {path.name} ===\n"
            content += f"(Scanned {row_count} rows, found {len(notes)} notes)\n\n"
            content += "\n".join(notes)
        else:
            content = f"=== {path.name} ===\n"
            content += f"(Scanned {row_count} rows, no notes column found)\n"
            content += f"Columns: {', '.join(headers)}"

        return ExtractedContent(
            filename=path.name,
            meaningful_content=content,
            original_size=original_size,
            extracted_size=len(content.encode("utf-8")),
            items_found=len(notes),
        )

    def extract_from_system_logs(self, filepath: str) -> ExtractedContent:
        """
        Extract only warnings, errors, and human comments from system logs.
        """
        path = Path(filepath)
        original_size = path.stat().st_size

        important_lines = []
        line_count = 0

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                line_count += 1

                # Keep warnings, errors, and human comments
                if any(
                    pattern in line.upper()
                    for pattern in ["[WARN", "[ERROR", "[FATAL", "[CRITICAL"]
                ):
                    important_lines.append(f"Line {line_num}: {line.strip()}")
                elif self.human_pattern.search(line):
                    important_lines.append(f"Line {line_num} (human): {line.strip()}")

        if important_lines:
            content = f"=== Important Items from {path.name} ===\n"
            content += f"(Scanned {line_count} lines, found {len(important_lines)} important)\n\n"
            content += "\n".join(important_lines)
        else:
            content = f"=== {path.name} ===\n"
            content += f"(Scanned {line_count} lines, all normal INFO logs)\n"
            content += "No warnings, errors, or human comments found."

        return ExtractedContent(
            filename=path.name,
            meaningful_content=content,
            original_size=original_size,
            extracted_size=len(content.encode("utf-8")),
            items_found=len(important_lines),
        )

    def extract_from_json(self, filepath: str) -> ExtractedContent:
        """
        Extract useful information from JSON file.
        """
        path = Path(filepath)
        original_size = path.stat().st_size

        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return ExtractedContent(
                    filename=path.name,
                    meaningful_content="Invalid JSON file",
                    original_size=original_size,
                    extracted_size=0,
                    items_found=0,
                )

        content = f"=== Extracted from {path.name} ===\n\n"
        items_found = 0

        # Handle API snapshots format
        if "snapshots" in data and isinstance(data.get("snapshots"), list):
            # Metadata
            if "test_snapshots" in data:
                meta = data["test_snapshots"]
                content += "--- Metadata ---\n"
                content += f"Description: {meta.get('description', 'N/A')}\n"
                content += f"Environment: {meta.get('environment', 'N/A')}\n"
                content += f"Generated: {meta.get('generated_at', 'N/A')}\n\n"

            # API Endpoints
            content += "--- API Endpoints ---\n"
            for snapshot in data["snapshots"]:
                endpoint = snapshot.get("endpoint", "")
                status = snapshot.get("status", "")
                content += f"- {endpoint} [{status}]\n"
                items_found += 1

            # Roles (if present)
            for snapshot in data["snapshots"]:
                if snapshot.get("endpoint") == "GET /api/roles":
                    content += "\n--- Roles Defined ---\n"
                    roles = snapshot.get("response", {}).get("data", [])
                    for role in roles:
                        content += f"- {role.get('name')}: {role.get('description')} ({role.get('user_count')} users)\n"

            # Error codes (if present)
            content += "\n--- Error Codes ---\n"
            for snapshot in data["snapshots"]:
                resp = snapshot.get("response", {})
                if isinstance(resp, dict) and "error" in resp:
                    err = resp["error"]
                    content += f"- {err.get('code')}: {err.get('message')}\n"

            # Health check
            for snapshot in data["snapshots"]:
                if snapshot.get("endpoint") == "GET /api/health":
                    content += "\n--- Health Check Info ---\n"
                    resp = snapshot.get("response", {})
                    content += f"Version: {resp.get('version')}\n"
                    checks = resp.get("checks", {})
                    for service, info in checks.items():
                        content += f"- {service}: {info.get('status')} ({info.get('latency_ms')}ms)\n"

            # Permissions structure
            for snapshot in data["snapshots"]:
                resp = snapshot.get("response", {})
                if isinstance(resp, dict):
                    user_data = resp.get("data", {})
                    if isinstance(user_data, dict) and "permissions" in user_data:
                        content += "\n--- Permissions Structure ---\n"
                        perms = user_data.get("permissions", [])
                        content += f"Permissions: {', '.join(perms)}\n"
                        break

        # Handle generic dict
        elif isinstance(data, dict):
            content += f"Type: Object with {len(data)} keys\n"
            content += f"Keys: {', '.join(list(data.keys())[:10])}\n\n"
            content += "--- Full Content ---\n"
            content += json.dumps(data, indent=2)
            items_found = len(data)

        # Handle array
        elif isinstance(data, list):
            content += f"Type: Array with {len(data)} items\n"
            content += "--- Full Content ---\n"
            content += json.dumps(data, indent=2)
            items_found = len(data)

        return ExtractedContent(
            filename=path.name,
            meaningful_content=content,
            original_size=original_size,
            extracted_size=len(content.encode("utf-8")),
            items_found=items_found,
        )


def test_extractor():
    """Test the smart extractor on the problematic files."""

    extractor = SmartExtractor()
    desktop_path = Path("./desktop")

    print("=" * 60)
    print("SMART EXTRACTOR TEST")
    print("=" * 60)

    # Test 1: Big log file
    print("\n" + "-" * 60)
    print("FILE: api-test-9-25.log")
    print("-" * 60)
    result = extractor.extract_from_log(desktop_path / "api-test-9-25.log")
    print(f"Original: {result.original_size:,} bytes")
    print(f"Extracted: {result.extracted_size:,} bytes")
    print(f"\nContent:\n{result.meaningful_content}")

    # Test 2: System logs
    print("\n" + "-" * 60)
    print("FILE: system_logs.txt")
    print("-" * 60)
    result = extractor.extract_from_system_logs(desktop_path / "system_logs.txt")
    print(f"Original: {result.original_size:,} bytes")
    print(f"Extracted: {result.extracted_size:,} bytes")
    print(f"\nContent:\n{result.meaningful_content}")

    # Test 3: JSON
    print("\n" + "-" * 60)
    print("FILE: api_responses_sample.json")
    print("-" * 60)
    result = extractor.extract_from_json(desktop_path / "api_responses_sample.json")
    print(f"Original: {result.original_size:,} bytes")
    print(f"Extracted: {result.extracted_size:,} bytes")
    print(f"\nContent:\n{result.meaningful_content}")

    # Test 4: CSV notes
    print("\n" + "-" * 60)
    print("FILE: dependencies_audit.csv")
    print("-" * 60)
    result = extractor.extract_from_csv_notes(desktop_path / "dependencies_audit.csv")
    print(f"Original: {result.original_size:,} bytes")
    print(f"Extracted: {result.extracted_size:,} bytes")
    print(f"\nContent:\n{result.meaningful_content}")


if __name__ == "__main__":
    test_extractor()
