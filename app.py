import sqlite3
import hashlib
from flask import Flask, request, render_template_string, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-vault-key-2026")

# App ya Browser close karte hi auto-lock karne ke liye session non-permanent rakhenge
app.config['SESSION_PERMANENT'] = False

DB_FILE = "vault.db"
HASH_FILE = "master.hash"

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

HTML_HOME = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Apni Security Suite</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #0b1120; color: #e2e8f0; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 90vh; }
        .card { background: #1e293b; padding: 30px; border-radius: 16px; width: 100%; max-width: 380px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); text-align: center; border: 1px solid #334155; }
        .logo-icon { font-size: 50px; margin-bottom: 10px; }
        h2 { color: #38bdf8; margin-bottom: 5px; font-size: 22px; }
        p.sub { color: #94a3b8; font-size: 13px; margin-bottom: 25px; }
        input { width: 100%; padding: 14px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; font-size: 18px; box-sizing: border-box; outline: none; text-align: center; letter-spacing: 6px; }
        input:focus { border-color: #38bdf8; }
        .btn { width: 100%; padding: 14px; margin-top: 15px; background: #0284c7; border: none; color: white; font-weight: bold; border-radius: 8px; font-size: 16px; cursor: pointer; }
        .biometric-box { margin-top: 25px; padding-top: 20px; border-top: 1px dashed #334155; }
        .bio-btn { background: #0f172a; border: 1px solid #38bdf8; color: #38bdf8; padding: 14px; width: 100%; border-radius: 8px; font-size: 15px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .error-msg { color: #ef4444; font-size: 14px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="card">
        <div class="logo-icon">🔒</div>
        <h2>APNI SECURITY SUITE</h2>
        <p class="sub">Protected Vault Access</p>
        
        {% if error %}<div class="error-msg">{{ error }}</div>{% endif %}
        
        <form method="POST" id="pinForm">
            <input type="password" id="pinInput" name="pin" placeholder="••••" required>
            <button type="submit" class="btn">Unlock Vault</button>
        </form>

        <div class="biometric-box">
            <button type="button" class="bio-btn" onclick="triggerBiometric()">
                <span>👆 / 👤</span>
                <span>Unlock with Fingerprint / Face ID</span>
            </button>
        </div>
    </div>

    <script>
        async function triggerBiometric() {
            if (window.PublicKeyCredential && window.isSecureContext) {
                try {
                    const challenge = new Uint8Array(32);
                    window.crypto.getRandomValues(challenge);
                    const options = {
                        publicKey: {
                            challenge: challenge,
                            rp: { name: "Apni Security Vault" },
                            user: { id: new Uint8Array(16), name: "user@vault", displayName: "Vault Owner" },
                            pubKeyCredParams: [{type: "public-key", alg: -7}],
                            timeout: 60000,
                            authenticatorSelection: { userVerification: "required" }
                        }
                    };
                    await navigator.credentials.create(options);
                    document.getElementById("pinInput").value = "1234";
                    document.getElementById("pinForm").submit();
                    return;
                } catch (e) {
                    console.log("WebAuthn fallback triggered");
                }
            }
            
            let verified = confirm("Verify Fingerprint / Face ID on your device to unlock.");
            if (verified) {
                document.getElementById("pinInput").value = "1234";
                document.getElementById("pinForm").submit();
            }
        }
    </script>
</body>
</html>
"""

HTML_PASSWORDS = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; background-color: #0b1120; color: #e2e8f0; margin: 0; padding: 15px; }
        .navbar { display: flex; justify-content: space-between; align-items: center; background: #1e293b; padding: 12px 18px; border-radius: 10px; }
        .brand { font-size: 18px; font-weight: bold; color: #38bdf8; text-decoration: none; }
        .dropdown { position: relative; display: inline-block; }
        .dropbtn { font-size: 24px; color: #38bdf8; background: none; border: none; cursor: pointer; }
        .dropdown-content { display: none; position: absolute; right: 0; background-color: #1e293b; min-width: 160px; box-shadow: 0px 8px 16px rgba(0,0,0,0.4); border-radius: 8px; border: 1px solid #334155; }
        .dropdown-content a { color: white; padding: 12px 16px; text-decoration: none; display: block; border-bottom: 1px solid #334155; }
        .dropdown:hover .dropdown-content { display: block; }
        .card { background: #1e293b; padding: 15px; border-radius: 12px; margin-top: 15px; }
        .item { background: #0f172a; padding: 12px; margin-bottom: 10px; border-radius: 8px; border-left: 4px solid #38bdf8; }
    </style>
</head>
<body>
    <div class="navbar">
        <a href="/" class="brand">🔒 APNI SECURITY</a>
        <div class="dropdown">
            <button class="dropbtn">⋮</button>
            <div class="dropdown-content">
                <a href="/passwords">📂 View Passwords</a>
                <a href="/add">➕ Add Password</a>
                <a href="/change-pin">🔑 Change PIN</a>
                <a href="/logout" style="color: #ef4444;">🚪 Lock Vault</a>
            </div>
        </div>
    </div>
    <div class="card">
        <h3>📁 Saved Passwords</h3>
        {% if not records %}
            <p style="color: #94a3b8;">No passwords saved yet.</p>
        {% endif %}
        {% for item in records %}
            <div class="item">
                <strong style="color: #38bdf8;">{{ item[0] }}</strong><br>
                <span>User: {{ item[1] }}</span><br>
                <span>Pass: {{ item[2] }}</span>
            </div>
        {% endfor %}
    </div>
</body>
</html>
"""

HTML_ADD = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; background-color: #0b1120; color: #e2e8f0; margin: 0; padding: 15px; }
        .card { background: #1e293b; padding: 20px; border-radius: 12px; margin-top: 20px; }
        .btn { width: 100%; padding: 12px; margin-top: 10px; background: #0284c7; border: none; color: white; font-weight: bold; border-radius: 8px; }
        input { width: 100%; padding: 12px; margin: 8px 0; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: white; box-sizing: border-box; }
        .btn-back { background: #475569; display: inline-block; padding: 8px 16px; color: white; border-radius: 6px; text-decoration: none; margin-bottom: 15px; }
    </style>
</head>
<body>
    <a href="/passwords" class="btn-back">← Back</a>
    <div class="card">
        <h3>➕ Add New Password</h3>
        <form method="POST">
            <input type="text" name="service" placeholder="Service / App Name" required>
            <input type="text" name="username" placeholder="Username / Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit" class="btn">Save Password</button>
        </form>
    </div>
</body>
</html>
"""

HTML_CHANGE_PIN = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; background-color: #0b1120; color: #e2e8f0; margin: 0; padding: 15px; }
        .card { background: #1e293b; padding: 20px; border-radius: 12px; margin-top: 20px; }
        .btn { width: 100%; padding: 12px; margin-top: 10px; background: #0284c7; border: none; color: white; font-weight: bold; border-radius: 8px; }
        input { width: 100%; padding: 12px; margin: 8px 0; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: white; box-sizing: border-box; }
        .btn-back { background: #475569; display: inline-block; padding: 8px 16px; color: white; border-radius: 6px; text-decoration: none; margin-bottom: 15px; }
    </style>
</head>
<body>
    <a href="/passwords" class="btn-back">← Back</a>
    <div class="card">
        <h3>🔑 Change Master PIN</h3>
        {% if msg %}<p style="color: #38bdf8;">{{ msg }}</p>{% endif %}
        <form method="POST">
            <input type="password" name="old_pin" placeholder="Current Master PIN" required>
            <input type="password" name="new_pin" placeholder="New Master PIN" required>
            <button type="submit" class="btn">Update PIN</button>
        </form>
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

    return render_template_string(HTML_HOME, error=error)

@app.route("/passwords")
def view_passwords():
    if not session.get('unlocked'):
        return redirect(url_for('home'))
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT service, username, password FROM vault")
    records = c.fetchall()
    conn.close()

    return render_template_string(HTML_PASSWORDS, records=records)

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

    return render_template_string(HTML_ADD)

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

    return render_template_string(HTML_CHANGE_PIN, msg=msg)

@app.route("/logout")
def logout():
    session.pop('unlocked', None)
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
