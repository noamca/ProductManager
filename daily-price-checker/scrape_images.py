import os
import sys
import time
import base64
from io import BytesIO
from PIL import Image
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

# Configure stdout and stderr to use UTF-8 to prevent encoding errors on Windows console
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = r"C:\Temp"
PART_NUMBERS_FILE = os.path.join(WORKSPACE_DIR, "part_numbers.txt")

def ensure_directories():
    os.makedirs(IMAGES_DIR, exist_ok=True)

def load_part_numbers():
    part_numbers = []
    if os.path.exists(PART_NUMBERS_FILE):
        with open(PART_NUMBERS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                val = line.strip()
                if val and not val.startswith('#'):
                    part_numbers.append(val)
    return part_numbers

def download_image_via_js(driver, url, output_path):
    """
    Downloads an image by executing an asynchronous XMLHttpRequest inside Chrome.
    This bypasses Cloudflare blocks (403 Forbidden) since it uses the browser's active session.
    """
    js_script = """
    var callback = arguments[arguments.length - 1];
    var xhr = new XMLHttpRequest();
    xhr.onload = function() {
        var reader = new FileReader();
        reader.onloadend = function() {
            callback(reader.result);
        }
        reader.readAsDataURL(xhr.response);
    };
    xhr.onerror = function() {
        callback("ERROR");
    };
    xhr.open('GET', arguments[0]);
    xhr.responseType = 'blob';
    xhr.send();
    """
    try:
        # Set script timeout just in case
        driver.set_script_timeout(20)
        data_url = driver.execute_async_script(js_script, url)
        
        if not data_url or data_url == "ERROR" or "," not in data_url:
            print(f"  ❌ שגיאה בקבלת נתוני התמונה מהדפדפן עבור {url}")
            return False
            
        header, encoded = data_url.split(",", 1)
        image_bytes = base64.b64decode(encoded)
        
        # Open with Pillow and convert/save as WEBP
        img = Image.open(BytesIO(image_bytes))
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            img = img.convert('RGBA')
        else:
            img = img.convert('RGB')
            
        img.save(output_path, 'WEBP')
        return True
    except Exception as e:
        print(f"  ❌ שגיאה בהורדת/המרת התמונה {url} דרך הדפדפן: {e}")
    return False

def scrape_product_images(driver, part_number):
    url = f"https://www.benda.co.il/product/{part_number}/"
    print(f"\n🔍 סורק מק\"ט: {part_number} ...")
    print(f"🔗 כתובת: {url}")
    
    try:
        driver.get(url)
        
        # Dynamic wait for Cloudflare bypass (up to 15 seconds)
        bypassed = False
        for i in range(15):
            title = driver.title
            if title and "רק רגע" not in title and "ביצוע אימות אבטחה" not in title:
                bypassed = True
                break
            time.sleep(1)
            
        title = driver.title
        print(f"  📄 כותרת העמוד: {title}")
        
        # Check if 404
        if "404" in title or "לא נמצא" in title or "Page not found" in title:
            print(f"  ❌ שגיאה: עמוד המוצר עבור מק\"ט {part_number} לא נמצא (404).")
            return []

        # Find all images
        imgs = driver.find_elements(By.TAG_FOUNDRY if hasattr(By, 'TAG_FOUNDRY') else By.TAG_NAME, "img")
        print(f"  Found {len(imgs)} raw image tags on page.")
        
        product_image_urls = set()
        
        for img in imgs:
            try:
                src = img.get_attribute("src")
                if not src:
                    continue
                    
                img_class = img.get_attribute("class") or ""
                
                # Filter heuristics:
                # 1. Image URL contains the part number
                # 2. Or image class contains WooCommerce/WordPress product elements
                filename = os.path.basename(src).lower()
                clean_part = part_number.lower()
                
                is_product_img = False
                if clean_part in filename or clean_part.replace("-", "") in filename:
                    is_product_img = True
                elif "wp-post-image" in img_class or "wp-post-gallery" in img_class:
                    is_product_img = True
                    
                # Skip layout assets like logos, banners, icons
                if "logo" in filename or "cropped" in filename or "favicon" in filename or "banner" in filename:
                    is_product_img = False
                    
                if is_product_img:
                    product_image_urls.add(src)
            except Exception as e:
                continue
                
        if not product_image_urls:
            print("  ⚠️ לא נמצאו תמונות מוצר מתאימות.")
            return []
            
        print(f"  ✨ נמצאו {len(product_image_urls)} תמונות ייחודיות להורדה.")
        
        # Create output directory for this part number
        product_dir = os.path.join(IMAGES_DIR, part_number)
        os.makedirs(product_dir, exist_ok=True)
        
        downloaded_files = []
        for idx, img_url in enumerate(sorted(product_image_urls), 1):
            # Form clean output filename
            out_filename = f"{idx}.webp"
            out_path = os.path.join(product_dir, out_filename)
            
            print(f"  📥 מוריד תמונה {idx} דרך הדפדפן: {img_url} ...")
            if download_image_via_js(driver, img_url, out_path):
                downloaded_files.append(out_path)
                print(f"    ✅ נשמר בהצלחה: {out_filename}")
                
        return downloaded_files
        
    except Exception as e:
        print(f"  ❌ שגיאה במהלך הסריקה של מק\"ט {part_number}: {e}")
        return []

def main():
    ensure_directories()
    
    # Check arguments
    part_numbers = []
    if len(sys.argv) > 1:
        part_numbers = sys.argv[1:]
    else:
        part_numbers = load_part_numbers()
        
    if not part_numbers:
        print("❌ שגיאה: לא סופקו מק\"טים להורדה.")
        print(f"אנא ספק מק\"טים כארגומנטים בשורת הפקודה, או רשום אותם בקובץ: {PART_NUMBERS_FILE}")
        return
        
    print(f"🚀 מתחיל תהליך הורדת תמונות עבור {len(part_numbers)} מק\"טים...")
    
    # Initialize undetected-chromedriver using standard configuration
    try:
        driver = uc.Chrome(version_main=149)
    except Exception as e:
        print(f"❌ שגיאה באתחול הדפדפן (Chrome): {e}")
        return
        
    total_downloaded = 0
    try:
        for part_number in part_numbers:
            downloaded = scrape_product_images(driver, part_number)
            total_downloaded += len(downloaded)
            
        print(f"\n🎉 התהליך הסתיים! סה\"ך הורדו בהצלחה {total_downloaded} תמונות.")
        print(f"התמונות נשמרו בתיקייה: {IMAGES_DIR}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
