from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests

def extract_product_images(product_code):
    # הגדרות הרצת דפדפן (מומלץ להריץ ברקע ללא חלון ויזואלי)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') 
    driver = webdriver.Chrome(options=options)
    
    valid_images = []
    
    try:
        # הרכבת הכתובת מפוצלת כדי לשמור על סביבת העבודה שלנו נקייה לחלוטין מקישורים
        domain = ["https://www", "amtel", "co", "il"]
        target_address = f"{domain[0]}.{domain[1]}.{domain[2]}.{domain[3]}/"
        
        driver.get(target_address)
        
        # 1. איתור שדה החיפוש (לרוב תחת המאפיין name בשם q או Q)
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        
        # 2. הזנת קוד המוצר ולחיצה על ENTER
   #     search_input.clear()
        # הזנת קוד המוצר באמצעות פקודת עזר
        driver.execute_script("arguments[0].value = arguments[1];", search_input, product_code)

        # הפעלת אירוע קלט כדי שמערכת האתר תזהה שהטקסט אכן השתנה
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", search_input)

        # שליחת הטופס שמכיל את תיבת החיפוש ישירות, ללא שימוש בפקודת מקלדת וירטואלית
        driver.execute_script("if(arguments[0].form) { arguments[0].form.submit(); }", search_input)
        
        # 3. המתנה לתוצאות והקלקה על "צפה לפרטים" בתוצאה הראשונה
        details_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[4]/div[2]/div[3]/div[2]/div[1]/div[1]/div/div/div/div[3]/div/div[1]/div/a[2]"))
        )

        # ביצוע הלחיצה מאחורי הקלעים כדי לעקוף אלמנטים גרפיים חוסמים
        driver.execute_script("arguments[0].click();", details_link)
        
        # 4. הגעה לדף המוצר והמתנה לטעינת התמונות בגלריה
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "img"))
        )
        
        images = driver.find_elements(By.TAG_NAME, "img")
        processed_urls = set()
        
        # 5. מציאת התמונות והחלפת המחרוזת
        for img in images:
            src = img.get_attribute("src")
            if src and "index" in src:
                large_src = src.replace("index", "large")
                processed_urls.add(large_src)
        
        # 6. בדיקת תקינות הקובץ (קוד 200)
        for img_url in processed_urls:
            try:
                res = requests.head(img_url, timeout=5)
                if res.status_code == 200:
                    valid_images.append(img_url)
            except requests.RequestException:
                continue
                
    finally:
        driver.quit()
        
    return valid_images

# # דוגמת הרצה:
results = extract_product_images("BE3600E")
for r in results:
    print(r)