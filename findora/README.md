# FINDORA — Online Shopping System (MySQL + Python Flask + HTML/CSS/JS)

Shopee-style storefront with user accounts, cart, checkout, orders, reviews and an Admin panel.
Currency PHP · free shipping at ₱1,000+ · temporary logo: `app/static/img/logo.svg`.

## Folder structure
```
findora/
├── app/
│   ├── app.py                 # Flask backend (routes, cart, checkout, admin)
│   ├── templates/             # HTML pages (+ admin/)
│   └── static/ css/ js/ img/  # style.css, main.js, logo.svg
├── database/                  # 01_schema, 02_views, 03_seed_data, queries/
├── setup_db.py                # runs the SQL files + creates demo accounts
├── docker-compose.yml         # MySQL 8 on port 3307
├── install.sql                # alternative: mysql -u root -p < install.sql
├── requirements.txt  .env  .vscode/
```

## Run it (VS Code terminal, internet needed only for the first install)
```bash
# 1. database (Docker)                      # or use your own MySQL and edit .env
docker compose up -d                        # wait ~20 seconds

# 2. python packages
python -m venv .venv
.venv\Scripts\activate                      # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 3. create tables, sample products, demo accounts
python setup_db.py

# 4. start website
python app/app.py                           # open http://127.0.0.1:5000
```
Or press **F5** in VS Code and pick *FINDORA: Run website*.

## Demo accounts
| Role | Email | Password |
|---|---|---|
| Admin | admin@findora.ph | admin123 |
| Customer | user@findora.ph | user123 |

## Features
- **Storefront:** hero carousel, categories, flash-sale countdown, top products, search, sort, product page, reviews
- **Customer:** register/login, cart (AJAX add), checkout with coupons (`WELCOME10`, `FINDORA20`), COD/GCash/Card (demo), order tabs, cancel order, profile
- **Admin (`/admin`):** dashboard, add/edit/hide products, update order status, customers list
- Stock is deducted in a database transaction at checkout and restored on cancel.

## Notes
- Theme: red primary (`--o` in `app/static/css/style.css`) with yellow accents (`--y`).
- Ad banners are editable SVGs in `app/static/img/ads/` (hero1-4, side1-2, promo1-3). Prices shown in the ads match `database/03_seed_data.sql`; update both together.
- Product names/prices are real-brand examples with approximate PHP prices. To load them into an existing database, just run `python setup_db.py` again (it updates the products by id).
- Product thumbnails are still emoji + colour placeholders. Replace the `.thumb` blocks with `<img>` when you have photos.
- Payments are simulated; add a real gateway before going live. Change `SECRET_KEY` in `.env`.
- If your MySQL uses another port/password, edit `.env`.
