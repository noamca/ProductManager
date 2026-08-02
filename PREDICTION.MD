# PREDICTION - תיעוד מלא של מנגנון הפרדיקציה

## מטרה
מסמך זה מתעד בצורה מדויקת ומעשית איך מנגנון הפרדיקציה עובד בפועל במערכת KINGGAMES, לפי סדר ריצה אמיתי בקוד.

המסלול הראשי:
- קובץ הרצה ראשי: [king_games_product_manager/update_products_batch_2.py](king_games_product_manager/update_products_batch_2.py)
- מנוע העשרה AI: [king_games_product_manager/product_scraper_engine/enricher.py](king_games_product_manager/product_scraper_engine/enricher.py)

המסמך מכסה:
- מה נכנס לריצה
- מה קורה בכל שלב
- מה נשמר במסד
- מה מתפרסם ל-MG
- מה נרשם בלוגים
- איך מנוהלים כשלים וזמני timeout

---

## 1) נקודת כניסה וטעינת סביבת עבודה

### 1.1 טעינת מודולים ונתיבים
ברגע שהסקריפט הראשי עולה, הוא מגדיר:
- נתיבי עבודה (WORKSPACE_DIR, ROOT_DIR)
- נתיב DB: products.db
- נתיבי קונפיגורציה: allowed_attribute_values, mapping_schema, specs_config, title_header_rules
- URL של חוקי כותרות מהשרת המקומי

בנוסף:
- מבוצע import למנוע enricher
- אם import נכשל, נשמרת השגיאה וניתן להמשיך רק במסלולים שלא תלויים ב-AI

### 1.2 דגלי ריצה
דגלי ברירת מחדל מנוהלים במבנה INGESTION_FLAGS, לדוגמה:
- ai_agent on/off
- img_scrpt on/off
- publish_to_mg
- שינוי קטגוריה
- בדיקת תמונות מקומיות קודם
- skip אם אין תמונות ספק
- force overrides לפרמטרי MG

המרה מארגומנטים לדגלים מתבצעת דרך parse_runtime_flags.

---

## 2) סדר ריצה על

מבחינת Flow ברמה הגבוהה:
1. טעינת קטגוריות leaf מה-DB
2. טעינת חוקי כותרות (API, ואם נופל אז קובץ)
3. בחירת מוצרים לעיבוד
4. שלב Local Enrichment (פרדיקציה + בניית תוכן + שמירה מקומית)
5. אם publish_to_mg דולק: שלב Publish ל-MG
6. סיכום סטטוסים, שגיאות, לוגים וארטיפקטים

---

## 3) בחירת מוצרים לריצה

המערכת יודעת לעבוד במצבים שונים:
- מוצר יחיד לפי MG ID
- טווח / רשימה ידנית
- מצבי אצווה לפי תנאים
- מצב Recommendation

בפועל, לפני פרדיקציה נוצרת רשימת MG IDs סופית לעיבוד.

---

## 4) שלב הפרדיקציה המקומית (Local Enrichment) - צעד אחר צעד

זה הלב של המנגנון.

### 4.1 טעינת הקשרים לפני AI
לכל מוצר נטען:
- נתוני מוצר מה-DB (title, ספק, קטגוריה וכו)
- רשימת קטגוריות leaf זמינות
- חוקי כותרות פעילים
- סכמת מפרט וערכים מותרים
- קודי מאפייני קטגוריה ל-pass-2

### 4.2 Phase 1 - נעילת קטגוריה
המנגנון מריץ סיווג ראשוני כדי לנעול קטגוריה לפני בניית המפרט הסופי.

בשלב זה יש Guardrails חשובים:
- override לפי כותרת (לדוגמה מארז מזוהה מתוך title)
- מניעת נעילת קטגוריית קירור כשאין סמני קירור אמיתיים
- נרמול כותרות "מורעלות" במקרי קצה

פלט השלב נשמר בשדות:
- PHASE1_CATEGORY_RECOMMENDED_ID
- PHASE1_CATEGORY_RECOMMENDED_NAME
- PHASE1_CATEGORY_CONFIDENCE_PERCENT
- PHASE1_CATEGORY_BLOCK_REASON
- PHASE2_CATEGORY_LOCKED_ID

### 4.3 קביעת product_type למנוע
לאחר נעילת קטגוריה, נקבע Product Type רלוונטי לפרומפט AI.

דוגמאות:
- קטגוריה 147 ממופה ל-desktop
- קטגוריות אחרות לפי לוגיקה פנימית וכותרת

