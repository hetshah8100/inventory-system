from flask import Flask, render_template, request, redirect, url_for
import psycopg
import os
from datetime import datetime

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

def db():
    return psycopg.connect(DATABASE_URL)

# ------------------ DB INIT ------------------
def init_db():
    with db() as con:
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
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            date TIMESTAMP,
            store TEXT,
            category TEXT,
            product TEXT,
            quantity INTEGER,
            entered_by TEXT
        )
        """)

        con.commit()

init_db()

# ------------------ SHOPKEEPER ------------------
@app.route("/", methods=["GET", "POST"])
def shopkeeper():
    selected_store = request.args.get("store")

    with db() as con:
        cur = con.cursor()

        if request.method == "POST":
            cur.execute("""
            INSERT INTO products (date, store, category, product, quantity, entered_by)
            VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                datetime.now(),
                request.form["store"],
                request.form["category"],
                request.form["product"],
                int(request.form["quantity"]),
                request.form["entered_by"]
            ))
            con.commit()
            return redirect(url_for("shopkeeper", store=request.form["store"]))

        cur.execute("SELECT name FROM stores ORDER BY name")
        stores = [s[0] for s in cur.fetchall()]

        cur.execute("SELECT name FROM categories ORDER BY name")
        categories = [c[0] for c in cur.fetchall()]

        products = []
        if selected_store:
            cur.execute("""
            SELECT date, category, product, quantity, entered_by
            FROM products
            WHERE store=%s
            ORDER BY date DESC
            """, (selected_store,))
            products = cur.fetchall()

    return render_template(
        "index.html",
        stores=stores,
        categories=categories,
        products=products,
        selected_store=selected_store
    )

# ------------------ SUPERVISOR (FIXED) ------------------
@app.route("/supervisor")
def supervisor():
    selected_category = request.args.get("category")

    with db() as con:
        cur = con.cursor()

        cur.execute("SELECT name FROM categories ORDER BY name")
        categories = [c[0] for c in cur.fetchall()]

        # ✅ FIX: treat empty or "All" as show everything
        if not selected_category or selected_category == "All":
            cur.execute("""
            SELECT id, date, store, category, product, quantity, entered_by
            FROM products
            ORDER BY date DESC
            """)
        else:
            cur.execute("""
            SELECT id, date, store, category, product, quantity, entered_by
            FROM products
            WHERE category=%s
            ORDER BY date DESC
            """, (selected_category,))

        products = cur.fetchall()

    return render_template(
        "supervisor.html",
        products=products,
        categories=categories,
        selected_category=selected_category or "All"
    )

# ------------------ EDIT PRODUCT ------------------
@app.route("/edit/<int:pid>", methods=["GET", "POST"])
def edit_product(pid):
    with db() as con:
        cur = con.cursor()

        if request.method == "POST":
            cur.execute("""
            UPDATE products
            SET store=%s, category=%s, product=%s, quantity=%s, entered_by=%s
            WHERE id=%s
            """, (
                request.form["store"],
                request.form["category"],
                request.form["product"],
                int(request.form["quantity"]),
                request.form["entered_by"],
                pid
            ))
            con.commit()
            return redirect(url_for("supervisor"))

        cur.execute("""
        SELECT id, store, category, product, quantity, entered_by
        FROM products
        WHERE id=%s
        """, (pid,))
        product = cur.fetchone()

        cur.execute("SELECT name FROM categories ORDER BY name")
        categories = [c[0] for c in cur.fetchall()]

        cur.execute("SELECT name FROM stores ORDER BY name")
        stores = [s[0] for s in cur.fetchall()]

    return render_template(
        "edit.html",
        product=product,
        categories=categories,
        stores=stores
    )

# ------------------ DELETE PRODUCT ------------------
@app.route("/delete/<int:pid>")
def delete_product(pid):
    with db() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM products WHERE id=%s", (pid,))
        con.commit()
    return redirect(url_for("supervisor"))

# ------------------ CLEAR INVENTORY ------------------
@app.route("/clear-inventory")
def clear_inventory():
    with db() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM products")
        con.commit()
    return redirect(url_for("supervisor"))

# ------------------ STORES ------------------
@app.route("/stores", methods=["GET", "POST"])
def manage_stores():
    with db() as con:
        cur = con.cursor()

        if request.method == "POST":
            cur.execute(
                "INSERT INTO stores (name) VALUES (%s) ON CONFLICT DO NOTHING",
                (request.form["name"],)
            )
            con.commit()

        cur.execute("SELECT name FROM stores ORDER BY name")
        stores = [s[0] for s in cur.fetchall()]

    return render_template("stores.html", stores=stores)

# ------------------ DELETE STORE ------------------
@app.route("/delete-store/<name>")
def delete_store(name):
    with db() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM stores WHERE name=%s", (name,))
        con.commit()
    return redirect(url_for("manage_stores"))

# ------------------ CATEGORIES ------------------
@app.route("/categories", methods=["GET", "POST"])
def manage_categories():
    with db() as con:
        cur = con.cursor()

        if request.method == "POST":
            cur.execute(
                "FINAL INSERT INTO categories (name) VALUES (%s) ON CONFLICT DO NOTHING",
                (request.form["name"],)
            )
            con.commit()

        cur.execute("SELECT name FROM categories ORDER BY name")
        categories = [c[0] for c in cur.fetchall()]

    return render_template("categories.html", categories=categories)

# ------------------ DELETE CATEGORY ------------------
@app.route("/delete-category/<name>")
def delete_category(name):
    with db() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM categories WHERE name=%s", (name,))
        con.commit()
    return redirect(url_for("manage_categories"))
