import os, functools
from decimal import Decimal
from datetime import date
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv
from flask import (Flask, render_template, request, redirect, url_for, session,
                   flash, jsonify, g, abort)
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "findora-dev-secret")

DB = dict(host=os.getenv("DB_HOST", "127.0.0.1"), port=int(os.getenv("DB_PORT", 3307)),
          user=os.getenv("DB_USER", "root"), password=os.getenv("DB_PASSWORD", "findora123"),
          database=os.getenv("DB_NAME", "findora"), charset="utf8mb4")
FREE_SHIPPING_AT = Decimal("1000")
SHIPPING_FEE = Decimal("50")
STATUSES = ["pending", "paid", "shipped", "delivered", "cancelled"]


# ---------- database helpers ----------
def get_db():
    if "db" not in g:
        g.db = pymysql.connect(**DB, cursorclass=DictCursor, autocommit=True)
    return g.db

@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db:
        db.close()

def query(sql, args=(), one=False):
    with get_db().cursor() as c:
        c.execute(sql, args)
        return c.fetchone() if one else c.fetchall()

def execute(sql, args=()):
    with get_db().cursor() as c:
        c.execute(sql, args)
        return c.lastrowid


# ---------- auth ----------
@app.before_request
def load_user():
    g.user = None
    if "uid" in session:
        try:
            g.user = query("SELECT id,full_name,email,phone,address,role FROM users WHERE id=%s", (session["uid"],), one=True)
        except pymysql.MySQLError:
            g.user = None
        if not g.user:
            session.clear()

def login_required(f):
    @functools.wraps(f)
    def w(*a, **k):
        if not g.user:
            flash("Please log in first.", "warn")
            return redirect(url_for("login", next=request.path))
        return f(*a, **k)
    return w

def admin_required(f):
    @functools.wraps(f)
    def w(*a, **k):
        if not g.user or g.user["role"] != "admin":
            abort(403)
        return f(*a, **k)
    return w

@app.context_processor
def inject():
    count = 0
    try:
        if g.user:
            r = query("SELECT COALESCE(SUM(qty),0) n FROM cart_items WHERE user_id=%s", (g.user["id"],), one=True)
            count = int(r["n"])
        cats = query("SELECT * FROM categories ORDER BY id")
    except pymysql.MySQLError:
        cats = []
    return dict(cart_count=count, all_categories=cats, user=g.user, STATUSES=STATUSES)

@app.template_filter("peso")
def peso(v):
    return "₱{:,.2f}".format(Decimal(v or 0)).replace(".00", "")

@app.template_filter("pct_off")
def pct_off(p):
    if p["original_price"] and p["original_price"] > p["price"]:
        return int(round((1 - p["price"] / p["original_price"]) * 100))
    return 0

@app.errorhandler(pymysql.MySQLError)
def db_error(e):
    return render_template("error.html", code=500,
        msg="Database not reachable. Start MySQL (docker compose up -d), run python setup_db.py, then refresh.\n" + str(e)), 500

@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403, msg="You don't have access to this page."), 403

@app.errorhandler(404)
def notfound(_):
    return render_template("error.html", code=404, msg="Page not found."), 404


# ---------- storefront ----------
@app.route("/")
def index():
    flash_sale = query("SELECT * FROM products WHERE is_active=1 AND original_price>price AND stock>0 "
                       "ORDER BY (1-price/original_price) DESC LIMIT 8")
    top = query("SELECT * FROM products WHERE is_active=1 ORDER BY sold DESC LIMIT 6")
    discover = query("SELECT * FROM products WHERE is_active=1 ORDER BY id DESC LIMIT 24")
    return render_template("index.html", flash_sale=flash_sale, top=top, discover=discover)

@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    cat = request.args.get("cat", type=int)
    sort = request.args.get("sort", "relevance")
    sql, args = "SELECT * FROM products WHERE is_active=1", []
    if q:
        sql += " AND (name LIKE %s OR description LIKE %s)"; args += [f"%{q}%"] * 2
    if cat:
        sql += " AND category_id=%s"; args.append(cat)
    order = {"price_asc": "price ASC", "price_desc": "price DESC", "sales": "sold DESC",
             "latest": "id DESC"}.get(sort, "sold DESC, rating DESC")
    products = query(sql + " ORDER BY " + order, args)
    return render_template("search.html", products=products, q=q, cat=cat, sort=sort)

