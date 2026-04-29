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
returns True if a new hackathon was inserted, False if an existing hackathon was updated
"""
def upsert_hackathon(data: list[dict]):
    connection = get_connection()
    df = pd.DataFrame(data)
    df.to_sql('events', connection, if_exists='replace', index=False)

    connection.close()

"""
Fetch all hackathons that are marked as new (is_new = 1) and return them as a list of dicts
"""
def get_new_hackathons() -> list[dict]:
    pass

if __name__ == "__main__":
    create_tables()