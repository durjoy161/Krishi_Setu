# app/services/product_service.py
# CRUD operations for products

from app.database.db_manager import get_connection
import app.utils.session as session


CATEGORIES = ["Vegetables", "Fruits", "Grains", "Fish", "Oil", "Dairy", "Spices", "Other"]


def get_all_products():
    """Return all products with farmer name joined."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.*, u.full_name AS farmer_name
        FROM products p
        JOIN users u ON p.farmer_id = u.id
        ORDER BY p.category, p.name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_farmer_products(farmer_id: int):
    """Return products belonging to a specific farmer."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM products WHERE farmer_id = ? ORDER BY category, name",
        (farmer_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_product_by_id(product_id: int):
    """Return a single product dict."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_product(name, category, description, price, stock_qty, unit, expiry_date):
    """Add a new product for the currently logged-in farmer."""
    farmer_id = session.get_id()
    conn = get_connection()
    conn.execute("""
        INSERT INTO products (farmer_id, name, category, description, price, stock_qty, unit, expiry_date)
        VALUES (?,?,?,?,?,?,?,?)
    """, (farmer_id, name, category, description, float(price), float(stock_qty), unit, expiry_date))
    conn.commit()
    conn.close()


def update_product(product_id, name, category, description, price, stock_qty, unit, expiry_date):
    """Update an existing product."""
    conn = get_connection()
    conn.execute("""
        UPDATE products
        SET name=?, category=?, description=?, price=?, stock_qty=?, unit=?, expiry_date=?
        WHERE id=?
    """, (name, category, description, float(price), float(stock_qty), unit, expiry_date, product_id))
    conn.commit()
    conn.close()


def delete_product(product_id: int):
    """Delete a product by id."""
    conn = get_connection()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


def reduce_stock(product_id: int, quantity: float):
    """Reduce stock when an order is placed."""
    conn = get_connection()
    conn.execute(
        "UPDATE products SET stock_qty = MAX(0, stock_qty - ?) WHERE id = ?",
        (quantity, product_id)
    )
    conn.commit()
    conn.close()
