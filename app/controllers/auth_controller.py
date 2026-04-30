# app/controllers/auth_controller.py
# Thin controller layer — delegates entirely to auth_service.
# Kept for backward compatibility with any code that already imports from here.

from app.services.auth_service import login as _login, logout as _logout


def authenticate(username: str, password: str) -> bool:
    """
    Backward-compatible wrapper used by existing code.
    Delegates to auth_service.login().
    Returns True on success, False on failure.
    """
    result = _login(username, password)
    return result["success"]


def sign_out():
    """Log out the current user and clear token."""
    _logout(clear_token=True)