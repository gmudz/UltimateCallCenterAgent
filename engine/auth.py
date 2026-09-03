"""
AI Sales Copilot — Authentication Engine
SQLite-based user management with bcrypt + JWT.
"""
import os
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List

import bcrypt
import jwt

# --- Config ---
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.db')
JWT_SECRET = os.environ.get('JWT_SECRET', secrets.token_hex(32))
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 24
COOKIE_NAME = 'copilot_session'


def get_db():
    """Get a database connection."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables and default admin."""
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'agent',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_login TEXT
        )
    ''')
    conn.commit()

    # Create default admin if no users exist
    cursor = conn.execute("SELECT COUNT(*) as cnt FROM users")
    count = cursor.fetchone()['cnt']
    if count == 0:
        hashed = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        conn.execute(
            "INSERT INTO users (username, password_hash, display_name, role) VALUES (?, ?, ?, ?)",
            ('admin', hashed, 'المدير', 'admin')
        )
        conn.commit()
        print("✅ Default admin created: admin / admin123")

    conn.close()


def create_user(username: str, password: str, display_name: str, role: str = 'agent') -> Dict:
    """Create a new user."""
    if role not in ('admin', 'agent'):
        return {"error": "الدور يجب أن يكون admin أو agent"}
    if len(username) < 3:
        return {"error": "اسم المستخدم يجب أن يكون 3 أحرف على الأقل"}
    if len(password) < 4:
        return {"error": "كلمة المرور يجب أن تكون 4 أحرف على الأقل"}

    conn = get_db()
    try:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        conn.execute(
            "INSERT INTO users (username, password_hash, display_name, role) VALUES (?, ?, ?, ?)",
            (username, hashed, display_name, role)
        )
        conn.commit()
        return {"success": True, "username": username, "role": role}
    except sqlite3.IntegrityError:
        return {"error": "اسم المستخدم موجود مسبقاً"}
    finally:
        conn.close()


def authenticate(username: str, password: str) -> Optional[Dict]:
    """Authenticate a user and return JWT token."""
    conn = get_db()
    cursor = conn.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (username,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return None

    if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        conn.close()
        return None

    # Update last login
    conn.execute("UPDATE users SET last_login = datetime('now') WHERE id = ?", (user['id'],))
    conn.commit()
    conn.close()

    # Generate JWT
    payload = {
        'user_id': user['id'],
        'username': user['username'],
        'display_name': user['display_name'],
        'role': user['role'],
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return {
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'display_name': user['display_name'],
            'role': user['role']
        }
    }


def verify_token(token: str) -> Optional[Dict]:
    """Verify a JWT token and return user data."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            'id': payload['user_id'],
            'username': payload['username'],
            'display_name': payload['display_name'],
            'role': payload['role']
        }
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def get_users() -> List[Dict]:
    """Get all users (for admin panel)."""
    conn = get_db()
    cursor = conn.execute("SELECT id, username, display_name, role, is_active, created_at, last_login FROM users ORDER BY id")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users


def delete_user(user_id: int) -> Dict:
    """Delete a user (cannot delete last admin)."""
    conn = get_db()
    # Check if this is the last admin
    user = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return {"error": "المستخدم غير موجود"}

    if user['role'] == 'admin':
        admin_count = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'admin' AND is_active = 1").fetchone()['cnt']
        if admin_count <= 1:
            conn.close()
            return {"error": "لا يمكن حذف آخر مدير"}

    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"success": True}


def change_password(user_id: int, new_password: str) -> Dict:
    """Change a user's password."""
    if len(new_password) < 4:
        return {"error": "كلمة المرور يجب أن تكون 4 أحرف على الأقل"}
    conn = get_db()
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed, user_id))
    conn.commit()
    conn.close()
    return {"success": True}


def toggle_user(user_id: int) -> Dict:
    """Toggle user active status."""
    conn = get_db()
    user = conn.execute("SELECT is_active, role FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return {"error": "المستخدم غير موجود"}
    if user['role'] == 'admin' and user['is_active']:
        admin_count = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'admin' AND is_active = 1").fetchone()['cnt']
        if admin_count <= 1:
            conn.close()
            return {"error": "لا يمكن تعطيل آخر مدير"}
    new_status = 0 if user['is_active'] else 1
    conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
    conn.commit()
    conn.close()
    return {"success": True, "is_active": new_status}


# Initialize on import
init_db()
