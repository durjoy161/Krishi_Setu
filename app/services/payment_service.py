# app/services/payment_service.py
# Dummy payment service — no real payment gateway needed

from app.database.db_manager import get_connection
from datetime import datetime


def get_payments_for_customer(customer_id: int):
    """Return all payment records for a customer's orders."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT pay.*, o.total_price, p.name AS product_name, o.order_type
        FROM payments pay
        JOIN orders   o ON pay.order_id   = o.id
        JOIN products p ON o.product_id   = p.id
        WHERE o.customer_id = ?
        ORDER BY pay.id DESC
    """, (customer_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_payments():
    """Return all payments with order and customer details (for agents)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT pay.*, c.full_name AS customer_name, p.name AS product_name
        FROM payments pay
        JOIN orders   o ON pay.order_id   = o.id
        JOIN users    c ON o.customer_id  = c.id
        JOIN products p ON o.product_id   = p.id
        ORDER BY pay.id DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def pay_full(payment_id: int, method: str = "online"):
    """Mark a payment as fully paid (dummy)."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)).fetchone()
    if not row:
        conn.close()
        return False
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        UPDATE payments
        SET amount_paid = amount_due, status = 'paid', method = ?, paid_at = ?
        WHERE id = ?
    """, (method, now, payment_id))
    conn.commit()
    conn.close()
    return True


def pay_partial(payment_id: int, amount: float, method: str = "cash"):
    """Make a partial payment."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)).fetchone()
    if not row:
        conn.close()
        return False
    total_paid = min(float(row["amount_paid"]) + amount, float(row["amount_due"]))
    status = "paid" if total_paid >= float(row["amount_due"]) else "partial"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        UPDATE payments
        SET amount_paid = ?, status = ?, method = ?, paid_at = ?
        WHERE id = ?
    """, (total_paid, status, method, now, payment_id))
    conn.commit()
    conn.close()
    return True
