"""One-time database setup.  Run:  python setup_db.py
Runs database/*.sql in order, then creates the demo admin + customer accounts
(with properly hashed passwords)."""
import os, glob, sys
import pymysql
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()
cfg = dict(host=os.getenv("DB_HOST", "127.0.0.1"), port=int(os.getenv("DB_PORT", 3307)),
           user=os.getenv("DB_USER", "root"), password=os.getenv("DB_PASSWORD", "findora123"),
           charset="utf8mb4", autocommit=True)

def split_sql(text):
    out, buf = [], []
    for line in text.splitlines():
        if line.strip().startswith("--"):
            continue
        buf.append(line)
        if line.rstrip().endswith(";"):
            out.append("\n".join(buf)); buf = []
    return [s for s in out if s.strip()]

try:
    conn = pymysql.connect(**cfg)
except Exception as e:
    sys.exit(f"\n[!] Cannot connect to MySQL at {cfg['host']}:{cfg['port']}  ->  {e}\n"
             "    * Using Docker?  run:  docker compose up -d   (wait ~20s) then retry\n"
             "    * Using local MySQL?  edit DB_PORT/DB_PASSWORD in the .env file\n")

with conn.cursor() as c:
    for f in sorted(glob.glob(os.path.join("database", "0*.sql"))):
        print("running", f)
        for stmt in split_sql(open(f, encoding="utf-8").read()):
            c.execute(stmt)
    c.execute("USE findora")
    for name, email, pw, role in [("FINDORA Admin", "admin@findora.ph", "admin123", "admin"),
                                  ("Juan Dela Cruz", "user@findora.ph", "user123", "customer")]:
        c.execute("SELECT id FROM users WHERE email=%s", (email,))
        if not c.fetchone():
            c.execute("INSERT INTO users (full_name,email,password_hash,role,phone,address) VALUES (%s,%s,%s,%s,%s,%s)",
                      (name, email, generate_password_hash(pw), role, "09171234567", "123 Sample St, Quezon City"))
            print("created", role, email, "/", pw)
print("\nDone. Start the site with:  python app/app.py   then open http://127.0.0.1:5000")
