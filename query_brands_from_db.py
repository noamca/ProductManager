import sqlite3

db_path = r"C:\Users\USER\.gemini\antigravity\scratch\king_games_product_manager\products.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("""
    SELECT brand_code, COUNT(*), group_concat(title, ' | ')
    FROM (
        SELECT brand_code, title 
        FROM products 
        WHERE brand_code IS NOT NULL AND brand_code != '0' AND brand_code != ''
        LIMIT 1000
    )
    GROUP BY brand_code
""")
rows = c.fetchall()

lines = []
for r in rows:
    # Get first 3 product titles as examples
    titles = r[2].split(' | ')[:5]
    lines.append(f"Brand Code: {r[0]} | Count in sample: {r[1]}")
    lines.append(f"  Sample Products: {', '.join(titles)}")
    lines.append("-" * 80)

with open(r"C:\Users\USER\.gemini\antigravity\scratch\db_brands_sample.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

conn.close()
print("Done")
