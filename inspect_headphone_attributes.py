import json

allowed_values_path = r"C:\Users\USER\.gemini\antigravity\scratch\king_games_product_manager\allowed_attribute_values.json"

with open(allowed_values_path, "r", encoding="utf-8") as f:
    allowed_values = json.load(f)

target_attributes = [
    "חברה",
    "שימוש",
    "אוזניות בלוטוס Bluetooth",
    "כיסוי לאוזניות",
    "מעמד לאוזניות",
    "סוג חיבור שמע"
]

lines = []
for attr in target_attributes:
    vals = allowed_values.get(attr, [])
    lines.append(f"Attribute: {attr}")
    lines.append(f"  Values: {vals}")
    lines.append("-" * 50)

with open(r"C:\Users\USER\.gemini\antigravity\scratch\headphone_attributes_allowed.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("Saved to headphone_attributes_allowed.txt")
