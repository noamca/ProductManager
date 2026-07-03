import json
import os

all_brands_path = r"C:\Users\USER\.gemini\antigravity\scratch\all_brands.json"

if os.path.exists(all_brands_path):
    with open(all_brands_path, "r", encoding="utf-8") as f:
        brands = json.load(f)
    
    target_names = ["razer", "corsair", "turtle beach", "miracase", "scorpius", "scorpio"]
    for t in target_names:
        found = False
        for b in brands:
            if t in b["text"].lower():
                print(f"Match for '{t}': Value={b['value']} | Text='{b['text']}'")
                found = True
        if not found:
            print(f"No match for '{t}'")
else:
    print("all_brands.json does not exist!")
