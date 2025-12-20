from flask import Flask, render_template, request, redirect
import psycopg
import os

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

def db():
    return psycopg.connect(DATABASE_URL)

# ---------------- HOME (SHOPKEEPER) ----------------
@app.route("/", methods=["GET", "POST"])
def add_stock():
    products = []
    selected_store = None

    with db() as con:
        cur = con.cursor()

        cur.execute("SELECT id, name FROM stores ORDER BY name")
        stores = cur.fetchall()

        cur.execute("SELECT id, name FROM categories ORDER BY name")
        categories = cur.fetchall()

        if request.method == "POST":
            product = request.form["product"]
            quantity = request.form["quantity"]
            store_id = request.form["store"]
            category_id = request.form["category"]
            entered_by = request.form["entered_by"]

            cur.execute("""
                INSERT INTO products (product, quantity, store_id, category_id, entered_by)
                VALUES (%s, %s, %s, %s, %s)
            """, (product, quantity, store_id, category_id, entered_by))

            con.commit()
            selected_store = store_id

        if selected_store:
            cur.execute("""
                SELECT p.created_at, s.name, c.name, p.product, p.quantity, p.entered_by
                FROM products p
                JOIN stores s ON p.store_id = s.id
                JOIN categories c ON p.category_id = c.id
                WHERE s.id = %s
                ORDER BY p.created_at DESC
            """, (selected_store,))
            products = cur.fetchall()

    return render_template(
        "index.html",
        stores=stores,
        categories=categories,
        products=products
    )

# ---------------- SUPERVISOR ----------------
@app.route("/supervisor")
def supervisor():
    with db() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT p.created_at, s.name, c.name, p.product, p.quantity, p.entered_by
            FROM products p
            JOIN stores s ON p.store_id = s.id
            JOIN categories c ON p.category_id = c.id
            ORDER BY p.created_at DESC
        """)
        products = cur.fetchall()

    return render_template("supervisor.html", products=products)

# ---------------- STORES ----------------
@app.route("/stores", methods=["GET", "POST"])
def stores():
    with db() as con:
        cur = con.cursor()

        if request.method == "POST":
            name = request.form["name"]
            cur.execute("INSERT INTO stores (name) VALUES (%s)", (name,))
            con.commit()

        cur.execute("SELECT id, name FROM stores ORDER BY name")
        stores = cur.fetchall()

    return render_template("stores.html", stores=stores)

@app.route("/delete_store/<int:id>")
def delete_store(id):
    with db() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM stores WHERE id = %s", (id,))
        con.commit()
    return redirect("/stores")

# ---------------- CATEGORIES ----------------
@app.route("/categories", methods=["GET", "POST"])
def categories():
    with db() as con:
        cur = con.cursor()

        if request.method == "POST":
            name = request.form["name"]
            cur.execute("INSERT INTO categories (name) VALUES (%s)", (name,))
            con.commit()

        cur.execute("SELECT id, name FROM categories ORDER BY name")
        categories = cur.fetchall()

    return render_template("categories.html", categories=categories)

@app.route("/delete_category/<int:id>")
def delete_category(id):
    with db() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM categories WHERE id = %s", (id,))
        con.commit()
    return redirect("/categories")

if __name__ == "__main__":
    app.run()
