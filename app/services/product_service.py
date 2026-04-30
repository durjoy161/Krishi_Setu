# app/services/product_service.py
# All product and inventory database operations.
# Returns plain dicts or lists of dicts — no PyQt5 here.

from app.database.db_manager import get_connection

VALID_CATEGORIES = [
    "Vegetables", "Fruits", "Grains", "Oil",
    "Fish", "Dairy", "Spices", "Other"
]
VALID_UNITS = ["kg", "ltr", "pcs", "dozen", "bag", "bundle"]


# ── Validation ─────────────────────────────────────────────────────────────────

def validate_product_data(name: str, category: str, price: str,
                          stock_qty: str, unit: str) -> str | None:
    """
    Validate product form inputs.
    Returns an error message string, or None if everything is valid.
    """
    if not name.strip():
        return "Product name cannot be empty."
    if len(name.strip()) < 2:
        return "Product name must be at least 2 characters."
    if category not in VALID_CATEGORIES:
        return f"Invalid category. Choose from: {', '.join(VALID_CATEGORIES)}."
    try:
        p = float(price)
        if p <= 0:
            return "Price must be greater than 0."
    except (ValueError, TypeError):
        return "Price must be a valid number."
    try:
        s = float(stock_qty)
        if s < 0:
            return "Stock quantity cannot be negative."
    except (ValueError, TypeError):
        return "Stock quantity must be a valid number."
    if unit not in VALID_UNITS:
        return f"Invalid unit. Choose from: {', '.join(VALID_UNITS)}."
    return None


# ── CRUD ───────────────────────────────────────────────────────────────────────

def add_product(farmer_id: int, name: str, category: str,
                description: str, price: float, stock_qty: float,
                unit: str, expiry_date: str = None) -> dict:
    """
    Insert a new product row.
    Returns {"success": True} or {"success": False, "message": "..."}.
    """
    error = validate_product_data(name, category, str(price), str(stock_qty), unit)
    if error:
        return {"success": False, "message": error}
    try:
        conn = get_connection()
        conn.execute("""
            INSERT INTO products
                (farmer_id, name, category, description, price, stock_qty, unit, expiry_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            farmer_id,
            name.strip(),
            category,
            description.strip(),
            float(price),
            float(stock_qty),
            unit,
            expiry_date.strip() if expiry_date and expiry_date.strip() else None,
        ))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as exc:
        return {"success": False, "message": f"Database error: {exc}"}


def update_product(product_id: int, farmer_id: int, name: str,
                   category: str, description: str, price: float,
                   stock_qty: float, unit: str,
                   expiry_date: str = None) -> dict:
    """
    Update an existing product. farmer_id check prevents editing
    another farmer's products.
    """
    error = validate_product_data(name, category, str(price), str(stock_qty), unit)
    if error:
        return {"success": False, "message": error}
    try:
        conn = get_connection()
        rows = conn.execute("""
            UPDATE products
            SET name=?, category=?, description=?, price=?,
                stock_qty=?, unit=?, expiry_date=?
            WHERE id=? AND farmer_id=?
        """, (
            name.strip(), category, description.strip(),
            float(price), float(stock_qty), unit,
            expiry_date.strip() if expiry_date and expiry_date.strip() else None,
            product_id, farmer_id,
        )).rowcount
        conn.commit()
        conn.close()
        if rows == 0:
            return {"success": False, "message": "Product not found or access denied."}
        return {"success": True}
    except Exception as exc:
        return {"success": False, "message": f"Database error: {exc}"}


def delete_product(product_id: int, farmer_id: int) -> dict:
    """
    Delete a product. Only the owning farmer can delete it.
    Prevents deletion if active orders reference this product.
    """
    try:
        conn = get_connection()
        active = conn.execute("""
            SELECT COUNT(*) FROM orders
            WHERE product_id = ? AND status NOT IN ('delivered', 'cancelled')
        """, (product_id,)).fetchone()[0]

        if active > 0:
            conn.close()
            return {
                "success": False,
                "message": f"Cannot delete — {active} active order(s) reference this product."
            }

        rows = conn.execute(
            "DELETE FROM products WHERE id = ? AND farmer_id = ?",
            (product_id, farmer_id)
        ).rowcount
        conn.commit()
        conn.close()
        if rows == 0:
            return {"success": False, "message": "Product not found or access denied."}
        return {"success": True}
    except Exception as exc:
        return {"success": False, "message": f"Database error: {exc}"}


def update_stock(product_id: int, farmer_id: int, new_qty: float) -> dict:
    """Quick stock-only update (used from order completion flow)."""
    if new_qty < 0:
        return {"success": False, "message": "Stock cannot be negative."}
    try:
        conn = get_connection()
        conn.execute(
            "UPDATE products SET stock_qty = ? WHERE id = ? AND farmer_id = ?",
            (new_qty, product_id, farmer_id)
        )
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as exc:
        return {"success": False, "message": f"Database error: {exc}"}


# ── Queries ────────────────────────────────────────────────────────────────────

def get_products_by_farmer(farmer_id: int) -> list[dict]:
    """Return all products belonging to a specific farmer."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT * FROM products
            WHERE farmer_id = ?
            ORDER BY created_at DESC
        """, (farmer_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[product_service] get_products_by_farmer error: {exc}")
        return []


def get_all_available_products(search: str = "",
                               category: str = "All") -> list[dict]:
    """
    Return all products with stock > 0, with optional search and category filter.
    Joins with users to include the farmer's name.
    """
    try:
        conn = get_connection()
        query = """
            SELECT p.*, u.full_name AS farmer_name, u.farm_name
            FROM products p
            JOIN users u ON u.id = p.farmer_id
            WHERE p.stock_qty > 0
        """
        params = []
        if search.strip():
            query += " AND (p.name LIKE ? OR p.description LIKE ?)"
            like = f"%{search.strip()}%"
            params += [like, like]
        if category and category != "All":
            query += " AND p.category = ?"
            params.append(category)
        query += " ORDER BY p.created_at DESC"

        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"[product_service] get_all_available_products error: {exc}")
        return []


def get_product_by_id(product_id: int) -> dict | None:
    """Fetch a single product row by id."""
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as exc:
        print(f"[product_service] get_product_by_id error: {exc}")
        return None