### 4.4 קריאת enrich_single_product
הקריאה למנוע נעשית דרך:
- [king_games_product_manager/product_scraper_engine/enricher.py](king_games_product_manager/product_scraper_engine/enricher.py)

בפנים המנוע:
1. נקבעים specs_keys לפי קטגוריה/טיפוס
2. מתבצע prefetch מספק (שם מוצר ותמונות)
3. נבנה Prompt עשיר מאוד כולל:
   - priority לשם ספק
   - ספק, MPN, קטגוריות leaf
   - חוקי כותרות
   - סכמת מפרט
   - ערכים מותרים למאפיינים
   - שדות נדרשים בפלט JSON
4. קריאה ל-Gemini עם responseSchema קשיח
5. retry על תקלות טרנזיינט:
   - HTTP 429/5xx
   - timeout/network
   - invalid JSON
   - מבנה תגובה לא צפוי
6. decode של מפתחות/ערכים URL-encoded
7. ולידציה לוגית של הפלט

### 4.5 טיפול ב-timeout וברשת
אם Gemini מחזיר timeout/network:
- נעשה retry עד 3 ניסיונות
- backoff: 2s ואז 4s
- אם נכשל סופית: RuntimeError עם פירוט

לוג לדוגמה שנראה בפועל:
- Warning: Gemini request timeout/network issue (attempt 2/3). Retrying in 4s...

### 4.6 טיפול בכותרת (Title Governance)
לאחר קבלת פלט AI:
- נבדקת התאמה משפחתית של הכותרת
- אם rendered title לא תואם מהות מוצר, הוא נדחה
- כותרת AI נשארת authoritative
- title_guard_blocked הוא warning/log-only ולא מפיל זרימה

### 4.7 נרמול PRODUCT_ATTRIBUTES
לאחר AI:
1. normalize לערכים מותרים בלבד
2. השלמות heuristic מתוך title/specs כשחסר
3. override חד-פעמי למוצרים ספציפיים (אם מוגדר)

### 4.8 בניית תוכן HTML למוצר
המערכת בונה Short/Full descriptions.

בנתיב הפול-טקסט (content2), בניית המפרט נעשית בפונקציה:
- build_full_desc_html_from_engine

וכעת (לאחר התיקון האחרון):
- כל פריט מפרט נכתב כ-LI נפרד
- כשנכנס שדה כללי בסגנון פרטי מפרט כללי עם רשימה מופרדת בפסיקים, נעשה פיצול לפריטים
- אין הצגה של שורת מפרט מאוחדת ארוכה
- ההצגה היא רשימה נקייה

### 4.9 שמירת תוצרים מקומית
נשמרים:
- נתוני enrichment בשדות המוצר
- short_desc, full_desc
- extra_info עם payload
- product_attributes בטבלת מאפיינים
- שדות tracking וסטטוסים

בנוסף נשמרים ארטיפקטים:
- JSON report
- HTML report
- Prompt report
בנתיב enricher_reports.

---

## 5) שלב Publish ל-MG (אם publish_to_mg=true)

### 5.1 עקרון בסיס
גם כשמפרסמים ל-MG:
- המערכת קודם מבצעת Local materialization
- רק אז שולחת payload ל-MG

### 5.2 בניית payload חיצוני
העדכון נשלח דרך מודול חיצוני:
- C:/Projects/AgentUpdateMGsystem/update_product.py

payload כולל למשל:
- name
- category + categories
- brand
- catalog_num + sup_sku0
- description/keywords
- content/content2
- param_* attributes
- image1..image5

### 5.3 תמונות
זרימה:
1. בדיקת תמונות מקומיות
2. הכנת קבצים ממוספרים
3. דחיסה לגודל MG
4. שיגור image1..image5

אם יש תמונות מקומיות:
- מדלגים על caching מרוחק מיותר

### 5.4 רישום payload ללוג
לפני שליחה למודול החיצוני נשמר קובץ payload מלא:
- mg_updater_payload_logs/mg_payload_<id>_<timestamp>.json

### 5.5 עדכון סטטוס מקומי אחרי הצלחה
לאחר הצלחת עדכון MG:
- מתבצע sync ל-DB המקומי
- סטטוסי sync/is_preupload מתעדכנים
- פריטי review tracking מתעדכנים

---

## 6) שגיאות, דיאגנוסטיקה ולוגים

### 6.1 product_errors
שגיאות פונקציונליות נרשמות לטבלת product_errors עם:
- product_id
- type
- description
- timestamp

