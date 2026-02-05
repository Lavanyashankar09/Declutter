"""
Journal Generator Module
Takes Claude's processed notes and saves as markdown files by topic.
"""

import os
from datetime import datetime

from .llm_processor import ProcessedResult


class JournalGenerator:
    """Generates markdown journal files from processed notes."""

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir
        self.journal_dir = os.path.join(output_dir, "journal")

    def generate(self, result: ProcessedResult) -> dict:
        """Generate markdown files for each topic."""

        # Create output directory
        os.makedirs(self.journal_dir, exist_ok=True)

        # Group notes by topic
        by_topic = {}
        for note in result.notes:
            topic = note.get("topic", "uncategorized")
            by_topic.setdefault(topic, []).append(note)

        files_created = {}

        for topic, notes in by_topic.items():
            filename = f"{topic}.md"
            filepath = os.path.join(self.journal_dir, filename)

            content = self._generate_markdown(topic, notes)

            with open(filepath, "w") as f:
                f.write(content)

            files_created[topic] = {
                "path": filepath,
                "notes_count": len(notes),
            }
            print(f"Created: {filepath} ({len(notes)} notes)")

        return files_created

    def _generate_markdown(self, topic: str, notes: list) -> str:
        """Generate markdown content for a topic."""

        lines = []

        # Header
        title = topic.replace("_", " ").title()
        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Group by source file
        by_source = {}
        for note in notes:
            source = note.get("source_file", "unknown")
            by_source.setdefault(source, []).append(note)

        for source, source_notes in by_source.items():
            lines.append(f"## From: {source}")
            lines.append("")

            for note in source_notes:
                content = note.get("content", "")
                tags = note.get("tags", [])

                lines.append(f"- {content}")

                if tags:
                    tag_str = " ".join([f"`#{t}`" for t in tags])
                    lines.append(f"  {tag_str}")

                lines.append("")

        return "\n".join(lines)


def test_generator():
    """Test the journal generator."""
    from .file_parser import FileParser
    from .llm_processor import LLMProcessor

    # Parse and process
    parser = FileParser("./desktop")
    files = parser.parse_all_files()

    processor = LLMProcessor()
    result = processor.process_all(files)

    # Generate journals
    generator = JournalGenerator("./output")
    files_created = generator.generate(result)

    print("\n" + "=" * 60)
    print("JOURNAL GENERATION COMPLETE")
    print("=" * 60)
    print(f"Topics: {list(files_created.keys())}")
    print(f"Files created: {len(files_created)}")


if __name__ == "__main__":
    test_generator()