@app.route("/product/<int:pid>")
def product(pid):
    p = query("SELECT p.*, c.name cat_name FROM products p JOIN categories c ON c.id=p.category_id "
              "WHERE p.id=%s AND p.is_active=1", (pid,), one=True)
    if not p:
        abort(404)
    reviews = query("SELECT r.*, u.full_name FROM reviews r JOIN users u ON u.id=r.user_id "
                    "WHERE product_id=%s ORDER BY r.id DESC LIMIT 20", (pid,))
    related = query("SELECT * FROM products WHERE category_id=%s AND id<>%s AND is_active=1 LIMIT 6", (p["category_id"], pid))
    return render_template("product.html", p=p, reviews=reviews, related=related)

@app.route("/product/<int:pid>/review", methods=["POST"])
@login_required
def add_review(pid):
    rating = min(5, max(1, request.form.get("rating", 5, type=int)))
    comment = request.form.get("comment", "").strip()[:500]
    execute("INSERT INTO reviews (product_id,user_id,rating,comment) VALUES (%s,%s,%s,%s)",
            (pid, g.user["id"], rating, comment))
    execute("UPDATE products SET rating=(SELECT ROUND(AVG(rating),1) FROM reviews WHERE product_id=%s) WHERE id=%s", (pid, pid))
    flash("Thanks for your review!", "ok")
    return redirect(url_for("product", pid=pid))


