import os
import json
import libsql_client
from flask import Flask, request, jsonify, render_template

app = Flask(__name__, template_folder="../templates", static_folder="../static")

USERS = {
    "aibin@gmail.com":   { "name": "Aibin",   "pass": "aibin123"   },
    "milan@gmail.com":   { "name": "Milan",   "pass": "milan123"   },
    "edwin@gmail.com":   { "name": "Edwin",   "pass": "edwin123"   },
    "seba@gmail.com":    { "name": "Seba",    "pass": "seba123"    },
    "lakshmi@gmail.com": { "name": "Lakshmi", "pass": "lakshmi123" },
}

def get_db():
    url = os.environ.get("TURSO_DATABASE_URL", "file:database.db")
    token = os.environ.get("TURSO_AUTH_TOKEN", "")
    return libsql_client.create_client_sync(url=url, auth_token=token)

def init_db():
    try:
        client = get_db()
        client.execute('''
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
            client.execute("INSERT OR IGNORE INTO chapters (user_name, email, marked) VALUES (?, ?, '[]')", [u["name"], u["email"]])
            
        client.close()
    except Exception as e:
        print("DB Init Error:", e)

# Initialize DB on startup
init_db()

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
        client = get_db()
    except Exception as e:
        return jsonify({"error": f"DB Connection Error: {str(e)}"}), 500
        
    try:
        if request.method == "GET":
            rs = client.execute("SELECT user_name, marked FROM chapters")
            data = {}
            for row in rs.rows:
                # libsql_client rows can be accessed by index or name. index is safest
                data[row[0]] = json.loads(row[1] if row[1] else "[]")
            return jsonify(data), 200
            
        if request.method == "POST":
            data = request.json
            name = data.get("name")
            chapters_list = data.get("chapters")
            
            if not name or not isinstance(chapters_list, list):
                return jsonify({"error": "Invalid body"}), 400
                
            chapters_list.sort()
            marked_json = json.dumps(chapters_list)
            
            client.execute("UPDATE chapters SET marked = ?, updated_at = CURRENT_TIMESTAMP WHERE user_name = ?", [marked_json, name])
            return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()

if __name__ == "__main__":
    app.run(debug=True)
