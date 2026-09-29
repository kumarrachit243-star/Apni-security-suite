import os
import sqlite3
import hashlib
from flask import Flask, request, render_template_string, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-vault-key-2026")

DB_FILE = "passwords.db"
HASH_FILE = "master_v2.hash"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS vault (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL
                )''')
    conn.commit()
    conn.close()

init_db()

def verify_pin(pin):
    if pin == "1234":
        return True
    if not os.path.exists(HASH_FILE):
        return False
    with open(HASH_FILE, "r") as f:
        stored_hash = f.read().strip()
    return hashlib.sha256(pin.encode()).hexdigest() == stored_hash

BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Apni Security Suite</title>
    <style>
        body { font-family: sans-serif; background-color: #0b1120; color: #e2e8f0; margin: 0; padding: 15px; }
        .navbar { display: flex; justify-content: space-between; align-items: center; background: #1e293b; padding: 12px 18px; border-radius: 10px; }
        .brand { font-size: 18px; font-weight: bold; color: #38bdf8; text-decoration: none; }
        .menu-container { position: relative; display: inline-block; }
        .three-dots { font-size: 24px; cursor: pointer; color: #38bdf8; background: none; border: none; padding: 0 10px; }
        .dropdown-menu { display: none; position: absolute; right: 0; top: 35px; background-color: #1e293b; min-width: 180px; box-shadow: 0px 8px 16px rgba(0,0,0,0.5); border-radius: 8px; z-index: 10; border: 1px solid #334155; }
        .dropdown-menu a { color: #f8fafc; padding: 12px 16px; text-decoration: none; display: block; font-size: 14px; border-bottom: 1px solid #334155; }
        .card { background: #1e293b; padding: 20px; border-radius: 12px; margin-top: 20px; }
        .btn { width: 100%; padding: 12px; margin-top: 10px; background: #0284c7; border: none; color: white; font-weight: bold; border-radius: 8px; cursor: pointer; }
        .btn-back { background: #475569; margin-bottom: 15px; display: inline-block; padding: 8px 16px; color: white; border-radius: 6px; text-decoration: none; font-weight: bold; }
        input { width: 100%; padding: 12px; margin: 8px 0; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: white; box-sizing: border-box; }
        .vault-item { background: #0f172a; padding: 12px; margin-bottom: 10px; border-radius: 8px; border-left: 4px solid #38bdf8; }
    </style>
    <script>
        function toggleMenu() {
            var menu = document.getElementById("myDropdown");
            menu.style.display = (menu.style.display === "block") ? "none" : "block";
        }
    </script>
</head>
<body>
    <div class="navbar">
        <a href="/" class="brand">🔒 APNI SECURITY SUITE</a>
        {% if session.get('unlocked') %}
        <div class="menu-container">
            <button class="three-dots" onclick="toggleMenu()">⋮</button>
            <div id="myDropdown" class="dropdown-menu">
                <a href="/passwords">📂 View Passwords</a>
                <a href="/add">➕ Add Password</a>
                <a href="/change-pin">🔑 Change Master PIN</a>
                <a href="/logout" style="color: #ef4444;">🚪 Lock Vault</a>
            </div>
        </div>
        {% endif %}
    </div>
    <div class="card">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    error = None
    if request.method == "POST":
        pin = request.form.get("pin")
        if verify_pin(pin):
            session['unlocked'] = True
            return redirect(url_for('view_passwords'))
        else:
            error = "Invalid Master PIN!"
            
    if session.get('unlocked'):
        return redirect(url_for('view_passwords'))
        
    html = BASE_LAYOUT.replace("{% block content %}{% endblock %}", """
        <h2 style="text-align: center; color: #38bdf8;">BIOMETRIC / PIN LOCK</h2>
        {% if error %}<p style="color: #ef4444; text-align: center;">{{ error }}</p>{% endif %}
        <form method="POST">
            <input type="password" name="pin" placeholder="Enter Master PIN (Default: 1234)" required>
            <button type="submit" class="btn">Unlock Vault</button>
        </form>
    """)
    return render_template_string(html, error=error)

@app.route("/passwords")
def view_passwords():
    if not session.get('unlocked'):
        return redirect(url_for('home'))
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT service, username, password FROM vault")
    records = c.fetchall()
    conn.close()
    
    html = BASE_LAYOUT.replace("{% block content %}{% endblock %}", """
        <h3>📁 Saved Passwords</h3>
        {% if not records %}
            <p style="color: #94a3b8;">No passwords saved yet.</p>
        {% endif %}
        {% for item in records %}
            <div class="vault-item">
                <strong style="color: #38bdf8;">{{ item[0] }}</strong><br>
                <span>User: {{ item[1] }}</span><br>
                <span>Pass: {{ item[2] }}</span>
            </div>
        {% endfor %}
    """)
    return render_template_string(html, records=records)

@app.route("/add", methods=["GET", "POST"])
def add_password():
    if not session.get('unlocked'):
        return redirect(url_for('home'))
        
    if request.method == "POST":
        service = request.form.get("service")
        username = request.form.get("username")
        password = request.form.get("password")
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO vault (service, username, password) VALUES (?, ?, ?)", (service, username, password))
        conn.commit()
        conn.close()
        return redirect(url_for('view_passwords'))

    html = BASE_LAYOUT.replace("{% block content %}{% endblock %}", """
        <a href="/passwords" class="btn-back">← Back</a>
        <h3>➕ Add New Password</h3>
        <form method="POST">
            <input type="text" name="service" placeholder="Service / App Name" required>
            <input type="text" name="username" placeholder="Username / Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit" class="btn">Save Password</button>
        </form>
    """)
    return render_template_string(html)

@app.route("/change-pin", methods=["GET", "POST"])
def change_pin():
    if not session.get('unlocked'):
        return redirect(url_for('home'))
        
    msg = None
    if request.method == "POST":
        old_pin = request.form.get("old_pin")
        new_pin = request.form.get("new_pin")
        
        if verify_pin(old_pin):
            with open(HASH_FILE, "w") as f:
                f.write(hashlib.sha256(new_pin.encode()).hexdigest())
            msg = "Master PIN Updated Successfully!"
        else:
            msg = "Incorrect Old PIN!"

    html = BASE_LAYOUT.replace("{% block content %}{% endblock %}", """
        <a href="/passwords" class="btn-back">← Back</a>
        <h3>🔑 Change Master PIN</h3>
        {% if msg %}<p style="color: #38bdf8; text-align: center;">{{ msg }}</p>{% endif %}
        <form method="POST">
            <input type="password" name="old_pin" placeholder="Current Master PIN" required>
            <input type="password" name="new_pin" placeholder="New Master PIN" required>
            <button type="submit" class="btn">Update PIN</button>
        </form>
    """)
    return render_template_string(html, msg=msg)

@app.route("/logout")
def logout():
    session.pop('unlocked', None)
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
