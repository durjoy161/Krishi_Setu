# app/controllers/auth_controller.py
# Thin controller layer — delegates to auth_service

from app.services.auth_service import authenticate as _authenticate


def authenticate(username: str, password: str) -> bool:
    """Authenticate user against database (replaces old dict-based check)."""
    return _authenticate(username, password)