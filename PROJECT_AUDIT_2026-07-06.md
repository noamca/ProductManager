# דוח בדיקת פרויקט KINGGAMES (2026-07-06)

## תקציר מנהלים
- המערכת הפעילה נמצאת בעיקר בתיקיה king_games_product_manager.
- יש תזמונים פעילים בשרת (daily export + automated processes scheduler).
- שרשרת האוטומציה של מור-לוי (login -> checkbox -> download) לא קיימת בפועל כרגע בגלל קבצי auto_run_* חסרים.
- שלבי עיבוד קובץ ועדכון DB/ייבוא ל-MG קיימים, אך תלויים בכך שקובץ ספק כבר התקבל.
- התיקיה king_games_product_manager_remote.git היא bare repository (ארכיון/remote), לא סביבת קוד רצה.

## מה יש בכל ספריה מרכזית

### king_games_product_manager
- שרת מקומי: server.py
- UI: index.html, app.js, style.css
- DB: products.db
- תהליכי ייצור עיקריים: update_products_batch_2.py, run_price_check.py, mg_import_runner.py, scrape_cms_parameters.py
- הרבה סקריפטי debug/inspect/test חד-פעמיים.

### king_games_product_manager_remote.git
- מאגר Git bare (HEAD, objects, refs, hooks).
- לא מיועד להרצת קוד ישירה, אלא לשמירת היסטוריית remote.

### daily-price-checker
- השוואת מחירים ודוחות: compare.py
- תמונות: scrape_images.py
- נתונים/פלט: data, reports, images

### chrome-* profiles
- פרופילי Chrome להרצות Selenium/remote debugging.
- משמשים מצב דפדפן שונה לפי תרחיש (headless/watch/morlevi/debug).

### scratch
- סביבת ניסוי/עותקים/ארטיפקטים.
- לא נראה כחלק core production.

## סקריפטים ברמת השורש (root) ומה כל אחד עושה
- dump_all_brands.py: חילוץ רשימת מותגים מ-CMS דרך Chrome Debug.
- dump_param_options.py: חילוץ אפשרויות select של פרמטרים (param_*) מעריכת מוצר.
- extract_brands.py: ניתוח transcript והפקת דוח brands.
- get_category_names.py: שליפת שמות קטגוריות מסוימות מ-SQLite חיצוני.
- get_headphone_categories.py: שליפת קטגוריות אוזניות מה-DB.
- inspect_attributes_for_categories.py: מיפוי מאפיינים לקטגוריות יעד.
- inspect_headphone_attributes.py: הצגת allowed values למאפייני אוזניות.
- inspect_json_schemas.py: בדיקת סכמות JSON (allowed values + mapping schema).
- inspect_products.py: דוח מוצרים/ספקים/מחירים מתוך DB.
- list_models.py: הדפסת מודלי Gemini זמינים.
- navigate_to_login.py: ניווט למסך login של MG דרך Chrome debug.
- parse_five_supplier_excel.py: המרת קובץ ספק Five ל-CSV במבנה הייבוא.
- query_brands_from_db.py: דגימת קודי מותגים מה-DB.
- search.py: חיפוש מחרוזות ב-transcript.
- take_screenshot_from_debugger.py: צילום מסך דרך Chrome debugger.
- verify_brands.py: אימות קיום מותגים ספציפיים בקובץ JSON.

## סיווג סקריפטים ב-king_games_product_manager

### Core production
- server.py
- update_products_batch_2.py
- run_price_check.py
- mg_import_runner.py
- scrape_cms_parameters.py
- browser_manager.py

### Ingestion / Update
- update_products_batch.py
- process_google_prices_update.py
- supplier_image_extraction_runner.py
- map_attributes.py
- audit_cms_products.py

### Diagnostics / One-off
- inspect_*.py
- check_*.py
- list_tabs*.py
- launch_*.py
- perform_login.py
- update_product_3510*.py

### Tests
- test_*.py (למשל test_endpoints.py, test_selenium.py, test_image_resolver.py)

## אוטומציית מור-לוי (בוקר) - מצב קיים

### מה קיים
- טריגר סנכרון ספק מה-UI ל-endpoint /api/supplier/sync.
- מיפוי ספק מור-לוי לסקריפט auto_run_morlevi.py ב-server.py.
- מנגנוני עיבוד/ייבוא לאחר שיש קובץ ספק (analyze/import ב-server.py).
- מנגנון ingestion ל-MG CMS דרך update_products_batch_2.py.

### מה חסר/שבור
- auto_run_morlevi.py לא קיים.
- כל משפחת auto_run_* לא קיימת (לא רק מור-לוי).
- שדות selectors/login של ספקים נשמרים אך לא ממומשים בפועל בהרצת הורדה.

## רשימת קבצים מוזכרים אך חסרים (Broken references)
- auto_run_morlevi.py
- auto_run_techno.py
- auto_run_amtel.py
- auto_run_benda.py
- auto_run_five.py
- auto_run_eastronics.py
- auto_run_cdata.py
- auto_run_asus_rog.py

## תזמונים פעילים במערכת
- daily_exporter_loop: רץ כל דקה; אחרי 07:00 מבצע export יומי פעם אחת ביום.
- automated_processes_loop: רץ כל 30 שניות ומריץ תהליכים שהגיע זמנם.
- תהליכי ברירת מחדל שנוצרים ב-init: עדכון מחירים בגוגל + בדיקת מחירי אתמול.

