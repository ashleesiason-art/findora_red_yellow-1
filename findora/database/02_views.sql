USE findora;
CREATE OR REPLACE VIEW v_best_sellers AS
  SELECT id, name, price, sold FROM products WHERE is_active = 1 ORDER BY sold DESC LIMIT 10;
CREATE OR REPLACE VIEW v_low_stock AS
  SELECT id, name, stock FROM products WHERE is_active = 1 AND stock <= 10 ORDER BY stock;
CREATE OR REPLACE VIEW v_monthly_sales AS
  SELECT DATE_FORMAT(created_at,'%Y-%m') AS month, COUNT(*) AS orders, SUM(total) AS revenue
  FROM orders WHERE status <> 'cancelled' GROUP BY month ORDER BY month;
