import sqlite3

db_path = r"C:\Users\USER\.gemini\antigravity\scratch\king_games_product_manager\products.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT id, name, parent FROM categories WHERE name LIKE '%אוזניות%' OR parent LIKE '%אוזניות%'")
rows = c.fetchall()

with open("headphone_categories.txt", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(f"ID: {r[0]} | Name: {r[1]} | Parent: {r[2]}\n")

conn.close()
print("Done")
