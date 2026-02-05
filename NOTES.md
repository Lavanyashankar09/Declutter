# Desktop Declutter Agent - NOTES

## Overview
A CLI tool that transforms a messy directory of scattered notes, todos, and ideas into an organized personal knowledge system.

**Input:** `desktop/` folder with 23 mixed files (markdown, text, CSV, JSON, code, images, logs)

**Output:**
- `output/journal/*.md` - Organized markdown notes by topic
- `output/calendar/events.json` - Calendar events in jCal (RFC 7265) format
- `output/vectordb/` - ChromaDB for semantic search

---

## Quick Start

### Option 1: Run Locally (Python)

```bash
# Install dependencies
pip install -r requirements.txt

# Run full pipeline (calls Claude API)
ANTHROPIC_API_KEY="your-key" python main.py

# Query the knowledge base
python query.py "AWS"
python query.py "cat"
```

### Option 2: Run with Docker

```bash
# Build the image
docker build -t desktop-declutter .

# Run full pipeline
docker run -e ANTHROPIC_API_KEY="your-key" \
  -v $(pwd)/desktop:/app/desktop:ro \
  -v $(pwd)/output:/app/output \
  desktop-declutter python main.py

# Query (after pipeline has run)
docker run -v $(pwd)/output:/app/output \
  desktop-declutter python query.py "AWS"
```

### Option 3: Docker Compose 

```bash
# Run with API key inline
ANTHROPIC_API_KEY="your-key" docker compose up declutter

# Query the knowledge base
docker compose run query "meetings"
```
---

## CLI Reference

### main.py - rebuild knowledge base
```bash
# Rebuild vector store only (no Claude API call) - uses existing output
python main.py --rebuild-vectordb
```

### query.py - Search Knowledge Base
```bash
# Basic search
python query.py "database tips"

# Limit results
python query.py "meetings" -n 10

# Filter by type
python query.py "appointments" -t calendar_event
python query.py "ideas" -t note
```
---


## Architecture & Design Decisions

### Single Claude API Call
Instead of processing files one-by-one (23 API calls), we send ALL content in one request:
- Total ~27K characters = ~3% of Claude's context limit
- Faster and cheaper
- Claude can see relationships between files

### Smart Extraction for Large Files
Large/machine-generated files are pre-processed before sending to Claude:

| File | Original Size | Extracted Size | What We Extract |
|------|--------------|----------------|-----------------|
| api-test-9-25.log | 610KB | 240 bytes | Human comments only (#NOTE, #TODO) |
| system_logs.txt | 6KB | 545 bytes | Warnings, errors, human comments |
| api_responses_sample.json | Large | Summary | Endpoints, roles, error codes |
| dependencies_audit.csv | 5KB | 2.3KB | Notes column only |

### LLM-Discovered Topics
Rather than pre-defining topics, Claude discovers 5-7 natural categories:
- "technical", "work", "personal", "meetings", "learning", "ideas", "expenses"

### Image Processing
Images are analyzed with Claude Vision API and descriptions are included in the content for categorization.

---

## Technologies Used
- **Python 3.11**
- **Anthropic Claude API** - Content classification and extraction
- **Claude Vision** - Image analysis
- **ChromaDB** - Vector database for semantic search
- **Docker** - Containerization

---

## Trade-offs & Limitations

### Limitations
- Topic consistency: Claude may generate slightly different topics on re-runs
- Claude might miss some content when processing all files at once

---

## Development Approach & Iterations

### Pass 1: Token Analysis by Topic (Initial Approach)
- Analyzed each file's tokens separately
- Grouped content by discovered topics
- **Problem:** Image files couldn't be assigned to a proper topic and were getting lost in the categorization

### Pass 2: Unified Pipeline (Planned, Not Implemented)
- Wanted to analyze each file individually first
- Then pass all extracted data through a unified pipeline
- Create outputs separately with better control
- **Status:** Didn't have time to implement

### Pass 3: Image Summary in VectorDB (Final Workaround)
- Added image descriptions (from Claude Vision) directly to VectorDB
- Images now searchable via semantic search (e.g., query "cat" finds `spritz.jpg`)
- Added `is_image` metadata flag to identify image results
- Query output shows 🖼️ icon and file path for images

---

### Cost Comparison - Sonnet Only

*Setup: 10 files × 1,000 tokens each = 10,000 tokens total*

| Approach | Input Tokens | Output Tokens | API Calls | Total Cost | vs All-at-Once |
|----------|--------------|---------------|-----------|------------|----------------|
| **All at Once** | 10,600 | 2,000 | 1 | $0.062 | baseline |
| File-by-File | 15,100 | 2,000 | 10 | $0.075 | +21% 💸 |
| Batched (2 files) | 12,600 | 2,000 | 5 | $0.068 | +10% |

**🏆 Winner: All at Once** - Cheapest, fastest, best quality.

### Why File-by-File Costs More
- Each API call has overhead (system prompt repeated)
- More input tokens total due to repeated context
- Loses cross-file context (Claude can't see relationships)

### Why Unified Pipeline is Still Valuable (Pass 2)
- **Reusability:** Can be used for many different use cases
- **Flexibility:** Each file processed independently, then merged
- **Debugging:** Easier to trace issues to specific files
- **Incremental:** Can add new files without reprocessing everything

### Trade-off
- All-at-once may miss some nuanced content
- Unified pipeline remains valid for more complex use cases and variety

---

## Future Improvements
- Implement Pass 2 unified pipeline for better content extraction
- Add incremental processing (only process new/changed files)
- Better date parsing with NLP date parser
