# app/services/investment_service.py
# All investment and contribution operations.
# Returns plain dicts or lists — no PyQt5 here.

from app.database.db_manager import get_connection


# ── Validation ─────────────────────────────────────────────────────────────────

def validate_investment(title: str, goal_amount: str,
                        expected_roi: str) -> str | None:
    """
    Validate investment form inputs.
    Returns an error message or None if valid.
    """
    if not title.strip():
        return "Title cannot be empty."
    if len(title.strip()) < 5:
        return "Title must be at least 5 characters."
    try:
        goal = float(goal_amount)
        if goal <= 0:
            return "Goal amount must be greater than 0."
    except (ValueError, TypeError):
        return "Goal amount must be a valid number."
    try:
        roi = float(expected_roi)
        if roi < 0:
            return "Expected ROI cannot be negative."
        if roi > 1000:
            return "Expected ROI seems unrealistic (max 1000%)."
    except (ValueError, TypeError):
        return "Expected ROI must be a valid number."
    return None


def validate_contribution(amount_str: str, goal: float,
                          raised: float) -> str | None:
    """
    Validate a contribution amount.
    Returns an error message or None if valid.
    """
    try:
        amount = float(amount_str)
        if amount <= 0:
            return "Contribution must be greater than 0."
        remaining = round(goal - raised, 2)
        if amount > remaining:
            return (
                f"Amount exceeds remaining goal. "
                f"Maximum contribution: ৳ {remaining:,.2f}"
            )
    except (ValueError, TypeError):
        return "Amount must be a valid number."
    return None


# ── Farmer Operations ──────────────────────────────────────────────────────────

def create_investment(farmer_id: int, title: str, description: str,
                      goal_amount: float, expected_roi: float) -> dict:
    """
    Create a new investment request from a farmer.
    Returns {"success": True, "id": int}
         or {"success": False, "message": str}
    """
    error = validate_investment(title, str(goal_amount), str(expected_roi))
    if error:
        return {"success": False, "message": error}

    try:
        conn = get_connection()
        cursor = conn.execute("""
            INSERT INTO investments
                (farmer_id, title, description, goal_amount,
                 raised_amount, expected_roi, status)
            VALUES (?, ?, ?, ?, 0, ?, 'open')
        """, (
            farmer_id,
            title.strip(),
            description.strip(),
            float(goal_amount),
            float(expected_roi),
        ))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return {"success": True, "id": new_id}
    except Exception as exc:
        return {"success": False, "message": f"Database error: {exc}"}


def close_investment(investment_id: int, farmer_id: int) -> dict:
    """
    Farmer manually closes an investment (marks as 'closed').
    Only allowed on 'open' investments owned by this farmer.
    """
    try:
        conn = get_connection()
        rows = conn.execute("""
            UPDATE investments
            SET status = 'closed'
            WHERE id = ? AND farmer_id = ? AND status = 'open'
        """, (investment_id, farmer_id)).rowcount
        conn.commit()
        conn.close()
        if rows == 0:
            return {
                "success": False,
                "message": "Investment not found, not yours, or already closed/funded."
            }
        return {"success": True}
    except Exception as exc:
        return {"success": False, "message": f"Database error: {exc}"}


