import sqlite3
import hashlib
import hmac
import secrets
from pathlib import Path
import streamlit as st

BASE = Path(__file__).resolve().parent
DB = BASE / 'ajaltoun.sqlite'
LEVELS = {99: 'Administrator', 50: 'Director', 20: 'Teacher', 10: 'Attendance Staff', 1: 'Student'}
PAGES = {
    'hello': {99, 50, 20, 10},
    'app2': {99, 50},
    'exam': {99, 50, 20, 1},
    'stdnote': {99, 50, 20},
    'stdnote_view': {99, 50, 20},
    'attendance': {99, 50, 10},
    'attendanceall': {99, 50, 10},
    'mygrades': {99},
    'users': {99},
}

def connect():
    con = sqlite3.connect(DB, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA busy_timeout=15000')
    return con

def init_db():
    with connect() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            level INTEGER NOT NULL CHECK(level IN (1,10,20,50,99)),
            student_num INTEGER,
            active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1))
        )''')

def hash_password(password):
    salt = secrets.token_bytes(16)
    rounds = 600000
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, rounds)
    return f'pbkdf2_sha256${rounds}${salt.hex()}${digest.hex()}'

def verify_password(password, encoded):
    try:
        algorithm, rounds, salt, expected = encoded.split('$')
        if algorithm != 'pbkdf2_sha256':
            return False
        actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), int(rounds))
        return hmac.compare_digest(actual, bytes.fromhex(expected))
    except (ValueError, TypeError):
        return False

def _student_by_number(number):
    # Compare the stored student number exactly, without wildcard matching.
    with connect() as con:
        return con.execute('''SELECT NUM, NAME, CLASS FROM student
                              WHERE CAST(NUM AS TEXT) = ? LIMIT 1''', (number,)).fetchone()

def authenticate(username, password):
    username = username.strip()
    if username.casefold() == 'student':
        number = password.strip()
        if not number or not number.isdecimal():
            return None
        row = _student_by_number(number)
        if row is None:
            return None
        return {'id': None, 'username': 'student', 'level': 1,
                'student_num': row['NUM'], 'student_name': row['NAME'],
                'student_class': row['CLASS'], 'student_login': True}
    with connect() as con:
        user = con.execute('SELECT * FROM users WHERE username=? AND active=1', (username,)).fetchone()
    if user is None or not verify_password(password, user['password_hash']):
        return None
    return {'id': user['id'], 'username': user['username'],
            'level': user['level'], 'student_num': user['student_num']}

def current_user():
    saved = st.session_state.get('user')
    if not saved:
        return None
    if saved.get('student_login') is True and saved.get('username') == 'student' and saved.get('level') == 1:
        number = str(saved.get('student_num', ''))
        row = _student_by_number(number)
        if row is None:
            st.session_state.pop('user', None)
            return None
        return {'id': None, 'username': 'student', 'level': 1,
                'student_num': row['NUM'], 'student_name': row['NAME'],
                'student_class': row['CLASS'], 'student_login': True}
    if saved.get('id') is None:
        return None
    with connect() as con:
        row = con.execute('SELECT id,username,level,student_num FROM users WHERE id=? AND active=1',
                          (saved['id'],)).fetchone()
    if row is None:
        st.session_state.pop('user', None)
        return None
    return dict(row)

def allowed(page, user=None):
    user = user if user is not None else current_user()
    return bool(user and user['level'] in PAGES.get(page, set()))

def require_page(page):
    if not allowed(page):
        st.error('Access denied. Please log in with an authorized account.')
        st.stop()

def create_first_admin(username, password):
    if not username.strip() or len(password) < 12:
        raise ValueError('Enter a username and a password of at least 12 characters.')
    if username.strip().casefold() == 'student':
        raise ValueError('The username student is reserved for student login.')
    with connect() as con:
        if con.execute('SELECT COUNT(*) FROM users').fetchone()[0]:
            raise ValueError('Initial setup is already complete.')
        con.execute('INSERT INTO users(username,password_hash,level) VALUES(?,?,99)',
                    (username.strip(), hash_password(password)))

def has_users():
    with connect() as con:
        return bool(con.execute('SELECT COUNT(*) FROM users').fetchone()[0])
