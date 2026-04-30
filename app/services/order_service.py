# app/services/order_service.py
# All order management database operations.
# Returns plain dicts or lists — no PyQt5 here.

from app.database.db_manager import get_connection

# Valid one-way status pipeline — order can only move forward
STATUS_PIPELINE = ["placed", "confirmed", "harvested", "delivered"]
VALID_ORDER_TYPES = ["instant", "advance"]


# ── Validation ─────────────────────────────────────────────────────────────────

def validate_order_data(quantity: str, order_type: str,
                        stock_qty: float) -> str | None:
    """
    Validate order form inputs.
    Returns an error message string, or None if valid.
    """
    try:
        qty = float(quantity)
        if qty <= 0:
            return "Quantity must be greater than 0."
        if qty > stock_qty:
            return f"Insufficient stock. Only {stock_qty} units available."
    except (ValueError, TypeError):
        return "Quantity must be a valid number."

    if order_type not in VALID_ORDER_TYPES:
        return "Invalid order type."

    return None


def next_status(current: str) -> str | None:
    """
    Return the next valid status in the pipeline.
    Returns None if already at the final status.
    """
    try:
        idx = STATUS_PIPELINE.index(current)
        if idx < len(STATUS_PIPELINE) - 1:
            return STATUS_PIPELINE[idx + 1]
        return None
    except ValueError:
        return None


# ── Place Order ────────────────────────────────────────────────────────────────

def place_order(customer_id: int, product_id: int,
                quantity: float, order_type: str,
                notes: str = "") -> dict:
    """
    Place a new order for a customer.
    - Validates stock availability
    - Calculates total price
    - Creates the order row
    - Creates a corresponding payment row (unpaid)
    - Deducts stock from the product

    Returns {"success": True, "order_id": int}
         or {"success": False, "message": str}
    """
    try:
        conn = get_connection()

        # Fetch product — verify it exists and has enough stock
        product = conn.execute(
            "SELECT * FROM products WHERE id = ? AND stock_qty >= ?",
            (product_id, quantity)
        ).fetchone()

        if not product:
            conn.close()
            return {
                "success": False,
                "message": "Product not found or insufficient stock."
            }

        error = validate_order_data(str(quantity), order_type, product["stock_qty"])
        if error:
            conn.close()
            return {"success": False, "message": error}

        total_price = round(product["price"] * quantity, 2)
        farmer_id   = product["farmer_id"]

        # Insert order
        cursor = conn.execute("""
            INSERT INTO orders
                (customer_id, product_id, farmer_id, quantity,
                 total_price, order_type, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, 'placed', ?)
        """, (customer_id, product_id, farmer_id,
              quantity, total_price, order_type,
              notes.strip()))
        order_id = cursor.lastrowid

        # Create matching payment record (unpaid)
        conn.execute("""
            INSERT INTO payments (order_id, amount_due, amount_paid, status, method)
            VALUES (?, ?, 0, 'unpaid', 'cash')
        """, (order_id, total_price))

        # Deduct stock
        conn.execute(
            "UPDATE products SET stock_qty = stock_qty - ? WHERE id = ?",
            (quantity, product_id)
        )

        conn.commit()
        conn.close()
        return {"success": True, "order_id": order_id}

    except Exception as exc:
        return {"success": False, "message": f"Database error: {exc}"}


# ── Status Updates ─────────────────────────────────────────────────────────────

def advance_order_status(order_id: int, farmer_id: int) -> dict:
    """
    Move an order one step forward in the status pipeline.
    Only the owning farmer can advance their orders.
    Cannot advance a cancelled or delivered order.
    """
    try:
        conn = get_connection()
        order = conn.execute(
            "SELECT * FROM orders WHERE id = ? AND farmer_id = ?",
            (order_id, farmer_id)
        ).fetchone()

        if not order:
            conn.close()
            return {"success": False, "message": "Order not found or access denied."}

        current = order["status"]
        new_status = next_status(current)

        if new_status is None:
            conn.close()
            return {
                "success": False,
                "message": f"Order is already at final status: '{current}'."
            }

        conn.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (new_status, order_id)
        )
        conn.commit()
        conn.close()
        return {"success": True, "new_status": new_status}

    except Exception as exc:
        return {"success": False, "message": f"Database error: {exc}"}


