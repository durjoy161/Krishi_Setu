# app/services/report_service.py
# All analytics and reporting queries.
# Returns plain dicts and lists — no PyQt5 here.

from app.database.db_manager import get_connection


# ── Farmer Reports ─────────────────────────────────────────────────────────────

def get_farmer_sales_summary(farmer_id: int) -> dict:
    """Overall sales summary for a farmer."""
    try:
        conn = get_connection()

        total_revenue = conn.execute("""
            SELECT COALESCE(SUM(pay.amount_paid), 0)
            FROM payments pay
            JOIN orders o ON o.id = pay.order_id
            WHERE o.farmer_id = ?
        """, (farmer_id,)).fetchone()[0]

        total_orders = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE farmer_id = ?",
            (farmer_id,)
        ).fetchone()[0]

        delivered = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE farmer_id=? AND status='delivered'",
            (farmer_id,)
        ).fetchone()[0]

        cancelled = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE farmer_id=? AND status='cancelled'",
            (farmer_id,)
        ).fetchone()[0]

        pending = conn.execute(
            """SELECT COUNT(*) FROM orders
               WHERE farmer_id = ?
               AND status NOT IN ('delivered','cancelled')""",
            (farmer_id,)
        ).fetchone()[0]

        outstanding = conn.execute("""
            SELECT COALESCE(SUM(pay.amount_due - pay.amount_paid), 0)
            FROM payments pay
            JOIN orders o ON o.id = pay.order_id
            WHERE o.farmer_id = ? AND pay.status != 'paid'
        """, (farmer_id,)).fetchone()[0]

        conn.close()
        return {
            "total_revenue": total_revenue,
            "outstanding":   outstanding,
            "total_orders":  total_orders,
            "delivered":     delivered,
            "cancelled":     cancelled,
            "pending":       pending,
        }
    except Exception as exc:
        print(f"[report_service] get_farmer_sales_summary error: {exc}")
        return {}


def get_top_products_for_farmer(farmer_id: int, limit: int = 5) -> list:
    """Top selling products by revenue for a farmer."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT p.name,
                   COUNT(o.id)          AS order_count,
                   SUM(o.quantity)      AS total_qty,
                   SUM(o.total_price)   AS total_revenue,
                   p.unit
            FROM orders o
            JOIN products p ON p.id = o.product_id
            WHERE o.farmer_id = ? AND o.status != 'cancelled'
            GROUP BY p.id
            ORDER BY total_revenue DESC
            LIMIT ?
        """, (farmer_id, limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[report_service] get_top_products_for_farmer error: {exc}")
        return []


def get_monthly_revenue_for_farmer(farmer_id: int) -> list:
    """Monthly revenue for the last 6 months for a farmer."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT strftime('%Y-%m', o.created_at) AS month,
                   COALESCE(SUM(pay.amount_paid), 0) AS revenue
            FROM orders o
            JOIN payments pay ON pay.order_id = o.id
            WHERE o.farmer_id = ?
            AND o.created_at >= date('now', '-6 months')
            GROUP BY month
            ORDER BY month ASC
        """, (farmer_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[report_service] get_monthly_revenue_for_farmer error: {exc}")
        return []


def get_order_status_breakdown_farmer(farmer_id: int) -> list:
    """Count of orders per status for a farmer."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT status, COUNT(*) AS count
            FROM orders WHERE farmer_id = ?
            GROUP BY status ORDER BY count DESC
        """, (farmer_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[report_service] get_order_status_breakdown_farmer error: {exc}")
        return []


# ── Investor Reports ───────────────────────────────────────────────────────────

def get_investor_report_data(investor_id: int) -> dict:
    """
    All report data for an investor in a single call.
    Returns a dict with keys:
        summary          — overall portfolio numbers
        contributions    — list of {title, my_contribution} for bar chart
        status_breakdown — list of {status, count, total_invested}
        portfolio        — full contribution detail rows
    """
    try:
        conn = get_connection()

        # Summary numbers
        total_invested = conn.execute(
            """SELECT COALESCE(SUM(amount), 0)
               FROM investment_contributions WHERE investor_id = ?""",
            (investor_id,)
        ).fetchone()[0]

        counts = conn.execute("""
            SELECT
                COUNT(DISTINCT ic.investment_id) AS total_count,
                COUNT(DISTINCT CASE WHEN i.status='open'   THEN ic.investment_id END) AS open_count,
                COUNT(DISTINCT CASE WHEN i.status='funded' THEN ic.investment_id END) AS funded_count,
                COUNT(DISTINCT CASE WHEN i.status='closed' THEN ic.investment_id END) AS closed_count
            FROM investment_contributions ic
            JOIN investments i ON i.id = ic.investment_id
            WHERE ic.investor_id = ?
        """, (investor_id,)).fetchone()

        active_count = (counts["open_count"] or 0)

        summary = {
            "total_invested": total_invested,
            "total_count":    counts["total_count"]  or 0,
            "open_count":     counts["open_count"]   or 0,
            "funded_count":   counts["funded_count"] or 0,
            "closed_count":   counts["closed_count"] or 0,
            "active_count":   active_count,
        }

        # Contributions per project (for bar chart)
        contrib_rows = conn.execute("""
            SELECT i.title,
                   SUM(ic.amount) AS my_contribution
            FROM investment_contributions ic
            JOIN investments i ON i.id = ic.investment_id
            WHERE ic.investor_id = ?
            GROUP BY ic.investment_id
            ORDER BY my_contribution DESC
        """, (investor_id,)).fetchall()
        contributions = [dict(r) for r in contrib_rows]

        # Status breakdown
        status_rows = conn.execute("""
            SELECT i.status,
                   COUNT(DISTINCT ic.investment_id) AS count,
                   COALESCE(SUM(ic.amount), 0)       AS total_invested
            FROM investment_contributions ic
            JOIN investments i ON i.id = ic.investment_id
            WHERE ic.investor_id = ?
            GROUP BY i.status
            ORDER BY total_invested DESC
        """, (investor_id,)).fetchall()
        status_breakdown = [dict(r) for r in status_rows]

        # Full portfolio detail
        portfolio_rows = conn.execute("""
            SELECT i.*,
                   u.full_name      AS farmer_name,
                   ic.amount        AS my_contribution,
                   ic.contributed_at,
                   ROUND((i.raised_amount * 100.0 / i.goal_amount), 1)
                       AS progress_pct
            FROM investment_contributions ic
            JOIN investments i ON i.id  = ic.investment_id
            JOIN users        u ON u.id = i.farmer_id
            WHERE ic.investor_id = ?
            ORDER BY ic.contributed_at DESC
        """, (investor_id,)).fetchall()
        portfolio = [dict(r) for r in portfolio_rows]

        conn.close()
        return {
            "summary":          summary,
            "contributions":    contributions,
            "status_breakdown": status_breakdown,
            "portfolio":        portfolio,
        }
    except Exception as exc:
        print(f"[report_service] get_investor_report_data error: {exc}")
        return {
            "summary": {}, "contributions": [],
            "status_breakdown": [], "portfolio": [],
        }


# ── Agent / Platform Reports ───────────────────────────────────────────────────

def get_platform_sales_summary() -> dict:
    """Platform-wide sales summary for agents."""
    try:
        conn = get_connection()

        total_revenue = conn.execute(
            "SELECT COALESCE(SUM(amount_paid), 0) FROM payments"
        ).fetchone()[0]

        outstanding = conn.execute(
            """SELECT COALESCE(SUM(amount_due - amount_paid), 0)
               FROM payments WHERE status != 'paid'"""
        ).fetchone()[0]

        total_orders = conn.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]

        delivered = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE status='delivered'"
        ).fetchone()[0]

        cancelled = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE status='cancelled'"
        ).fetchone()[0]

        total_users = conn.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]

        total_products = conn.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]

        total_invested = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM investment_contributions"
        ).fetchone()[0]

        conn.close()
        return {
            "total_revenue":  total_revenue,
            "outstanding":    outstanding,
            "total_orders":   total_orders,
            "delivered":      delivered,
            "cancelled":      cancelled,
            "total_users":    total_users,
            "total_products": total_products,
            "total_invested": total_invested,
        }
    except Exception as exc:
        print(f"[report_service] get_platform_sales_summary error: {exc}")
        return {}


