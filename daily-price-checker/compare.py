import os
import sys
import csv
import io
import shutil
from datetime import datetime

# Configure stdout and stderr to use UTF-8 to prevent encoding errors on Windows console
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Paths
TEMP_DIR = r"C:\Temp"
SOURCE_FILE = os.path.join(TEMP_DIR, "יומי.csv")
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(WORKSPACE_DIR, "data")
REPORTS_DIR = os.path.join(WORKSPACE_DIR, "reports")
YESTERDAY_FILE = os.path.join(DATA_DIR, "yesterday.csv")

def ensure_directories():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

def read_csv(file_path):
    encodings = ['utf-8-sig', 'cp1255', 'utf-8', 'latin-1', 'cp1252']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                content = f.read()
                # Parse using csv.reader
                reader = csv.reader(io.StringIO(content))
                rows = list(reader)
                if rows:
                    return rows, enc
        except (UnicodeDecodeError, PermissionError):
            continue
    raise Exception(f"שגיאה: לא ניתן לקרוא את הקובץ {file_path} עם קידודים נפוצים.")

def parse_price(val):
    # Remove whitespace, currency symbols, commas, and other formatting
    clean = "".join(c for c in val if c.isdigit() or c in ['.', '-'])
    if not clean:
        return None
    try:
        return float(clean)
    except ValueError:
        return None

def load_data(file_path):
    rows, enc = read_csv(file_path)
    if not rows or len(rows) < 2:
        return {}, [], []
    
    headers = [h.strip() for h in rows[0]]
    
    # Try to find 'מזהה' and 'מחיר לצרכן'
    id_idx = None
    price_idx = None
    for idx, h in enumerate(headers):
        if "מזהה" in h:
            id_idx = idx
        if "מחיר לצרכן" in h:
            price_idx = idx
            
    # Fallback to defaults if not found
    if id_idx is None:
        id_idx = 0
    if price_idx is None:
        price_idx = 1 if len(headers) > 1 else 0

    data = {}
    raw_data = {}  # Keep raw values for displaying in report
    for row in rows[1:]:
        if len(row) <= max(id_idx, price_idx):
            continue
        item_id = row[id_idx].strip()
        price_raw = row[price_idx].strip()
        if not item_id:
            continue
            
        # Filter out invalid keys (HTML tags, excessively long strings, etc.)
        if "<" in item_id or ">" in item_id or "{" in item_id or "}" in item_id:
            continue
        if len(item_id) > 30:
            continue
            
        price_val = parse_price(price_raw)
        if price_val is None:
            continue
            
        data[item_id] = price_val
        raw_data[item_id] = price_raw
        
    return data, raw_data, headers

def format_number(val):
    if isinstance(val, float):
        # Format nice float
        if val.is_integer():
            return f"{int(val)}"
        return f"{val:.2f}"
    return str(val)

def get_product_titles():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "king_games_product_manager", "products.db"))
    titles = {}
    if not os.path.exists(db_path):
        return titles
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT mg_id, title FROM products")
        for row in cursor.fetchall():
            titles[str(row[0])] = row[1]
        conn.close()
    except Exception as e:
        print(f"Warning: could not load product titles from DB: {e}")
    return titles

def main():
    ensure_directories()
    
    # Check if today's file exists
    if not os.path.exists(SOURCE_FILE):
        print(f"### ❌ שגיאה: לא נמצא קובץ בנתיב: `{SOURCE_FILE}`")
        print("נא לוודא שהקובץ הועלה לתיקיית `C:\\Temp` בשם `יומי.csv` לפני הפעלת הבדיקה.")
        return

    # Check if yesterday's file exists
    if not os.path.exists(YESTERDAY_FILE):
        # Initial run: just copy the file and notify
        shutil.copy2(SOURCE_FILE, YESTERDAY_FILE)
        print("### ℹ️ הרצה ראשונית")
        print(f"קובץ הנתונים הוגדר כבסיס להשוואה להרצות הבאות. עותק נשמר ב-`data/yesterday.csv`.")
        return

    # Load both files
    try:
        today_data, today_raw, headers_today = load_data(SOURCE_FILE)
        yesterday_data, yesterday_raw, headers_yesterday = load_data(YESTERDAY_FILE)
    except Exception as e:
        print(f"### ❌ שגיאה בטעינת הקבצים:\n{e}")
        return

    # Fetch product titles
    titles = get_product_titles()

    # Compare
    added = []
    removed = []
    changed = []

    # Check for added and changed items
    for item_id, price_today in today_data.items():
        if item_id not in yesterday_data:
            added.append((item_id, today_raw[item_id]))
        else:
            price_yesterday = yesterday_data[item_id]
            if abs(price_today - price_yesterday) > 0.001:
                changed.append((item_id, yesterday_raw[item_id], today_raw[item_id], price_yesterday, price_today))

    # Check for removed items
    for item_id, price_yesterday in yesterday_data.items():
        if item_id not in today_data:
            removed.append((item_id, yesterday_raw[item_id]))

    # Generate Markdown Report
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_lines = []
    report_lines.append(f"# דוח שינוי מחירים - {now_str}")
    report_lines.append("")

    if not added and not removed and not changed:
        report_lines.append("### ✅ לא נמצאו שינויים במחירים או במק\"טים בהשוואה לאתמול.")
    else:
        # Table of Price Changes
        if changed:
            report_lines.append("## 🔄 שינויי מחירים")
            report_lines.append("| מזהה | שם מוצר | מחיר אתמול | מחיר היום | הפרש | שינוי באחוזים |")
            report_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for item_id, old_raw, new_raw, old_val, new_val in sorted(changed):
                diff = new_val - old_val
                pct = (diff / old_val * 100) if old_val != 0 else 0
                sign = "+" if diff > 0 else ""
                title = titles.get(str(item_id), "מוצר לא נמצא במערכת")
                report_lines.append(f"| `{item_id}` | {title} | {old_raw} | {new_raw} | {sign}{format_number(diff)} | {sign}{pct:.1f}% |")
            report_lines.append("")

        # Table of Added Items
        if added:
            report_lines.append("## ➕ מק\"טים חדשים שנוספו")
            report_lines.append("| מזהה | שם מוצר | מחיר לצרכן |")
            report_lines.append("| :--- | :--- | :--- |")
            for item_id, price in sorted(added):
                title = titles.get(str(item_id), "מוצר חדש / לא מופיע במערכת")
                report_lines.append(f"| `{item_id}` | {title} | {price} |")
            report_lines.append("")

        # Table of Removed Items
        if removed:
            report_lines.append("## ➖ מק\"טים שהוסרו")
            report_lines.append("| מזהה | שם מוצר | מחיר אחרון |")
            report_lines.append("| :--- | :--- | :--- |")
            for item_id, price in sorted(removed):
                title = titles.get(str(item_id), "מוצר לא נמצא במערכת")
                report_lines.append(f"| `{item_id}` | {title} | {price} |")
            report_lines.append("")

    report_content = "\n".join(report_lines)
    
    # Print the report to stdout (which agent reads)
    print(report_content)

    # Save report to history
    report_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path = os.path.join(REPORTS_DIR, report_filename)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    # Archive today's file as yesterday's file for the next run
    shutil.copy2(SOURCE_FILE, YESTERDAY_FILE)


if __name__ == "__main__":
    main()
