# app/services/investment_service.py
# Handles investment funding requests and investor contributions

from app.database.db_manager import get_connection
import app.utils.session as session


def get_all_investments():
    """Return all investment rounds with farmer info."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT i.*, u.full_name AS farmer_name, u.farm_name
        FROM investments i
        JOIN users u ON i.farmer_id = u.id
        ORDER BY i.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_farmer_investments(farmer_id: int):
    """Return investment rounds created by a specific farmer."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM investments WHERE farmer_id = ? ORDER BY created_at DESC",
        (farmer_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_investor_contributions(investor_id: int):
    """Return all contributions made by an investor, with investment details."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT ic.*, i.title, i.goal_amount, i.raised_amount, i.expected_roi, i.status AS inv_status,
               u.full_name AS farmer_name
        FROM investment_contributions ic
        JOIN investments i ON ic.investment_id = i.id
        JOIN users       u ON i.farmer_id      = u.id
        WHERE ic.investor_id = ?
        ORDER BY ic.contributed_at DESC
    """, (investor_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_investment_request(title, description, goal_amount, expected_roi):
    """Farmer creates a new funding request."""
    farmer_id = session.get_id()
    conn = get_connection()
    conn.execute("""
        INSERT INTO investments (farmer_id, title, description, goal_amount, expected_roi)
        VALUES (?,?,?,?,?)
    """, (farmer_id, title, description, float(goal_amount), float(expected_roi)))
    conn.commit()
    conn.close()


def invest(investment_id: int, amount: float):
    """Investor contributes an amount to an investment round."""
    investor_id = session.get_id()
    conn = get_connection()
    cursor = conn.cursor()

    # Add contribution
    cursor.execute("""
        INSERT INTO investment_contributions (investment_id, investor_id, amount)
        VALUES (?,?,?)
    """, (investment_id, investor_id, amount))

    # Update raised amount
    cursor.execute("""
        UPDATE investments
        SET raised_amount = raised_amount + ?
        WHERE id = ?
    """, (amount, investment_id))

    # Auto-close if fully funded
    cursor.execute("""
        UPDATE investments
        SET status = 'funded'
        WHERE id = ? AND raised_amount >= goal_amount
    """, (investment_id,))

    conn.commit()
    conn.close()
