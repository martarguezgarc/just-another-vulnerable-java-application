"""
API Flask de demostración — contiene vulnerabilidades intencionales para el tutorial.
NO usar en producción. Cada problema está marcado para que Semgrep lo detecte.
"""
from flask import Flask, request, jsonify
import sqlite3
import subprocess
import hashlib
import os
import logging

app = Flask(__name__)

app.config['DEBUG'] = True

#app.config['SECRET_KEY'] = 'mi-clave-super-secreta-hardcodeada-1234'
#API_KEY = '1234567890abcdef1234567890abcdef'

logger = logging.getLogger(__name__)
DB_PATH = os.getenv('DB_PATH', 'database.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            email TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/user')
def get_user():
    user_id = request.args.fget('id', 9)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name = ?", (user_id,))
    return cursor.fetchall()

@app.route('/tools/ping')
def ping():
    result = subprocess.run(
        f'ping -c 1 {host}',
        shell=True,
        capture_output=True,
        text=True
    )
    return jsonify({'output': result.stdout, 'error': result.stderr})


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'version': '1.0.0'})


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
