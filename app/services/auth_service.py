# app/services/auth_service.py
# Authentication service — the ONLY place that touches passwords.
# UI and controllers must never handle raw hashes.

import re
import secrets
import bcrypt

from app.database.db_manager import (
    get_user_by_username,
    create_user,
    save_remember_token,
    get_user_by_remember_token,
    clear_remember_token,
)
import app.utils.session as session


# ── Password hashing ───────────────────────────────────────────────────────────

def hash_password(plain_text: str) -> str:
    """
    Hash a plain-text password with bcrypt (cost factor 12).
    Returns the hash as a UTF-8 string ready to store in the DB.

    bcrypt automatically generates a unique salt per hash —
    you never need to manage salt yourself.
    """
    password_bytes = plain_text.encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def verify_password(plain_text: str, stored_hash: str) -> bool:
    """
    Safely compare a plain-text attempt against a stored bcrypt hash.
    bcrypt.checkpw is timing-safe (prevents timing attacks).
    Returns True if they match, False otherwise.
    """
    try:
        return bcrypt.checkpw(
            plain_text.encode("utf-8"),
            stored_hash.encode("utf-8")
        )
    except Exception:
        # Handles corrupted hash or encoding issues gracefully
        return False


# ── Input validation ───────────────────────────────────────────────────────────

def validate_username(username: str) -> str | None:
    """
    Validate username format.
    Returns an error message string, or None if valid.
    Rules: 3-30 chars, alphanumeric + underscores only.
    """
    username = username.strip()
    if not username:
        return "Username cannot be empty."
    if len(username) < 3:
        return "Username must be at least 3 characters."
    if len(username) > 30:
        return "Username cannot exceed 30 characters."
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return "Username may only contain letters, numbers, and underscores."
    return None


def validate_email(email: str) -> str | None:
    """
    Validate email format (optional field — empty string is allowed).
    Returns an error message, or None if valid.
    """
    email = email.strip()
    if not email:
        return None     # email is optional
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email):
        return "Please enter a valid email address."
    return None


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Check password strength.
    Returns (is_valid: bool, message: str).

    Rules:
      - At least 8 characters
      - At least one uppercase letter
      - At least one lowercase letter
      - At least one digit
      - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit (0-9)."
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
        return False, "Password must contain at least one special character (!@#$... etc)."
    return True, "Strong password ✓"


def get_password_strength_label(password: str) -> tuple[str, str]:
    """
    Return a (label, color) tuple for real-time UI feedback.
    E.g. ("Weak", "#e63946") or ("Strong", "#2d6a4f")
    """
    length = len(password)
    checks = [
        bool(re.search(r"[A-Z]", password)),
        bool(re.search(r"[a-z]", password)),
        bool(re.search(r"\d", password)),
        bool(re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password)),
    ]
    score = sum(checks) + (1 if length >= 8 else 0) + (1 if length >= 12 else 0)

    if score <= 2:
        return "Weak", "#e63946"
    elif score <= 4:
        return "Fair", "#f4a261"
    elif score == 5:
        return "Good", "#2a9d8f"
    else:
        return "Strong", "#52b788"


# ── Core auth operations ───────────────────────────────────────────────────────

