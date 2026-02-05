"""
Desktop Declutter Agent - Main Pipeline
Orchestrates the full processing pipeline with a single Claude API call.
"""

import argparse
import os
import sys

from src.calendar_generator import CalendarGenerator
from src.file_parser import FileParser
from src.journal_generator import JournalGenerator
from src.llm_processor import LLMProcessor
from src.vector_store import VectorStore


def main():
    parser = argparse.ArgumentParser(
        description="Desktop Declutter Agent - Organize messy files into structured knowledge"
    )
    parser.add_argument(
        "input_dir",
        nargs="?",
        default="./desktop",
        help="Input directory with files to process (default: ./desktop)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="./output",
        help="Output directory (default: ./output)",
    )
    parser.add_argument(
        "--rebuild-vectordb",
        action="store_true",
        help="Only rebuild vector store from existing output (no Claude API call)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("DESKTOP DECLUTTER AGENT")
    print("=" * 60)
    print(f"Input:  {args.input_dir}")
    print(f"Output: {args.output}")
    print()

    # If --rebuild-vectordb flag, skip Claude and just rebuild from existing files
    if args.rebuild_vectordb:
        print("Mode: Rebuilding vector store from existing output...")
        print()
        from build_vectordb import build_from_existing

        build_from_existing(args.output)
        return

    # Check input directory exists
    if not os.path.isdir(args.input_dir):
        print(f"ERROR: Input directory not found: {args.input_dir}")
        sys.exit(1)

    # Step 1: Parse all files
    print("STEP 1: Parsing files...")
    file_parser = FileParser(args.input_dir)
    parsed_files = file_parser.parse_all_files()
    print(f"  → Parsed {len(parsed_files)} files")
    print()

    # Step 2: Process with Claude (ONE API call)
    print("STEP 2: Processing with Claude...")
    processor = LLMProcessor()
    result = processor.process_all(parsed_files)
    print(f"  → Topics discovered: {result.topics}")
    print(f"  → Calendar events: {len(result.calendar_events)}")
    print(f"  → Notes: {len(result.notes)}")
    print()

    # Step 3: Generate journal files
    print("STEP 3: Generating journal files...")
    journal_gen = JournalGenerator(args.output)
    journal_files = journal_gen.generate(result)
    print()

    # Step 4: Generate calendar file
    print("STEP 4: Generating calendar (jCal)...")
    calendar_gen = CalendarGenerator(args.output)
    calendar_file = calendar_gen.generate(result)
    print()

    # Step 5: Store in vector database
    print("STEP 5: Building vector store (ChromaDB)...")
    vector_store = VectorStore(args.output)
    vector_stats = vector_store.store(result)
    print()

    # Summary
    print("=" * 60)
    print("COMPLETE!")
    print("=" * 60)
    print(f"Journal files: {len(journal_files)}")
    for topic, info in journal_files.items():
        print(f"  • {info['path']} ({info['notes_count']} notes)")
    print(f"\nCalendar: {calendar_file}")
    print(f"  • {len(result.calendar_events)} events")
    print(f"\nVector store: {vector_stats['db_path']}")
    print(f"  • {vector_stats['total_documents']} documents indexed")
    print(f'\nRun queries with: python query.py "your search query"')


if __name__ == "__main__":
    main()
