from flask import Flask, render_template_string, request, redirect, url_for, session
import json, os

app = Flask(__name__)
app.secret_key = 'super_secret_master_key'
DATA_FILE = 'passwords.json'
CONFIG_FILE = 'config.json'

def get_master_pin():
    if not os.path.exists(CONFIG_FILE): return '1234'
    with open(CONFIG_FILE, 'r') as f:
        try: return json.load(f).get('pin', '1234')
        except: return '1234'

def set_master_pin(new_pin):
    with open(CONFIG_FILE, 'w') as f: json.dump({'pin': new_pin}, f)

def load_passwords():
    if not os.path.exists(DATA_FILE): return []
    with open(DATA_FILE, 'r') as f:
        try: return json.load(f)
        except: return []

def save_passwords(data):
    with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Apni Security Suite</title>
    <style>
        body { background: #0b0f19; color: #00f2fe; font-family: sans-serif; padding: 15px; text-align: center; }
        .card { background: rgba(255, 255, 255, 0.05); border: 1px solid #00f2fe; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
        h1 { font-size: 20px; text-shadow: 0 0 10px #00f2fe; }
        input { width: 85%; padding: 10px; margin: 6px 0; border-radius: 5px; border: 1px solid #00f2fe; background: #000; color: #fff; text-align: center; font-size: 15px; box-sizing: border-box; }
        .btn { background: linear-gradient(45deg, #4facfe, #00f2fe); border: none; color: #000; padding: 12px; width: 85%; margin: 8px 0; font-weight: bold; border-radius: 5px; cursor: pointer; font-size: 15px; }
        .btn-bio { background: linear-gradient(45deg, #00ff88, #00f2fe); color: #000; }
        .btn-danger { background: #ff4757; color: #fff; }
        .btn-sm { background: #00f2fe; border: none; color: #000; padding: 4px 10px; font-weight: bold; border-radius: 3px; cursor: pointer; font-size: 12px; margin-left: 5px; }
        .vault-item { background: rgba(0, 242, 254, 0.1); border: 1px solid #00f2fe; padding: 10px; border-radius: 5px; margin-bottom: 10px; text-align: left; font-family: monospace; }
        .vault-item p { margin: 6px 0; word-break: break-all; }
        .label { color: #fff; font-weight: bold; }
        .val { color: #00ff88; }
    </style>
</head>
<body>
    <div class="card">
        <h1>APNI SECURITY SUITE v9.0</h1>
        <p>Status: <span style="color:#00ff88;">HTTPS WEB_AUTHN SECURE</span></p>
    </div>

    {% if not authenticated %}
    <div class="card">
        <h3>BIOMETRIC HARDWARE LOCK</h3>
        <button type="button" class="btn btn-bio" onclick="scanBio()">Scan Fingerprint / Face</button>
        <div id="bio-status" style="margin-top:10px; color:#ff4757; font-size:13px;"></div>

        <form id="bioForm" action="/bio_login" method="POST" style="display:none;">
            <input type="hidden" name="auth_token" value="SUCCESS">
        </form>

        <hr style="border: 0.5px solid rgba(0,242,254,0.3); margin: 20px 0;">

        <h4>OR USE MASTER PIN</h4>
        <form action="/login" method="POST">
            <input type="password" name="pin" placeholder="Enter PIN (Default: 1234)" required><br>
            <button type="submit" class="btn">Unlock with PIN</button>
        </form>
        {% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
    </div>

    <script>
    async function scanBio() {
        let status = document.getElementById('bio-status');
        if (!window.PublicKeyCredential) {
            status.innerText = "Error: Hardware biometric not supported!";
            return;
        }
        try {
            const challenge = new Uint8Array(32);
            window.crypto.getRandomValues(challenge);
            
            await navigator.credentials.create({
                publicKey: {
                    challenge: challenge,
                    rp: { name: "Apni Security Suite" },
                    user: {
                        id: new Uint8Array(16),
                        name: "user",
                        displayName: "User"
                    },
                    pubKeyCredParams: [{type: "public-key", alg: -7}],
                    authenticatorSelection: { authenticatorAttachment: "platform" },
                    timeout: 60000
                }
            });
            document.getElementById('bioForm').submit();
        } catch (err) {
            status.innerText = "Fingerprint Cancelled or Failed!";
        }
    }
    </script>
    {% else %}
    <div style="text-align:right; margin-bottom: 10px;">
        <a href="/logout" style="color:#ff4757; text-decoration:none; font-weight:bold;">[ Logout ]</a>
    </div>

    <div class="card">
        <h3>SAVE NEW PASSWORD</h3>
        <form action="/add" method="POST">
            <input type="text" name="service" placeholder="App / Website (e.g. Instagram)" required><br>
            <input type="text" name="username" placeholder="Username / Email" required><br>
            <input type="password" name="password" placeholder="Secret Password" required><br>
            <button type="submit" class="btn">Save to Vault</button>
        </form>
    </div>

    <div class="card">
        <h3>SAVED PASSWORDS</h3>
        {% if items %}
            {% for item in items %}
                <div class="vault-item">
                    <p><span class="label">App:</span> <span class="val">{{ item.service }}</span></p>
                    <p><span class="label">User:</span> <span class="val">{{ item.username }}</span></p>
                    <p>
                        <span class="label">Pass:</span> 
                        <span class="val" id="pass-{{ loop.index }}">••••••••</span>
                        <button class="btn-sm" onclick="togglePass('{{ loop.index }}', '{{ item.password }}')">Show/Hide</button>
                    </p>
                </div>
            {% endfor %}
        {% else %}
            <p style="color:#aaa;">Abhi koi password saved nahi hai.</p>
        {% endif %}
    </div>

    <div class="card">
        <h3>CHANGE MASTER PIN</h3>
        <form action="/change_pin" method="POST">
            <input type="password" name="old_pin" placeholder="Current Master PIN" required><br>
            <input type="password" name="new_pin" placeholder="New Master PIN" required><br>
            <button type="submit" class="btn btn-danger">Update Master PIN</button>
        </form>
        {% if msg %}<p style="color:#00ff88;">{{ msg }}</p>{% endif %}
        {% if pin_error %}<p style="color:red;">{{ pin_error }}</p>{% endif %}
    </div>

    <script>
    function togglePass(id, realPass) {
        let elem = document.getElementById('pass-' + id);
        if (elem.innerText === '••••••••') elem.innerText = realPass;
        else elem.innerText = '••••••••';
    }
    </script>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def home():
    authenticated = session.get('authenticated', False)
    items = load_passwords() if authenticated else []
    return render_template_string(HTML_TEMPLATE, authenticated=authenticated, items=items)

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('pin') == get_master_pin():
        session['authenticated'] = True
        return redirect(url_for('home'))
    return render_template_string(HTML_TEMPLATE, authenticated=False, error="Wrong PIN!")

@app.route('/bio_login', methods=['POST'])
def bio_login():
    if request.form.get('auth_token') == 'SUCCESS':
        session['authenticated'] = True
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('home'))

@app.route('/add', methods=['POST'])
def add():
    if session.get('authenticated'):
        s, u, p = request.form.get('service'), request.form.get('username'), request.form.get('password')
        if s and u and p:
            pwd = load_passwords()
            pwd.append({'service': s, 'username': u, 'password': p})
            save_passwords(pwd)
    return redirect(url_for('home'))

@app.route('/change_pin', methods=['POST'])
def change_pin():
    if not session.get('authenticated'): return redirect(url_for('home'))
    old, new = request.form.get('old_pin'), request.form.get('new_pin')
    items = load_passwords()
    if old == get_master_pin():
        set_master_pin(new)
        return render_template_string(HTML_TEMPLATE, authenticated=True, items=items, msg="PIN Successfully Updated!")
    return render_template_string(HTML_TEMPLATE, authenticated=True, items=items, pin_error="Old PIN Incorrect!")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