def get_investments_by_farmer(farmer_id: int) -> list:
    """Return all investments created by a specific farmer."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT i.*,
                   (i.goal_amount - i.raised_amount) AS remaining,
                   COUNT(ic.id) AS contributor_count
            FROM investments i
            LEFT JOIN investment_contributions ic ON ic.investment_id = i.id
            WHERE i.farmer_id = ?
            GROUP BY i.id
            ORDER BY i.created_at DESC
        """, (farmer_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[investment_service] get_investments_by_farmer error: {exc}")
        return []


# ── Investor Operations ────────────────────────────────────────────────────────

def contribute(investor_id: int, investment_id: int,
               amount: float) -> dict:
    """
    Record an investor's contribution to an investment.
    - Validates the amount does not exceed the remaining goal
    - Updates raised_amount
    - Auto-sets status to 'funded' when goal is reached
    Returns {"success": True} or {"success": False, "message": str}
    """
    try:
        conn = get_connection()

        inv = conn.execute(
            "SELECT * FROM investments WHERE id = ?", (investment_id,)
        ).fetchone()

        if not inv:
            conn.close()
            return {"success": False, "message": "Investment not found."}

        if inv["status"] != "open":
            conn.close()
            return {
                "success": False,
                "message": f"This investment is '{inv['status']}' and not accepting contributions."
            }

        error = validate_contribution(
            str(amount), inv["goal_amount"], inv["raised_amount"]
        )
        if error:
            conn.close()
            return {"success": False, "message": error}

        new_raised = round(inv["raised_amount"] + amount, 2)
        new_status = "funded" if new_raised >= inv["goal_amount"] else "open"

        # Record contribution
        conn.execute("""
            INSERT INTO investment_contributions
                (investment_id, investor_id, amount)
            VALUES (?, ?, ?)
        """, (investment_id, investor_id, amount))

        # Update investment totals
        conn.execute("""
            UPDATE investments
            SET raised_amount = ?, status = ?
            WHERE id = ?
        """, (new_raised, new_status, investment_id))

        conn.commit()
        conn.close()
        return {"success": True, "new_status": new_status,
                "total_raised": new_raised}
    except Exception as exc:
        return {"success": False, "message": f"Database error: {exc}"}


def get_open_investments(search: str = "") -> list:
    """
    Return all open investments with farmer info.
    Optional search by title or farmer name.
    """
    try:
        conn = get_connection()
        query = """
            SELECT i.*,
                   u.full_name  AS farmer_name,
                   u.farm_name  AS farm_name,
                   (i.goal_amount - i.raised_amount) AS remaining,
                   ROUND((i.raised_amount * 100.0 / i.goal_amount), 1)
                       AS progress_pct,
                   COUNT(ic.id) AS contributor_count
            FROM investments i
            JOIN users u ON u.id = i.farmer_id
            LEFT JOIN investment_contributions ic ON ic.investment_id = i.id
            WHERE i.status = 'open'
        """
        params = []
        if search.strip():
            query += " AND (i.title LIKE ? OR u.full_name LIKE ?)"
            like = f"%{search.strip()}%"
            params += [like, like]
        query += " GROUP BY i.id ORDER BY i.created_at DESC"

        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[investment_service] get_open_investments error: {exc}")
        return []


def get_portfolio(investor_id: int) -> list:
    """
    Return all investments this investor has contributed to,
    with their contribution amount and investment status.
    """
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT i.*,
                   u.full_name  AS farmer_name,
                   u.farm_name  AS farm_name,
                   ic.amount    AS my_contribution,
                   ic.contributed_at,
                   ROUND((i.raised_amount * 100.0 / i.goal_amount), 1)
                       AS progress_pct
            FROM investment_contributions ic
            JOIN investments i ON i.id = ic.investment_id
            JOIN users u ON u.id = i.farmer_id
            WHERE ic.investor_id = ?
            ORDER BY ic.contributed_at DESC
        """, (investor_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[investment_service] get_portfolio error: {exc}")
        return []


def get_all_investments() -> list:
    """All investments platform-wide, newest first."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT i.*,
                   u.full_name  AS farmer_name,
                   (i.goal_amount - i.raised_amount) AS remaining,
                   ROUND((i.raised_amount * 100.0 / i.goal_amount), 1)
                       AS progress_pct,
                   COUNT(ic.id) AS contributor_count
            FROM investments i
            JOIN users u ON u.id = i.farmer_id
            LEFT JOIN investment_contributions ic ON ic.investment_id = i.id
            GROUP BY i.id
            ORDER BY i.created_at DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[investment_service] get_all_investments error: {exc}")
        return []
