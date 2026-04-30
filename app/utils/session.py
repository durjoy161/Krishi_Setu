# app/utils/session.py
# Global in-memory session store + local token file for "Remember Me"

import os
import json

# ── In-memory session ──────────────────────────────────────────────────────────
# Populated on successful login, cleared on logout.
# Password hash is NEVER stored here.
_current_user: dict = {}

# ── Remember Me token file ─────────────────────────────────────────────────────
# Stored in user's home dir (cross-platform, writable without admin rights)
_TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".krishi_setu_session")


# ── In-memory session API ──────────────────────────────────────────────────────

def set_user(user_dict: dict):
    """Store the logged-in user's info (password fields must already be stripped)."""
    global _current_user
    _current_user = dict(user_dict)


def get_user() -> dict:
    """Return the currently logged-in user dict (empty dict if not logged in)."""
    return _current_user


def is_logged_in() -> bool:
    """Return True if a user is currently in session."""
    return bool(_current_user)


def clear():
    """Clear in-memory session (call on logout)."""
    global _current_user
    _current_user = {}


def get_role() -> str:
    """Convenience: return role string or empty string."""
    return _current_user.get("role", "")


def get_id() -> int:
    """Convenience: return user id or 0."""
    return _current_user.get("id", 0)


def get_name() -> str:
    """Convenience: return full name or fallback."""
    return _current_user.get("full_name", "User")


# ── Remember Me token persistence ─────────────────────────────────────────────

def save_remember_token(token: str):
    """
    Write a Remember Me token to a local file.
    Used so the app can auto-login on next launch.
    """
    try:
        with open(_TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump({"token": token}, f)
    except OSError:
        pass    # Silently ignore — Remember Me is non-critical


def load_remember_token() -> str | None:
    """
    Read the persisted Remember Me token from disk.
    Returns None if the file doesn't exist or is invalid.
    """
    try:
        if not os.path.exists(_TOKEN_FILE):
            return None
        with open(_TOKEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("token")
    except (OSError, json.JSONDecodeError):
        return None


def delete_remember_token():
    """Remove the local token file on explicit logout."""
    try:
        if os.path.exists(_TOKEN_FILE):
            os.remove(_TOKEN_FILE)
    except OSError:
        pass