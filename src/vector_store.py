"""
Vector Store Module
Stores notes and calendar events in ChromaDB for semantic search.
"""

import os

import chromadb
from chromadb.config import Settings

from .llm_processor import ProcessedResult


class VectorStore:
    """ChromaDB vector store for semantic search."""

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir
        self.db_path = os.path.join(output_dir, "vectordb")

        # Create persistent ChromaDB client
        os.makedirs(self.db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.db_path)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="desktop_knowledge",
            metadata={"description": "Desktop declutter knowledge base"},
        )

    def store(self, result: ProcessedResult) -> dict:
        """Store all notes and calendar events in ChromaDB."""

        documents = []
        metadatas = []
        ids = []

        # Store notes
        for i, note in enumerate(result.notes):
            doc_id = f"note_{i}"
            content = note.get("content", "")

            if not content.strip():
                continue

            documents.append(content)
            metadatas.append(
                {
                    "type": "note",
                    "topic": note.get("topic", "uncategorized"),
                    "source_file": note.get("source_file", "unknown"),
                    "tags": ",".join(note.get("tags", [])),
                    "is_image": (
                        "true"
                        if note.get("source_file", "")
                        .lower()
                        .endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))
                        else "false"
                    ),
                }
            )
            ids.append(doc_id)

        # Store calendar events
        for i, event in enumerate(result.calendar_events):
            doc_id = f"event_{i}"

            # Create searchable text from event
            title = event.get("title", "")
            description = event.get("description", "")
            content = f"{title}. {description}".strip()

            if not content.strip():
                continue

            documents.append(content)
            metadatas.append(
                {
                    "type": "calendar_event",
                    "date": event.get("date", ""),
                    "time": event.get("time", "") or "",
                    "source_file": event.get("source_file", "unknown"),
                    "tags": "",
                }
            )
            ids.append(doc_id)

        # Clear existing and add new
        # First, try to delete existing items
        try:
            existing = self.collection.get()
            if existing["ids"]:
                self.collection.delete(ids=existing["ids"])
        except Exception:
            pass

        # Add documents to collection
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )

        stats = {
            "total_documents": len(documents),
            "notes": len([m for m in metadatas if m["type"] == "note"]),
            "events": len([m for m in metadatas if m["type"] == "calendar_event"]),
            "db_path": self.db_path,
        }

        print(f"Stored {stats['notes']} notes and {stats['events']} events in ChromaDB")
        print(f"Database path: {self.db_path}")

        return stats

    def query(
        self, query_text: str, n_results: int = 5, filter_type: str = None
    ) -> list:
        """Query the vector store for relevant documents."""

        where_filter = None
        if filter_type:
            where_filter = {"type": filter_type}

        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_filter,
        )

        # Format results
        formatted = []
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i]
            distance = results["distances"][0][i] if results.get("distances") else None

            formatted.append(
                {
                    "content": doc,
                    "type": meta.get("type"),
                    "topic": meta.get("topic"),
                    "source_file": meta.get("source_file"),
                    "date": meta.get("date"),
                    "score": 1 - distance if distance else None,
                    "is_image": meta.get("is_image", "false"),
                }
            )

        return formatted


def test_store():
    """Test the vector store."""
    from .file_parser import FileParser
    from .llm_processor import LLMProcessor

    # Parse and process
    parser = FileParser("./desktop")
    files = parser.parse_all_files()

    processor = LLMProcessor()
    result = processor.process_all(files)

    # Store in vector DB
    store = VectorStore("./output")
    stats = store.store(result)

    print("\n" + "=" * 60)
    print("VECTOR STORE TEST")
    print("=" * 60)
    print(f"Stored: {stats}")

    # Test queries
    print("\n--- Test Query: 'database' ---")
    results = store.query("database tips")
    for r in results[:3]:
        print(f"  [{r['topic']}] {r['content'][:60]}...")

    print("\n--- Test Query: 'meetings' ---")
    results = store.query("upcoming meetings", filter_type="calendar_event")
    for r in results[:3]:
        print(f"  [{r['date']}] {r['content'][:60]}...")


if __name__ == "__main__":
    test_store()
