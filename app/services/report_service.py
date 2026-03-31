# app/services/report_service.py
# Aggregate queries for reports and analytics

from app.database.db_manager import get_connection
import app.utils.session as session


def get_sales_report(farmer_id: int = None):
    """
    Return total sales per product.
    If farmer_id given, scoped to that farmer.
    """
    conn = get_connection()
    if farmer_id:
        rows = conn.execute("""
            SELECT p.name AS product, p.category, p.unit,
                   COUNT(o.id) AS total_orders,
                   SUM(o.quantity) AS total_qty,
                   SUM(o.total_price) AS total_revenue
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.farmer_id = ? AND o.status != 'cancelled'
            GROUP BY p.id
            ORDER BY total_revenue DESC
        """, (farmer_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT p.name AS product, p.category, p.unit,
                   COUNT(o.id) AS total_orders,
                   SUM(o.quantity) AS total_qty,
                   SUM(o.total_price) AS total_revenue
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.status != 'cancelled'
            GROUP BY p.id
            ORDER BY total_revenue DESC
        """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_inventory_report(farmer_id: int = None):
    """Return stock levels for all products."""
    conn = get_connection()
    if farmer_id:
        rows = conn.execute("""
            SELECT p.name, p.category, p.unit, p.stock_qty, p.price, p.expiry_date,
                   u.full_name AS farmer_name
            FROM products p JOIN users u ON p.farmer_id = u.id
            WHERE p.farmer_id = ?
            ORDER BY p.stock_qty ASC
        """, (farmer_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT p.name, p.category, p.unit, p.stock_qty, p.price, p.expiry_date,
                   u.full_name AS farmer_name
            FROM products p JOIN users u ON p.farmer_id = u.id
            ORDER BY p.stock_qty ASC
        """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_profit_report(farmer_id: int = None):
    """Return payment summary: total due vs total received."""
    conn = get_connection()
    if farmer_id:
        rows = conn.execute("""
            SELECT p.name AS product,
                   SUM(pay.amount_due)  AS total_due,
                   SUM(pay.amount_paid) AS total_paid,
                   SUM(pay.amount_due - pay.amount_paid) AS outstanding
            FROM payments pay
            JOIN orders   o ON pay.order_id  = o.id
            JOIN products p ON o.product_id  = p.id
            WHERE o.farmer_id = ? AND o.status != 'cancelled'
            GROUP BY p.id
            ORDER BY total_paid DESC
        """, (farmer_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT p.name AS product,
                   SUM(pay.amount_due)  AS total_due,
                   SUM(pay.amount_paid) AS total_paid,
                   SUM(pay.amount_due - pay.amount_paid) AS outstanding
            FROM payments pay
            JOIN orders   o ON pay.order_id  = o.id
            JOIN products p ON o.product_id  = p.id
            WHERE o.status != 'cancelled'
            GROUP BY p.id
            ORDER BY total_paid DESC
        """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_dashboard_stats(role: str, user_id: int) -> dict:
    """Return summary statistics for the dashboard based on role."""
    conn = get_connection()
    stats = {}

    if role == "farmer":
        stats["products"] = conn.execute(
            "SELECT COUNT(*) FROM products WHERE farmer_id=?", (user_id,)).fetchone()[0]
        stats["orders"] = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE farmer_id=? AND status NOT IN ('delivered','cancelled')",
            (user_id,)).fetchone()[0]
        stats["revenue"] = conn.execute(
            "SELECT COALESCE(SUM(amount_paid),0) FROM payments pay JOIN orders o ON pay.order_id=o.id WHERE o.farmer_id=?",
            (user_id,)).fetchone()[0]
        stats["investment_requests"] = conn.execute(
            "SELECT COUNT(*) FROM investments WHERE farmer_id=?", (user_id,)).fetchone()[0]

    elif role == "customer":
        stats["my_orders"] = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE customer_id=?", (user_id,)).fetchone()[0]
        stats["pending_orders"] = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE customer_id=? AND status NOT IN ('delivered','cancelled')",
            (user_id,)).fetchone()[0]
        stats["amount_spent"] = conn.execute(
            "SELECT COALESCE(SUM(amount_paid),0) FROM payments pay JOIN orders o ON pay.order_id=o.id WHERE o.customer_id=?",
            (user_id,)).fetchone()[0]
        stats["unpaid"] = conn.execute(
            "SELECT COALESCE(SUM(amount_due - amount_paid),0) FROM payments pay JOIN orders o ON pay.order_id=o.id WHERE o.customer_id=?",
            (user_id,)).fetchone()[0]

    elif role == "agent":
        stats["total_orders"] = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        stats["active_orders"] = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE status NOT IN ('delivered','cancelled')").fetchone()[0]
        stats["total_revenue"] = conn.execute(
            "SELECT COALESCE(SUM(amount_paid),0) FROM payments").fetchone()[0]
        stats["farmers"] = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role='farmer'").fetchone()[0]

    elif role == "investor":
        stats["total_investments"] = conn.execute("SELECT COUNT(*) FROM investments").fetchone()[0]
        stats["open_rounds"] = conn.execute(
            "SELECT COUNT(*) FROM investments WHERE status='open'").fetchone()[0]
        stats["my_invested"] = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM investment_contributions WHERE investor_id=?",
            (user_id,)).fetchone()[0]
        stats["my_rounds"] = conn.execute(
            "SELECT COUNT(*) FROM investment_contributions WHERE investor_id=?",
            (user_id,)).fetchone()[0]

    conn.close()
    return stats
