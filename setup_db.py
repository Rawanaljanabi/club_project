import sqlite3

DB_FILE = "club.db"

def setup_and_populate():
    # Connect to the database file
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print("Creating tables if they don't exist...")
    # 1. Create the users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL
        )
    """)

    # 2. Create the messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Define your club members list here (username, password, display_name)
    club_members = [
        ("alice12", "pass123", "Alice"),
        ("bob34", "pass456", "Bob"),
        ("charlie56", "pass789", "Charlie")
    ]

    print("Inserting users into the database...")
    # Using INSERT OR IGNORE so running this script multiple times won't crash on duplicates
    cursor.executemany("""
        INSERT OR IGNORE INTO users (username, password, name) 
        VALUES (?, ?, ?)
    """, club_members)

    # Save changes and close connection
    conn.commit()
    conn.close()
    print("✨ Database setup complete and users added successfully!")

if __name__ == "__main__":
    setup_and_populate()