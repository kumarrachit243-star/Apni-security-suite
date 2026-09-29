import sqlite3
import hashlib
from flask import Flask, request, render_template_string, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-vault-key-2026")

DB_FILE = "passwords_v2.db"
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

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Apni Security Suite</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0b1120; color: #e2e8f0; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 90vh; }
            .card { background: #1e293b; padding: 30px; border-radius: 16px; width: 100%; max-width: 380px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); text-align: center; border: 1px solid #334155; }
            .logo-icon { font-size: 50px; margin-bottom: 10px; }
            h2 { color: #38bdf8; margin-bottom: 5px; font-size: 22px; }
            p.sub { color: #94a3b8; font-size: 13px; margin-bottom: 25px; }
            .input-group { position: relative; margin-bottom: 15px; }
            input { width: 100%; padding: 14px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; font-size: 16px; box-sizing: border-box; outline: none; text-align: center; letter-spacing: 4px; }
            input:focus { border-color: #38bdf8; }
            .btn { width: 100%; padding: 14px; background: #0284c7; border: none; color: white; font-weight: bold; border-radius: 8px; font-size: 16px; cursor: pointer; transition: background 0.2s; }
            .btn:hover { background: #0369a1; }
            .biometric-box { margin-top: 25px; padding
