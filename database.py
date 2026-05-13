"""
This is the database for Lucky. 
"""
import sqlite3
from datetime import datetime
import pandas as pd

def get_connection():
    connection = sqlite3.connect('lucky.db')
    return connection

def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

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

"""
Insert a new hackathon into the database, or update an existing one
TODO: add logic to check if new or old event is being added
"""
def upsert_hackathon(data: list[dict]):
    connection = get_connection()

    df = pd.DataFrame(data)
    df.to_sql('events', connection, if_exists='replace', index=False)

    connection.close()

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

"""
Fetch all hackathons that are marked as new (is_new = 1) and return them as a list of dicts
"""
def get_new_hackathons() -> list[dict]:
    pass

if __name__ == "__main__":
    create_tables()