def register_user(username: str, password: str, confirm_password: str,
                  role: str, full_name: str, email: str = "",
                  phone: str = "", address: str = "") -> dict:
    """
    Register a new user.

    Returns a result dict:
        {"success": True,  "message": "..."}
        {"success": False, "message": "..."}

    Validation order: empty fields → username format → email format →
    password strength → passwords match → duplicate check → DB insert.
    """
    # ── 1. Required field checks ───────────────────────────────────────────────
    if not full_name.strip():
        return {"success": False, "message": "Full name cannot be empty."}

    username_error = validate_username(username)
    if username_error:
        return {"success": False, "message": username_error}

    email_error = validate_email(email)
    if email_error:
        return {"success": False, "message": email_error}

    if not password:
        return {"success": False, "message": "Password cannot be empty."}

    # ── 2. Password strength ───────────────────────────────────────────────────
    is_strong, strength_msg = validate_password_strength(password)
    if not is_strong:
        return {"success": False, "message": strength_msg}

    # ── 3. Password confirmation ───────────────────────────────────────────────
    if password != confirm_password:
        return {"success": False, "message": "Passwords do not match."}

    # ── 4. Role validation ─────────────────────────────────────────────────────
    valid_roles = ("farmer", "customer", "agent", "investor")
    if role not in valid_roles:
        return {"success": False, "message": f"Invalid role. Choose from: {', '.join(valid_roles)}."}

    # ── 5. Hash password and save ──────────────────────────────────────────────
    try:
        password_hash = hash_password(password)
        create_user(
            username=username.strip(),
            password_hash=password_hash,
            role=role,
            full_name=full_name.strip(),
            email=email.strip() or None,
            phone=phone.strip() or None,
            address=address.strip() or None,
        )
        return {
            "success": True,
            "message": f"Account created successfully! Welcome, {full_name.strip()}."
        }
    except ValueError as exc:
        # Duplicate username from db_manager
        return {"success": False, "message": str(exc)}
    except RuntimeError as exc:
        return {"success": False, "message": f"Could not create account: {exc}"}


def login(username: str, password: str, remember_me: bool = False) -> dict:
    """
    Authenticate a user.

    Returns:
        {"success": True,  "user": {...}, "token": "..." or None}
        {"success": False, "message": "..."}
    """
    # ── 1. Input presence check ────────────────────────────────────────────────
    if not username.strip() or not password:
        return {"success": False, "message": "Username and password are required."}

    # ── 2. Look up user ────────────────────────────────────────────────────────
    try:
        user = get_user_by_username(username)
    except RuntimeError as exc:
        return {"success": False, "message": f"Login error: {exc}"}

    if user is None:
        # Return a generic message to not reveal whether the username exists
        return {"success": False, "message": "Invalid username or password."}

    # ── 3. Verify password hash ────────────────────────────────────────────────
    stored_hash = user.get("password_hash", "")
    if not stored_hash or not verify_password(password, stored_hash):
        return {"success": False, "message": "Invalid username or password."}

    # ── 4. Populate session ────────────────────────────────────────────────────
    # Strip password_hash from the session dict for safety
    safe_user = {k: v for k, v in user.items() if k not in ("password_hash", "password")}
    session.set_user(safe_user)

    # ── 5. Remember Me ────────────────────────────────────────────────────────
    token = None
    if remember_me:
        token = _generate_remember_token(user["id"])

    return {"success": True, "user": safe_user, "token": token}


def login_with_token(token: str) -> dict:
    """
    Restore a session using a stored Remember Me token.
    Returns {"success": True, "user": {...}} or {"success": False}.
    """
    if not token or not token.strip():
        return {"success": False, "message": "No token provided."}
    try:
        user = get_user_by_remember_token(token.strip())
    except RuntimeError:
        return {"success": False, "message": "Token lookup failed."}

    if user is None:
        return {"success": False, "message": "Invalid or expired token."}

    safe_user = {k: v for k, v in user.items() if k not in ("password_hash", "password")}
    session.set_user(safe_user)
    return {"success": True, "user": safe_user}


def logout(clear_token: bool = True):
    """
    Clear the current session.
    If clear_token=True, also removes the remember_me token from the DB.
    """
    user = session.get_user()
    if clear_token and user:
        try:
            clear_remember_token(user.get("id", 0))
        except RuntimeError:
            pass    # Non-critical — still clear the session
    session.clear()


# ── Internal helpers ───────────────────────────────────────────────────────────

def _generate_remember_token(user_id: int) -> str:
    """
    Generate a cryptographically secure random token,
    persist it in the DB, and return it so the UI can store it locally.
    """
    token = secrets.token_urlsafe(48)
    save_remember_token(user_id, token)
    return token