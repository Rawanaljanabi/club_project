import sqlite3

conn = sqlite3.connect("club.db")
cursor = conn.cursor()

# Users table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        picked INTEGER DEFAULT 0
    )
""")

# Messages table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        to_user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(to_user_id) REFERENCES users(id)
    )
""")

conn.commit()
conn.close()

print("✅ Database ready safely!")