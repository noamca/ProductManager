from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import json
import time

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

driver = webdriver.Chrome(options=chrome_options)

try:
    print("Navigating to product edit page...")
    driver.get("https://www.king-games.co.il/apanel/products&edit=35105")
    time.sleep(3)
    
    print("Extracting brand options...")
    brand_sel = driver.find_element(By.NAME, "brand")
    options = brand_sel.find_elements(By.TAG_NAME, "option")
    
    brands = []
    for opt in options:
        val = opt.get_attribute("value")
        text = opt.text.strip()
        brands.append({"value": val, "text": text})
        
    with open("all_brands.json", "w", encoding="utf-8") as f:
        json.dump(brands, f, indent=2, ensure_ascii=False)
        
    print(f"Extracted {len(brands)} brands successfully to all_brands.json")
except Exception as e:
    print(f"Error: {e}")
# Do not call close or quit to keep Chrome open and active
