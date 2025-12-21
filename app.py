from flask import Flask, render_template, request, redirect, url_for
import psycopg
import os
from datetime import datetime

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

def db():
    return psycopg.connect(DATABASE_URL)

# ---------- DATABASE SETUP ----------
def init_db():
    with db() as con:
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        );
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
        );
        """)
        con.commit()

init_db()

# ---------- SHOPKEEPER ----------
@app.route("/", methods=["GET", "POST"])
def shopkeeper():
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

        cur.execute("SELECT name FROM stores ORDER BY name")
        stores = cur.fetchall()

        cur.execute("SELECT name FROM categories ORDER BY name")
        categories = cur.fetchall()

        cur.execute("""
            SELECT id, date, store, category, product, quantity, entered_by
            FROM products
            ORDER BY date DESC
        """)
        products = cur.fetchall()

    return render_template(
        "index.html",
        stores=stores,
        categories=categories,
        products=products
    )

# ---------- STORES ----------
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
        stores = cur.fetchall()

    return render_template("stores.html", stores=stores)

# ---------- CATEGORIES ----------
@app.route("/categories", methods=["GET", "POST"])
def manage_categories():
    with db() as con:
        cur = con.cursor()
        if request.method == "POST":
            cur.execute(
                "INSERT INTO categories (name) VALUES (%s) ON CONFLICT DO NOTHING",
                (request.form["name"],)
            )
            con.commit()

        cur.execute("SELECT name FROM categories ORDER BY name")
        categories = cur.fetchall()

    return render_template("categories.html", categories=categories)

# ---------- SUPERVISOR ----------
@app.route("/supervisor")
def supervisor():
    selected_category = request.args.get("category")

    with db() as con:
        cur = con.cursor()

        cur.execute("SELECT name FROM categories ORDER BY name")
        categories = [c[0] for c in cur.fetchall()]

        if selected_category:
            cur.execute("""
                SELECT id, date, store, category, product, quantity, entered_by
                FROM products
                WHERE category = %s
                ORDER BY date DESC
            """, (selected_category,))
        else:
            cur.execute("""
                SELECT id, date, store, category, product, quantity, entered_by
                FROM products
                ORDER BY date DESC
            """)

        products = cur.fetchall()

    return render_template(
        "supervisor.html",
        products=products,
        categories=categories,
        selected_category=selected_category
    )

# ---------- DELETE PRODUCT ----------
@app.route("/delete/<int:product_id>")
def delete_product(product_id):
    with db() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
        con.commit()
    return redirect(url_for("supervisor"))

# ---------- CLEAR ALL ----------
@app.route("/clear-all")
def clear_all():
    with db() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM products")
        con.commit()
    return redirect(url_for("supervisor"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
