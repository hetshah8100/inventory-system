from flask import Flask, render_template, request, redirect, url_for
import os
import psycopg

app = Flask(__name__)

# =========================
# DATABASE CONNECTION
# =========================
DATABASE_URL = os.environ.get("DATABASE_URL")

def db():
    return psycopg.connect(DATABASE_URL)

# =========================
# AUTO CREATE TABLES
# =========================
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
        CREATE TABLE IF NOT EXISTS inventory (
            id SERIAL PRIMARY KEY,
            product TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            store_id INTEGER REFERENCES stores(id),
            category_id INTEGER REFERENCES categories(id),
            entered_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        con.commit()

# =========================
# ROUTES
# =========================

@app.route("/", methods=["GET", "POST"])
def add_stock():
    with db() as con:
        cur = con.cursor()

        # Add product
        if request.method == "POST":
            product = request.form["product"]
            quantity = request.form["quantity"]
            store_id = request.form["store"]
            category_id = request.form["category"]
            entered_by = request.form["entered_by"]

            cur.execute("""
                INSERT INTO inventory (product, quantity, store_id, category_id, entered_by)
                VALUES (%s, %s, %s, %s, %s)
            """, (product, quantity, store_id, category_id, entered_by))

            con.commit()
            return redirect(url_for("add_stock"))

        # Fetch stores & categories
        cur.execute("SELECT id, name FROM stores ORDER BY name")
        stores = cur.fetchall()

        cur.execute("SELECT id, name FROM categories ORDER BY name")
        categories = cur.fetchall()

    return render_template("index.html", stores=stores, categories=categories)


@app.route("/supervisor")
def supervisor():
    with db() as con:
        cur = con.cursor()

        cur.execute("""
            SELECT inventory.id, product, quantity,
                   stores.name AS store,
                   categories.name AS category,
                   entered_by, created_at
            FROM inventory
            LEFT JOIN stores ON inventory.store_id = stores.id
            LEFT JOIN categories ON inventory.category_id = categories.id
            ORDER BY created_at DESC
        """)

        items = cur.fetchall()

    return render_template("supervisor.html", items=items)


@app.route("/stores", methods=["GET", "POST"])
def manage_stores():
    with db() as con:
        cur = con.cursor()

        if request.method == "POST":
            name = request.form["name"]
            cur.execute("INSERT INTO stores (name) VALUES (%s) ON CONFLICT DO NOTHING", (name,))
            con.commit()
            return redirect(url_for("manage_stores"))

        cur.execute("SELECT id, name FROM stores ORDER BY name")
        stores = cur.fetchall()

    return render_template("stores.html", stores=stores)


@app.route("/delete_store/<int:id>")
def delete_store(id):
    with db() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM stores WHERE id = %s", (id,))
        con.commit()
    return redirect(url_for("manage_stores"))


@app.route("/categories", methods=["GET", "POST"])
def manage_categories():
    with db() as con:
        cur = con.cursor()

        if request.method == "POST":
            name = request.form["name"]
            cur.execute("INSERT INTO categories (name) VALUES (%s) ON CONFLICT DO NOTHING", (name,))
            con.commit()
            return redirect(url_for("manage_categories"))

        cur.execute("SELECT id, name FROM categories ORDER BY name")
        categories = cur.fetchall()

    return render_template("categories.html", categories=categories)


@app.route("/delete_category/<int:id>")
def delete_category(id):
    with db() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM categories WHERE id = %s", (id,))
        con.commit()
    return redirect(url_for("manage_categories"))


@app.route("/clear_inventory")
def clear_inventory():
    with db() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM inventory")
        con.commit()
    return redirect(url_for("supervisor"))

# =========================
# STARTUP
# =========================
init_db()

if __name__ == "__main__":
    app.run()

