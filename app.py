from flask import Flask, request, render_template, jsonify
import sqlite3
import random
import os

app = Flask(__name__)

DB_FILE = "club.db"


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
            name TEXT UNIQUE NOT NULL,
            picked INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            to_user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ===================== ROUTES =====================
@app.route("/")
def home():
    return render_template("page1.html")


# ---- Join user ----
@app.route("/join", methods=["POST"])
def join():
    try:
        name = request.form.get("name")

        if not name or not name.strip():
            return jsonify({"error": "Name is required"}), 400

        name = name.strip()

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (name, picked) VALUES (?, ?)",
                (name, 0)
            )
            conn.commit()
            conn.close()

            return jsonify({"success": True, "message": "User added"})

        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"success": True, "message": "User already exists"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---- Random user ----
@app.route("/random-user")
def random_user():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM users WHERE picked = 0")
        users = cursor.fetchall()

        # reset if all picked
        if len(users) == 0:
            cursor.execute("UPDATE users SET picked = 0")
            conn.commit()
            cursor.execute("SELECT id, name FROM users WHERE picked = 0")
            users = cursor.fetchall()

        if len(users) == 0:
            conn.close()
            return jsonify({"error": "No users available"}), 400

        chosen = random.choice(users)

        cursor.execute(
            "UPDATE users SET picked = 1 WHERE id = ?",
            (chosen["id"],)
        )

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "id": chosen["id"],
            "name": chosen["name"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---- Send message ----
@app.route("/send-appreciation", methods=["POST"])
def send_appreciation():
    try:
        data = request.get_json() or {}

        to_user_id = data.get("to_user_id")
        message = data.get("message")

        if not to_user_id:
            return jsonify({"error": "Missing user"}), 400

        if not message or not message.strip():
            return jsonify({"error": "Empty message"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO messages (to_user_id, message) VALUES (?, ?)",
            (to_user_id, message.strip())
        )

        conn.commit()
        conn.close()

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---- Inbox ----
@app.route("/inbox")
def inbox():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.name, m.message, m.timestamp
            FROM messages m
            JOIN users u ON m.to_user_id = u.id
            ORDER BY m.timestamp DESC
        """)

        messages = cursor.fetchall()
        conn.close()

        return jsonify({
            "messages": [
                {
                    "from_name": m["name"],
                    "message": m["message"],
                    "timestamp": m["timestamp"]
                }
                for m in messages
            ]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===================== RUN =====================
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

   if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)