## סדר מומלץ (תוכנית שיקום)
1. לשחזר/לכתוב מחדש את משפחת auto_run_* בתוך helper_scripts/supplier_sync.
2. להתחיל ב-auto_run_morlevi.py לפי flow: login -> checkbox -> download -> normalize -> import.
3. לחבר בפועל את שדות selector_checkbox_* ו-selector_download_excel למנוע ההרצה.
4. להפריד קבצי debug/one-off לתיקיה ייעודית scripts_archive או scripts_debug.
5. ליצור קונבנציה ברורה:
   - core/
   - automations/suppliers/
   - diagnostics/
   - tests/
6. להוסיף מסמך RUNBOOK להרצות בוקר + בדיקת תקינות.
7. להעביר סיסמאות/קרדנצ'לים ל-env בלבד ולסובב סיסמאות חשופות.

## הערת אבטחה
נמצאו בפרויקט רמזים לקרדנצ'לים בקוד/קבצי קונפיג. מומלץ לבצע רוטציה לסודות ולהעביר הכל ל-environment variables.

## סטטוס מיפוי מלא (בפועל)
- בוצע מיפוי קבצי Python בתוך ה-workspace: 138 קבצים.
- חלוקה לפי אזור:
  - root: 16 קבצי Python
  - king_games_product_manager: 120 קבצי Python (כולל helper_scripts/image_extractors)
  - daily-price-checker: 2 קבצי Python
  - scratch (בתוך ה-workspace): ללא קבצי Python
- בנוסף קיים מקור חיצוני מחוץ ל-workspace:
  - C:\Users\USER\.gemini\antigravity\brain\927a6b7a-5605-4ec0-afe6-1028d82db6dc\scratch
  - בתיקיה זו נמצאים auto_run_morlevi.py ועוד עשרות סקריפטים תומכים (download/process/upload/inspect/search/test).

## איך עושים סדר בלי לשבור את המערכת

### עקרונות
1. לא מזיזים קבצי production פעילים בשלב ראשון.
2. קודם יוצרים קטלוג וסיווג, ורק אחר כך העברה/מחיקה.
3. כל שינוי מבני מתבצע ב-batch קטן עם בדיקת הרצה.

### שלב 1 - קטלוג רשמי (ללא שינוי קוד)
1. ליצור מסמך בעלות ותפקיד לכל סקריפט:
   - מי מריץ אותו
   - מתי הוא רץ (ידני/מתוזמן/API)
   - האם הוא production או debug
2. לסמן כל סקריפט בסטטוס:
   - ACTIVE
   - CANDIDATE_ARCHIVE
   - UNKNOWN

### שלב 2 - איחוד אוטומציות ספקים
1. ליצור תיקיה קבועה:
   - king_games_product_manager/helper_scripts/supplier_sync/
2. להעביר אליה את auto_run_morlevi.py ואת שאר auto_run_* ממקור ה-antigravity.
3. להשאיר wrapper דק בנתיבים הישנים (אם צריך תאימות לאחור).
4. לוודא שהמיפוי ב-server.py מצביע לקבצים קיימים.

### שלב 3 - הפרדת רעש דיבאג
1. להעביר סקריפטים מסוג inspect_*/check_*/test_* לארכיון מסודר:
   - king_games_product_manager/scripts_archive/debug/
   - king_games_product_manager/scripts_archive/tests/
2. להשאיר בשורש רק סקריפטים תפעוליים.

### שלב 4 - Runbook והפעלה יומית
1. ליצור RUNBOOK יומי עם flow מלא:
   - login supplier
   - checkbox selection
   - download file
   - process
   - import/update MG
2. להוסיף בדיקת בריאות (health check) לפני כל ריצה יומית.

## החלטות קונקרטיות להמשך (מומלץ לבצע לפי הסדר)
1. להעתיק את auto_run_morlevi.py + כל סקריפט auto_run_* ממקור ה-antigravity לתיקיית supplier_sync בפרויקט.
2. להריץ בדיקת קיום קבצים מול מפת הספקים ב-server.py ולסגור את כל ה-broken references.
3. להגדיר batch ראשון של ניקוי: להעביר רק קבצי update_product_3510*.py לארכיון.
4. לבצע smoke test: server עולה, sync supplier עובד, process log נכתב.

## מה לא לעשות כרגע
1. לא למחוק תיקיות chrome-profile*.
2. לא להזיז server.py / update_products_batch_2.py / run_price_check.py לפני שיש wrappers וריצה מאומתת.
3. לא לאחד עשרות inspect/test בבת אחת בלי סבב בדיקה בין batches.

## ממצא קריטי - למה "נעלם פיתוח"
- יש שני עותקים של המערכת:
   - עותק עדכני: C:\Projects\KINGGAMES\king_games_product_manager
   - עותק ישן (legacy): C:\Projects\KINGGAMES\scratch\king_games_product_manager
- במסך "עדכון קטגוריות למוצרים" הפיצ'ר של "קטגוריה חדשה (ידני) + שמירה" קיים בעותק העדכני ולא קיים בעותק הישן.
- לכן אם רץ server.py מתוך scratch מתקבלת תחושה שהפיתוח "נעלם".

## מה בוצע כדי למנוע בלבול חוזר
1. עותק scratch סומן כ-LEGACY בכותרת ה-UI.
2. פורט ה-scratch שונה ל-8010 (במקום 8000).
3. נוסף launcher אחיד להפעלת המערכת העדכנית:
    - C:\Projects\KINGGAMES\START_MAIN_MANAGER.bat
