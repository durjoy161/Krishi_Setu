# app/database/db_manager.py
# Manages SQLite database connection and table creation for Krishi Setu.

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "krishi_setu.db")


def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row_factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def initialize_database():
    """
    Create all tables if they don't already exist.
    Run safe migrations for schema upgrades.
    Then seed with sample data.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ── Users ──────────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT    UNIQUE NOT NULL,
            password_hash   TEXT    NOT NULL DEFAULT '',
            password        TEXT,
            role            TEXT    NOT NULL
                            CHECK(role IN ('farmer','customer','agent','investor')),
            full_name       TEXT    NOT NULL,
            email           TEXT,
            phone           TEXT,
            address         TEXT,
            farm_name       TEXT,
            farm_size       TEXT,
            is_active       INTEGER NOT NULL DEFAULT 1,
            remember_token  TEXT,
            created_at      TEXT    DEFAULT (datetime('now'))
        )
    """)

    # Safe migrations — add columns that may not exist in older DBs
    _safe_add_column(cursor, "users", "password_hash",  "TEXT NOT NULL DEFAULT ''")
    _safe_add_column(cursor, "users", "remember_token", "TEXT")
    _safe_add_column(cursor, "users", "is_active",      "INTEGER NOT NULL DEFAULT 1")

    # ── Products ───────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id    INTEGER NOT NULL REFERENCES users(id),
            name         TEXT    NOT NULL,
            category     TEXT    NOT NULL,
            description  TEXT,
            price        REAL    NOT NULL,
            stock_qty    REAL    NOT NULL DEFAULT 0,
            unit         TEXT    NOT NULL DEFAULT 'kg',
            expiry_date  TEXT,
            created_at   TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Orders ─────────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id   INTEGER NOT NULL REFERENCES users(id),
            product_id    INTEGER NOT NULL REFERENCES products(id),
            farmer_id     INTEGER NOT NULL REFERENCES users(id),
            quantity      REAL    NOT NULL,
            total_price   REAL    NOT NULL,
            order_type    TEXT    NOT NULL DEFAULT 'instant'
                          CHECK(order_type IN ('instant','advance')),
            status        TEXT    NOT NULL DEFAULT 'placed'
                          CHECK(status IN
                            ('placed','confirmed','harvested','delivered','cancelled')),
            notes         TEXT,
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Payments ───────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id       INTEGER NOT NULL REFERENCES orders(id),
            amount_due     REAL    NOT NULL,
            amount_paid    REAL    NOT NULL DEFAULT 0,
            status         TEXT    NOT NULL DEFAULT 'unpaid'
                           CHECK(status IN ('unpaid','partial','paid')),
            method         TEXT    DEFAULT 'cash',
            paid_at        TEXT
        )
    """)

    # ── Investments ────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id       INTEGER NOT NULL REFERENCES users(id),
            title           TEXT    NOT NULL,
            description     TEXT,
            goal_amount     REAL    NOT NULL,
            raised_amount   REAL    NOT NULL DEFAULT 0,
            expected_roi    REAL    NOT NULL DEFAULT 0,
            status          TEXT    NOT NULL DEFAULT 'open'
                            CHECK(status IN ('open','funded','closed')),
            created_at      TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Investment Contributions ───────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investment_contributions (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            investment_id  INTEGER NOT NULL REFERENCES investments(id),
            investor_id    INTEGER NOT NULL REFERENCES users(id),
            amount         REAL    NOT NULL,
            contributed_at TEXT    DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()

    # Run data migrations
    _migrate_plaintext_passwords()

    # Seed only if empty
    from app.database.seed import seed_data
    seed_data()


# ── User CRUD helpers ──────────────────────────────────────────────────────────

def create_user(username: str, password_hash: str, role: str,
                full_name: str, email: str = None, phone: str = None,
                address: str = None, farm_name: str = None,
                farm_size: str = None) -> int:
    """Insert a new user and return the new row id."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users
                (username, password_hash, role, full_name,
                 email, phone, address, farm_name, farm_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (username.strip(), password_hash, role, full_name.strip(),
              email, phone, address, farm_name, farm_size))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return new_id
    except sqlite3.IntegrityError as exc:
        raise ValueError(f"Username '{username}' is already taken.") from exc
    except sqlite3.Error as exc:
        raise RuntimeError(f"Database error while creating user: {exc}") from exc


def get_user_by_username(username: str):
    """Fetch a single user row by username. Returns dict or None."""
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username.strip(),)
        ).fetchone()
        conn.close()
        return dict(row) if row else None
    except sqlite3.Error as exc:
        raise RuntimeError(f"Database error fetching user: {exc}") from exc


def get_user_by_id(user_id: int):
    """Fetch a user row by primary key."""
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None
    except sqlite3.Error as exc:
        raise RuntimeError(f"Database error fetching user: {exc}") from exc


def save_remember_token(user_id: int, token: str):
    """Persist a Remember Me token for the given user."""
    try:
        conn = get_connection()
        conn.execute(
            "UPDATE users SET remember_token = ? WHERE id = ?",
            (token, user_id)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as exc:
        raise RuntimeError(f"Database error saving token: {exc}") from exc


def get_user_by_remember_token(token: str):
    """Find a user whose remember_token matches."""
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE remember_token = ?", (token,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None
    except sqlite3.Error as exc:
        raise RuntimeError(f"Database error: {exc}") from exc


def clear_remember_token(user_id: int):
    """Remove the remember-me token on logout."""
    try:
        conn = get_connection()
        conn.execute(
            "UPDATE users SET remember_token = NULL WHERE id = ?",
            (user_id,)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as exc:
        raise RuntimeError(f"Database error: {exc}") from exc


def update_password_hash(user_id: int, new_hash: str):
    """Update a user's password hash."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET password_hash = ?, password = NULL WHERE id = ?",
        (new_hash, user_id)
    )
    conn.commit()
    conn.close()


# ── Internal helpers ───────────────────────────────────────────────────────────

def _safe_add_column(cursor, table: str, column: str, definition: str):
    """Add a column only if it doesn't already exist."""
    existing = [
        row[1] for row in
        cursor.execute(f"PRAGMA table_info({table})").fetchall()
    ]
    if column not in existing:
        cursor.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


def _migrate_plaintext_passwords():
    """
    One-time migration: hash any plain-text passwords still in the DB.
    After hashing, plain-text value is set to NULL.
    """
    import bcrypt
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, password FROM users
           WHERE (password_hash IS NULL OR password_hash = '')
           AND password IS NOT NULL"""
    ).fetchall()

    if rows:
        print(f"[Migration] Hashing {len(rows)} plain-text password(s)…")
        for row in rows:
            uid, plain = row["id"], row["password"]
            hashed = bcrypt.hashpw(
                plain.encode(), bcrypt.gensalt()
            ).decode()
            conn.execute(
                "UPDATE users SET password_hash = ?, password = NULL WHERE id = ?",
                (hashed, uid)
            )
        conn.commit()
        print("[Migration] Done.")
    conn.close()