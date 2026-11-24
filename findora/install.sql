-- Run from the project root:
--   mysql -u root -p < install.sql
-- (SOURCE paths are relative to the current directory)
-- Or simply run:  python setup_db.py   (no mysql CLI needed)
SOURCE database/01_schema.sql;
SOURCE database/02_views.sql;
SOURCE database/03_seed_data.sql;