### 6.2 לוגים ייעודיים במנוע AI
ב-enricher:
- gemini_invalid_json.log
- gemini_connectivity.log

### 6.3 סיווג כשלים נפוצים
- timeout/network מול Gemini
- invalid JSON
- schema mismatch במפרט
- title essence mismatch
- בעיות publish/selector במודול MG

---

## 7) תיעוד שדות פלט קריטיים

### שדות AI מרכזיים
- PRODUCT_NAME
- PRODUCT_DESCRIPTION
- PRODUCT_TECHNICAL_DETAILS
- PRODUCT_ATTRIBUTES
- RECOMMENDED_CATEGORY_ID
- RECOMMENDED_CATEGORY_ATTRIBUTES
- FORMATTED_TITLE
- INTERNATIONAL_PART_NUMBER
- FAQ
- HTML_TITLE
- CONFIDENCE_PERCENT
- IMAGES

### מטא שדות ריצה
- METADATA.REQUEST_DURATION
- METADATA.REQUEST_CREDITS
- METADATA.REQUEST_PROMPT
- METADATA.SUPPLIER_PRODUCT_NAME

### שדות phase
- PHASE1_CATEGORY_RECOMMENDED_ID
- PHASE1_CATEGORY_CONFIDENCE_PERCENT
- PHASE1_CATEGORY_BLOCK_REASON
- PHASE2_CATEGORY_LOCKED_ID

---

## 8) דוגמת Trace מעשית למוצר יחיד

תרחיש טיפוסי למוצר יחיד:
1. קליטת ID
2. טעינת מוצר מה-DB
3. קביעת override קטגוריה לפי title
4. נעילת קטגוריה ב-Phase 1
5. בניית prompt ל-Phase 2 עם קטגוריה נעולה
6. קריאת Gemini עם retry
7. ולידציות title/spec/schema
8. נרמול מאפיינים
9. בניית content2 עם רשימות LI
10. שמירה מקומית
11. אם publish דולק: בניית payload + שליחה ל-MG
12. עדכון DB וסגירת run

---

## 9) נקודת התיקון האחרונה בפורמט המפרט

תיקון זה נועד לבעיה שבה מפרט טכני הופיע כשורה מאוחדת בסגנון:
- פרטי מפרט כללי: ... , ... , ...

מה תוקן:
- פיצול ערך מפרט כללי לפריטים נפרדים
- יצירת LI נפרד לכל פריט
- ביטול תלות בהצגת נקודתיים כמפריד מרכזי
- שמירה על מבנה רשימתי קריא

נקודת הקוד:
- [king_games_product_manager/update_products_batch_2.py](king_games_product_manager/update_products_batch_2.py)

---

## 10) הערות תפעול

1. דוח HTML של enricher הוא דוח פנימי נפרד, והוא יכול להציג טבלה גם אם content2 למוצר נשמר כרשימה. המסלול הקובע לכרטיס MG הוא content/content2 שנשלחים ב-publish payload.
2. במסלולי timeout של Gemini המערכת עושה retries אוטומטית; לא כל Warning מצביע על כשל סופי.
3. כאשר publish_to_mg דולק, תמיד מומלץ לבדוק את payload log של המוצר כדי לראות בדיוק מה נשלח.

---

## 11) קבצים מרכזיים לעיון

- [king_games_product_manager/update_products_batch_2.py](king_games_product_manager/update_products_batch_2.py)
- [king_games_product_manager/product_scraper_engine/enricher.py](king_games_product_manager/product_scraper_engine/enricher.py)
- [king_games_product_manager/title_header_rules.json](king_games_product_manager/title_header_rules.json)
- [king_games_product_manager/product_scraper_engine/specs_config.json](king_games_product_manager/product_scraper_engine/specs_config.json)

---

## 12) סיכום קצר

מנגנון הפרדיקציה במערכת הוא מנגנון דו-שלבי קשיח:
- קודם נעילת קטגוריה עם Guardrails
- אחר כך העשרה מלאה וולידציה
- ואז שמירה מקומית, ורק אם נדרש גם publish ל-MG

המערכת כבר כוללת:
- retry ורשת
- דיאגנוסטיקה מפורטת
- שומרי מהות כותרת
- נרמול מאפיינים
- תיעוד payload ולוגים מלא

והחל מהתיקון האחרון:
- המפרט מוצג ומוזרם כרשימת LI מסודרת, ללא שורת מפרט מאוחדת ארוכה.
