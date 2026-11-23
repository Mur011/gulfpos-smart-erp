import sqlite3
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DB_NAME = "pos_erp.db"

# 1. Initialize Relational ERP Schema (Products, Sales Header, Sale Line-Items)
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT UNIQUE,
                    name_en TEXT,
                    name_ar TEXT,
                    cost_price_kwd REAL,
                    price_kwd REAL,
                    stock INTEGER
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subtotal_kwd REAL,
                    discount_kwd REAL DEFAULT 0,
                    tax_kwd REAL,
                    total_kwd REAL,
                    profit_kwd REAL,
                    currency_used TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER,
                    product_id INTEGER,
                    sku TEXT,
                    name_en TEXT,
                    qty INTEGER,
                    unit_price_kwd REAL,
                    unit_cost_kwd REAL,
                    FOREIGN KEY (sale_id) REFERENCES sales(id)
                )''')

    # Insert starter GCC retail products with wholesale Cost vs Selling Price
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        starter_items = [
            ("SKU-101", "Royal Dates Box (1kg)", "علبة تمر ملكي", 2.800, 4.500, 25),
            ("SKU-102", "Arabica Coffee Beans", "حبوب قهوة عربية", 1.950, 3.250, 18),
            ("SKU-103", "Saffron Premium Tin", "زعفران فاخر", 5.200, 8.000, 8),
            ("SKU-104", "Smart Wireless Scanner", "ماسح باركود ذكي", 10.500, 15.750, 4)
        ]
        c.executemany(
            "INSERT INTO products (sku, name_en, name_ar, cost_price_kwd, price_kwd, stock) VALUES (?, ?, ?, ?, ?, ?)",
            starter_items
        )
    conn.commit()
    conn.close()

# 2. Fetch Live Exchange Rates (Base: KWD)
def get_exchange_rates():
    try:
        res = requests.get("https://open.er-api.com/v6/latest/KWD", timeout=4).json()
        rates = res.get("rates", {})
        return {"KWD": 1.0, "INR": rates.get("INR", 274.50), "USD": rates.get("USD", 3.25)}
    except Exception:
        return {"KWD": 1.0, "INR": 274.50, "USD": 3.25}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/data")
def get_data():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    products = [dict(row) for row in conn.execute("SELECT * FROM products").fetchall()]
    
    # Aggregate Revenue & Net Profit
    totals = conn.execute("SELECT COALESCE(SUM(total_kwd), 0), COALESCE(SUM(profit_kwd), 0) FROM sales").fetchone()
    
    # Fetch Past Invoices with Line Items for Audit Trail
    sales_rows = conn.execute("SELECT * FROM sales ORDER BY id DESC LIMIT 30").fetchall()
    invoices = []
    for s in sales_rows:
        s_dict = dict(s)
        s_dict["invoice_no"] = f"INV-2026-{s['id']:04d}"
        items = conn.execute("SELECT * FROM sale_items WHERE sale_id = ?", (s["id"],)).fetchall()
        s_dict["items"] = [dict(i) for i in items]
        invoices.append(s_dict)

    conn.close()
    return jsonify({
        "products": products,
        "rates": get_exchange_rates(),
        "total_revenue_kwd": round(totals[0], 3),
        "total_profit_kwd": round(totals[1], 3),
        "invoices": invoices
    })

@app.route("/api/add_product", methods=["POST"])
def add_product():
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute(
            "INSERT INTO products (sku, name_en, name_ar, cost_price_kwd, price_kwd, stock) VALUES (?, ?, ?, ?, ?, ?)",
            (data["sku"], data["name_en"], data["name_ar"], float(data["cost_price_kwd"]), float(data["price_kwd"]), int(data["stock"]))
        )
        conn.commit()
        return jsonify({"status": "success"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "SKU already exists!"}), 400
    finally:
        conn.close()

@app.route("/api/checkout", methods=["POST"])
def checkout():
    data = request.json
    cart = data.get("cart", [])
    currency = data.get("currency", "KWD")
    sub_kwd = float(data.get("sub_kwd", 0))
    discount_kwd = float(data.get("discount_kwd", 0))
    tax_kwd = float(data.get("tax_kwd", 0))
    total_kwd = float(data.get("total_kwd", 0))

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Calculate true net profit after discount
    total_cost_kwd = sum(float(item.get("cost_price_kwd", 0)) * int(item["qty"]) for item in cart)
    net_sales_kwd = sub_kwd - discount_kwd
    profit_kwd = round(net_sales_kwd - total_cost_kwd, 3)

    c.execute(
        "INSERT INTO sales (subtotal_kwd, discount_kwd, tax_kwd, total_kwd, profit_kwd, currency_used) VALUES (?, ?, ?, ?, ?, ?)",
        (sub_kwd, discount_kwd, tax_kwd, total_kwd, profit_kwd, currency)
    )
    sale_id = c.lastrowid

    # Deduct inventory & save immutable audit line-items
    for item in cart:
        c.execute("UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
                  (item["qty"], item["id"], item["qty"]))
        c.execute(
            "INSERT INTO sale_items (sale_id, product_id, sku, name_en, qty, unit_price_kwd, unit_cost_kwd) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (sale_id, item["id"], item["sku"], item["name_en"], item["qty"], item["price_kwd"], item.get("cost_price_kwd", 0))
        )

    conn.commit()
    conn.close()

    invoice_no = f"INV-2026-{sale_id:04d}"
    return jsonify({"status": "success", "invoice_no": invoice_no})

init_db()

if __name__ == "__main__":
    app.run(debug=True)