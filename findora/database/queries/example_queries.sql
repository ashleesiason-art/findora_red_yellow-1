USE findora;
SELECT * FROM v_best_sellers;
SELECT * FROM v_low_stock;
SELECT * FROM v_monthly_sales;
SELECT o.id, u.full_name, o.status, o.total FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.id DESC;
SELECT c.name, COUNT(*) products, SUM(p.stock) units FROM products p JOIN categories c ON c.id=p.category_id GROUP BY c.name;
