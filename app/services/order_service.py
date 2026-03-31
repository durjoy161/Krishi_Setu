# app/services/order_service.py
# Handles order creation, cancellation, and status advancement

from app.database.db_manager import get_connection
from app.services.product_service import reduce_stock
import app.utils.session as session

# Valid status transitions
STATUS_FLOW = ["placed", "confirmed", "harvested", "delivered"]


def get_all_orders():
    """Return all orders with customer, product, and farmer names (for agents)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT o.*,
               c.full_name AS customer_name,
               p.name      AS product_name,
               p.unit      AS product_unit,
               u.full_name AS farmer_name
        FROM orders o
        JOIN users    c ON o.customer_id = c.id
        JOIN products p ON o.product_id  = p.id
        JOIN users    u ON o.farmer_id   = u.id
        ORDER BY o.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_customer_orders(customer_id: int):
    """Return orders placed by a specific customer."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT o.*,
               p.name      AS product_name,
               p.unit      AS product_unit,
               u.full_name AS farmer_name
        FROM orders o
        JOIN products p ON o.product_id = p.id
        JOIN users    u ON o.farmer_id  = u.id
        WHERE o.customer_id = ?
        ORDER BY o.created_at DESC
    """, (customer_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_farmer_orders(farmer_id: int):
    """Return orders for products owned by a farmer."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT o.*,
               c.full_name AS customer_name,
               p.name      AS product_name,
               p.unit      AS product_unit
        FROM orders o
        JOIN products p ON o.product_id  = p.id
        JOIN users    c ON o.customer_id = c.id
        WHERE o.farmer_id = ?
        ORDER BY o.created_at DESC
    """, (farmer_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def place_order(product_id: int, farmer_id: int, quantity: float,
                unit_price: float, order_type: str = "instant", notes: str = ""):
    """Place a new order and create an associated unpaid payment record."""
    customer_id = session.get_id()
    total = round(quantity * unit_price, 2)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (customer_id, product_id, farmer_id, quantity, total_price, order_type, notes)
        VALUES (?,?,?,?,?,?,?)
    """, (customer_id, product_id, farmer_id, quantity, total, order_type, notes))
    order_id = cursor.lastrowid

    # Create payment record
    cursor.execute("""
        INSERT INTO payments (order_id, amount_due) VALUES (?,?)
    """, (order_id, total))

    conn.commit()
    conn.close()

    # Reduce stock for instant orders
    if order_type == "instant":
        reduce_stock(product_id, quantity)

    return order_id


def advance_order_status(order_id: int):
    """Move an order to the next status in the flow."""
    conn = get_connection()
    row = conn.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not row:
        conn.close()
        return False
    current = row["status"]
    if current == "cancelled" or current == "delivered":
        conn.close()
        return False
    idx = STATUS_FLOW.index(current) if current in STATUS_FLOW else -1
    if idx < len(STATUS_FLOW) - 1:
        next_status = STATUS_FLOW[idx + 1]
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (next_status, order_id))
        conn.commit()
    conn.close()
    return True


def cancel_order(order_id: int):
    """Cancel an order (only if placed/confirmed)."""
    conn = get_connection()
    row = conn.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
    if row and row["status"] in ("placed", "confirmed"):
        conn.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False
