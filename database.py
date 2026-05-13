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
            is_new INTEGER NOT NULL DEFAULT 1
        )
    """)

    connection.commit()
    connection.close()
    print("Database tables created successfully.")

def upsert_hackathon(data: list[dict]) -> int:
    """Insert new events (is_new=1) or refresh metadata for existing ones (is_new unchanged).
    Returns the number of genuinely new events inserted."""
    create_tables()
    connection = get_connection()
    cursor = connection.cursor()

    incoming_urls = [row["url"] for row in data if row.get("url")]
    if incoming_urls:
        placeholders = ",".join("?" * len(incoming_urls))
        cursor.execute(f"SELECT url FROM events WHERE url IN ({placeholders})", incoming_urls)
        existing_urls = {row[0] for row in cursor.fetchall()}
    else:
        existing_urls = set()

    new_count = sum(1 for url in incoming_urls if url not in existing_urls)

    cursor.executemany("""
        INSERT INTO events (url, title, event_type, source, deadline, start_date, location, themes)
        VALUES (:url, :title, :event_type, :source, :deadline, :start_date, :location, :themes)
        ON CONFLICT(url) DO UPDATE SET
            title      = excluded.title,
            deadline   = excluded.deadline,
            start_date = excluded.start_date,
            themes     = excluded.themes
    """, data)

    connection.commit()
    connection.close()
    return new_count

def remove_expired_events() -> int:
    "Remove events whose start date has already passed. The function removes the number of events removed"
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    print(today)

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT url, start_date FROM events")
    rows = cursor.fetchall()

    expired = [
        url for url, start_date in rows
        if start_date and _before_today(start_date, today)
    ]

    if expired:
        cursor.executemany("DELETE FROM events WHERE url = ?", [(u,) for u in expired])
        connection.commit()

    connection.close()
    return len(expired)

# ============================================================================
# Helper Function
# ============================================================================
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