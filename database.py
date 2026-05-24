"""
This is the database for Lucky.
"""
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "lucky.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    # If the table exists without url as PRIMARY KEY, drop and recreate it
    cursor.execute("PRAGMA table_info(events)")
    columns = {row[1]: row[5] for row in cursor.fetchall()}  # {name: is_pk}
    if columns and columns.get("url", 0) != 1:
        cursor.execute("DROP TABLE events")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            url TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            event_type TEXT,
            source TEXT NOT NULL,
            deadline TEXT,
            start_date TEXT,
            location TEXT,
            themes TEXT,
            relevance_score INTEGER,
            relevance_reasoning TEXT,
            is_new INTEGER NOT NULL DEFAULT 0
        )
    """)
    migrate_events_table(cursor)

    connection.commit()
    connection.close()
    print("Database tables created successfully.")

def migrate_events_table(cursor):
    cursor.execute("PRAGMA table_info(events)")
    columns = {row[1] for row in cursor.fetchall()}

    if "relevance_score" not in columns:
        cursor.execute("ALTER TABLE events ADD COLUMN relevance_score INTEGER")

    if "relevance_reasoning" not in columns:
        cursor.execute("ALTER TABLE events ADD COLUMN relevance_reasoning TEXT")

def upsert_hackathon(data: list[dict]) -> int:
    """Insert new events (is_new=1) or refresh metadata for existing ones (is_new unchanged).
    Returns the number of genuinely new events inserted."""
    expired_urls = [
        row["url"] for row in data
        if row.get("url") and is_expired_start_date(row.get("start_date"))
    ]
    data = [row for row in data if not is_expired_start_date(row.get("start_date"))]

    connection = get_connection()
    cursor = connection.cursor()

    if expired_urls:
        cursor.executemany("DELETE FROM events WHERE url = ?", [(u,) for u in expired_urls])

    incoming_urls = [row["url"] for row in data if row.get("url")]
    if incoming_urls:
        placeholders = ",".join("?" * len(incoming_urls))
        cursor.execute(f"SELECT url FROM events WHERE url IN ({placeholders})", incoming_urls)
        existing_urls = {row[0] for row in cursor.fetchall()}
    else:
        existing_urls = set()

    new_count = sum(1 for url in incoming_urls if url not in existing_urls)

    rows = [
        {
            **row,
            "relevance_score": row.get("relevance_score"),
            "relevance_reasoning": row.get("relevance_reasoning"),
            "is_new": 0 if row.get("url") in existing_urls else 1,
        }
        for row in data
    ]

    cursor.executemany("""
        INSERT INTO events (url, title, event_type, source, deadline, start_date, location, themes, relevance_score, relevance_reasoning, is_new)
        VALUES (:url, :title, :event_type, :source, :deadline, :start_date, :location, :themes, :relevance_score, :relevance_reasoning, :is_new)
        ON CONFLICT(url) DO UPDATE SET
            title      = excluded.title,
            event_type = excluded.event_type,
            source     = excluded.source,
            deadline   = excluded.deadline,
            start_date = excluded.start_date,
            location   = excluded.location,
            themes     = excluded.themes, 
            relevance_score     = excluded.relevance_score,
            relevance_reasoning = excluded.relevance_reasoning
    """, rows)

    connection.commit()
    connection.close()
    return new_count

def remove_expired_events() -> int:
    "Remove events whose start date has already passed. The function removes the number of events removed"
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT url, start_date FROM events")
    rows = cursor.fetchall()

    expired = [
        url for url, start_date in rows
        if is_expired_start_date(start_date)
    ]

    if expired:
        cursor.executemany("DELETE FROM events WHERE url = ?", [(u,) for u in expired])
        connection.commit()

    connection.close()
    return len(expired)

# ============================================================================
# Helper Functions
# ============================================================================
def is_expired_start_date(start_date: str | None, today: datetime | None = None) -> bool:
    """Return True when start_date is before today."""
    if not start_date:
        return False

    if today is None:
        today = datetime.today()

    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    return _before_today(start_date, today)

def _before_today(start_date:str, today: datetime) -> bool:
    try:
        return datetime.strptime(start_date, "%d/%m/%Y") < today
    except ValueError:
        return False

def get_new_hackathons() -> list[dict]:
    """Return all events marked as new (is_new=1) as a list of dicts."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM events WHERE is_new = 1")
    columns = [col[0] for col in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    connection.close()
    return rows

def mark_all_seen() -> int:
    """
    Set is_new=0 for all events. Returns the number of rows updated.
    This happens every morning before the scraping run.
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE events SET is_new = 0 WHERE is_new = 1")
    updated = cursor.rowcount
    connection.commit()
    connection.close()
    return updated
