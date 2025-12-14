import os
import psycopg2
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# ---------------- DATABASE CONNECTION ----------------
DATABASE_URL = os.environ.get("DATABASE_URL")

def db():
    return psycopg2.connect(DATABASE_URL)

# ---------------- INIT DATABASE ----------------
def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS stores (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id SERIAL PRIMARY KEY,
        date DATE,
        store TEXT,
        product TEXT,
        category TEXT,
        quantity INTEGER,
        entered_by TEXT
    )
    """)

    con.commit()
    cur.close()
    con.close()

# ---------------- SHOPKEEPER ----------------
@app.route("/", methods=["GET", "POST"])
def add_stock():
    con = db()
    cur = con.cursor()

    if request.method == "POST":
        d = request.form
        cur.execute("""
            INSERT INTO inventory
            (date, store, product, category, quantity, entered_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            d["date"],
            d["store"],
            d["product"],
            d["category"],
            d["quantity"],
            d["entered_by"]
        ))
        con.commit()

    cur.execute("SELECT name FROM stores ORDER BY name")
    stores = cur.fetchall()

    cur.execute("SELECT name FROM categories ORDER BY name")
    categories = cur.fetchall()

    cur.close()
    con.close()

    return render_template("add.html", stores=stores, categories=categories)

# ---------------- SUPERVISOR ----------------
@app.route("/supervisor")
def supervisor():
    selected_category = request.args.get("category", "ALL")
    con = db()
    cur = con.cursor()

    cur.execute("SELECT name FROM categories ORDER BY name")
    categories = cur.fetchall()

    if selected_category == "ALL":
        cur.execute("""
            SELECT id, date, store, product, category, quantity, entered_by
            FROM inventory
            ORDER BY category, product, store
        """)
    else:
        cur.execute("""
            SELECT id, date, store, product, category, quantity, entered_by
            FROM inventory
            WHERE category = %s
            ORDER BY product, store
        """, (selected_category,))

    rows = cur.fetchall()
    cur.close()
    con.close()

    return render_template(
        "view.html",
        rows=rows,
        categories=categories,
        selected_category=selected_category
    )

# ---------------- EDIT ITEM ----------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    con = db()
    cur = con.cursor()

    if request.method == "POST":
        d = request.form
        cur.execute("""
            UPDATE inventory
            SET date=%s, store=%s, product=%s, category=%s,
                quantity=%s, entered_by=%s
            WHERE id=%s
        """, (
            d["date"],
            d["store"],
            d["product"],
            d["category"],
            d["quantity"],
            d["entered_by"],
            id
        ))
        con.commit()
        cur.close()
        con.close()
        return redirect("/supervisor")

    cur.execute("SELECT * FROM inventory WHERE id=%s", (id,))
    row = cur.fetchone()

    cur.execute("SELECT name FROM stores ORDER BY name")
    stores = cur.fetchall()

    cur.execute("SELECT name FROM categories ORDER BY name")
    categories = cur.fetchall()

    cur.close()
    con.close()

    return render_template(
        "edit.html",
        row=row,
        stores=stores,
        categories=categories
    )

# ---------------- DELETE SINGLE ITEM ----------------
@app.route("/delete/<int:id>")
def delete(id):
    con = db()
    cur = con.cursor()
    cur.execute("DELETE FROM inventory WHERE id=%s", (id,))
    con.commit()
    cur.close()
    con.close()
    return redirect("/supervisor")

# ---------------- CLEAR ALL INVENTORY ----------------
@app.route("/clear_inventory")
def clear_inventory():
    con = db()
    cur = con.cursor()
    cur.execute("DELETE FROM inventory")
    con.commit()
    cur.close()
    con.close()
    return redirect("/supervisor")

# ---------------- MANAGE STORES & CATEGORIES ----------------
@app.route("/stores", methods=["GET", "POST"])
def manage_admin():
    con = db()
    cur = con.cursor()

    if request.method == "POST" and request.form.get("type") == "store":
        cur.execute(
            "INSERT INTO stores (name) VALUES (%s) ON CONFLICT DO NOTHING",
            (request.form["name"],)
        )
        con.commit()

    if request.method == "POST" and request.form.get("type") == "category":
        cur.execute(
            "INSERT INTO categories (name) VALUES (%s) ON CONFLICT DO NOTHING",
            (request.form["name"],)
        )
        con.commit()

    cur.execute("SELECT * FROM stores ORDER BY name")
    stores = cur.fetchall()

    cur.execute("SELECT * FROM categories ORDER BY name")
    categories = cur.fetchall()

    cur.close()
    con.close()

    return render_template(
        "stores.html",
        stores=stores,
        categories=categories
    )

# ---------------- DELETE STORE ----------------
@app.route("/delete_store/<int:id>")
def delete_store(id):
    con = db()
    cur = con.cursor()

    cur.execute("SELECT name FROM stores WHERE id=%s", (id,))
    store = cur.fetchone()

    cur.execute("SELECT 1 FROM inventory WHERE store=%s LIMIT 1", (store[0],))
    used = cur.fetchone()

    if used:
        cur.close()
        con.close()
        return "Cannot delete store. Store is used.", 400

    cur.execute("DELETE FROM stores WHERE id=%s", (id,))
    con.commit()
    cur.close()
    con.close()
    return redirect("/stores")

# ---------------- DELETE CATEGORY ----------------
@app.route("/delete_category/<int:id>")
def delete_category(id):
    con = db()
    cur = con.cursor()

    cur.execute("SELECT name FROM categories WHERE id=%s", (id,))
    cat = cur.fetchone()

    cur.execute("SELECT 1 FROM inventory WHERE category=%s LIMIT 1", (cat[0],))
    used = cur.fetchone()

    if used:
        cur.close()
        con.close()
        return "Cannot delete category. Category is used.", 400

    cur.execute("DELETE FROM categories WHERE id=%s", (id,))
    con.commit()
    cur.close()
    con.close()
    return redirect("/stores")

# ---------------- START APP ----------------
if __name__ == "__main__":
    init_db()
    print("FLASK INVENTORY SYSTEM (POSTGRES) STARTED")
    app.run(host="0.0.0.0", port=5000)
