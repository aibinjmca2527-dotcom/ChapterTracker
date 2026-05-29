import os
import json
import sqlite3
import urllib.request
import urllib.parse
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

# Vercel KV Credentials (automatically supplied by Vercel when connected)
KV_URL = os.environ.get("KV_REST_API_URL")
KV_TOKEN = os.environ.get("KV_REST_API_TOKEN")

# Initial data seed for either local database or cloud KV store
INITIAL_SEED = {
    "Aibin": [],
    "Milan": [],
    "Edwin": [],
    "Seba": [],
    "Lakshmi": []
}

def call_kv(command):
    """
    Executes a Redis command on Vercel KV via its REST API using the 
    built-in urllib.request library (zero external dependencies).
    """
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
    """Returns a local SQLite connection (fallback / local development)."""
    db_path = '/tmp/database.db' if os.environ.get('VERCEL') else 'database.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the local SQLite database if not exists."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chapters (
                user_name TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                marked TEXT NOT NULL DEFAULT '[]',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        seed_users = [
            {"name": "Aibin",   "email": "aibin@gmail.com"},
            {"name": "Milan",   "email": "milan@gmail.com"},
            {"name": "Edwin",   "email": "edwin@gmail.com"},
            {"name": "Seba",    "email": "seba@gmail.com"},
            {"name": "Lakshmi", "email": "lakshmi@gmail.com"},
        ]
        
        for u in seed_users:
            cursor.execute("INSERT OR IGNORE INTO chapters (user_name, email, marked) VALUES (?, ?, '[]')", (u["name"], u["email"]))
            
        conn.commit()
        conn.close()
    except Exception as e:
        print("Local SQLite Init Error:", e)

# Always initialize local SQLite for local execution/fallbacks
init_db()

def get_chapters_data():
    """Gets the full state of all chapters read, either from Vercel KV or SQLite fallback."""
    # 1. Try Vercel KV first if it's set up
    if KV_URL and KV_TOKEN:
        result = call_kv(["GET", "chapters_data"])
        if result is not None:
            try:
                return json.loads(result)
            except Exception as e:
                print("Failed to parse Vercel KV payload:", e)
        else:
            # Key does not exist in Redis, seed it with the default template
            print("Vercel KV empty. Seeding INITIAL_SEED...")
            call_kv(["SET", "chapters_data", json.dumps(INITIAL_SEED)])
            return INITIAL_SEED

    # 2. Local Fallback: Use SQLite
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT user_name, marked FROM chapters")
        rows = cursor.fetchall()
        data = {}
        for row in rows:
            data[row["user_name"]] = json.loads(row["marked"] if row["marked"] else "[]")
        conn.close()
        return data
    except Exception as e:
        print("SQLite get error (using fallback):", e)
        return INITIAL_SEED

def save_chapters_data(name, chapters_list):
    """Saves the updated chapter state for a user, either to Vercel KV or SQLite."""
    # 1. Try Vercel KV first if configured
    if KV_URL and KV_TOKEN:
        current_data = get_chapters_data()
        current_data[name] = chapters_list
        result = call_kv(["SET", "chapters_data", json.dumps(current_data)])
        if result == "OK":
            return True
        print("Vercel KV write failed, falling back to SQLite...")

    # 2. Local Fallback: Use SQLite
    try:
        conn = get_db()
        cursor = conn.cursor()
        marked_json = json.dumps(chapters_list)
        cursor.execute("UPDATE chapters SET marked = ?, updated_at = CURRENT_TIMESTAMP WHERE user_name = ?", (marked_json, name))
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
            data = get_chapters_data()
            return jsonify(data), 200
            
        if request.method == "POST":
            data = request.json
            name = data.get("name")
            chapters_list = data.get("chapters")
            
            if not name or not isinstance(chapters_list, list):
                return jsonify({"error": "Invalid payload format."}), 400
                
            chapters_list.sort()
            if save_chapters_data(name, chapters_list):
                return jsonify({"ok": True}), 200
            else:
                return jsonify({"error": "Failed to save chapter progress."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
