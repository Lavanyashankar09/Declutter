"""
Query CLI
Search the vector store for relevant information.
"""

import argparse
import sys

from src.vector_store import VectorStore


def main():
    parser = argparse.ArgumentParser(
        description="Query your organized desktop knowledge"
    )
    parser.add_argument(
        "query",
        help="Search query (e.g., 'database tips', 'meetings next week')",
    )
    parser.add_argument(
        "-n",
        "--num-results",
        type=int,
        default=5,
        help="Number of results to return (default: 5)",
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=["note", "calendar_event", "all"],
        default="all",
        help="Filter by type: note, calendar_event, or all (default: all)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="./output",
        help="Output directory with vector store (default: ./output)",
    )

    args = parser.parse_args()

    # Initialize vector store
    try:
        store = VectorStore(args.output)
    except Exception as e:
        print(f"ERROR: Could not load vector store: {e}")
        print("Run 'python main.py' first to build the vector store.")
        sys.exit(1)

    # Run query
    filter_type = None if args.type == "all" else args.type
    results = store.query(
        args.query, n_results=args.num_results, filter_type=filter_type
    )

    if not results:
        print(f"No results found for: '{args.query}'")
        sys.exit(0)

    # Display results
    print(f"\n🔍 Results for: '{args.query}'")
    print("=" * 60)

    for i, r in enumerate(results, 1):
        if r["type"] == "calendar_event":
            icon = "📅"
            header = f"{r.get('date', '?')} {r.get('time', '') or ''}".strip()
        elif r.get("is_image") == "true":
            icon = "🖼️"
            header = f"[{r.get('topic', 'image')}]"
        else:
            icon = "📝"
            header = f"[{r.get('topic', 'note')}]"

        score = f" (score: {r['score']:.2f})" if r.get("score") else ""

        print(f"\n{icon} {i}. {header}{score}")
        print(f"   {r['content']}")
        print(f"   Source: {r.get('source_file', 'unknown')}")
        if r.get("is_image") == "true":
            print(f"   📎 Image file: desktop/{r.get('source_file', '')}")

    print()


if __name__ == "__main__":
    main()
