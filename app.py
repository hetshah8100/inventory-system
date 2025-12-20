from flask import Flask, render_template, request, redirect, url_for
import psycopg
import os
from datetime import datetime

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

def db():
    return psycopg.connect(DATABASE_URL)

# ---------------- INIT DB ----------------
def init_db():
    with db() as con:
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            date TIMESTAMP,
            store TEXT,
            category TEXT,
            product TEXT,
            quantity INTEGER,
            entered_by TEXT
        )""")
        con.commit()

init_db()

# ---------------- SHOPKEEPER ----------------
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
                request.form["quantity"],
                request.form["entered_by"]
            ))
            con.commit()
            return redirect(url_for("shopkeeper", store=request.form["store"]))

        cur.execute("SELECT name FROM stores ORDER BY name")
        stores = [s[0] for s in cur.fetchall()]

        cur.execute("SELECT name FROM categories ORDER BY name")
        categories = [c[0] for c in cur.fetchall()]

        if selected_store:
            cur.execute("""
            SELECT id, date, category, product, quantity, entered_by
            FROM products
            WHERE store=%s
            ORDER BY date DESC
            """, (selected_store,))
        else:
            cur.execute("SELECT id, date, category, product, quantity, entered_by FROM products WHERE false")

        products = cur.fetchall()

    return render_template(
        "index.html",
        stores=stores,
        categories=categories,
        products=products,
        selected_store=selected_store
    )

# ---------------- SUPERVISOR ----------------
@app.route("/supervisor")
def supervisor():
    with db() as con:
        cur = con.cursor()
        cur.execute("""
        SELECT id, date, store, category, product, quantity, entered_by
        FROM products
        ORDER BY date DESC
        """)
        products = cur.fetchall()

    return render_template("supervisor.html", products=products)

# ---------------- EDIT PRODUCT ----------------
@app.route("/edit/<int:pid>", methods=["GET", "POST"])
def edit(pid):
    with db() as con:
        cur = con.cursor()

        if request.method == "POST":
            cur.execute("""
            UPDATE products
            SET category=%s, product=%s, quantity=%s
            WHERE id=%s
            """, (
                request.form["category"],
                request.form["product"],
                request.form["quantity"],
                pid
            ))
            con.commit()
            return redirect(url_for("supervisor"))

        cur.execute("SELECT id, category, product, quantity FROM products WHERE id=%s", (pid,))
        product = cur.fetchone()

        cur.execute("SELECT name FROM categories ORDER BY name")
        categories = [c[0] for c in cur.fetchall()]

    return render_template("edit.html", product=product, categories=categories)

# ---------------- DELETE PRODUCT ----------------
@app.route("/delete/<int:pid>")
def delete(pid):
    with db() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM products WHERE id=%s", (pid,))
        con.commit()
    return redirect(url_for("supervisor"))

# ---------------- CLEAR INVENTORY ----------------
@app.route("/clear_inventory")
def clear_inventory():
    with db() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM products")
        con.commit()
    return redirect(url_for("supervisor"))

# ---------------- STORES ----------------
@app.route("/stores", methods=["GET", "POST"])
def stores():
    with db() as con:
        cur = con.cursor()
        if request.method == "POST":
            cur.execute("INSERT INTO stores (name) VALUES (%s) ON CONFLICT DO NOTHING",
                        (request.form["name"],))
            con.commit()
        cur.execute("SELECT name FROM stores ORDER BY name")
        stores = cur.fetchall()
    return render_template("stores.html", stores=stores)

# ---------------- CATEGORIES ----------------
@app.route("/categories", methods=["GET", "POST"])
def categories():
    with db() as con:
        cur = con.cursor()
        if request.method == "POST":
            cur.execute("INSERT INTO categories (name) VALUES (%s) ON CONFLICT DO NOTHING",
                        (request.form["name"],))
            con.commit()
        cur.execute("SELECT name FROM categories ORDER BY name")
        categories = cur.fetchall()
    return render_template("categories.html", categories=categories)
