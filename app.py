password" placeholder="Password" required>
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


