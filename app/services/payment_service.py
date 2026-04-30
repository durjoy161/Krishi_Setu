# app/services/payment_service.py
# All payment recording and query operations.
# Returns plain dicts — no PyQt5 here.

from datetime import datetime
from app.database.db_manager import get_connection

VALID_METHODS = ["cash", "bKash", "Nagad", "Rocket", "bank_transfer"]


# ── Validation ─────────────────────────────────────────────────────────────────

def validate_payment(amount_str: str, amount_due: float,
                     amount_already_paid: float) -> str | None:
    """
    Validate a payment amount entry.
    Returns error string or None if valid.
    """
    try:
        amount = float(amount_str)
    except (ValueError, TypeError):
        return "Amount must be a valid number."

    if amount <= 0:
        return "Amount must be greater than 0."

    remaining = round(amount_due - amount_already_paid, 2)
    if amount > remaining:
        return (
            f"Amount exceeds remaining balance. "
            f"Maximum payable: ৳ {remaining:,.2f}"
        )
    return None


# ── Record Payment ─────────────────────────────────────────────────────────────

def record_payment(order_id: int, amount: float, method: str) -> dict:
    """
    Record a payment against an existing order.

    - Adds the amount to amount_paid
    - Updates status:
        amount_paid == 0              → unpaid
        0 < amount_paid < amount_due  → partial
        amount_paid >= amount_due     → paid  (records paid_at timestamp)
    - Blocked on cancelled orders.

    Returns {"success": True, "new_status": str, "total_paid": float}
         or {"success": False, "message": str}
    """
    if method not in VALID_METHODS:
        return {
            "success": False,
            "message": f"Invalid method. Choose from: {', '.join(VALID_METHODS)}."
        }

    try:
        conn = get_connection()

        payment = conn.execute(
            "SELECT * FROM payments WHERE order_id = ?", (order_id,)
        ).fetchone()

        if not payment:
            conn.close()
            return {"success": False,
                    "message": "No payment record found for this order."}

        order_status = conn.execute(
            "SELECT status FROM orders WHERE id = ?", (order_id,)
        ).fetchone()

        if order_status and order_status["status"] == "cancelled":
            conn.close()
            return {"success": False,
                    "message": "Cannot record payment for a cancelled order."}

        error = validate_payment(
            str(amount), payment["amount_due"], payment["amount_paid"]
        )
        if error:
            conn.close()
            return {"success": False, "message": error}

        new_paid = round(payment["amount_paid"] + amount, 2)
        due      = round(payment["amount_due"], 2)

        if new_paid >= due:
            new_status = "paid"
            paid_at    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif new_paid > 0:
            new_status = "partial"
            paid_at    = payment["paid_at"]
        else:
            new_status = "unpaid"
            paid_at    = None

        conn.execute("""
            UPDATE payments
            SET amount_paid = ?, status = ?, method = ?, paid_at = ?
            WHERE order_id = ?
        """, (new_paid, new_status, method, paid_at, order_id))
        conn.commit()
        conn.close()
        return {"success": True, "new_status": new_status, "total_paid": new_paid}

    except Exception as exc:
        return {"success": False, "message": f"Database error: {exc}"}


# ── Queries ────────────────────────────────────────────────────────────────────

def get_payments_for_customer(customer_id: int) -> list:
    """All payment records for a customer's orders, newest first."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT pay.*,
                   o.total_price,
                   o.status        AS order_status,
                   o.created_at    AS order_date,
                   p.name          AS product_name,
                   u.full_name     AS farmer_name
            FROM payments pay
            JOIN orders   o  ON o.id  = pay.order_id
            JOIN products p  ON p.id  = o.product_id
            JOIN users    u  ON u.id  = o.farmer_id
            WHERE o.customer_id = ?
            ORDER BY o.created_at DESC
        """, (customer_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[payment_service] get_payments_for_customer error: {exc}")
        return []


def get_payments_for_farmer(farmer_id: int) -> list:
    """All payment records for a farmer's orders, newest first."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT pay.*,
                   o.total_price,
                   o.status        AS order_status,
                   o.created_at    AS order_date,
                   p.name          AS product_name,
                   u.full_name     AS customer_name
            FROM payments pay
            JOIN orders   o  ON o.id  = pay.order_id
            JOIN products p  ON p.id  = o.product_id
            JOIN users    u  ON u.id  = o.customer_id
            WHERE o.farmer_id = ?
            ORDER BY o.created_at DESC
        """, (farmer_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[payment_service] get_payments_for_farmer error: {exc}")
        return []


def get_all_payments() -> list:
    """All payment records platform-wide (for agents), newest first."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT pay.*,
                   o.total_price,
                   o.status        AS order_status,
                   o.created_at    AS order_date,
                   p.name          AS product_name,
                   c.full_name     AS customer_name,
                   f.full_name     AS farmer_name
            FROM payments pay
            JOIN orders   o  ON o.id  = pay.order_id
            JOIN products p  ON p.id  = o.product_id
            JOIN users    c  ON c.id  = o.customer_id
            JOIN users    f  ON f.id  = o.farmer_id
            ORDER BY o.created_at DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[payment_service] get_all_payments error: {exc}")
        return []


def get_payment_summary() -> dict:
    """Platform-wide payment totals for the agent dashboard."""
    try:
        conn = get_connection()
        row = conn.execute("""
            SELECT
                COALESCE(SUM(pay.amount_due),  0) AS total_due,
                COALESCE(SUM(pay.amount_paid), 0) AS total_paid,
                COUNT(CASE WHEN pay.status = 'unpaid'  THEN 1 END) AS unpaid_count,
                COUNT(CASE WHEN pay.status = 'partial' THEN 1 END) AS partial_count,
                COUNT(CASE WHEN pay.status = 'paid'    THEN 1 END) AS paid_count
            FROM payments pay
            JOIN orders o ON o.id = pay.order_id
            WHERE o.status != 'cancelled'
        """).fetchone()
        conn.close()
        d = dict(row)
        d["total_outstanding"] = round(d["total_due"] - d["total_paid"], 2)
        return d
    except Exception as exc:
        print(f"[payment_service] get_payment_summary error: {exc}")
        return {
            "total_due": 0.0, "total_paid": 0.0, "total_outstanding": 0.0,
            "unpaid_count": 0, "partial_count": 0, "paid_count": 0,
        }