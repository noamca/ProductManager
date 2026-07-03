import json

allowed_values_path = r"C:\Users\USER\.gemini\antigravity\scratch\king_games_product_manager\allowed_attribute_values.json"
mapping_schema_path = r"C:\Users\USER\.gemini\antigravity\scratch\king_games_product_manager\mapping_schema.json"

with open(allowed_values_path, "r", encoding="utf-8") as f:
    allowed_values = json.load(f)

with open(mapping_schema_path, "r", encoding="utf-8") as f:
    mapping_schema = json.load(f)

lines = []

lines.append("Allowed values keys:")
lines.append(str(list(allowed_values.keys())))
lines.append("\n" + "="*80 + "\n")

# Look for brand or specific attributes
for k, v in allowed_values.items():
    if "מותג" in k or "חברה" in k or "brand" in k.lower():
        lines.append(f"Attribute Name: {k}")
        lines.append(f"Values: {v[:50]}")
        lines.append("-" * 40)

# Check brand select options from the website. 
# Wait! Brand in the product form is a standard select element: <select name="brand">.
# Let's check if there is a file that dumped the brand select options!
# Let's see: we had "category_options.json" or "inspect_select_options.py" or "select_options_decoded.json" in king_games_product_manager!
# Yes! Let's search for "select_options_decoded.json" or similar in king_games_product_manager.

with open(r"C:\Users\USER\.gemini\antigravity\scratch\schema_inspection_utf8.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("Schema inspection written to schema_inspection_utf8.txt")
