import os
import json
import sqlite3
import urllib.request
from flask import Flask, request, jsonify, render_template

app = Flask(__name__, template_folder="../templates", static_folder="../static")

# Default credentials for user sign-in
USERS = {
    "aibin@gmail.com":   { "name": "Aibin",   "pass": "aibin123"   },
    "milan@gmail.com":   { "name": "Milan",   "pass": "milan123"   },
    "edwin@gmail.com":   { "name": "Edwin",   "pass": "edwin123"   },
    "seba@gmail.com":    { "name": "Seba",    "pass": "seba123"    },
    "lakshmi@gmail.com": { "name": "Lakshmi", "pass": "lakshmi123" },
}

# Vercel KV Credentials
KV_URL = os.environ.get("KV_REST_API_URL")
KV_TOKEN = os.environ.get("KV_REST_API_TOKEN")

# Global state format mapping chapter string to user name: {"1": "Aibin", "3": "Milan"}
INITIAL_SEED = {}

def call_kv(command):
    if not KV_URL or not KV_TOKEN:
        return None
    try:
        req = urllib.request.Request(
            KV_URL,
            data=json.dumps(command).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {KV_TOKEN}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode("utf-8"))
            return res.get("result")
    except Exception as e:
        print("Vercel KV Error:", e)
        return None

def get_db():
    db_path = '/tmp/database.db' if os.environ.get('VERCEL') else 'database.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shared_state (
                id TEXT PRIMARY KEY,
                marked TEXT NOT NULL DEFAULT '{}',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute("INSERT OR IGNORE INTO shared_state (id, marked) VALUES ('global', '{}')")
        conn.commit()
        conn.close()
    except Exception as e:
        print("Local SQLite Init Error:", e)

init_db()

def get_shared_data():
    if KV_URL and KV_TOKEN:
        result = call_kv(["GET", "shared_chapters_data"])
        if result is not None:
            try:
                data = json.loads(result)
                if isinstance(data, list): # if they have the old list format, reset it
                    return INITIAL_SEED
                return data
            except Exception:
                pass
        else:
            call_kv(["SET", "shared_chapters_data", json.dumps(INITIAL_SEED)])
            return INITIAL_SEED

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT marked FROM shared_state WHERE id = 'global'")
        row = cursor.fetchone()
        conn.close()
        if row and row["marked"]:
            data = json.loads(row["marked"])
            if isinstance(data, list):
                return INITIAL_SEED
            return data
        return INITIAL_SEED
    except Exception as e:
        print("SQLite get error:", e)
        return INITIAL_SEED

def save_shared_data(new_data):
    if KV_URL and KV_TOKEN:
        result = call_kv(["SET", "shared_chapters_data", json.dumps(new_data)])
        if result == "OK":
            return True
            
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE shared_state SET marked = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 'global'", (json.dumps(new_data),))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("SQLite save error:", e)
        return False

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email", "").lower()
    password = data.get("password", "")
    
    user = USERS.get(email)
    if not user or user["pass"] != password:
        return jsonify({"error": "Invalid email or password."}), 401
        
    return jsonify({"name": user["name"], "email": email}), 200

@app.route("/api/chapters", methods=["GET", "POST"])
def chapters():
    try:
        if request.method == "GET":
            return jsonify(get_shared_data()), 200
            
        if request.method == "POST":
            payload = request.json
            action = payload.get("action")
            chapter = str(payload.get("chapter"))
            user_name = payload.get("user")
            
            if not action or not chapter:
                return jsonify({"error": "Invalid payload format."}), 400
                
            current_data = get_shared_data()
            
            if action == "mark":
                if not user_name:
                    return jsonify({"error": "User name required to mark."}), 400
                current_data[chapter] = user_name
            elif action == "unmark":
                if chapter in current_data:
                    del current_data[chapter]
                    
            if save_shared_data(current_data):
                return jsonify({"ok": True, "data": current_data}), 200
            else:
                return jsonify({"error": "Failed to save chapter progress."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
