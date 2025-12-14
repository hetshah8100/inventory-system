import os
import psycopg
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

def db():
    return psycopg.connect(DATABASE_URL)

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

@app.route("/", methods=["GET", "POST"])
def add_stock():
    with db() as con:
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

        cur.execute("SELECT name FROM stores ORDER BY name")
        stores = cur.fetchall()

        cur.execute("SELECT name FROM categories ORDER BY name")
        categories = cur.fetchall()

    return render_template("add.html", stores=stores, categories=categories)

@app.route("/supervisor")
def supervisor():
    selected_category = request.args.get("category", "ALL")

    with db() as con:
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

    return render_template(
        "view.html",
        rows=rows,
        categories=categories,
        selected_category=selected_category
    )

@app.route("/clear_inventory")
def clear_inventory():
    with db() as con:
        con.cursor().execute("DELETE FROM inventory")
    return redirect("/supervisor")

@app.route("/stores", methods=["GET", "POST"])
def manage_admin():
    with db() as con:
        cur = con.cursor()

        if request.method == "POST":
            if request.form["type"] == "store":
                cur.execute(
                    "INSERT INTO stores (name) VALUES (%s) ON CONFLICT DO NOTHING",
                    (request.form["name"],)
                )
            elif request.form["type"] == "category":
                cur.execute(
                    "INSERT INTO categories (name) VALUES (%s) ON CONFLICT DO NOTHING",
                    (request.form["name"],)
                )

        cur.execute("SELECT * FROM stores ORDER BY name")
        stores = cur.fetchall()

        cur.execute("SELECT * FROM categories ORDER BY name")
        categories = cur.fetchall()

    return render_template("stores.html", stores=stores, categories=categories)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
