"""
Build Vector Store from existing output
No Claude API call needed - uses the already processed data.
"""

import json
import os
import sys

import chromadb


def build_from_existing(output_dir: str = "./output"):
    """Build vector store from existing journal and calendar files."""

    journal_dir = os.path.join(output_dir, "journal")
    calendar_file = os.path.join(output_dir, "calendar", "events.json")
    db_path = os.path.join(output_dir, "vectordb")

    # Check files exist
    if not os.path.exists(journal_dir):
        print(f"ERROR: No journal files found at {journal_dir}")
        print("Run 'python main.py' first to process files.")
        sys.exit(1)

    print("Building vector store from existing output...")
    print(f"  Journal dir: {journal_dir}")
    print(f"  Calendar file: {calendar_file}")

    # Create ChromaDB
    os.makedirs(db_path, exist_ok=True)
    client = chromadb.PersistentClient(path=db_path)

    # Delete existing collection if exists
    try:
        client.delete_collection("desktop_knowledge")
    except:
        pass

    collection = client.create_collection(
        name="desktop_knowledge",
        metadata={"description": "Desktop declutter knowledge base"},
    )

    documents = []
    metadatas = []
    ids = []
    note_count = 0

    # Read journal files (markdown)
    for filename in os.listdir(journal_dir):
        if filename.endswith(".md"):
            topic = filename.replace(".md", "")
            filepath = os.path.join(journal_dir, filename)

            with open(filepath, "r") as f:
                content = f.read()

            # Extract notes from markdown (lines starting with -)
            lines = content.split("\n")
            current_source = "unknown"

            for line in lines:
                if line.startswith("## From:"):
                    current_source = line.replace("## From:", "").strip()
                elif line.startswith("- "):
                    note_text = line[2:].strip()
                    if note_text:
                        doc_id = f"note_{note_count}"
                        documents.append(note_text)
                        metadatas.append(
                            {
                                "type": "note",
                                "topic": topic,
                                "source_file": current_source,
                                "tags": "",
                            }
                        )
                        ids.append(doc_id)
                        note_count += 1

    print(f"  → Loaded {note_count} notes from journals")

    # Read calendar events (jCal JSON)
    event_count = 0
    if os.path.exists(calendar_file):
        with open(calendar_file, "r") as f:
            jcal = json.load(f)

        # jCal structure: ["vcalendar", [props], [events]]
        events = jcal[2] if len(jcal) > 2 else []

        for event in events:
            # event: ["vevent", [props], []]
            if event[0] == "vevent":
                props = {p[0]: p[3] for p in event[1]}

                title = props.get("summary", "")
                description = props.get("description", "")
                date = props.get("dtstart", "")
                source = props.get("x-source-file", "")

                content = f"{title}. {description}".strip()
                if content:
                    doc_id = f"event_{event_count}"
                    documents.append(content)
                    metadatas.append(
                        {
                            "type": "calendar_event",
                            "date": date,
                            "time": "",
                            "source_file": source,
                            "tags": "",
                        }
                    )
                    ids.append(doc_id)
                    event_count += 1

    print(f"  → Loaded {event_count} calendar events")

    # Add to collection
    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

    print(f"\n✅ Vector store built: {db_path}")
    print(f"   Total documents: {len(documents)}")
    print(f'\nTest with: python query.py "database tips"')


if __name__ == "__main__":
    build_from_existing()
