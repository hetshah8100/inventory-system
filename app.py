from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# ---------- DATABASE ----------
def db():
    return sqlite3.connect("inventory.db")

# ---------- SHOPKEEPER ----------
@app.route("/", methods=["GET", "POST"])
def add_stock():
    con = db()

    if request.method == "POST":
        d = request.form
        con.execute("""
            INSERT INTO inventory
            (date, store, product, category, quantity, entered_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            d["date"],
            d["store"],
            d["product"],
            d["category"],
            d["quantity"],
            d["entered_by"]
        ))
        con.commit()

    stores = con.execute("SELECT name FROM stores ORDER BY name").fetchall()
    categories = con.execute("SELECT name FROM categories ORDER BY name").fetchall()
    con.close()

    return render_template("add.html", stores=stores, categories=categories)

# ---------- SUPERVISOR (WITH FILTER) ----------
@app.route("/supervisor")
def supervisor():
    selected_category = request.args.get("category", "ALL")
    con = db()

    categories = con.execute(
        "SELECT name FROM categories ORDER BY name"
    ).fetchall()

    if selected_category == "ALL":
        rows = con.execute("""
            SELECT id, date, store, product, category, quantity, entered_by
            FROM inventory
            ORDER BY category, product, store
        """).fetchall()
    else:
        rows = con.execute("""
            SELECT id, date, store, product, category, quantity, entered_by
            FROM inventory
            WHERE category=?
            ORDER BY product, store
        """, (selected_category,)).fetchall()

    con.close()

    return render_template(
        "view.html",
        rows=rows,
        categories=categories,
        selected_category=selected_category
    )

# ---------- EDIT ITEM ----------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    con = db()

    if request.method == "POST":
        d = request.form
        con.execute("""
            UPDATE inventory
            SET date=?, store=?, product=?, category=?, quantity=?, entered_by=?
            WHERE id=?
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
        con.close()
        return redirect("/supervisor")

    row = con.execute("SELECT * FROM inventory WHERE id=?", (id,)).fetchone()
    stores = con.execute("SELECT name FROM stores ORDER BY name").fetchall()
    categories = con.execute("SELECT name FROM categories ORDER BY name").fetchall()
    con.close()

    return render_template(
        "edit.html",
        row=row,
        stores=stores,
        categories=categories
    )

# ---------- DELETE SINGLE ITEM ----------
@app.route("/delete/<int:id>")
def delete(id):
    con = db()
    con.execute("DELETE FROM inventory WHERE id=?", (id,))
    con.commit()
    con.close()
    return redirect("/supervisor")

# ---------- CLEAR ALL INVENTORY ----------
@app.route("/clear_inventory")
def clear_inventory():
    con = db()
    con.execute("DELETE FROM inventory")
    con.commit()
    con.close()
    return redirect("/supervisor")

# ---------- MANAGE STORES & CATEGORIES ----------
@app.route("/stores", methods=["GET", "POST"])
def manage_admin():
    con = db()

    if request.method == "POST" and request.form.get("type") == "store":
        con.execute(
            "INSERT OR IGNORE INTO stores (name) VALUES (?)",
            (request.form["name"],)
        )
        con.commit()

    if request.method == "POST" and request.form.get("type") == "category":
        con.execute(
            "INSERT OR IGNORE INTO categories (name) VALUES (?)",
            (request.form["name"],)
        )
        con.commit()

    stores = con.execute("SELECT * FROM stores ORDER BY name").fetchall()
    categories = con.execute("SELECT * FROM categories ORDER BY name").fetchall()
    con.close()

    return render_template(
        "stores.html",
        stores=stores,
        categories=categories
    )

# ---------- DELETE STORE ----------
@app.route("/delete_store/<int:id>")
def delete_store(id):
    con = db()
    store = con.execute("SELECT name FROM stores WHERE id=?", (id,)).fetchone()

    used = con.execute(
        "SELECT 1 FROM inventory WHERE store=? LIMIT 1",
        (store[0],)
    ).fetchone()

    if used:
        con.close()
        return "Cannot delete store. Store is used.", 400

    con.execute("DELETE FROM stores WHERE id=?", (id,))
    con.commit()
    con.close()
    return redirect("/stores")

# ---------- DELETE CATEGORY ----------
@app.route("/delete_category/<int:id>")
def delete_category(id):
    con = db()
    cat = con.execute("SELECT name FROM categories WHERE id=?", (id,)).fetchone()

    used = con.execute(
        "SELECT 1 FROM inventory WHERE category=? LIMIT 1",
        (cat[0],)
    ).fetchone()

    if used:
        con.close()
        return "Cannot delete category. Category is used.", 400

    con.execute("DELETE FROM categories WHERE id=?", (id,))
    con.commit()
    con.close()
    return redirect("/stores")

# ---------- RUN FLASK (THIS WAS THE CRITICAL FIX) ----------
if __name__ == "__main__":
    print("FLASK INVENTORY SYSTEM STARTING")
    app.run(host="0.0.0.0", port=5000, debug=False)
