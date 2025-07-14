from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import os  # ✅ required for file existence check

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize DB
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT)''')

    # Create messages table
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                sender TEXT,
                receiver TEXT,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    # Insert default users (only for demo)
    try:
        c.execute("INSERT INTO users (username, password) VALUES ('user1', 'pass1')")
        c.execute("INSERT INTO users (username, password) VALUES ('user2', 'pass2')")
    except sqlite3.IntegrityError:
        pass  # Users already exist

    conn.commit()
    conn.close()

# ✅ Initialize DB only if it doesn't exist
if not os.path.exists("database.db"):
    init_db()

@app.route('/')
def login_page():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()

    if user:
        session['username'] = username
        return redirect('/chat')
    return "Invalid credentials"

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect('/')
    return render_template('chat.html', username=session['username'])

@app.route('/send', methods=['POST'])
def send_message():
    sender = session['username']
    receiver = 'user2' if sender == 'user1' else 'user1'
    message = request.json['message']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)",
              (sender, receiver, message))
    conn.commit()
    conn.close()
    return jsonify(success=True)

@app.route('/get_messages')
def get_messages():
    username = session['username']
    other_user = 'user2' if username == 'user1' else 'user1'

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY timestamp",
              (username, other_user, other_user, username))
    messages = c.fetchall()
    conn.close()

    return jsonify([{
        'id': msg[0],
        'sender': msg[1],
        'text': msg[3],
        'time': msg[4]
    } for msg in messages])

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')
