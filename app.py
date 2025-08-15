from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import requests
import random
import os

app = Flask(__name__)

# sqllite database
def init_db():
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            joke TEXT,
            votes INTEGER DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            ip TEXT
        )
    ''')
    conn.commit()
    conn.close()
init_db()
#//////

@app.route('/')
def index():
    return render_template('smile.html')

@app.route('/index')
def home():
    return render_template('index.html')

@app.route('/smile', methods=['GET', 'POST'])
def smile():
    joke = ""
    latest_id = None
    latest_votes = 0
    if request.method == 'POST':
        try:
            data = requests.get("https://official-joke-api.appspot.com/random_joke").json()
            joke = f"{data['setup']} - {data['punchline']}"
        except Exception:
            fallback_jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "Why did the scarecrow win an award? Because he was outstanding in his field!",
                "Why don't skeletons fight each other? They don't have the guts!",
            ]
            joke = random.choice(fallback_jokes)

        conn = sqlite3.connect('messages.db')
        c = conn.cursor()
        c.execute('INSERT INTO messages (joke, votes) VALUES (?, ?)', (joke, 0))  #vote
        conn.commit()
        latest_id = c.lastrowid
        conn.close()
    
    return render_template('smile.html', joke=joke, latest_id=latest_id, latest_votes=latest_votes)


@app.route('/vote/<int:message_id>', methods=['POST'])
def vote(message_id):
    user_ip = request.remote_addr
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()

    c.execute('SELECT * FROM votes WHERE message_id = ? AND ip = ?', (message_id, user_ip))
    if c.fetchone() is None:
        c.execute('INSERT INTO votes (message_id, ip) VALUES (?, ?)', (message_id, user_ip))
        c.execute('UPDATE messages SET votes = votes + 1 WHERE id = ?', (message_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('smile'))

@app.route('/all')
def all_messages():
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('SELECT * FROM messages ORDER BY votes DESC') #vote
    messages = c.fetchall()
    conn.close()
    return render_template('all.html', messages=messages)

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
