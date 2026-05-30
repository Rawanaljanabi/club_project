from flask import Flask, request, render_template, jsonify, session
import sqlite3
import random
import os

app = Flask(__name__)
# CRITICAL: Set a secret key to enable secure user sessions
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-club-key-12345")

DB_FILE = "club.db"

@app.route('/secret-db-check')
def view_database():
    try:
        conn = sqlite3.connect('club.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Pull everything from your messages table
        cursor.execute("SELECT * FROM messages;")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "Database file exists, but it is completely empty."
        
        # Convert rows to a readable list of dictionaries
        return {"messages": [dict(r) for r in rows]}
    except Exception as e:
        return f"Error reading database: {str(e)}"
    
# ===================== DB =====================
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

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

    # 2. SMART SEEDING: Notice the passwords are all set to "PENDING"
    club_members = [
        ("alice12", "PENDING", "Alice"),
        ("bob34", "PENDING", "Bob"),
        ("charlie56", "PENDING", "Charlie"),
        ("rory", "PENDING", "Rory"),
        ("hanan", "PENDING", "Hanan"),
        ("amnah", "PENDING", "Amnah"),
        ("amal", "PENDING", "Amal"),
        ("aljawhara", "PENDING", "Aljawhara"),
        ("farah", "PENDING", "Farah"),
        ("lamya", "PENDING", "Lamya"),
        ("ola", "PENDING", "Ola"),
        ("malak", "PENDING", "Malak"),
        ("rawan", "PENDING", "Rawan"),
        ("anoud", "PENDING", "Anoud"),
        ("shahad", "PENDING", "Shahad"),
        ("raghad", "PENDING", "Raghad"),
        ("khuzama", "PENDING", "khuzama"),
        ("nuha", "PENDING", "Nuha"),
        ("omar", "PENDING", "Omar"),
        ("nabil", "PENDING", "the count of monte cristo: Nabil"),
        ("mohammed", "PENDING", "Mohammed"),
        ("ateem", "PENDING", "Ateem"),
        ("rawabi", "PENDING", "Rawabi"),
        ("sarah", "PENDING", "Sara"),
        ("najah", "PENDING", "Najah"),
        ("ren", "PENDING", "Ren"),
        ("alia", "PENDING", "Alia"),
        ("afnan", "PENDING", "Afnan"),
    ]

    for username, password, name in club_members:
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO users (username, password, name) 
                VALUES (?, ?, ?)
            """, (username, password, name))
            print(f"👤 Pre-seeded club member: {username}")
            
            #cursor.execute("UPDATE users SET password = 'PENDING' WHERE username = 'hanan'")
    conn.commit()
    conn.close()


# ===================== ROUTES =====================
@app.route("/")
def home():
    return render_template("page1.html")


# ---- Smart Login & First-Time Password Setter ----
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json() or {}
        username = data.get("username", "").strip().lower()
        password = data.get("password", "")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Look up the user by username first to see if they are on your hardcoded list
        cursor.execute("SELECT id, username, password, name FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return jsonify({"error": "You are not registered as an authorized club member! ❌"}), 401

        # CASE A: First time logging in! Set their typed password as permanent
        if user["password"] == "PENDING":
            cursor.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (password, user["id"])
            )
            conn.commit()
            
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["name"] = user["name"]
            conn.close()
            return jsonify({"success": True, "message": f"Welcome first timer! Your custom password has been saved! 🔒"})

        # CASE B: Returning user! Verify their password matches what they chose previously
        if user["password"] == password:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["name"] = user["name"]
            conn.close()
            return jsonify({"success": True, "message": f"Welcome back, {user['name']}!"})
        else:
            conn.close()
            return jsonify({"error": "Incorrect password for this club member!"}), 401

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