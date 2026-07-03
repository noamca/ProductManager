import sqlite3

db_path = r"C:\Users\USER\.gemini\antigravity\scratch\king_games_product_manager\products.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("""
    SELECT mg_id, title, category_code, brand_code, sap_sku, supplier1_name, supplier1_sku, supplier1_price, supplier1_stock 
    FROM products 
    WHERE CAST(mg_id AS INTEGER) >= 35107 AND CAST(mg_id AS INTEGER) <= 35123
""")
products = c.fetchall()

lines = []
for p in products:
    mg_id, title, cat, brand, sku, s_name, s_sku, s_price, s_stock = p
    lines.append(f"ID: {mg_id}")
    lines.append(f"  Title: {title}")
    lines.append(f"  SAP SKU: {sku}")
    lines.append(f"  Category: {cat}")
    lines.append(f"  Brand: {brand}")
    lines.append(f"  Supplier: {s_name} | SKU: {s_sku} | Cost: {s_price} | Stock: {s_stock}")
    lines.append("-" * 60)

with open(r"C:\Users\USER\.gemini\antigravity\scratch\products_list_utf8.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

conn.close()
print("Dumped successfully to products_list_utf8.txt")