def get_top_products_platform(limit: int = 8) -> list:
    """Top selling products platform-wide by revenue."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT p.name,
                   u.full_name          AS farmer_name,
                   COUNT(o.id)          AS order_count,
                   SUM(o.quantity)      AS total_qty,
                   SUM(o.total_price)   AS total_revenue,
                   p.unit,
                   p.category
            FROM orders o
            JOIN products p ON p.id = o.product_id
            JOIN users    u ON u.id = o.farmer_id
            WHERE o.status != 'cancelled'
            GROUP BY p.id
            ORDER BY total_revenue DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[report_service] get_top_products_platform error: {exc}")
        return []


def get_monthly_revenue_platform() -> list:
    """Monthly platform revenue for the last 6 months."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT strftime('%Y-%m', o.created_at) AS month,
                   COALESCE(SUM(pay.amount_paid), 0) AS revenue
            FROM orders o
            JOIN payments pay ON pay.order_id = o.id
            WHERE o.created_at >= date('now', '-6 months')
            GROUP BY month
            ORDER BY month ASC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[report_service] get_monthly_revenue_platform error: {exc}")
        return []


def get_revenue_by_category() -> list:
    """Revenue grouped by product category, platform-wide."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT p.category,
                   COUNT(o.id)          AS order_count,
                   SUM(o.total_price)   AS total_revenue
            FROM orders o
            JOIN products p ON p.id = o.product_id
            WHERE o.status != 'cancelled'
            GROUP BY p.category
            ORDER BY total_revenue DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[report_service] get_revenue_by_category error: {exc}")
        return []


def get_order_status_breakdown_platform() -> list:
    """Count of orders per status, platform-wide."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT status, COUNT(*) AS count
            FROM orders
            GROUP BY status ORDER BY count DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[report_service] get_order_status_breakdown_platform error: {exc}")
        return []


def get_top_farmers_by_revenue(limit: int = 5) -> list:
    """Top farmers ranked by total revenue received."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT u.full_name,
                   u.farm_name,
                   COUNT(DISTINCT o.id)             AS order_count,
                   COALESCE(SUM(pay.amount_paid), 0) AS revenue
            FROM users u
            JOIN orders   o   ON o.farmer_id  = u.id
            JOIN payments pay ON pay.order_id = o.id
            WHERE u.role = 'farmer'
            GROUP BY u.id
            ORDER BY revenue DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[report_service] get_top_farmers_by_revenue error: {exc}")
        return []