def cancel_order(order_id: int, requestor_id: int,
                 role: str) -> dict:
    """
    Cancel an order.
    - Customers can cancel only their own 'placed' orders
    - Agents can cancel any order not yet delivered
    Restores stock when cancelled.
    """
    try:
        conn = get_connection()

        if role == "customer":
            order = conn.execute(
                "SELECT * FROM orders WHERE id = ? AND customer_id = ? AND status = 'placed'",
                (order_id, requestor_id)
            ).fetchone()
        elif role == "agent":
            order = conn.execute(
                "SELECT * FROM orders WHERE id = ? AND status != 'delivered'",
                (order_id,)
            ).fetchone()
        else:
            conn.close()
            return {"success": False, "message": "Permission denied."}

        if not order:
            conn.close()
            return {
                "success": False,
                "message": "Order not found, already delivered, or cannot be cancelled."
            }

        # Restore stock
        conn.execute(
            "UPDATE products SET stock_qty = stock_qty + ? WHERE id = ?",
            (order["quantity"], order["product_id"])
        )

        # Cancel order
        conn.execute(
            "UPDATE orders SET status = 'cancelled' WHERE id = ?",
            (order_id,)
        )

        # Mark payment as unpaid/void
        conn.execute(
            "UPDATE payments SET status = 'unpaid', amount_paid = 0 WHERE order_id = ?",
            (order_id,)
        )

        conn.commit()
        conn.close()
        return {"success": True}

    except Exception as exc:
        return {"success": False, "message": f"Database error: {exc}"}


# ── Queries ────────────────────────────────────────────────────────────────────

def get_orders_for_customer(customer_id: int) -> list[dict]:
    """All orders placed by this customer, newest first."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT o.*,
                   p.name   AS product_name,
                   p.unit   AS product_unit,
                   u.full_name AS farmer_name
            FROM orders o
            JOIN products p ON p.id = o.product_id
            JOIN users    u ON u.id = o.farmer_id
            WHERE o.customer_id = ?
            ORDER BY o.created_at DESC
        """, (customer_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[order_service] get_orders_for_customer error: {exc}")
        return []


def get_orders_for_farmer(farmer_id: int) -> list[dict]:
    """All orders for this farmer's products, newest first."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT o.*,
                   p.name     AS product_name,
                   p.unit     AS product_unit,
                   u.full_name AS customer_name
            FROM orders o
            JOIN products p ON p.id = o.product_id
            JOIN users    u ON u.id = o.customer_id
            WHERE o.farmer_id = ?
            ORDER BY o.created_at DESC
        """, (farmer_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[order_service] get_orders_for_farmer error: {exc}")
        return []


def get_all_orders() -> list[dict]:
    """All orders across the platform (for agents). Newest first."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT o.*,
                   p.name      AS product_name,
                   p.unit      AS product_unit,
                   c.full_name AS customer_name,
                   f.full_name AS farmer_name
            FROM orders o
            JOIN products p ON p.id = o.product_id
            JOIN users    c ON c.id = o.customer_id
            JOIN users    f ON f.id = o.farmer_id
            ORDER BY o.created_at DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[order_service] get_all_orders error: {exc}")
        return []


def get_order_by_id(order_id: int) -> dict | None:
    """Fetch a single order with all joined details."""
    try:
        conn = get_connection()
        row = conn.execute("""
            SELECT o.*,
                   p.name      AS product_name,
                   p.unit      AS product_unit,
                   p.price     AS unit_price,
                   c.full_name AS customer_name,
                   f.full_name AS farmer_name
            FROM orders o
            JOIN products p ON p.id = o.product_id
            JOIN users    c ON c.id = o.customer_id
            JOIN users    f ON f.id = o.farmer_id
            WHERE o.id = ?
        """, (order_id,)).fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as exc:
        print(f"[order_service] get_order_by_id error: {exc}")
        return None
