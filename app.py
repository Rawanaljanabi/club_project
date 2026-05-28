from flask import Flask, request, render_template, jsonify, session
import sqlite3
import random
import os

app = Flask(__name__)
# CRITICAL: Set a secret key to enable secure user sessions
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-club-key-12345")

DB_FILE = "club.db"


# ===================== DB =====================
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. SEED USERS AUTOMATICALLY
    # Check if the table is empty first
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        club_members = [
            ("alice12", "pass123", "Alice"),
            ("bob34", "pass456", "Bob"),
            ("charlie56", "pass789", "Charlie")
        ]
        cursor.executemany("""
            INSERT INTO users (username, password, name) 
            VALUES (?, ?, ?)
        """, club_members)
        print("✨ Database automatically seeded with club members!")

    conn.commit()
    conn.close()


# ===================== ROUTES =====================
@app.route("/")
def home():
    return render_template("page1.html")


# ---- Replaced /join with /login ----
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json() or {}
        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Search for the pre-configured admin user accounts
        cursor.execute(
            "SELECT id, username, name FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            # Store the logged-in user details inside the encrypted session cookie
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["name"] = user["name"]
            return jsonify({"success": True, "message": f"Welcome back, {user['name']}!"})
        else:
            return jsonify({"error": "Invalid username or password"}), 401

    except Exception as e:
        return jsonify({"error": f"Login backend error: {str(e)}"}), 500


# ---- Random user (FIXED & ROBUST) ----
@app.route("/random-user")
def random_user():
    try:
        # Check if the current user is logged in
        current_user_id = session.get("user_id")
        if not current_user_id:
            return jsonify({"error": "Unauthorized. Please log in first."}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        # Grab random users EXCLUDING the logged-in user themselves
        cursor.execute("SELECT id, name FROM users WHERE id != ?", (current_user_id,))
        rows = cursor.fetchall()
        conn.close()

        # SAFE CONVERSION: Turn sqlite3.Row objects into standard Python dictionaries
        users_list = [{"id": row["id"], "name": row["name"]} for row in rows]

        if len(users_list) == 0:
            return jsonify({"error": "No other users available to select"}), 400

        # Safely pick from a clean dictionary list
        chosen = random.choice(users_list)

        return jsonify({
            "success": True,
            "id": chosen["id"],
            "name": chosen["name"]
        })

    except Exception as e:
        return jsonify({"error": f"Randomizer backend error: {str(e)}"}), 500


# ---- Send message ----
@app.route("/send-appreciation", methods=["POST"])
def send_appreciation():
    try:
        current_user_id = session.get("user_id")
        if not current_user_id:
            return jsonify({"error": "Unauthorized"}), 401

        data = request.get_json() or {}
        to_user_id = data.get("to_user_id")
        message = data.get("message", "").strip()

        if not to_user_id:
            return jsonify({"error": "Missing recipient user"}), 400

        if not message:
            return jsonify({"error": "Empty message"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO messages (from_user_id, to_user_id, message) VALUES (?, ?, ?)",
            (current_user_id, to_user_id, message)
        )

        conn.commit()
        conn.close()

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": f"Send backend error: {str(e)}"}), 500


# ---- Secure Personal Inbox ----
@app.route("/inbox")
def inbox():
    try:
        current_user_id = session.get("user_id")
        if not current_user_id:
            return jsonify({"error": "Unauthorized"}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.name AS from_name, m.message, m.timestamp
            FROM messages m
            JOIN users u ON m.from_user_id = u.id
            WHERE m.to_user_id = ?
            ORDER BY m.timestamp DESC
        """, (current_user_id,))

        messages = cursor.fetchall()
        conn.close()

        return jsonify({
            "messages": [
                {
                    "from_name": m["from_name"],
                    "message": m["message"],
                    "timestamp": m["timestamp"]
                }
                for m in messages
            ]
        })

    except Exception as e:
        return jsonify({"error": f"Inbox backend error: {str(e)}"}), 500


# ===================== RUN =====================
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port)