"""
File Parser Module
Reads all file types from the desktop directory and extracts content.
Uses SmartExtractor for large/machine-generated files.
"""

import base64
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .smart_extractor import SmartExtractor


@dataclass
class ParsedFile:
    """Represents a parsed file with its content and metadata."""

    filename: str
    filepath: str
    file_type: str
    content: str
    is_code: bool = False
    image_base64: Optional[str] = None


class FileParser:
    """Parser for various file types in the desktop directory."""

    # File extensions and their types
    TEXT_EXTENSIONS = {".md", ".txt"}
    CODE_EXTENSIONS = {".py", ".tsx", ".ts", ".js", ".sql"}
    DATA_EXTENSIONS = {".csv", ".json"}
    LOG_EXTENSIONS = {".log"}
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

    # Files that need smart extraction
    SMART_EXTRACT_FILES = {
        "api-test-9-25.log": "log",
        "system_logs.txt": "system_log",
        "api_responses_sample.json": "json",
        "dependencies_audit.csv": "csv_notes",
    }

    def __init__(self, desktop_path: str):
        self.desktop_path = Path(desktop_path)
        self.smart_extractor = SmartExtractor()

    def parse_all_files(self) -> list[ParsedFile]:
        """Parse all files in the desktop directory."""
        parsed_files = []

        for filepath in sorted(self.desktop_path.iterdir()):
            if filepath.is_file():
                parsed = self.parse_file(filepath)
                if parsed:
                    parsed_files.append(parsed)

        return parsed_files

    def parse_file(self, filepath: Path) -> Optional[ParsedFile]:
        """Parse a single file based on its type."""
        filename = filepath.name
        ext = filepath.suffix.lower()

        # Skip hidden files
        if filename.startswith("."):
            return None

        # Check if file needs smart extraction
        if filename in self.SMART_EXTRACT_FILES:
            return self._smart_extract(filepath, self.SMART_EXTRACT_FILES[filename])

        # Route to appropriate parser
        if ext in self.TEXT_EXTENSIONS:
            return self._parse_text_file(filepath)
        elif ext in self.CODE_EXTENSIONS:
            return self._parse_code_file(filepath)
        elif ext == ".csv":
            return self._parse_csv_file(filepath)
        elif ext == ".json":
            return self._parse_json_file(filepath)
        elif ext in self.LOG_EXTENSIONS:
            return self._smart_extract(filepath, "log")
        elif ext in self.IMAGE_EXTENSIONS:
            return self._parse_image_file(filepath)
        else:
            # Try to read as text
            try:
                return self._parse_text_file(filepath)
            except:
                return None

    def _smart_extract(self, filepath: Path, extract_type: str) -> ParsedFile:
        """Use smart extractor for large/machine files."""
        if extract_type == "log":
            result = self.smart_extractor.extract_from_log(str(filepath))
        elif extract_type == "system_log":
            result = self.smart_extractor.extract_from_system_logs(str(filepath))
        elif extract_type == "json":
            result = self.smart_extractor.extract_from_json(str(filepath))
        elif extract_type == "csv_notes":
            result = self.smart_extractor.extract_from_csv_notes(str(filepath))
        else:
            result = self.smart_extractor.extract_from_log(str(filepath))

        return ParsedFile(
            filename=filepath.name,
            filepath=str(filepath),
            file_type=extract_type,
            content=result.meaningful_content,
            is_code=False,
        )

    def _parse_text_file(self, filepath: Path) -> ParsedFile:
        """Parse markdown and text files."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        return ParsedFile(
            filename=filepath.name,
            filepath=str(filepath),
            file_type="text",
            content=content,
            is_code=False,
        )

    def _parse_code_file(self, filepath: Path) -> ParsedFile:
        """Parse code files - extract full content + highlight comments."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        return ParsedFile(
            filename=filepath.name,
            filepath=str(filepath),
            file_type="code",
            content=content,
            is_code=True,
        )

    def _parse_csv_file(self, filepath: Path) -> ParsedFile:
        """Parse CSV files into readable text."""
        rows = []
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            for row in reader:
                rows.append(row)

        # Format as readable text
        content = f"CSV File: {filepath.name}\n"
        content += f"Columns: {', '.join(headers)}\n"
        content += f"Rows: {len(rows)}\n\n"

        for row in rows:
            content += str(row) + "\n"

        return ParsedFile(
            filename=filepath.name,
            filepath=str(filepath),
            file_type="csv",
            content=content,
            is_code=False,
        )

    def _parse_json_file(self, filepath: Path) -> ParsedFile:
        """Parse JSON files."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        content = json.dumps(data, indent=2)

        return ParsedFile(
            filename=filepath.name,
            filepath=str(filepath),
            file_type="json",
            content=content,
            is_code=False,
        )

    def _parse_image_file(self, filepath: Path) -> ParsedFile:
        """Parse image files by encoding to base64 for LLM analysis."""
        with open(filepath, "rb") as f:
            image_data = f.read()

        image_base64 = base64.b64encode(image_data).decode("utf-8")

        # Determine media type
        ext = filepath.suffix.lower()
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        media_type = media_types.get(ext, "image/jpeg")

        return ParsedFile(
            filename=filepath.name,
            filepath=str(filepath),
            file_type="image",
            content=f"[Image file: {filepath.name}]",
            is_code=False,
            image_base64=f"data:{media_type};base64,{image_base64}",
        )


def test_parser():
    """Test the file parser."""
    parser = FileParser("./desktop")
    files = parser.parse_all_files()

    print("=" * 60)
    print("FILE PARSER TEST")
    print("=" * 60)
    print(f"\nTotal files parsed: {len(files)}\n")

    for f in files:
        icon = "🖼️" if f.file_type == "image" else "📄"
        print(f"{icon} {f.filename} [{f.file_type}]")
        print(f"   Content: {len(f.content)} chars")
        print(f"   Preview: {f.content[:100]}...")
        print()


if __name__ == "__main__":
    test_parser()
