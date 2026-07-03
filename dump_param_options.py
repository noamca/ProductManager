from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import json

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

driver = webdriver.Chrome(options=chrome_options)

try:
    print("Navigating to product edit page to inspect parameters...")
    driver.get("https://www.king-games.co.il/apanel/products&edit=35105")
    
    # Wait for the page/form to load
    import time
    time.sleep(3)
    
    params = {}
    
    # We want to scan all selects with name starting with param_
    selects = driver.find_elements(By.XPATH, "//select[starts-with(@name, 'param_')]")
    print(f"Found {len(selects)} parameter select elements.")
    
    for sel in selects:
        name = sel.get_attribute("name")
        # Get label from preceding td
        label_text = driver.execute_script("""
            var el = arguments[0];
            var td = el.closest('td');
            if (td && td.previousElementSibling) {
                return td.previousElementSibling.innerText || td.previousElementSibling.textContent;
            }
            return '';
        """, sel)
        
        # Get options
        options = sel.find_elements(By.TAG_NAME, "option")
        opts_list = []
        for opt in options:
            val = opt.get_attribute("value")
            text = opt.text.strip()
            if val or text:
                opts_list.append({"value": val, "text": text})
                
        params[name] = {
            "label": label_text.strip(),
            "options": opts_list
        }
        
    with open("all_params_options.json", "w", encoding="utf-8") as f:
        json.dump(params, f, indent=2, ensure_ascii=False)
        
    print("Successfully dumped all parameters to all_params_options.json")
except Exception as e:
    print(f"Error: {e}")
finally:
    driver.close()
