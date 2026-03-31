# app/services/auth_service.py
# Handles user authentication against the SQLite database

from app.database.db_manager import get_connection
import app.utils.session as session


def authenticate(username: str, password: str) -> bool:
    """
    Verify credentials against the database.
    On success, populates the global session and returns True.
    """
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username.strip(), password.strip())
    ).fetchone()
    conn.close()

    if row:
        # Store all user fields in the global session dict
        session.set_user(dict(row))
        return True
    return False


def get_all_users():
    """Return list of all users (for agent view)."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM users ORDER BY role, full_name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_users_by_role(role: str):
    """Return all users with a given role."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM users WHERE role = ? ORDER BY full_name", (role,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
