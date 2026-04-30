# app/database/seed.py
# Seeds the database with sample data for all roles.
# Passwords are bcrypt-hashed — never stored as plain text.

from app.database.db_manager import get_connection
from app.services.auth_service import hash_password


def seed_data():
    """Insert sample data only if the users table is empty."""
    conn = get_connection()
    cursor = conn.cursor()

    count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count > 0:
        conn.close()
        return

    print("[Seed] Seeding sample data with hashed passwords…")

    # ── Hash the demo password once, reuse for all seed users ─────────────────
    # Demo password for ALL seed accounts is: Demo@1234
    demo_hash = hash_password("Demo@1234")

    # ── Users ──────────────────────────────────────────────────────────────────
    users = [
        ("farmer1",   demo_hash, "farmer",   "Rahim Uddin",   "rahim@farm.com",    "01711111111", "Rajshahi, Bangladesh",   "Rahim Agro Farm",  "5 acres"),
        ("farmer2",   demo_hash, "farmer",   "Karim Ali",     "karim@farm.com",    "01722222222", "Rangpur, Bangladesh",    "Karim Green Farm", "3 acres"),
        ("customer1", demo_hash, "customer", "Sumaiya Begum", "sumaiya@mail.com",  "01733333333", "Dhaka, Bangladesh",      None, None),
        ("customer2", demo_hash, "customer", "Tanvir Hasan",  "tanvir@mail.com",   "01744444444", "Chittagong, Bangladesh", None, None),
        ("agent1",    demo_hash, "agent",    "Nayeem Khan",   "nayeem@agent.com",  "01755555555", "Dhaka, Bangladesh",      None, None),
        ("investor1", demo_hash, "investor", "Sarwar Jahan",  "sarwar@invest.com", "01766666666", "Sylhet, Bangladesh",     None, None),
        ("investor2", demo_hash, "investor", "Fatema Khatun", "fatema@invest.com", "01777777777", "Dhaka, Bangladesh",      None, None),
    ]
    cursor.executemany("""
        INSERT INTO users
            (username, password_hash, role, full_name, email, phone, address, farm_name, farm_size)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, users)

    # ── Products ───────────────────────────────────────────────────────────────
    products = [
        (1, "Tomato",       "Vegetables", "Fresh red tomatoes",          35.0,  200, "kg",  "2026-05-01"),
        (1, "Potato",       "Vegetables", "High-quality white potatoes", 25.0,  500, "kg",  "2026-06-15"),
        (1, "Mango",        "Fruits",     "Rajshahi alphonso mango",     90.0,  150, "kg",  "2026-04-20"),
        (1, "Rice (Fine)",  "Grains",     "Premium fine rice",           65.0, 1000, "kg",  "2026-12-31"),
        (1, "Mustard Oil",  "Oil",        "Cold-pressed mustard oil",   120.0,   80, "ltr", "2027-01-01"),
        (2, "Brinjal",      "Vegetables", "Fresh purple brinjal",        20.0,  300, "kg",  "2026-04-30"),
        (2, "Green Chilli", "Vegetables", "Hot green chilli",            60.0,  100, "kg",  "2026-04-25"),
        (2, "Lentils",      "Grains",     "Red masoor lentils",          85.0,  400, "kg",  "2026-11-30"),
        (2, "Hilsa Fish",   "Fish",       "Fresh Padma hilsa",          600.0,   50, "kg",  "2026-04-10"),
        (2, "Guava",        "Fruits",     "Sweet white guava",           45.0,  120, "kg",  "2026-04-15"),
    ]
    cursor.executemany("""
        INSERT INTO products (farmer_id, name, category, description, price, stock_qty, unit, expiry_date)
        VALUES (?,?,?,?,?,?,?,?)
    """, products)

    # ── Orders ─────────────────────────────────────────────────────────────────
    orders = [
        (3, 1, 1, 10.0,  350.0, "instant", "placed",    "Please deliver fresh"),
        (3, 3, 1,  5.0,  450.0, "instant", "confirmed", ""),
        (4, 2, 1, 20.0,  500.0, "instant", "harvested", ""),
        (4, 6, 2, 15.0,  300.0, "advance", "placed",    "Advance booking"),
        (3, 4, 1, 50.0, 3250.0, "instant", "delivered", ""),
    ]
    cursor.executemany("""
        INSERT INTO orders (customer_id, product_id, farmer_id, quantity, total_price, order_type, status, notes)
        VALUES (?,?,?,?,?,?,?,?)
    """, orders)

    # ── Payments ───────────────────────────────────────────────────────────────
    payments = [
        (1,  350.0,    0.0, "unpaid",  "cash",   None),
        (2,  450.0,  450.0, "paid",    "online", "2026-03-28 10:00:00"),
        (3,  500.0,  250.0, "partial", "cash",   "2026-03-29 14:00:00"),
        (4,  300.0,    0.0, "unpaid",  "cash",   None),
        (5, 3250.0, 3250.0, "paid",    "online", "2026-03-25 09:00:00"),
    ]
    cursor.executemany("""
        INSERT INTO payments (order_id, amount_due, amount_paid, status, method, paid_at)
        VALUES (?,?,?,?,?,?)
    """, payments)

    # ── Investments ────────────────────────────────────────────────────────────
    investments = [
        (1, "Mango Orchard Expansion",
         "Expanding our mango orchard by 2 acres with drip irrigation. ROI expected in 8 months.",
         50000.0, 20000.0, 18.0, "open"),
        (2, "Greenhouse Vegetable Unit",
         "Setting up a modern greenhouse for year-round vegetable production.",
         80000.0, 80000.0, 22.0, "funded"),
    ]
    cursor.executemany("""
        INSERT INTO investments (farmer_id, title, description, goal_amount, raised_amount, expected_roi, status)
        VALUES (?,?,?,?,?,?,?)
    """, investments)

    # ── Investment Contributions ────────────────────────────────────────────────
    contributions = [
        (1, 6, 10000.0),
        (1, 7, 10000.0),
        (2, 6, 40000.0),
        (2, 7, 40000.0),
    ]
    cursor.executemany("""
        INSERT INTO investment_contributions (investment_id, investor_id, amount)
        VALUES (?,?,?)
    """, contributions)

    conn.commit()
    conn.close()
    print("[Seed] Done. All passwords hashed with bcrypt. Demo password: Demo@1234")