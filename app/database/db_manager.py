# app/database/db_manager.py
# Manages SQLite database connection and table creation for Krishi Setu

import sqlite3
import os

# Database file location — stored next to this file
DB_PATH = os.path.join(os.path.dirname(__file__), "krishi_setu.db")


def get_connection():
    """Return a new SQLite connection with row_factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # Access columns by name
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    """Create all tables if they don't already exist, then seed with sample data."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── Users ──────────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            role        TEXT    NOT NULL CHECK(role IN ('farmer','customer','agent','investor')),
            full_name   TEXT    NOT NULL,
            email       TEXT,
            phone       TEXT,
            address     TEXT,
            farm_name   TEXT,    -- for farmers
            farm_size   TEXT,    -- for farmers
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

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
            order_type    TEXT    NOT NULL DEFAULT 'instant' CHECK(order_type IN ('instant','advance')),
            status        TEXT    NOT NULL DEFAULT 'placed'
                          CHECK(status IN ('placed','confirmed','harvested','delivered','cancelled')),
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

    # ── Investment Contributions ────────────────────────────────────────────────
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

    # Seed only if users table is empty
    from app.database.seed import seed_data
    seed_data()
