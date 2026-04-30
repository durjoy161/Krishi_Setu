# app/services/agent_service.py
# Agent-specific operations: user management, platform overview.
# Returns plain dicts — no PyQt5 here.

from app.database.db_manager import get_connection


# ── Schema migration (called from db_manager.initialize_database) ──────────────

def ensure_is_active_column():
    """
    Add is_active column to users table if it doesn't exist.
    Called once at startup from initialize_database().
    All existing users default to active (1).
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        existing = [
            row[1] for row in
            cursor.execute("PRAGMA table_info(users)").fetchall()
        ]
        if "is_active" not in existing:
            cursor.execute(
                "ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1"
            )
            conn.commit()
            print("[Migration] Added is_active column to users table.")
        conn.close()
    except Exception as exc:
        print(f"[agent_service] ensure_is_active_column error: {exc}")


# ── User management ────────────────────────────────────────────────────────────

def get_all_users(role_filter: str = "All",
                  search: str = "") -> list:
    """
    Return all users with optional role filter and name/username search.
    Excludes the currently logged-in agent from the list.
    """
    try:
        import app.utils.session as session
        conn = get_connection()

        query = """
            SELECT id, username, full_name, email, phone,
                   role, address, farm_name, farm_size,
                   is_active, created_at
            FROM users
            WHERE id != ?
        """
        params = [session.get_id()]

        if role_filter != "All":
            query += " AND role = ?"
            params.append(role_filter)

        if search.strip():
            query += " AND (full_name LIKE ? OR username LIKE ? OR email LIKE ?)"
            like = f"%{search.strip()}%"
            params += [like, like, like]

        query += " ORDER BY role, full_name"

        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[agent_service] get_all_users error: {exc}")
        return []


def toggle_user_active(user_id: int) -> dict:
    """
    Flip the is_active flag for a user.
    Returns {"success": True, "is_active": new_value}
    """
    try:
        conn = get_connection()
        current = conn.execute(
            "SELECT is_active FROM users WHERE id = ?", (user_id,)
        ).fetchone()

        if not current:
            conn.close()
            return {"success": False, "message": "User not found."}

        new_val = 0 if current["is_active"] else 1
        conn.execute(
            "UPDATE users SET is_active = ? WHERE id = ?",
            (new_val, user_id)
        )
        conn.commit()
        conn.close()
        return {"success": True, "is_active": new_val}
    except Exception as exc:
        return {"success": False, "message": f"Database error: {exc}"}


def get_user_stats(user_id: int, role: str) -> dict:
    """
    Return activity statistics for a specific user.
    Used in the user detail popup.
    """
    try:
        conn = get_connection()
        stats = {}

        if role == "farmer":
            stats["products"] = conn.execute(
                "SELECT COUNT(*) FROM products WHERE farmer_id = ?",
                (user_id,)
            ).fetchone()[0]
            stats["orders"] = conn.execute(
                "SELECT COUNT(*) FROM orders WHERE farmer_id = ?",
                (user_id,)
            ).fetchone()[0]
            stats["revenue"] = conn.execute(
                """SELECT COALESCE(SUM(p.amount_paid), 0)
                   FROM payments p JOIN orders o ON o.id = p.order_id
                   WHERE o.farmer_id = ?""",
                (user_id,)
            ).fetchone()[0]

        elif role == "customer":
            stats["orders"] = conn.execute(
                "SELECT COUNT(*) FROM orders WHERE customer_id = ?",
                (user_id,)
            ).fetchone()[0]
            stats["spent"] = conn.execute(
                """SELECT COALESCE(SUM(p.amount_paid), 0)
                   FROM payments p JOIN orders o ON o.id = p.order_id
                   WHERE o.customer_id = ?""",
                (user_id,)
            ).fetchone()[0]

        elif role == "investor":
            stats["invested"] = conn.execute(
                """SELECT COALESCE(SUM(amount), 0)
                   FROM investment_contributions WHERE investor_id = ?""",
                (user_id,)
            ).fetchone()[0]
            stats["investments"] = conn.execute(
                """SELECT COUNT(DISTINCT investment_id)
                   FROM investment_contributions WHERE investor_id = ?""",
                (user_id,)
            ).fetchone()[0]

        conn.close()
        return stats
    except Exception as exc:
        print(f"[agent_service] get_user_stats error: {exc}")
        return {}


def get_platform_summary() -> dict:
    """
    High-level platform summary for agent overview.
    """
    try:
        conn = get_connection()
        row = conn.execute("""
            SELECT
                COUNT(CASE WHEN role='farmer'   THEN 1 END) AS farmers,
                COUNT(CASE WHEN role='customer' THEN 1 END) AS customers,
                COUNT(CASE WHEN role='agent'    THEN 1 END) AS agents,
                COUNT(CASE WHEN role='investor' THEN 1 END) AS investors,
                COUNT(CASE WHEN is_active=0     THEN 1 END) AS inactive
            FROM users
        """).fetchone()

        orders = conn.execute("""
            SELECT
                COUNT(*) AS total,
                COUNT(CASE WHEN status='placed'    THEN 1 END) AS placed,
                COUNT(CASE WHEN status='delivered' THEN 1 END) AS delivered,
                COUNT(CASE WHEN status='cancelled' THEN 1 END) AS cancelled
            FROM orders
        """).fetchone()

        revenue = conn.execute(
            "SELECT COALESCE(SUM(amount_paid), 0) FROM payments"
        ).fetchone()[0]

        conn.close()
        return {
            "farmers":   row["farmers"],
            "customers": row["customers"],
            "agents":    row["agents"],
            "investors": row["investors"],
            "inactive":  row["inactive"],
            "orders_total":     orders["total"],
            "orders_placed":    orders["placed"],
            "orders_delivered": orders["delivered"],
            "orders_cancelled": orders["cancelled"],
            "total_revenue":    revenue,
        }
    except Exception as exc:
        print(f"[agent_service] get_platform_summary error: {exc}")
        return {}
