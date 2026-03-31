# app/utils/session.py
# Global session store — holds the currently logged-in user

# This dict is populated after a successful login and cleared on logout.
current_user = {}


def set_user(user_dict: dict):
    """Store the logged-in user's info."""
    global current_user
    current_user = dict(user_dict)


def get_user() -> dict:
    """Return the currently logged-in user dict."""
    return current_user


def clear():
    """Clear session on logout."""
    global current_user
    current_user = {}


def get_role() -> str:
    """Convenience: return role string or empty string."""
    return current_user.get("role", "")


def get_id() -> int:
    """Convenience: return user id or 0."""
    return current_user.get("id", 0)


def get_name() -> str:
    """Convenience: return full name."""
    return current_user.get("full_name", "User")
