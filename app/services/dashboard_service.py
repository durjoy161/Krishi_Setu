# app/services/dashboard_service.py
# Provides summary statistics for each role's dashboard home page.
# Returns plain dicts — no PyQt5 here, keeping UI and data fully separated.

from app.database.db_manager import get_connection


def get_farmer_stats(farmer_id: int) -> dict:
    """
    Return overview numbers for a farmer's home page.
    All queries are scoped to the given farmer_id.
    """
    try:
        conn = get_connection()

        total_products = conn.execute(
            "SELECT COUNT(*) FROM products WHERE farmer_id = ?", (farmer_id,)
        ).fetchone()[0]

        total_orders = conn.execute(
            """SELECT COUNT(*) FROM orders WHERE farmer_id = ?""",
            (farmer_id,)
        ).fetchone()[0]

        pending_orders = conn.execute(
            """SELECT COUNT(*) FROM orders
               WHERE farmer_id = ? AND status NOT IN ('delivered','cancelled')""",
            (farmer_id,)
        ).fetchone()[0]

        revenue_row = conn.execute(
            """SELECT COALESCE(SUM(p.amount_paid), 0)
               FROM payments p
               JOIN orders o ON o.id = p.order_id
               WHERE o.farmer_id = ?""",
            (farmer_id,)
        ).fetchone()
        total_revenue = revenue_row[0] if revenue_row else 0.0

        active_investments = conn.execute(
            "SELECT COUNT(*) FROM investments WHERE farmer_id = ? AND status = 'open'",
            (farmer_id,)
        ).fetchone()[0]

        conn.close()
        return {
            "total_products":    total_products,
            "total_orders":      total_orders,
            "pending_orders":    pending_orders,
            "total_revenue":     total_revenue,
            "active_investments": active_investments,
        }
    except Exception as exc:
        print(f"[dashboard_service] get_farmer_stats error: {exc}")
        return {
            "total_products": 0, "total_orders": 0,
            "pending_orders": 0, "total_revenue": 0.0,
            "active_investments": 0,
        }


def get_customer_stats(customer_id: int) -> dict:
    """Return overview numbers for a customer's home page."""
    try:
        conn = get_connection()

        total_orders = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE customer_id = ?", (customer_id,)
        ).fetchone()[0]

        active_orders = conn.execute(
            """SELECT COUNT(*) FROM orders
               WHERE customer_id = ? AND status NOT IN ('delivered','cancelled')""",
            (customer_id,)
        ).fetchone()[0]

        total_spent = conn.execute(
            """SELECT COALESCE(SUM(p.amount_paid), 0)
               FROM payments p
               JOIN orders o ON o.id = p.order_id
               WHERE o.customer_id = ?""",
            (customer_id,)
        ).fetchone()[0]

        available_products = conn.execute(
            "SELECT COUNT(*) FROM products WHERE stock_qty > 0"
        ).fetchone()[0]

        conn.close()
        return {
            "total_orders":       total_orders,
            "active_orders":      active_orders,
            "total_spent":        total_spent,
            "available_products": available_products,
        }
    except Exception as exc:
        print(f"[dashboard_service] get_customer_stats error: {exc}")
        return {
            "total_orders": 0, "active_orders": 0,
            "total_spent": 0.0, "available_products": 0,
        }


def get_agent_stats() -> dict:
    """Return platform-wide overview numbers for an agent."""
    try:
        conn = get_connection()

        total_farmers = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role='farmer'"
        ).fetchone()[0]

        total_customers = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role='customer'"
        ).fetchone()[0]

        total_orders = conn.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]

        pending_orders = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE status NOT IN ('delivered','cancelled')"
        ).fetchone()[0]

        total_revenue = conn.execute(
            "SELECT COALESCE(SUM(amount_paid), 0) FROM payments"
        ).fetchone()[0]

        conn.close()
        return {
            "total_farmers":   total_farmers,
            "total_customers": total_customers,
            "total_orders":    total_orders,
            "pending_orders":  pending_orders,
            "total_revenue":   total_revenue,
        }
    except Exception as exc:
        print(f"[dashboard_service] get_agent_stats error: {exc}")
        return {
            "total_farmers": 0, "total_customers": 0,
            "total_orders": 0, "pending_orders": 0, "total_revenue": 0.0,
        }


def get_investor_stats(investor_id: int) -> dict:
    """Return investment overview for an investor."""
    try:
        conn = get_connection()

        total_invested = conn.execute(
            """SELECT COALESCE(SUM(amount), 0)
               FROM investment_contributions WHERE investor_id = ?""",
            (investor_id,)
        ).fetchone()[0]

        active_investments = conn.execute(
            """SELECT COUNT(DISTINCT ic.investment_id)
               FROM investment_contributions ic
               JOIN investments i ON i.id = ic.investment_id
               WHERE ic.investor_id = ? AND i.status = 'open'""",
            (investor_id,)
        ).fetchone()[0]

        open_opportunities = conn.execute(
            "SELECT COUNT(*) FROM investments WHERE status = 'open'"
        ).fetchone()[0]

        total_opportunities = conn.execute(
            "SELECT COUNT(*) FROM investments"
        ).fetchone()[0]

        conn.close()
        return {
            "total_invested":      total_invested,
            "active_investments":  active_investments,
            "open_opportunities":  open_opportunities,
            "total_opportunities": total_opportunities,
        }
    except Exception as exc:
        print(f"[dashboard_service] get_investor_stats error: {exc}")
        return {
            "total_invested": 0.0, "active_investments": 0,
            "open_opportunities": 0, "total_opportunities": 0,
        }