# ---------- accounts ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        f = request.form
        name, email, pw = f.get("full_name", "").strip(), f.get("email", "").strip().lower(), f.get("password", "")
        if not name or "@" not in email or len(pw) < 6:
            flash("Enter your name, a valid email, and a password of 6+ characters.", "err")
        elif query("SELECT id FROM users WHERE email=%s", (email,), one=True):
            flash("That email is already registered.", "err")
        else:
            uid = execute("INSERT INTO users (full_name,email,password_hash,phone) VALUES (%s,%s,%s,%s)",
                          (name, email, generate_password_hash(pw), f.get("phone", "").strip()))
            session["uid"] = uid
            flash("Welcome to FINDORA!", "ok")
            return redirect(url_for("index"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email, pw = request.form.get("email", "").strip().lower(), request.form.get("password", "")
        u = query("SELECT * FROM users WHERE email=%s", (email,), one=True)
        if u and check_password_hash(u["password_hash"], pw):
            session["uid"] = u["id"]
            nxt = request.args.get("next") or ""
            if u["role"] == "admin" and not nxt:
                return redirect(url_for("admin_dashboard"))
            return redirect(nxt if nxt.startswith("/") else url_for("index"))
        flash("Wrong email or password.", "err")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        execute("UPDATE users SET full_name=%s, phone=%s, address=%s WHERE id=%s",
                (request.form["full_name"].strip(), request.form.get("phone", ""), request.form.get("address", ""), g.user["id"]))
        flash("Profile updated.", "ok")
        return redirect(url_for("account"))
    return render_template("account.html")


# ---------- cart ----------
def cart_rows():
    return query("SELECT ci.id, ci.qty, p.id pid, p.name, p.price, p.stock, p.emoji, p.color "
                 "FROM cart_items ci JOIN products p ON p.id=ci.product_id "
                 "WHERE ci.user_id=%s AND p.is_active=1 ORDER BY ci.id DESC", (g.user["id"],))

@app.route("/cart")
@login_required
def cart():
    rows = cart_rows()
    subtotal = sum(r["price"] * r["qty"] for r in rows)
    return render_template("cart.html", rows=rows, subtotal=subtotal)

@app.route("/api/cart/add", methods=["POST"])
def api_cart_add():
    if not g.user:
        return jsonify(ok=False, login=True, msg="Please log in to add items to your cart."), 401
    pid, qty = request.json.get("id"), max(1, int(request.json.get("qty", 1)))
    p = query("SELECT stock FROM products WHERE id=%s AND is_active=1", (pid,), one=True)
    if not p or p["stock"] < 1:
        return jsonify(ok=False, msg="Out of stock."), 400
    execute("INSERT INTO cart_items (user_id,product_id,qty) VALUES (%s,%s,%s) "
            "ON DUPLICATE KEY UPDATE qty=LEAST(qty+VALUES(qty), %s)", (g.user["id"], pid, qty, p["stock"]))
    n = query("SELECT COALESCE(SUM(qty),0) n FROM cart_items WHERE user_id=%s", (g.user["id"],), one=True)["n"]
    return jsonify(ok=True, count=int(n), msg="Added to cart!")

@app.route("/cart/update", methods=["POST"])
@login_required
def cart_update():
    qty = request.form.get("qty", 1, type=int)
    pid = request.form.get("pid", type=int)
    if qty <= 0:
        execute("DELETE FROM cart_items WHERE user_id=%s AND product_id=%s", (g.user["id"], pid))
    else:
        stock = query("SELECT stock FROM products WHERE id=%s", (pid,), one=True)["stock"]
        execute("UPDATE cart_items SET qty=%s WHERE user_id=%s AND product_id=%s", (min(qty, stock), g.user["id"], pid))
    return redirect(url_for("cart"))

@app.route("/cart/remove/<int:pid>", methods=["POST"])
@login_required
def cart_remove(pid):
    execute("DELETE FROM cart_items WHERE user_id=%s AND product_id=%s", (g.user["id"], pid))
    return redirect(url_for("cart"))


# ---------- checkout & orders ----------
def apply_coupon(code, subtotal):
    if not code:
        return None, Decimal(0)
    c = query("SELECT * FROM coupons WHERE code=%s AND active=1 AND expires_at>=%s AND min_spend<=%s",
              (code.upper(), date.today(), subtotal), one=True)
    if not c:
        return None, Decimal(0)
    return c, (subtotal * c["discount_percent"] / 100).quantize(Decimal("0.01"))

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    rows = cart_rows()
    if not rows:
        flash("Your cart is empty.", "warn")
        return redirect(url_for("cart"))
    subtotal = sum(r["price"] * r["qty"] for r in rows)
    code = (request.values.get("coupon") or "").strip()
    coupon, discount = apply_coupon(code, subtotal)
    if code and not coupon:
        flash("Coupon is invalid, expired, or minimum spend not met.", "warn")
    shipping = Decimal(0) if subtotal >= FREE_SHIPPING_AT else SHIPPING_FEE
    total = subtotal - discount + shipping

    if request.method == "POST" and request.form.get("place") == "1":
        f = request.form
        name, phone, addr = f.get("ship_name", "").strip(), f.get("ship_phone", "").strip(), f.get("ship_address", "").strip()
        method = f.get("payment_method", "COD")
        if not (name and phone and addr) or method not in ("COD", "GCash", "Card"):
            flash("Please complete your shipping details.", "err")
        else:
            db = get_db()
            db.autocommit(False)
            try:
                with db.cursor() as c:
                    c.execute("SELECT ci.product_id pid, ci.qty, p.name, p.price, p.stock FROM cart_items ci "
                              "JOIN products p ON p.id=ci.product_id WHERE ci.user_id=%s AND p.is_active=1 FOR UPDATE",
                              (g.user["id"],))
                    items = c.fetchall()
                    for it in items:
                        if it["qty"] > it["stock"]:
                            raise ValueError(f"Sorry, only {it['stock']} left of “{it['name']}”.")
                    sub = sum(i["price"] * i["qty"] for i in items)
                    cp, disc = apply_coupon(code, sub)
                    ship = Decimal(0) if sub >= FREE_SHIPPING_AT else SHIPPING_FEE
                    c.execute("INSERT INTO orders (user_id,status,payment_method,subtotal,shipping_fee,discount,total,"
                              "coupon_code,ship_name,ship_phone,ship_address) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                              (g.user["id"], "paid" if method != "COD" else "pending", method, sub, ship, disc,
                               sub - disc + ship, cp["code"] if cp else None, name, phone, addr))
                    oid = c.lastrowid
                    for it in items:
                        c.execute("INSERT INTO order_items (order_id,product_id,name,price,qty) VALUES (%s,%s,%s,%s,%s)",
                                  (oid, it["pid"], it["name"], it["price"], it["qty"]))
                        c.execute("UPDATE products SET stock=stock-%s, sold=sold+%s WHERE id=%s", (it["qty"], it["qty"], it["pid"]))
                    c.execute("DELETE FROM cart_items WHERE user_id=%s", (g.user["id"],))
                db.commit()
                flash(f"Order #{oid} placed. Thank you for shopping at FINDORA!", "ok")
                return redirect(url_for("orders"))
            except ValueError as e:
                db.rollback(); flash(str(e), "err")
            except Exception:
                db.rollback(); raise
            finally:
                db.autocommit(True)
    return render_template("checkout.html", rows=rows, subtotal=subtotal, discount=discount,
                           shipping=shipping, total=total, coupon=coupon, code=code)

@app.route("/orders")
@login_required
def orders():
    tab = request.args.get("status", "all")
    sql, args = "SELECT * FROM orders WHERE user_id=%s", [g.user["id"]]
    if tab in STATUSES:
        sql += " AND status=%s"; args.append(tab)
    os_ = query(sql + " ORDER BY id DESC", args)
    for o in os_:
        o["items"] = query("SELECT oi.*, p.emoji, p.color FROM order_items oi JOIN products p ON p.id=oi.product_id WHERE order_id=%s", (o["id"],))
    return render_template("orders.html", orders=os_, tab=tab)

def restock(order_id):
    for it in query("SELECT product_id,qty FROM order_items WHERE order_id=%s", (order_id,)):
        execute("UPDATE products SET stock=stock+%s, sold=GREATEST(sold-%s,0) WHERE id=%s", (it["qty"], it["qty"], it["product_id"]))

@app.route("/orders/<int:oid>/cancel", methods=["POST"])
@login_required
def cancel_order(oid):
    o = query("SELECT * FROM orders WHERE id=%s AND user_id=%s", (oid, g.user["id"]), one=True)
    if o and o["status"] in ("pending", "paid"):
        execute("UPDATE orders SET status='cancelled' WHERE id=%s", (oid,))
        restock(oid)
        flash(f"Order #{oid} cancelled.", "ok")
    else:
        flash("This order can no longer be cancelled.", "warn")
    return redirect(url_for("orders"))


# ---------- admin ----------
@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = query("SELECT (SELECT COALESCE(SUM(total),0) FROM orders WHERE status<>'cancelled') revenue,"
                  "(SELECT COUNT(*) FROM orders) orders,(SELECT COUNT(*) FROM users WHERE role='customer') customers,"
                  "(SELECT COUNT(*) FROM products WHERE is_active=1) products", one=True)
    return render_template("admin/dashboard.html", s=stats,
        recent=query("SELECT o.*, u.full_name FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.id DESC LIMIT 6"),
        best=query("SELECT * FROM v_best_sellers LIMIT 5"), low=query("SELECT * FROM v_low_stock LIMIT 6"),
        monthly=query("SELECT * FROM v_monthly_sales ORDER BY month DESC LIMIT 6"))

@app.route("/admin/products")
@admin_required
def admin_products():
    q = request.args.get("q", "").strip()
    rows = query("SELECT p.*, c.name cat_name FROM products p JOIN categories c ON c.id=p.category_id "
                 "WHERE p.name LIKE %s ORDER BY p.id DESC", (f"%{q}%",))
    return render_template("admin/products.html", rows=rows, q=q)

@app.route("/admin/products/new", methods=["GET", "POST"])
@app.route("/admin/products/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
def admin_product_form(pid=None):
    p = query("SELECT * FROM products WHERE id=%s", (pid,), one=True) if pid else None
    if pid and not p:
        abort(404)
    if request.method == "POST":
        f = request.form
        vals = (f["name"].strip(), f.get("description", ""), f["price"], f.get("original_price") or f["price"],
                f.get("stock", 0), f.get("category_id"), f.get("emoji") or "📦", f.get("color") or "#fff3bf",
                1 if f.get("is_active") else 0)
        if pid:
            execute("UPDATE products SET name=%s,description=%s,price=%s,original_price=%s,stock=%s,category_id=%s,"
                    "emoji=%s,color=%s,is_active=%s WHERE id=%s", vals + (pid,))
        else:
            execute("INSERT INTO products (name,description,price,original_price,stock,category_id,emoji,color,is_active) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", vals)
        flash("Product saved.", "ok")
        return redirect(url_for("admin_products"))
    return render_template("admin/product_form.html", p=p)

@app.route("/admin/products/<int:pid>/toggle", methods=["POST"])
@admin_required
def admin_product_toggle(pid):
    execute("UPDATE products SET is_active=1-is_active WHERE id=%s", (pid,))
    return redirect(url_for("admin_products"))

@app.route("/admin/orders")
@admin_required
def admin_orders():
    st = request.args.get("status", "")
    sql, args = "SELECT o.*, u.full_name, u.email FROM orders o JOIN users u ON u.id=o.user_id", []
    if st in STATUSES:
        sql += " WHERE o.status=%s"; args.append(st)
    rows = query(sql + " ORDER BY o.id DESC", args)
    for o in rows:
        o["items"] = query("SELECT name, qty FROM order_items WHERE order_id=%s", (o["id"],))
    return render_template("admin/orders.html", rows=rows, st=st)

@app.route("/admin/orders/<int:oid>/status", methods=["POST"])
@admin_required
def admin_order_status(oid):
    new = request.form.get("status")
    o = query("SELECT status FROM orders WHERE id=%s", (oid,), one=True)
    if o and new in STATUSES and new != o["status"]:
        if new == "cancelled" and o["status"] != "cancelled":
            restock(oid)
        execute("UPDATE orders SET status=%s WHERE id=%s", (new, oid))
        flash(f"Order #{oid} → {new}", "ok")
    return redirect(request.referrer or url_for("admin_orders"))

@app.route("/admin/users")
@admin_required
def admin_users():
    rows = query("SELECT u.*, (SELECT COUNT(*) FROM orders WHERE user_id=u.id) n_orders, "
                 "(SELECT COALESCE(SUM(total),0) FROM orders WHERE user_id=u.id AND status<>'cancelled') spent "
                 "FROM users u ORDER BY u.id DESC")
    return render_template("admin/users.html", rows=rows)


if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))
