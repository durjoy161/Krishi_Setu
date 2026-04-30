# app/utils/helpers.py
# Shared utility functions used across all modules.
# NO imports from app.ui or app.services here — keeps this layer dependency-free.

import re
from datetime import datetime


# ── String / Format Helpers ────────────────────────────────────────────────────

def format_currency(amount: float, symbol: str = "৳") -> str:
    """Format a float as a currency string.  e.g.  1234.5  →  '৳ 1,234.50'"""
    try:
        return f"{symbol} {amount:,.2f}"
    except (TypeError, ValueError):
        return f"{symbol} 0.00"


def format_date(dt_string: str, fmt: str = "%d %b %Y") -> str:
    """
    Convert a SQLite datetime string to a human-readable date.
    e.g. '2026-04-20 10:30:00' → '20 Apr 2026'
    Returns the original string if parsing fails.
    """
    for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(dt_string, pattern).strftime(fmt)
        except (ValueError, TypeError):
            continue
    return str(dt_string) if dt_string else "—"


def truncate(text: str, max_len: int = 40) -> str:
    """Shorten a string and add '…' if it exceeds max_len."""
    text = str(text or "")
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


# ── Validation Helpers ─────────────────────────────────────────────────────────

def is_positive_number(value: str) -> bool:
    """Return True if value is a non-negative numeric string."""
    try:
        return float(value) >= 0
    except (ValueError, TypeError):
        return False


def is_valid_phone(phone: str) -> bool:
    """Basic Bangladeshi phone number check (01XXXXXXXXX, 11 digits)."""
    return bool(re.match(r"^01[3-9]\d{8}$", str(phone or "").strip()))


# ── Role Helpers ───────────────────────────────────────────────────────────────

ROLE_LABELS = {
    "farmer":   "🌾 Farmer",
    "customer": "🛒 Customer",
    "agent":    "🤝 Agent",
    "investor": "💰 Investor",
}

ROLE_COLORS = {
    "farmer":   "#52b788",
    "customer": "#4895ef",
    "agent":    "#f4a261",
    "investor": "#9b5de5",
}


def role_label(role: str) -> str:
    """Return a display-friendly role label with emoji."""
    return ROLE_LABELS.get(role, role.capitalize())


def role_color(role: str) -> str:
    """Return the brand color hex for a given role."""
    return ROLE_COLORS.get(role, "#ffffff")


# ── Status Badge Helpers ───────────────────────────────────────────────────────

ORDER_STATUS_COLORS = {
    "placed":     "#4895ef",
    "confirmed":  "#f4a261",
    "harvested":  "#9b5de5",
    "delivered":  "#52b788",
    "cancelled":  "#e63946",
}

PAYMENT_STATUS_COLORS = {
    "unpaid":   "#e63946",
    "partial":  "#f4a261",
    "paid":     "#52b788",
}

INVESTMENT_STATUS_COLORS = {
    "open":   "#4895ef",
    "funded": "#52b788",
    "closed": "#888888",
}


def order_status_color(status: str) -> str:
    return ORDER_STATUS_COLORS.get(status, "#888888")


def payment_status_color(status: str) -> str:
    return PAYMENT_STATUS_COLORS.get(status, "#888888")


def investment_status_color(status: str) -> str:
    return INVESTMENT_STATUS_COLORS.get(status, "#888888")
