import json

mapping_schema_path = r"C:\Users\USER\.gemini\antigravity\scratch\king_games_product_manager\mapping_schema.json"

with open(mapping_schema_path, "r", encoding="utf-8") as f:
    mapping_schema = json.load(f)

attributes = mapping_schema.get("attributes", [])

def get_attrs_for_category(cat_id):
    cat_attrs = []
    for attr in attributes:
        for mc in attr.get("matched_categories", []):
            if mc.get("id") == cat_id:
                cat_attrs.append(attr)
                break
    return cat_attrs

lines = []

lines.append("Attributes for Category 281 (אוזניות אלחוטיות):")
attrs_281 = get_attrs_for_category("281")
for a in sorted(attrs_281, key=lambda x: x['index']):
    lines.append(f"  Index {a['index']} | Col {a['column']} | Name: {a['name']}")

lines.append("\n" + "="*80 + "\n")

lines.append("Attributes for Category 282 (אוזניות חוטיות):")
attrs_282 = get_attrs_for_category("282")
for a in sorted(attrs_282, key=lambda x: x['index']):
    lines.append(f"  Index {a['index']} | Col {a['column']} | Name: {a['name']}")

with open(r"C:\Users\USER\.gemini\antigravity\scratch\category_attributes_utf8.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("Category attributes decoded successfully")
