USE findora;
INSERT IGNORE INTO categories (id,name,icon) VALUES
 (1,'Electronics','📱'),(2,'Fashion','👕'),(3,'Home & Living','🏠'),(4,'Beauty','💄'),
 (5,'Groceries','🛒'),(6,'Toys & Kids','🧸'),(7,'Sports','⚽'),(8,'Books','📚');

INSERT INTO products (id,category_id,name,description,price,original_price,stock,sold,rating,emoji,color) VALUES
 (1,1,'Apple AirPods Pro (2nd Gen)','Active noise cancellation, MagSafe charging case.',11990,14490,60,1240,4.8,'🎧','#ffe3e3'),
 (2,1,'Samsung Galaxy A16 5G 128GB','Large display, 5G, 5000mAh battery.',11990,13990,25,310,4.7,'📱','#fff3bf'),
 (3,1,'Anker PowerCore 20,000mAh Power Bank','Dual-output fast charging power bank.',2495,3295,80,980,4.6,'🔋','#ffe3e3'),
 (4,1,'Xiaomi Redmi Watch 5 Active','Heart-rate and sleep tracking, long battery life.',2299,2999,40,670,4.5,'⌚','#fff3bf'),
 (5,2,'Uniqlo U Crew Neck T-Shirt','Cotton crew neck tee, relaxed everyday fit.',590,790,200,3500,4.7,'👕','#ffe3e3'),
 (6,2,'Levi''s 511 Slim Fit Jeans','Slim-fit stretch denim jeans.',3299,4599,90,820,4.4,'👖','#fff3bf'),
 (7,2,'Converse Chuck Taylor All Star Low','Classic low-top canvas sneakers.',3295,3995,70,1500,4.6,'👟','#ffe3e3'),
 (8,2,'Charles & Keith Mini Crossbody Bag','Compact crossbody bag with adjustable strap.',2990,3990,45,430,4.5,'👜','#fff3bf'),
 (9,3,'Lock & Lock Ceramic Mug Set (4 pcs)','Set of four ceramic mugs.',899,1299,100,760,4.7,'☕','#ffe3e3'),
 (10,3,'Philips LED Desk Lamp (USB)','USB-powered LED lamp for study and work.',1299,1799,55,540,4.6,'💡','#fff3bf'),
 (11,3,'Uratex Memory Foam Pillow','Contoured memory foam pillow.',799,1199,65,910,4.8,'🛏️','#ffe3e3'),
 (12,3,'Tefal Non-stick Frying Pan 28cm','Non-stick coating, even heat distribution.',1499,2199,85,640,4.5,'🍳','#fff3bf'),
 (13,4,'The Ordinary Hyaluronic Acid 2% + B5 30ml','Hydrating serum with hyaluronic acid and vitamin B5.',790,990,120,2100,4.8,'🧴','#ffe3e3'),
 (14,4,'Maybelline Super Stay Matte Ink Lipstick','Long-wear liquid matte lipstick.',449,599,150,1750,4.6,'💄','#fff3bf'),
 (15,4,'Biore UV Aqua Rich Watery Essence SPF50+ 50g','Lightweight daily sunscreen.',399,499,130,2600,4.9,'🧴','#ffe3e3'),
 (16,5,'Lavazza Qualita Rossa Coffee Beans 1kg','Medium roast whole coffee beans.',1299,1599,75,1100,4.8,'☕','#fff3bf'),
 (17,5,'Kirkland Signature Mixed Nuts 1.13kg','Roasted mixed nuts value pack.',1450,1799,60,720,4.5,'🥜','#ffe3e3'),
 (18,5,'Lucky Me! Pancit Canton Original (Box of 24)','Instant pancit canton, original flavor.',360,432,200,3900,4.7,'🍜','#fff3bf'),
 (19,6,'LEGO Classic Large Creative Brick Box 10698','790 pieces for open-ended building.',3995,4495,50,480,4.8,'🧱','#ffe3e3'),
 (20,6,'Sanrio Hello Kitty Plush Toy 40cm','Soft plush toy.',899,1299,90,1320,4.9,'🧸','#fff3bf'),
 (21,7,'Decathlon Domyos Yoga Mat 8mm','Cushioned non-slip yoga mat.',699,999,100,850,4.6,'🧘','#ffe3e3'),
 (22,7,'Decathlon Cast Iron Dumbbell Set 2 x 10kg','Pair of 10kg dumbbells.',2499,3199,30,260,4.5,'🏋️','#fff3bf'),
 (23,8,'Atomic Habits by James Clear (Paperback)','Tiny changes, remarkable results.',749,899,70,1900,4.9,'📘','#ffe3e3'),
 (24,8,'Canson XL Sketch Pad A4 (60 sheets)','Heavyweight paper for sketching.',599,799,110,560,4.7,'📓','#fff3bf')
ON DUPLICATE KEY UPDATE name=VALUES(name),description=VALUES(description),price=VALUES(price),original_price=VALUES(original_price),emoji=VALUES(emoji),color=VALUES(color);

-- Sample coupons (expire 2026-12-31 -> change if needed)
INSERT IGNORE INTO coupons (code,discount_percent,min_spend,expires_at,active) VALUES
 ('WELCOME10',10,500,'2027-12-31',1),
 ('FINDORA20',20,2000,'2027-12-31',1);
