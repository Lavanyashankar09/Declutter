"""
Streamlit UI for the Desktop Declutter Agent.

Run with: streamlit run app.py
"""

import json
import os
import subprocess
import sys
from collections import Counter

import streamlit as st
from dotenv import load_dotenv

from src.vector_store import VectorStore

load_dotenv()

OUTPUT_DIR = "./output"
DESKTOP_DIR = "./desktop"
EXAMPLE_QUERIES = ["database tips", "cat", "meetings", "AWS", "book recommendations"]
MONTHS = {
    "01": "January", "02": "February", "03": "March", "04": "April",
    "05": "May", "06": "June", "07": "July", "08": "August",
    "09": "September", "10": "October", "11": "November", "12": "December",
}

st.set_page_config(page_title="Desktop Declutter", page_icon="🗂️", layout="wide")

st.markdown(
    """
    <style>
      .block-container { padding-top: 2.5rem; max-width: 1100px; }
      [data-testid="stMetricValue"] { font-size: 1.6rem; }
      .source-tag {
        background: rgba(128,128,128,.16); border-radius: 4px;
        padding: 1px 7px; font-size: .78rem; font-family: monospace;
      }
      /* Roomier pill navigation in place of Streamlit's cramped default tabs */
      [data-testid="stSegmentedControl"] button {
        padding: .55rem 1.6rem;
        font-size: 1.02rem;
        font-weight: 500;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_store(db_signature: str) -> VectorStore:
    """Load the vector store. Keyed on a signature so it reloads after a rebuild."""
    return VectorStore(OUTPUT_DIR)


def db_signature() -> str:
    """Change whenever the ChromaDB file changes, to bust the cached store."""
    db_file = os.path.join(OUTPUT_DIR, "vectordb", "chroma.sqlite3")
    if not os.path.exists(db_file):
        return "missing"
    return str(os.path.getmtime(db_file))


def collection_stats(store: VectorStore) -> dict:
    """Count indexed documents by type and topic."""
    data = store.collection.get(include=["metadatas"])
    metadatas = data.get("metadatas") or []
    types = Counter(m.get("type") for m in metadatas)
    topics = {m.get("topic") for m in metadatas if m.get("topic")}
    return {
        "total": len(metadatas),
        "notes": types.get("note", 0),
        "events": types.get("calendar_event", 0),
        "topics": len(topics),
    }


def load_events() -> list[dict]:
    """Flatten the jCal calendar file into plain dicts."""
    path = os.path.join(OUTPUT_DIR, "calendar", "events.json")
    if not os.path.exists(path):
        return []

    with open(path) as f:
        jcal = json.load(f)

    # jCal: ["vcalendar", [properties], [components]]
    if len(jcal) < 3:
        return []

    events = []
    for component in jcal[2]:
        if not component or component[0] != "vevent":
            continue
        fields = {prop[0]: prop[3] for prop in component[1] if len(prop) >= 4}
        events.append(
            {
                "date": fields.get("dtstart", ""),
                "title": fields.get("summary", "(untitled)"),
                "description": fields.get("description", ""),
            }
        )

    return sorted(events, key=lambda e: e["date"])


def load_journals() -> dict[str, str]:
    journal_dir = os.path.join(OUTPUT_DIR, "journal")
    if not os.path.isdir(journal_dir):
        return {}

    journals = {}
    for name in sorted(os.listdir(journal_dir)):
        if name.endswith(".md"):
            with open(os.path.join(journal_dir, name)) as f:
                journals[name[:-3]] = f.read()
    return journals


def pretty_date(raw: str) -> str:
    """Render '2025-01-15T11:00:00' as '15 Jan · 11:00'."""
    if not raw:
        return "undated"
    date_part, _, time_part = raw.partition("T")
    pieces = date_part.split("-")
    if len(pieces) != 3:
        return raw
    _, month, day = pieces
    label = f"{int(day)} {MONTHS.get(month, month)[:3]}"
    if time_part:
        label += f" · {time_part[:5]}"
    return label


def set_query(value: str) -> None:
    st.session_state.query = value


def render_result(rank: int, result: dict) -> None:
    is_image = result.get("is_image") == "true"
    source = result.get("source_file", "unknown")

    if result["type"] == "calendar_event":
        icon, label = "📅", pretty_date(result.get("date", ""))
    elif is_image:
        icon, label = "🖼️", result.get("topic", "image")
    else:
        icon, label = "📝", result.get("topic", "note")

    with st.container(border=True):
        head, meta = st.columns([5, 2])
        with head:
            st.markdown(f"{icon}  **{label}**")
        with meta:
            st.markdown(
                f"<div style='text-align:right'><span class='source-tag'>{source}</span></div>",
                unsafe_allow_html=True,
            )

        st.write(result["content"])

        score = result.get("score")
        if score is not None:
            st.progress(max(0.0, min(1.0, float(score))), text=f"relevance {score:.2f}")

        if is_image:
            image_path = os.path.join(DESKTOP_DIR, source)
            if os.path.exists(image_path):
                st.image(image_path, width=260)


st.title("🗂️ Desktop Declutter")
st.caption("Messy desktop files, turned into a searchable knowledge base.")

output_exists = os.path.exists(os.path.join(OUTPUT_DIR, "vectordb", "chroma.sqlite3"))

with st.sidebar:
    st.header("Pipeline")

    if os.environ.get("OPENROUTER_API_KEY"):
        st.success("OPENROUTER_API_KEY loaded")
    else:
        st.error("No OPENROUTER_API_KEY found in .env")

    st.caption(
        f"Model: `{os.environ.get('OPENROUTER_MODEL', 'google/gemini-2.5-flash')}`"
    )

    st.divider()
    st.write(
        "Re-run the full pipeline over `desktop/`. This calls the API and takes about a minute."
    )

    if st.button("Run pipeline", type="primary", use_container_width=True):
        with st.spinner("Processing files..."):
            proc = subprocess.run(
                [sys.executable, "main.py"], capture_output=True, text=True
            )
        if proc.returncode == 0:
            st.success("Pipeline complete.")
            get_store.clear()
        else:
            st.error("Pipeline failed.")
        with st.expander("Output"):
            st.code((proc.stdout or "") + (proc.stderr or ""))

if not output_exists:
    st.warning("No knowledge base yet. Run the pipeline from the sidebar to build one.")
    st.stop()

store = get_store(db_signature())
stats = collection_stats(store)
events = load_events()
journals = load_journals()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Indexed", stats["total"])
c2.metric("Notes", stats["notes"])
c3.metric("Events", stats["events"])
c4.metric("Topics", stats["topics"])

st.divider()

VIEWS = ["🔍  Search", "📓  Journals", "📅  Calendar"]

# Falls back to Search because deselecting the active pill returns None.
view = (
    st.segmented_control(
        "View", VIEWS, default=VIEWS[0], label_visibility="collapsed", width="stretch"
    )
    or VIEWS[0]
)

st.write("")

if view == VIEWS[0]:
    st.text_input(
        "Search",
        key="query",
        placeholder="Search your notes, events and images...",
        label_visibility="collapsed",
    )

    st.caption("Try:")
    for col, example in zip(st.columns(len(EXAMPLE_QUERIES)), EXAMPLE_QUERIES):
        col.button(
            example,
            key=f"ex_{example}",
            on_click=set_query,
            args=(example,),
            use_container_width=True,
        )

    with st.expander("Filters"):
        kind = st.selectbox(
            "Type",
            ["all", "note", "calendar_event"],
            format_func=lambda v: v.replace("_", " "),
        )
        limit = st.slider("Results", min_value=1, max_value=20, value=5)

    query = st.session_state.get("query", "")
    if query:
        results = store.query(
            query, n_results=limit, filter_type=None if kind == "all" else kind
        )
        if not results:
            st.info(f"No results for '{query}'.")
        else:
            st.caption(f"{len(results)} results for **{query}**")
            for i, result in enumerate(results, 1):
                render_result(i, result)
    else:
        st.info("Enter a search term above, or pick one of the examples.")

elif view == VIEWS[1]:
    if not journals:
        st.info("No journal files found.")
    else:
        topic = st.selectbox(
            "Topic",
            list(journals),
            format_func=lambda t: f"{t.replace('_', ' ')}  ({journals[t].count('- ')} notes)",
        )
        st.markdown(journals[topic])

elif view == VIEWS[2]:
    if not events:
        st.info("No calendar events found.")
    else:
        st.caption(f"{len(events)} events")
        current_month = None
        for event in events:
            month_key = event["date"][:7]
            if month_key != current_month:
                current_month = month_key
                year, _, month = month_key.partition("-")
                st.subheader(f"{MONTHS.get(month, month)} {year}")

            with st.container(border=True):
                left, right = st.columns([1, 5])
                left.markdown(f"**{pretty_date(event['date'])}**")
                right.markdown(event["title"])
                if event["description"]:
                    right.caption(event["description"])
