import http.server
import socketserver
import json
import sqlite3
import urllib.parse
import csv
import os
import sys
import subprocess
import threading
import time
import base64
import io
import math
import re
import uuid
import unicodedata
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
try:
    import pyodbc
except Exception:
    pyodbc = None
try:
    from google.oauth2.service_account import Credentials as GoogleServiceAccountCredentials
    from googleapiclient.discovery import build as google_build
except Exception:
    GoogleServiceAccountCredentials = None
    google_build = None
try:
    from openpyxl import load_workbook
except Exception:
    load_workbook = None
try:
    import xlrd
except Exception:
    xlrd = None
import replace_desktop_tree_component as desktop_replace

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_API_VERSION = "0.21"

PORT = 8000
DB_PATH = os.path.join(BASE_DIR, "products.db")
ALLOWED_VALUES_PATH = os.path.join(BASE_DIR, "allowed_attribute_values.json")
MAPPING_SCHEMA_PATH = os.path.join(BASE_DIR, "mapping_schema.json")
SUPPLIER_SCRIPTS_PATH = os.path.join(BASE_DIR, "supplier_image_scripts.json")
SUPPLIER_PRICELIST_SCRIPTS_PATH = os.path.join(BASE_DIR, "supplier_pricelist_scripts.json")
SUPPLIER_FIELD_MAPPINGS_PATH = os.path.join(BASE_DIR, "supplier_field_mappings.json")
APP_SETTINGS_PATH = os.path.join(BASE_DIR, "app_settings.json")
DEFAULT_IMAGES_ROOT = r"C:\Temp\ProducsImages"
IMAGE_EXTRACTION_JOB_PATH = r"C:\Temp\supplier_image_extraction_job.json"
MG_IMPORT_JOB_PATH = r"C:\Temp\mg_import_job.json"
MG_IMPORT_PROGRESS_PATH = r"C:\Temp\mg_import_progress.json"

SAP_ODBC_SERVER = os.environ.get("SAP_ODBC_SERVER", "193.163.2.37")
SAP_ODBC_DATABASE = os.environ.get("SAP_ODBC_DATABASE", "KingGames")
SAP_ODBC_USER = os.environ.get("SAP_ODBC_USER", "odbc")
SAP_ODBC_PASSWORD = os.environ.get("SAP_ODBC_PASSWORD", "Taz04092024!")
GOOGLE_SHEETS_CREDENTIALS_PATH = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_PATH", "google_service_account.json")
GOOGLE_SHEETS_SPREADSHEET_ID = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", "13LS71yd1lhxDjO2c9E9e1bCS3Q8M-Wvx7K7mh-ARY6I")
GOOGLE_SHEETS_TARGET_GID = int(os.environ.get("GOOGLE_SHEETS_TARGET_GID", "423496934"))

current_process = None
process_log_file = os.path.join(BASE_DIR, "process_run.log")
process_type = None  # "ingestion" or "crawler"
desktop_scan_running = False
desktop_scan_stop_requested = threading.Event()

active_run_id = None
automated_processes_running = set()
automated_processes_lock = threading.Lock()
intake_completion_jobs = {}
intake_completion_jobs_lock = threading.Lock()

DEFAULT_GOOGLE_PROCESS_NAME = "עדכון מחירים בגוגל"
DEFAULT_GOOGLE_PROCESS_SCRIPT = "process_google_prices_update.py"
DEFAULT_GOOGLE_MONTHLY_PROCESS_NAME = "עדכון מכירות גוגל חודשי"
DEFAULT_GOOGLE_MONTHLY_PROCESS_SCRIPT = "process_google_prices_update_clone.py"
DEFAULT_DAILY_PRICE_CHECK_NAME = "בדיקת מחירי אתמול"
DEFAULT_DAILY_PRICE_CHECK_SCRIPT = "run_price_check.py"

FIVE_SHEET_MAPPINGS = {
    "COUGAR GAMING": ("B", "C", "G", 1.0),
    "COUGAR ACC": ("B", "C", "G", 1.0),
    "COUGAR PC": ("B", "C", "F", 1.0),
    "ANTEC": ("B", "C", "G", 1.0),
    "ANTEC PSU": ("B", "C", "F", 1.0),
    "ANTEC COOL": ("B", "C", "G", 1.0),
    "NOCTUA": ("B", "C", "F", 1.0),
    "CREATIVE": ("B", "C", "H", 1.0),
    "BE QUIET": ("B", "C", "G", 1.0),
    "LEADTEC GPU": ("A", "C", "G", 1.0),
}

VISUAL_SHEET_MAPPINGS = {
    "תחנות": ("A", "B", "C"),
    "תחנות גיימינג + AIO": ("A", "B", "C"),
    "DSW": ("A", "B", "C"),
    "מסכים": ("B", "C", "D"),
    "ניידים 6U": ("A", "B", "C"),
    "ניידי קומרשל": ("A", "B", "C"),
    "ניידי ZBOOK": ("A", "B", "C"),
    "ניידי קונסיומר": ("A", "B", "C"),
    "אביזרים": ("A", "B", "C"),
}

FIVE_SHEET_ALIASES = {
    "COUGAR GAMING": ["COUGAR GAMING"],
    "COUGAR ACC": ["COUGAR ACC", "COUGAR ACCESSORIES"],
    "COUGAR PC": ["COUGAR PC", "COUGAR CASE"],
    "ANTEC": ["ANTEC"],
    "ANTEC PSU": ["ANTEC PSU", "ANTEC POWER SUPPLY"],
    "ANTEC COOL": ["ANTEC COOL", "ANTEC COOLING"],
    "NOCTUA": ["NOCTUA"],
    "CREATIVE": ["CREATIVE"],
    "BE QUIET": ["BE QUIET", "BEQUIET"],
    "LEADTEC GPU": ["LEADTEC GPU", "LEADTEK GPU", "LEADTEK"],
}

VISUAL_SHEET_ALIASES = {
    "תחנות": ["תחנות"],
    "תחנות גיימינג + AIO": ["תחנות גיימינג + AIO", "תחנות גיימינג AIO", "תחנות גיימינג"],
    "DSW": ["DSW"],
    "מסכים": ["מסכים"],
    "ניידים 6U": ["ניידים 6U", "ניידים6U"],
    "ניידי קומרשל": ["ניידי קומרשל", "ניידים קומרשל"],
    "ניידי ZBOOK": ["ניידי ZBOOK", "ניידי Z BOOK", "ניידי ZBOOKS"],
    "ניידי קונסיומר": ["ניידי קונסיומר", "ניידים קונסיומר"],
    "אביזרים": ["אביזרים"],
}

TECHNO_SHEET_ALIASES = {
    "Computing": ["Computing", "COMPUTING"],
    "Printing": ["Printing", "PRINTING"],
}

TECHNO_CATEGORY_BASE_MARGINS = {
    "מחשבים ניידים": 1.1,
    "אביזרים": 1.3,
    "מחשבים נייחים": 1.1,
    "aio": 1.1,
    "מחשבים נייחים גיימינג": 1.1,
    "מסכים ניידים": 1.1,
    "כרטיס מסך": 1.15,
    "תקשורת": 1.29,
    "מדפסות": 1.29,
    "פלוטרים": 1.29,
    "מתכלים": 1.29,
}

TECHNO_MONITOR_BRAND_MARGINS = {
    "DELL": 1.15,
    "ASUS": 1.15,
    "GIGABYTE": 1.15,
}

TECHNO_MONITOR_DEFAULT_MARGIN = 1.27
TECHNO_UNKNOWN_CATEGORY_DEFAULT_MARGIN = 1.3

# User-approved Techno prototype mapping (Excel columns):
# A category, C sub category, D sub-sub category, F manufacturer/supplier SKU,
# E processed title source, K raw price, J currency, B brand, G details,
# H manufacturer link, N notes, P availability.
TECHNO_PROTOTYPE_COLUMN_MAPPING = {
    "category": "A",
    "brand": "B",
    "sub_category": "C",
    "sub_sub_category": "D",
    "processed_title_source": "E",
    "manufacturer_sku": "F",
    "supplier_sku": "F",
    "details": "G",
    "manufacturer_link": "H",
    "currency": "J",
    "raw_price": "K",
    "notes": "N",
    "availability": "P",
}


def _get_excel_row_value(row_values, col_letter, fallback_idx=None):
    idx = None
    try:
        idx = col_to_idx(col_letter)
    except Exception:
        idx = None

    if idx is not None and idx >= 0 and idx < len(row_values):
        return row_values[idx]

    if fallback_idx is not None and fallback_idx >= 0 and fallback_idx < len(row_values):
        return row_values[fallback_idx]

    return None


def _open_sap_odbc_connection():
    if pyodbc is None:
        raise RuntimeError("pyodbc is not installed")

    available = [d for d in pyodbc.drivers()]
    preferred = [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "SQL Server",
    ]

    candidates = []
    for name in preferred:
        if name in available:
            candidates.append(name)
    for name in available:
        if "SQL Server" in name and name not in candidates:
            candidates.append(name)

    if not candidates:
        raise RuntimeError("No SQL Server ODBC driver is installed")

    last_error = None
    for driver_name in candidates:
        conn_str = (
            f"Driver={{{driver_name}}};"
            f"Server={SAP_ODBC_SERVER};"
            f"Database={SAP_ODBC_DATABASE};"
            f"Uid={SAP_ODBC_USER};"
            f"Pwd={SAP_ODBC_PASSWORD};"
            "TrustServerCertificate=Yes;"
        )
        try:
            conn = pyodbc.connect(conn_str, timeout=15)
            return conn, driver_name
        except Exception as ex:
            last_error = ex

    raise RuntimeError(f"ODBC connection failed: {last_error}")


def _open_google_sheets_service():
    if GoogleServiceAccountCredentials is None or google_build is None:
        raise RuntimeError("google-api-python-client/google-auth are not installed")

    creds_path = GOOGLE_SHEETS_CREDENTIALS_PATH
    if not os.path.isabs(creds_path):
        creds_path = os.path.join(BASE_DIR, creds_path)

    if not os.path.exists(creds_path):
        raise RuntimeError(f"Google credentials file not found: {creds_path}")

    creds = GoogleServiceAccountCredentials.from_service_account_file(
        creds_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return google_build("sheets", "v4", credentials=creds, cache_discovery=False)


def _format_int_with_thousands(value):
    dec_val = Decimal(str(value or 0)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return f"{int(dec_val):,}"


def _parse_iso_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        return None


def _interval_to_seconds(interval_value, interval_unit):
    interval_unit = _normalize_interval_unit(interval_unit)
    unit_map = {
        "minutes": 60,
        "hours": 3600,
        "days": 86400,
        "weeks": 604800,
    }
    return int(interval_value) * unit_map.get(interval_unit, 0)


def _validate_interval(interval_value, interval_unit):
    interval_unit = _normalize_interval_unit(interval_unit)
    allowed_units = {"minutes", "hours", "days", "weeks"}
    if interval_unit not in allowed_units:
        raise ValueError("interval_unit must be one of: minutes, hours, days, weeks")

    try:
        val = int(interval_value)
    except Exception:
        raise ValueError("interval_value must be an integer")

    if val <= 0:
        raise ValueError("interval_value must be greater than zero")

    seconds = _interval_to_seconds(val, interval_unit)
    min_seconds = 5 * 60
    max_seconds = 5 * 7 * 24 * 60 * 60

    if seconds < min_seconds or seconds > max_seconds:
        raise ValueError("האינטרוול חייב להיות בין 5 דקות ל-5 שבועות")

    return val


def _normalize_interval_unit(interval_unit):
    raw = str(interval_unit or "").strip().lower()
    mapping = {
        "minute": "minutes",
        "minutes": "minutes",
        "min": "minutes",
        "mins": "minutes",
        "דקה": "minutes",
        "דקות": "minutes",
        "hour": "hours",
        "hours": "hours",
        "hr": "hours",
        "hrs": "hours",
        "שעה": "hours",
        "שעות": "hours",
        "day": "days",
        "days": "days",
        "יום": "days",
        "ימים": "days",
        "week": "weeks",
        "weeks": "weeks",
        "שבוע": "weeks",
        "שבועות": "weeks",
    }
    return mapping.get(raw, raw)


def _next_7am_datetime(from_dt=None):
    ref = from_dt or datetime.now()
    next_7 = ref.replace(hour=7, minute=0, second=0, microsecond=0)
    if ref >= next_7:
        next_7 = next_7 + timedelta(days=1)
    return next_7


def _compute_next_run_at(process_row, finished_at):
    script_path = str(process_row.get("script_path") or "").strip().lower()
    # Keep this specific job pinned to 07:00 every day.
    if DEFAULT_GOOGLE_MONTHLY_PROCESS_SCRIPT.lower() in script_path:
        return _next_7am_datetime(finished_at)

    interval_value = int(process_row.get("interval_value") or 5)
    interval_unit = str(process_row.get("interval_unit") or "minutes")
    return finished_at + timedelta(seconds=_interval_to_seconds(interval_value, interval_unit))


def _ensure_default_automated_processes(cursor):
    now_iso = datetime.now().isoformat()
    next_run_iso = (datetime.now() + timedelta(days=1)).isoformat()
    next_run_7am_iso = _next_7am_datetime(datetime.now()).isoformat()
    cursor.execute(
        """
        INSERT INTO automated_processes
        (name, script_path, interval_value, interval_unit, enabled, next_run_at, created_at, updated_at, last_status, last_message)
        VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
        ON CONFLICT(name) DO NOTHING
        """,
        (
            DEFAULT_GOOGLE_PROCESS_NAME,
            DEFAULT_GOOGLE_PROCESS_SCRIPT,
            1,
            "days",
            next_run_iso,
            now_iso,
            now_iso,
            "idle",
            "Default process",
        ),
    )

    cursor.execute(
        """
        INSERT INTO automated_processes
        (name, script_path, interval_value, interval_unit, enabled, next_run_at, created_at, updated_at, last_status, last_message)
        VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
        ON CONFLICT(name) DO NOTHING
        """,
        (
            DEFAULT_GOOGLE_MONTHLY_PROCESS_NAME,
            DEFAULT_GOOGLE_MONTHLY_PROCESS_SCRIPT,
            1,
            "days",
            next_run_7am_iso,
            now_iso,
            now_iso,
            "idle",
            "Default process at 07:00",
        ),
    )

    cursor.execute(
        """
        INSERT INTO automated_processes
        (name, script_path, interval_value, interval_unit, enabled, next_run_at, created_at, updated_at, last_status, last_message)
        VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
        ON CONFLICT(name) DO NOTHING
        """,
        (
            DEFAULT_DAILY_PRICE_CHECK_NAME,
            DEFAULT_DAILY_PRICE_CHECK_SCRIPT,
            1,
            "days",
            next_run_iso,
            now_iso,
            now_iso,
            "idle",
            "Default process",
        ),
    )


def _default_supplier_image_scripts():
    return [
        {
            "supplier": "טכנו",
            "has_image_extractor": True,
            "use_enabled": True,
            "loader_script_path": "helper_scripts/image_extractors/LOAD_IMAGES_TECHNO.py",
            "images_download_dir": DEFAULT_IMAGES_ROOT,
        },
        {
            "supplier": "אסוס ROG",
            "has_image_extractor": True,
            "use_enabled": True,
            "loader_script_path": "helper_scripts/image_extractors/LOAD_IMAGES_ASUS_ROG_new.py",
            "images_download_dir": DEFAULT_IMAGES_ROOT,
        },
        {
            "supplier": "SERPAPI",
            "has_image_extractor": True,
            "use_enabled": True,
            "loader_script_path": "helper_scripts/image_extractors/SEARCH_IMAGES_FOR_PRDS_SERPAPI_KEY.py",
            "images_download_dir": DEFAULT_IMAGES_ROOT,
        },
        {"supplier": "מור לוי", "has_image_extractor": False, "use_enabled": False, "loader_script_path": "", "images_download_dir": DEFAULT_IMAGES_ROOT},
        {"supplier": "אמטל", "has_image_extractor": False, "use_enabled": False, "loader_script_path": "", "images_download_dir": DEFAULT_IMAGES_ROOT},
        {"supplier": "בנדא", "has_image_extractor": False, "use_enabled": False, "loader_script_path": "", "images_download_dir": DEFAULT_IMAGES_ROOT},
        {"supplier": "פייב", "has_image_extractor": False, "use_enabled": False, "loader_script_path": "", "images_download_dir": DEFAULT_IMAGES_ROOT},
        {"supplier": "איסטרוניקס", "has_image_extractor": False, "use_enabled": False, "loader_script_path": "", "images_download_dir": DEFAULT_IMAGES_ROOT},
        {"supplier": "סי-דאטה", "has_image_extractor": False, "use_enabled": False, "loader_script_path": "", "images_download_dir": DEFAULT_IMAGES_ROOT},
    ]


def _ensure_supplier_scripts_registry():
    if not os.path.exists(SUPPLIER_SCRIPTS_PATH):
        with open(SUPPLIER_SCRIPTS_PATH, "w", encoding="utf-8") as f:
            json.dump(_default_supplier_image_scripts(), f, ensure_ascii=False, indent=2)


def _load_supplier_scripts_registry():
    _ensure_supplier_scripts_registry()
    with open(SUPPLIER_SCRIPTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = []

    normalized = []
    for row in data:
        if not isinstance(row, dict):
            continue
        normalized.append(
            {
                "supplier": str(row.get("supplier", "")).strip(),
                "has_image_extractor": bool(row.get("has_image_extractor", False)),
                "use_enabled": bool(row.get("use_enabled", False)),
                "loader_script_path": str(row.get("loader_script_path", "")).strip(),
                "images_download_dir": str(row.get("images_download_dir", DEFAULT_IMAGES_ROOT)).strip() or DEFAULT_IMAGES_ROOT,
            }
        )
    return normalized


def _save_supplier_scripts_registry(entries):
    with open(SUPPLIER_SCRIPTS_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def _resolve_existing_workspace_path(path_text):
    raw = str(path_text or "").strip()
    if not raw:
        return ""
    candidates = []
    if os.path.isabs(raw):
        candidates.append(raw)
    else:
        candidates.append(os.path.join(BASE_DIR, raw))
        candidates.append(os.path.join(os.getcwd(), raw))
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return os.path.abspath(candidate)
    return ""


def _supplier_image_status_label(row):
    has_extractor = bool((row or {}).get("has_image_extractor"))
    use_enabled = bool((row or {}).get("use_enabled"))
    script_exists = bool((row or {}).get("script_file_exists"))

    if has_extractor and use_enabled and script_exists:
        return "ready"
    if has_extractor and not script_exists:
        return "missing_file"
    if has_extractor and not use_enabled:
        return "disabled"
    return "not_configured"


def _merge_supplier_image_scripts_with_catalog(entries, supplier_catalog):
    merged = []
    seen = set()
    source_by_key = {
        str((item or {}).get("name", "")).strip().casefold(): sorted(list((item or {}).get("sources", []) or []))
        for item in (supplier_catalog or [])
        if str((item or {}).get("name", "")).strip()
    }

    def _append_row(raw):
        supplier_name = str((raw or {}).get("supplier", "")).strip()
        if not supplier_name:
            return
        key = supplier_name.casefold()
        if key in seen:
            return
        seen.add(key)

        script_path = str((raw or {}).get("loader_script_path", "")).strip()
        script_abs_path = _resolve_existing_workspace_path(script_path)
        row = {
            "supplier": supplier_name,
            "has_image_extractor": bool((raw or {}).get("has_image_extractor", False)),
            "use_enabled": bool((raw or {}).get("use_enabled", False)),
            "loader_script_path": script_path,
            "images_download_dir": str((raw or {}).get("images_download_dir", DEFAULT_IMAGES_ROOT)).strip() or DEFAULT_IMAGES_ROOT,
            "script_file_exists": bool(script_abs_path),
            "script_abs_path": script_abs_path,
            "sources": source_by_key.get(key, []),
        }
        row["capability_status"] = _supplier_image_status_label(row)
        merged.append(row)

    for row in entries or []:
        _append_row(row)

    for item in supplier_catalog or []:
        supplier_name = str((item or {}).get("name", "")).strip()
        if not supplier_name:
            continue
        _append_row({
            "supplier": supplier_name,
            "has_image_extractor": False,
            "use_enabled": False,
            "loader_script_path": "",
            "images_download_dir": DEFAULT_IMAGES_ROOT,
        })

    merged.sort(key=lambda x: (str(x.get("supplier", "")).casefold(),))
    return merged


def _build_supplier_image_scripts_summary(rows):
    rows = list(rows or [])
    ready_rows = [r for r in rows if r.get("capability_status") == "ready"]
    configured_rows = [r for r in rows if r.get("has_image_extractor")]
    missing_rows = [r for r in rows if r.get("capability_status") == "missing_file"]
    disabled_rows = [r for r in rows if r.get("capability_status") == "disabled"]
    return {
        "total_suppliers": len(rows),
        "configured_suppliers": len(configured_rows),
        "ready_suppliers": len(ready_rows),
        "missing_file_suppliers": len(missing_rows),
        "disabled_suppliers": len(disabled_rows),
        "ready_supplier_names": [str(r.get("supplier", "")).strip() for r in ready_rows],
    }


def _default_supplier_pricelist_scripts():
    return [
        {"supplier": "מור לוי", "process_enabled": False, "process_type": "manual_csv", "process_script_path": "", "notes": ""},
        {"supplier": "אמטל", "process_enabled": False, "process_type": "manual_csv", "process_script_path": "", "notes": ""},
        {
            "supplier": "טכנו",
            "process_enabled": True,
            "process_type": "techno_excel_tabs",
            "process_script_path": "",
            "sample_file_path": r"C:\סנכרון אתר\קבצים לטיפול\Techno-Rezef Reseller Pricelist - JUNE2026.xlsm",
            "notes": "Techno Computing/Printing mapping + availability filter + VAT*margin rounded to next 9",
        },
        {"supplier": "בנדא", "process_enabled": False, "process_type": "manual_csv", "process_script_path": "", "notes": ""},
        {
            "supplier": "פייב",
            "process_enabled": True,
            "process_type": "five_excel_tabs",
            "process_script_path": "parse_five_supplier_excel.py",
            "sample_file_path": "",
            "notes": "Excel tabs mapping + formula x1.18 x1.3 rounded to next 9",
        },
        {
            "supplier": "ויזואל",
            "process_enabled": True,
            "process_type": "visual_excel_tabs",
            "process_script_path": "",
            "sample_file_path": "",
            "notes": "Visual tabs mapping (USD) + formula x1.18 x1.3 rounded to next 9",
        },
        {"supplier": "איסטרוניקס", "process_enabled": False, "process_type": "manual_csv", "process_script_path": "", "sample_file_path": "", "notes": ""},
        {"supplier": "סי-דאטה", "process_enabled": False, "process_type": "manual_csv", "process_script_path": "", "sample_file_path": "", "notes": ""},
    ]


def _default_app_settings():
    return {
        "usd_rate": 3.6,
        "vat_rate": 0.18,
    }


def _ensure_app_settings_file():
    if not os.path.exists(APP_SETTINGS_PATH):
        with open(APP_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(_default_app_settings(), f, ensure_ascii=False, indent=2)


def _load_app_settings():
    _ensure_app_settings_file()
    with open(APP_SETTINGS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        data = {}

    defaults = _default_app_settings()
    merged = dict(defaults)
    merged.update(data)

    try:
        merged["usd_rate"] = float(merged.get("usd_rate", defaults["usd_rate"]))
    except Exception:
        merged["usd_rate"] = defaults["usd_rate"]

    try:
        merged["vat_rate"] = float(merged.get("vat_rate", defaults["vat_rate"]))
    except Exception:
        merged["vat_rate"] = defaults["vat_rate"]

    if merged["usd_rate"] <= 0:
        merged["usd_rate"] = defaults["usd_rate"]

    if merged["vat_rate"] < 0 or merged["vat_rate"] > 1:
        merged["vat_rate"] = defaults["vat_rate"]

    return merged


def _save_app_settings(settings_data):
    merged = _load_app_settings()
    merged.update(settings_data or {})

    usd_rate = merged.get("usd_rate", _default_app_settings()["usd_rate"])
    try:
        usd_rate = float(usd_rate)
    except Exception:
        raise ValueError("usd_rate must be numeric")

    if usd_rate <= 0 or usd_rate > 50:
        raise ValueError("usd_rate must be > 0 and <= 50")

    vat_rate = merged.get("vat_rate", _default_app_settings()["vat_rate"])
    try:
        vat_rate = float(vat_rate)
    except Exception:
        raise ValueError("vat_rate must be numeric")

    if vat_rate < 0 or vat_rate > 1:
        raise ValueError("vat_rate must be between 0 and 1")

    merged["usd_rate"] = usd_rate
    merged["vat_rate"] = vat_rate

    with open(APP_SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    return merged


def _get_usd_rate():
    return float(_load_app_settings().get("usd_rate", _default_app_settings()["usd_rate"]))


def _get_vat_rate():
    return float(_load_app_settings().get("vat_rate", _default_app_settings()["vat_rate"]))


def _default_supplier_field_mappings_registry():
    return []


def _normalize_supplier_lookup_key(name):
    value = str(name or "")
    if not value:
        return ""
    try:
        value = unicodedata.normalize("NFKC", value)
    except Exception:
        pass
    value = value.strip()
    if not value:
        return ""
    value = re.sub(r"[\u05BE\-–—_]+", " ", value)
    value = re.sub(r"[\"'׳״`]+", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value.casefold()


def _load_supplier_field_mappings_registry_from_legacy_json():
    if not os.path.exists(SUPPLIER_FIELD_MAPPINGS_PATH):
        return []
    try:
        with open(SUPPLIER_FIELD_MAPPINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    normalized = []
    for row in data:
        if not isinstance(row, dict):
            continue
        supplier = str(row.get("supplier", "")).strip()
        if not supplier:
            continue
        tabs = row.get("tabs", [])
        if not isinstance(tabs, list):
            tabs = []
        normalized.append(
            {
                "supplier": supplier,
                "supplier_key": _normalize_supplier_lookup_key(row.get("supplier_key", "") or supplier),
                "tabs": [_normalize_tab_field_mapping(t) for t in tabs],
                "category_margins": dict(row.get("category_margins", {}) or {}),
                "category_import_toggles": dict(row.get("category_import_toggles", {}) or {}),
                "brand_import_toggles": dict(row.get("brand_import_toggles", {}) or {}),
                "last_sample_file": str(row.get("last_sample_file", "")).strip(),
                "updated_at": str(row.get("updated_at", "")).strip(),
            }
        )
    return normalized


def _normalize_tab_field_mapping(tab):
    if not isinstance(tab, dict):
        tab = {}
    defaults = {
        "tab_name": "",
        "tab_enabled": True,
        "field_mapping": {},
        "import_toggles": {},
        "display_toggles": {},
    }
    merged = dict(defaults)
    merged.update(tab)
    merged["tab_name"] = str(merged.get("tab_name", "")).strip()
    merged["tab_enabled"] = bool(merged.get("tab_enabled", True))
    merged["field_mapping"] = dict(merged.get("field_mapping", {}) or {})
    merged["import_toggles"] = dict(merged.get("import_toggles", {}) or {})
    merged["display_toggles"] = dict(merged.get("display_toggles", {}) or {})
    return merged


def _upsert_supplier_field_mapping_entry(entry):
    supplier = str((entry or {}).get("supplier", "")).strip()
    supplier_key = _normalize_supplier_lookup_key((entry or {}).get("supplier_key", "") or supplier)
    if not supplier or not supplier_key:
        return None

    tabs = [_normalize_tab_field_mapping(t) for t in ((entry or {}).get("tabs", []) or []) if isinstance(t, dict)]
    category_margins = dict((entry or {}).get("category_margins", {}) or {})
    category_import_toggles = dict((entry or {}).get("category_import_toggles", {}) or {})
    brand_import_toggles = dict((entry or {}).get("brand_import_toggles", {}) or {})
    last_sample_file = str((entry or {}).get("last_sample_file", "") or "").strip()
    updated_at = str((entry or {}).get("updated_at", "") or "").strip() or datetime.now().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO supplier_field_mappings (
            supplier_name,
            supplier_key,
            tabs_json,
            category_margins_json,
            category_import_toggles_json,
            brand_import_toggles_json,
            last_sample_file,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(supplier_key) DO UPDATE SET
            supplier_name = excluded.supplier_name,
            tabs_json = excluded.tabs_json,
            category_margins_json = excluded.category_margins_json,
            category_import_toggles_json = excluded.category_import_toggles_json,
            brand_import_toggles_json = excluded.brand_import_toggles_json,
            last_sample_file = excluded.last_sample_file,
            updated_at = excluded.updated_at
        """,
        (
            supplier,
            supplier_key,
            json.dumps(tabs, ensure_ascii=False),
            json.dumps(category_margins, ensure_ascii=False),
            json.dumps(category_import_toggles, ensure_ascii=False),
            json.dumps(brand_import_toggles, ensure_ascii=False),
            last_sample_file,
            updated_at,
        ),
    )
    conn.commit()
    conn.close()

    return {
        "supplier": supplier,
        "supplier_key": supplier_key,
        "tabs": tabs,
        "category_margins": category_margins,
        "category_import_toggles": category_import_toggles,
        "brand_import_toggles": brand_import_toggles,
        "last_sample_file": last_sample_file,
        "updated_at": updated_at,
    }


def _ensure_default_supplier_field_mappings_in_db(cursor):
    for entry in _default_supplier_field_mappings_registry():
        supplier = str((entry or {}).get("supplier", "")).strip()
        supplier_key = _normalize_supplier_lookup_key(supplier)
        if not supplier_key:
            continue
        cursor.execute("SELECT 1 FROM supplier_field_mappings WHERE supplier_key = ? LIMIT 1", (supplier_key,))
        if cursor.fetchone():
            continue
        now_iso = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO supplier_field_mappings (
                supplier_name,
                supplier_key,
                tabs_json,
                category_margins_json,
                category_import_toggles_json,
                brand_import_toggles_json,
                last_sample_file,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                supplier,
                supplier_key,
                json.dumps([_normalize_tab_field_mapping(t) for t in (entry.get("tabs", []) or [])], ensure_ascii=False),
                json.dumps(dict(entry.get("category_margins", {}) or {}), ensure_ascii=False),
                json.dumps(dict(entry.get("category_import_toggles", {}) or {}), ensure_ascii=False),
                json.dumps(dict(entry.get("brand_import_toggles", {}) or {}), ensure_ascii=False),
                str(entry.get("last_sample_file", "") or "").strip(),
                now_iso,
            ),
        )


def _migrate_supplier_field_mappings_legacy_json_to_db_if_needed(cursor):
    cursor.execute("SELECT COUNT(*) FROM supplier_field_mappings")
    count_row = cursor.fetchone()
    existing_count = int(count_row[0] or 0) if count_row else 0
    if existing_count > 0:
        return

    legacy_entries = _load_supplier_field_mappings_registry_from_legacy_json()
    if not legacy_entries:
        return

    now_iso = datetime.now().isoformat()
    for entry in legacy_entries:
        supplier = str((entry or {}).get("supplier", "")).strip()
        supplier_key = _normalize_supplier_lookup_key((entry or {}).get("supplier_key", "") or supplier)
        if not supplier or not supplier_key:
            continue

        tabs = [_normalize_tab_field_mapping(t) for t in ((entry or {}).get("tabs", []) or []) if isinstance(t, dict)]
        category_margins = dict((entry or {}).get("category_margins", {}) or {})
        category_import_toggles = dict((entry or {}).get("category_import_toggles", {}) or {})
        brand_import_toggles = dict((entry or {}).get("brand_import_toggles", {}) or {})
        last_sample_file = str((entry or {}).get("last_sample_file", "") or "").strip()
        updated_at = str((entry or {}).get("updated_at", "") or "").strip() or now_iso

        cursor.execute(
            """
            INSERT OR REPLACE INTO supplier_field_mappings (
                supplier_name,
                supplier_key,
                tabs_json,
                category_margins_json,
                category_import_toggles_json,
                brand_import_toggles_json,
                last_sample_file,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                supplier,
                supplier_key,
                json.dumps(tabs, ensure_ascii=False),
                json.dumps(category_margins, ensure_ascii=False),
                json.dumps(category_import_toggles, ensure_ascii=False),
                json.dumps(brand_import_toggles, ensure_ascii=False),
                last_sample_file,
                updated_at,
            ),
        )


def _load_supplier_field_mappings_registry():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT supplier_name, supplier_key, tabs_json,
               category_margins_json, category_import_toggles_json,
               brand_import_toggles_json, last_sample_file, updated_at
        FROM supplier_field_mappings
        ORDER BY updated_at DESC, id DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()

    normalized = []
    for row in rows:
        if not row:
            continue
        supplier = str(row["supplier_name"] or "").strip()
        if not supplier:
            continue
        try:
            tabs = json.loads(row["tabs_json"] or "[]")
        except Exception:
            tabs = []
        try:
            category_margins = json.loads(row["category_margins_json"] or "{}")
            if not isinstance(category_margins, dict):
                category_margins = {}
        except Exception:
            category_margins = {}
        try:
            category_import_toggles = json.loads(row["category_import_toggles_json"] or "{}")
            if not isinstance(category_import_toggles, dict):
                category_import_toggles = {}
        except Exception:
            category_import_toggles = {}
        try:
            brand_import_toggles = json.loads(row["brand_import_toggles_json"] or "{}")
            if not isinstance(brand_import_toggles, dict):
                brand_import_toggles = {}
        except Exception:
            brand_import_toggles = {}
        normalized.append(
            {
                "supplier": supplier,
                "supplier_key": _normalize_supplier_lookup_key(row["supplier_key"] or supplier),
                "tabs": [_normalize_tab_field_mapping(t) for t in tabs],
                "category_margins": category_margins,
                "category_import_toggles": category_import_toggles,
                "brand_import_toggles": brand_import_toggles,
                "last_sample_file": str(row["last_sample_file"] or "").strip(),
                "updated_at": str(row["updated_at"] or "").strip(),
            }
        )
    return normalized


def _save_supplier_field_mappings_registry(entries):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM supplier_field_mappings")
    conn.commit()
    conn.close()

    for entry in entries or []:
        try:
            _upsert_supplier_field_mapping_entry(entry)
        except Exception:
            continue


def _get_supplier_field_mapping_entry(supplier_name):
    supplier_key = _normalize_supplier_lookup_key(supplier_name)
    if not supplier_key:
        return None
    entries = _load_supplier_field_mappings_registry()
    for row in entries:
        row_key = _normalize_supplier_lookup_key(row.get("supplier_key", "") or row.get("supplier", ""))
        if row_key == supplier_key:
            return row
    return None


def _ensure_supplier_pricelist_scripts_registry():
    if not os.path.exists(SUPPLIER_PRICELIST_SCRIPTS_PATH):
        with open(SUPPLIER_PRICELIST_SCRIPTS_PATH, "w", encoding="utf-8") as f:
            json.dump(_default_supplier_pricelist_scripts(), f, ensure_ascii=False, indent=2)


def _load_supplier_pricelist_scripts_registry():
    _ensure_supplier_pricelist_scripts_registry()
    with open(SUPPLIER_PRICELIST_SCRIPTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = []

    normalized = []
    for row in data:
        if not isinstance(row, dict):
            continue
        normalized.append(
            {
                "supplier": str(row.get("supplier", "")).strip(),
                "process_enabled": bool(row.get("process_enabled", False)),
                "process_type": str(row.get("process_type", "manual_csv")).strip() or "manual_csv",
                "process_script_path": str(row.get("process_script_path", "")).strip(),
                "sample_file_path": str(row.get("sample_file_path", "")).strip(),
                "notes": str(row.get("notes", "")).strip(),
            }
        )
    return normalized


def _save_supplier_pricelist_scripts_registry(entries):
    with open(SUPPLIER_PRICELIST_SCRIPTS_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def _build_unified_supplier_catalog():
    source_priority = {
        "supplier_contacts": 1,
        "supplier_pricelist_scripts": 2,
        "supplier_image_scripts": 3,
        "supplier_field_mappings": 4,
        "sap_suppliers": 5,
    }
    catalog = {}

    def _add_name(raw_name, source):
        name = str(raw_name or "").strip()
        if not name:
            return
        key = name.casefold()
        item = catalog.get(key)
        if item is None:
            catalog[key] = {
                "name": name,
                "source_rank": source_priority.get(source, 99),
                "sources": {source},
            }
            return
        item["sources"].add(source)
        rank = source_priority.get(source, 99)
        if rank < item.get("source_rank", 99):
            item["name"] = name
            item["source_rank"] = rank

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT name FROM supplier_contacts ORDER BY name")
            for row in cursor.fetchall():
                _add_name(row["name"], "supplier_contacts")
        except Exception:
            pass

        try:
            cursor.execute("SELECT mg_supplier_name FROM sap_suppliers ORDER BY mg_supplier_name")
            for row in cursor.fetchall():
                _add_name(row["mg_supplier_name"], "sap_suppliers")
        except Exception:
            pass
    except Exception:
        pass
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass

    for row in _load_supplier_pricelist_scripts_registry():
        _add_name(row.get("supplier"), "supplier_pricelist_scripts")

    for row in _load_supplier_scripts_registry():
        _add_name(row.get("supplier"), "supplier_image_scripts")

    for row in _load_supplier_field_mappings_registry():
        _add_name(row.get("supplier"), "supplier_field_mappings")

    result = []
    for item in catalog.values():
        result.append(
            {
                "name": item.get("name", ""),
                "sources": sorted(list(item.get("sources", set()))),
            }
        )

    result.sort(key=lambda x: str(x.get("name", "")).casefold())
    return result


def _merge_pricelist_scripts_with_catalog(entries, supplier_catalog):
    merged = []
    seen = set()

    for row in entries or []:
        supplier_name = str((row or {}).get("supplier", "")).strip()
        if not supplier_name:
            continue
        key = supplier_name.casefold()
        if key in seen:
            continue
        seen.add(key)
        merged.append(
            {
                "supplier": supplier_name,
                "process_enabled": bool((row or {}).get("process_enabled", False)),
                "process_type": str((row or {}).get("process_type", "manual_csv") or "manual_csv").strip() or "manual_csv",
                "process_script_path": str((row or {}).get("process_script_path", "")).strip(),
                "sample_file_path": str((row or {}).get("sample_file_path", "")).strip(),
                "notes": str((row or {}).get("notes", "")).strip(),
            }
        )

    for item in supplier_catalog or []:
        supplier_name = str((item or {}).get("name", "")).strip()
        if not supplier_name:
            continue
        key = supplier_name.casefold()
        if key in seen:
            continue
        seen.add(key)
        merged.append(
            {
                "supplier": supplier_name,
                "process_enabled": False,
                "process_type": "manual_csv",
                "process_script_path": "",
                "sample_file_path": "",
                "notes": "",
            }
        )

    merged.sort(key=lambda x: str(x.get("supplier", "")).casefold())
    return merged


def _parse_numeric_price(value):
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    text = text.replace("\u00a0", "")
    cleaned = re.sub(r"[^0-9,.-]", "", text)
    if not cleaned:
        return None

    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        parts = cleaned.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")

    try:
        return float(cleaned)
    except ValueError:
        return None


def _round_up_to_next_9(value):
    rounded_up = math.ceil(float(value))
    remainder = rounded_up % 10
    if remainder == 9:
        return int(rounded_up)
    return int(rounded_up + (9 - remainder))


def _calculate_price_from_local_currency(base_price):
    vat_multiplier = 1.0 + _get_vat_rate()
    return _round_up_to_next_9(float(base_price) * vat_multiplier * 1.3)


def _calculate_price_with_vat_and_margin(base_price, margin_multiplier):
    vat_multiplier = 1.0 + _get_vat_rate()
    return _round_up_to_next_9(float(base_price) * vat_multiplier * float(margin_multiplier))


def _normalize_supplier_category(value):
    txt = str(value or "").replace("\u00a0", " ").strip()
    txt = re.sub(r"\s+", " ", txt)
    return txt


def _is_available_status(value):
    txt = str(value or "").strip().lower()
    if not txt:
        return False
    if "לא זמין" in txt or "not available" in txt or "out of stock" in txt:
        return False
    # Treat positive numeric stock values as available (e.g., "5", "12.0").
    num_txt = txt.replace(",", "")
    try:
        if float(num_txt) > 0:
            return True
    except Exception:
        pass

    positive_tokens = {"זמין", "available", "in stock", "כן", "yes", "true", "1", "x", "v", "במלאי", "יש מלאי"}
    if txt in positive_tokens:
        return True
    if "זמין" in txt or "available" in txt or "in stock" in txt or "מלאי" in txt:
        return True
    return False


def _is_usd_currency(value):
    txt = str(value or "").strip().lower()
    return any(token in txt for token in ["usd", "$", "דולר"]) 


def _get_techno_margin(category_value, manufacturer_value):
    category = _normalize_supplier_category(category_value)
    category_lower = category.lower()

    if "מסכי מחשב" in category_lower or "מסכי גיימינג" in category_lower:
        brand = str(manufacturer_value or "").strip().upper()
        return TECHNO_MONITOR_BRAND_MARGINS.get(brand, TECHNO_MONITOR_DEFAULT_MARGIN)

    for key, margin in TECHNO_CATEGORY_BASE_MARGINS.items():
        if key.lower() in category_lower:
            return margin

    return None


def _join_title_parts(parts):
    cleaned = [str(p).strip() for p in parts if str(p or "").strip()]
    return " ".join(cleaned)


def _safe_text(value):
    return str(value or "").replace("\u00a0", " ").strip()


def _category_key(category, sub_category, sub_sub_category):
    return " | ".join([
        _safe_text(category),
        _safe_text(sub_category),
        _safe_text(sub_sub_category),
    ])


def _build_supplier_category_tree(rows):
    tree = {}
    for row in rows or []:
        cat = _safe_text((row or {}).get("category"))
        sub = _safe_text((row or {}).get("sub_category"))
        sub_sub = _safe_text((row or {}).get("sub_sub_category"))
        if not cat:
            continue
        if cat not in tree:
            tree[cat] = {}
        if sub not in tree[cat]:
            tree[cat][sub] = set()
        if sub_sub:
            tree[cat][sub].add(sub_sub)

    output = []
    for cat_name in sorted(tree.keys()):
        sub_items = []
        for sub_name in sorted(tree[cat_name].keys()):
            children = sorted(tree[cat_name][sub_name])
            sub_items.append(
                {
                    "name": sub_name,
                    "children": children,
                }
            )
        output.append(
            {
                "name": cat_name,
                "children": sub_items,
            }
        )
    return output


def _build_techno_computing_title(category_value, manufacturer, family, model, supplier_sku):
    category = _normalize_supplier_category(category_value)
    if "מחשבים ניידים" in category:
        return _join_title_parts(["מחשב נייד", manufacturer, model, supplier_sku])
    return _join_title_parts([manufacturer, family, model, supplier_sku])


def _transform_techno_excel_to_csv_data(file_content_b64):
    payload = _extract_base64_payload(file_content_b64)
    if not payload:
        raise RuntimeError("Missing file content")

    raw_bytes = base64.b64decode(payload)
    if not raw_bytes.startswith(b"PK"):
        return _transform_techno_legacy_xls_to_csv_data(raw_bytes)

    if load_workbook is None:
        raise RuntimeError("openpyxl is not installed on server")

    workbook = load_workbook(filename=io.BytesIO(raw_bytes), data_only=True, read_only=True)
    usd_rate = _get_usd_rate()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "supplier_sku",
        "title",
        "price",
        "stock",
        "category",
        "sub_category",
        "sub_sub_category",
        "manufacturer_sku",
        "brand",
        "details",
        "notes",
        "currency",
        "raw_price",
        "margin",
        "manufacturer_link",
        "availability",
        "tab_name",
    ])

    tabs_summary = []
    total_extracted = 0
    normalized_rows = []

    sheet_order = ["Computing", "Printing"]
    for configured_sheet in sheet_order:
        matched_sheet_name = _resolve_sheet_name(workbook, configured_sheet, TECHNO_SHEET_ALIASES)
        if not matched_sheet_name:
            tabs_summary.append(
                {
                    "tab": configured_sheet,
                    "exists": False,
                    "matched_tab": "",
                    "rows_scanned": 0,
                    "extracted": 0,
                    "skipped_not_available": 0,
                    "skipped_invalid_price": 0,
                    "skipped_missing_required": 0,
                    "skipped_unknown_category": 0,
                    "rows_with_link": 0,
                }
            )
            continue

        sheet = workbook[matched_sheet_name]
        rows_scanned = 0
        extracted = 0
        skipped_not_available = 0
        skipped_invalid_price = 0
        skipped_missing_required = 0
        skipped_unknown_category = 0
        rows_with_link = 0

        # Some supplier files have inflated max_row due formatting; stop after
        # a long empty streak to avoid scanning hundreds of thousands of blanks.
        empty_streak = 0
        if configured_sheet == "Computing":
            rows_iter = sheet.iter_rows(min_row=1, max_col=16, values_only=True)
        else:
            rows_iter = sheet.iter_rows(min_row=1, max_col=15, values_only=True)

        for row_values in rows_iter:
            if not any(str(v or "").strip() for v in row_values):
                empty_streak += 1
                if empty_streak >= 500:
                    break
                continue
            empty_streak = 0

            if configured_sheet == "Computing":
                category = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["category"], fallback_idx=0)
                manufacturer = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["brand"], fallback_idx=1)
                sub_category = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["sub_category"], fallback_idx=2)
                sub_sub_category = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["sub_sub_category"], fallback_idx=3)
                family = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["sub_sub_category"], fallback_idx=3)
                model = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["processed_title_source"], fallback_idx=4)
                supplier_sku = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["supplier_sku"], fallback_idx=5)
                details = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["details"], fallback_idx=6)
                manufacturer_link = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["manufacturer_link"], fallback_idx=7)
                currency = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["currency"], fallback_idx=9)
                base_price_raw = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["raw_price"], fallback_idx=10)
                notes = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["notes"], fallback_idx=13)
                availability = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["availability"], fallback_idx=15)

                sku_txt = str(supplier_sku or "").strip()
                category_txt = _normalize_supplier_category(category)
                sub_category_txt = _normalize_supplier_category(sub_category)
                sub_sub_category_txt = _normalize_supplier_category(sub_sub_category)
                manufacturer_txt = str(manufacturer or "").strip()
                family_txt = str(family or "").strip()
                model_txt = str(model or "").strip()
                details_txt = str(details or "").strip()
                link_txt = str(manufacturer_link or "").strip()
                notes_txt = str(notes or "").strip()
            else:
                category = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["category"], fallback_idx=0)
                manufacturer = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["brand"], fallback_idx=1)
                sub_category = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["sub_category"], fallback_idx=2)
                sub_sub_category = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["sub_sub_category"], fallback_idx=3)
                supplier_sku = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["supplier_sku"], fallback_idx=5)
                printer_name = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["processed_title_source"], fallback_idx=6)
                details = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["details"], fallback_idx=6)
                manufacturer_link = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["manufacturer_link"], fallback_idx=7)
                currency = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["currency"], fallback_idx=9)
                base_price_raw = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["raw_price"], fallback_idx=10)
                notes = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["notes"], fallback_idx=13)
                availability = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["availability"], fallback_idx=14)

                sku_txt = str(supplier_sku or "").strip()
                category_txt = _normalize_supplier_category(category)
                sub_category_txt = _normalize_supplier_category(sub_category)
                sub_sub_category_txt = _normalize_supplier_category(sub_sub_category)
                manufacturer_txt = str(manufacturer or "").strip()
                family_txt = ""
                model_txt = str(printer_name or "").strip()
                details_txt = str(details or printer_name or "").strip()
                link_txt = str(manufacturer_link or "").strip()
                notes_txt = str(notes or "").strip()

            base_price_txt = str(base_price_raw or "").strip()
            availability_txt = str(availability or "").strip()

            if not any([sku_txt, category_txt, model_txt, base_price_txt, availability_txt]):
                continue

            rows_scanned += 1

            if not sku_txt or not category_txt:
                skipped_missing_required += 1
                continue

            if not _is_available_status(availability):
                skipped_not_available += 1
                continue

            base_price = _parse_numeric_price(base_price_raw)
            if base_price is None or base_price <= 0:
                skipped_invalid_price += 1
                continue

            if _is_usd_currency(currency):
                local_price = float(base_price) * float(usd_rate)
            else:
                local_price = float(base_price)

            margin = _get_techno_margin(category_txt, manufacturer_txt)
            needs_margin_decision = margin is None
            if needs_margin_decision:
                skipped_unknown_category += 1
                margin = TECHNO_UNKNOWN_CATEGORY_DEFAULT_MARGIN

            final_price = _calculate_price_with_vat_and_margin(local_price, margin)

            if configured_sheet == "Computing":
                title = _build_techno_computing_title(category_txt, manufacturer_txt, family_txt, model_txt, sku_txt)
            else:
                title = _join_title_parts([model_txt, manufacturer_txt, sku_txt])

            if not title:
                skipped_missing_required += 1
                continue

            writer.writerow([
                sku_txt,
                title,
                str(final_price),
                "10",
                category_txt,
                sub_category_txt,
                sub_sub_category_txt,
                sku_txt,
                manufacturer_txt,
                details_txt,
                notes_txt,
                str(currency or "").strip(),
                str(base_price),
                str(margin),
                link_txt,
                availability_txt,
                configured_sheet,
            ])

            normalized_rows.append(
                {
                    "tab_name": configured_sheet,
                    "category": category_txt,
                    "sub_category": sub_category_txt,
                    "sub_sub_category": sub_sub_category_txt,
                    "manufacturer_sku": sku_txt,
                    "supplier_sku": sku_txt,
                    "processed_title": title,
                    "raw_price": float(base_price),
                    "currency": str(currency or "").strip(),
                    "margin": float(margin),
                    "final_price": float(final_price),
                    "needs_margin_decision": needs_margin_decision,
                    "brand": manufacturer_txt,
                    "details": details_txt,
                    "notes": notes_txt,
                    "availability": availability_txt,
                    "manufacturer_link": link_txt,
                    "category_key": _category_key(category_txt, sub_category_txt, sub_sub_category_txt),
                }
            )
            extracted += 1
            if link_txt:
                rows_with_link += 1

        tabs_summary.append(
            {
                "tab": configured_sheet,
                "exists": True,
                "matched_tab": matched_sheet_name,
                "rows_scanned": rows_scanned,
                "extracted": extracted,
                "skipped_not_available": skipped_not_available,
                "skipped_invalid_price": skipped_invalid_price,
                "skipped_missing_required": skipped_missing_required,
                "skipped_unknown_category": skipped_unknown_category,
                "rows_with_link": rows_with_link,
            }
        )
        total_extracted += extracted

    return output.getvalue(), {
        "tabs": tabs_summary,
        "total_extracted": total_extracted,
        "normalized_rows": normalized_rows,
        "category_tree": _build_supplier_category_tree(normalized_rows),
        "unique_brands": sorted({str((r or {}).get("brand", "")).strip() for r in normalized_rows if str((r or {}).get("brand", "")).strip()}),
    }


def _transform_techno_legacy_xls_to_csv_data(raw_bytes):
    if xlrd is None:
        raise RuntimeError("xlrd is not installed on server (required for legacy .xls files)")

    workbook = xlrd.open_workbook(file_contents=raw_bytes)
    usd_rate = _get_usd_rate()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "supplier_sku",
        "title",
        "price",
        "stock",
        "category",
        "sub_category",
        "sub_sub_category",
        "manufacturer_sku",
        "brand",
        "details",
        "notes",
        "currency",
        "raw_price",
        "margin",
        "manufacturer_link",
        "availability",
        "tab_name",
    ])

    tabs_summary = []
    total_extracted = 0
    normalized_rows = []

    sheet_order = ["Computing", "Printing"]
    for configured_sheet in sheet_order:
        matched_sheet_name = _resolve_sheet_name(workbook, configured_sheet, TECHNO_SHEET_ALIASES)
        if not matched_sheet_name:
            tabs_summary.append(
                {
                    "tab": configured_sheet,
                    "exists": False,
                    "matched_tab": "",
                    "rows_scanned": 0,
                    "extracted": 0,
                    "skipped_not_available": 0,
                    "skipped_invalid_price": 0,
                    "skipped_missing_required": 0,
                    "skipped_unknown_category": 0,
                    "rows_with_link": 0,
                }
            )
            continue

        sheet = workbook.sheet_by_name(matched_sheet_name)
        rows_scanned = 0
        extracted = 0
        skipped_not_available = 0
        skipped_invalid_price = 0
        skipped_missing_required = 0
        skipped_unknown_category = 0
        rows_with_link = 0

        for row_idx in range(1, sheet.nrows):
            row_values = [sheet.cell_value(row_idx, c) for c in range(sheet.ncols)]
            if configured_sheet == "Computing":
                category = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["category"], fallback_idx=0)
                manufacturer = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["brand"], fallback_idx=1)
                sub_category = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["sub_category"], fallback_idx=2)
                sub_sub_category = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["sub_sub_category"], fallback_idx=3)
                family = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["sub_sub_category"], fallback_idx=3)
                model = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["processed_title_source"], fallback_idx=4)
                supplier_sku = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["supplier_sku"], fallback_idx=5)
                details = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["details"], fallback_idx=6)
                manufacturer_link = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["manufacturer_link"], fallback_idx=7)
                currency = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["currency"], fallback_idx=9)
                base_price_raw = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["raw_price"], fallback_idx=10)
                notes = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["notes"], fallback_idx=13)
                availability = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["availability"], fallback_idx=15)

                sku_txt = str(supplier_sku or "").strip()
                category_txt = _normalize_supplier_category(category)
                sub_category_txt = _normalize_supplier_category(sub_category)
                sub_sub_category_txt = _normalize_supplier_category(sub_sub_category)
                manufacturer_txt = str(manufacturer or "").strip()
                family_txt = str(family or "").strip()
                model_txt = str(model or "").strip()
                details_txt = str(details or "").strip()
                link_txt = str(manufacturer_link or "").strip()
                notes_txt = str(notes or "").strip()
            else:
                category = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["category"], fallback_idx=0)
                manufacturer = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["brand"], fallback_idx=1)
                sub_category = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["sub_category"], fallback_idx=2)
                sub_sub_category = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["sub_sub_category"], fallback_idx=3)
                supplier_sku = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["supplier_sku"], fallback_idx=5)
                printer_name = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["processed_title_source"], fallback_idx=6)
                details = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["details"], fallback_idx=6)
                manufacturer_link = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["manufacturer_link"], fallback_idx=7)
                currency = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["currency"], fallback_idx=9)
                base_price_raw = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["raw_price"], fallback_idx=10)
                notes = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["notes"], fallback_idx=13)
                availability = _get_excel_row_value(row_values, TECHNO_PROTOTYPE_COLUMN_MAPPING["availability"], fallback_idx=14)

                sku_txt = str(supplier_sku or "").strip()
                category_txt = _normalize_supplier_category(category)
                sub_category_txt = _normalize_supplier_category(sub_category)
                sub_sub_category_txt = _normalize_supplier_category(sub_sub_category)
                manufacturer_txt = str(manufacturer or "").strip()
                family_txt = ""
                model_txt = str(printer_name or "").strip()
                details_txt = str(details or printer_name or "").strip()
                link_txt = str(manufacturer_link or "").strip()
                notes_txt = str(notes or "").strip()

            base_price_txt = str(base_price_raw or "").strip()
            availability_txt = str(availability or "").strip()

            if not any([sku_txt, category_txt, model_txt, base_price_txt, availability_txt]):
                continue

            rows_scanned += 1

            if not sku_txt or not category_txt:
                skipped_missing_required += 1
                continue

            if not _is_available_status(availability):
                skipped_not_available += 1
                continue

            base_price = _parse_numeric_price(base_price_raw)
            if base_price is None or base_price <= 0:
                skipped_invalid_price += 1
                continue

            if _is_usd_currency(currency):
                local_price = float(base_price) * float(usd_rate)
            else:
                local_price = float(base_price)

            margin = _get_techno_margin(category_txt, manufacturer_txt)
            needs_margin_decision = margin is None
            if needs_margin_decision:
                skipped_unknown_category += 1
                margin = TECHNO_UNKNOWN_CATEGORY_DEFAULT_MARGIN

            final_price = _calculate_price_with_vat_and_margin(local_price, margin)

            if configured_sheet == "Computing":
                title = _build_techno_computing_title(category_txt, manufacturer_txt, family_txt, model_txt, sku_txt)
            else:
                title = _join_title_parts([model_txt, manufacturer_txt, sku_txt])

            if not title:
                skipped_missing_required += 1
                continue

            writer.writerow([
                sku_txt,
                title,
                str(final_price),
                "10",
                category_txt,
                sub_category_txt,
                sub_sub_category_txt,
                sku_txt,
                manufacturer_txt,
                details_txt,
                notes_txt,
                str(currency or "").strip(),
                str(base_price),
                str(margin),
                link_txt,
                availability_txt,
                configured_sheet,
            ])

            normalized_rows.append(
                {
                    "tab_name": configured_sheet,
                    "category": category_txt,
                    "sub_category": sub_category_txt,
                    "sub_sub_category": sub_sub_category_txt,
                    "manufacturer_sku": sku_txt,
                    "supplier_sku": sku_txt,
                    "processed_title": title,
                    "raw_price": float(base_price),
                    "currency": str(currency or "").strip(),
                    "margin": float(margin),
                    "final_price": float(final_price),
                    "needs_margin_decision": needs_margin_decision,
                    "brand": manufacturer_txt,
                    "details": details_txt,
                    "notes": notes_txt,
                    "availability": availability_txt,
                    "manufacturer_link": link_txt,
                    "category_key": _category_key(category_txt, sub_category_txt, sub_sub_category_txt),
                }
            )
            extracted += 1
            if link_txt:
                rows_with_link += 1

        tabs_summary.append(
            {
                "tab": configured_sheet,
                "exists": True,
                "matched_tab": matched_sheet_name,
                "rows_scanned": rows_scanned,
                "extracted": extracted,
                "skipped_not_available": skipped_not_available,
                "skipped_invalid_price": skipped_invalid_price,
                "skipped_missing_required": skipped_missing_required,
                "skipped_unknown_category": skipped_unknown_category,
                "rows_with_link": rows_with_link,
            }
        )
        total_extracted += extracted

    return output.getvalue(), {
        "tabs": tabs_summary,
        "total_extracted": total_extracted,
        "normalized_rows": normalized_rows,
        "category_tree": _build_supplier_category_tree(normalized_rows),
        "unique_brands": sorted({str((r or {}).get("brand", "")).strip() for r in normalized_rows if str((r or {}).get("brand", "")).strip()}),
    }


def _extract_base64_payload(raw):
    txt = str(raw or "").strip()
    if not txt:
        return ""
    if txt.startswith("data:") and "," in txt:
        return txt.split(",", 1)[1]
    return txt


def _normalize_sheet_name(name):
    txt = str(name or "")
    txt = txt.replace("\u00a0", " ")
    txt = txt.replace("\u200f", "")
    txt = txt.replace("\u200e", "")
    txt = txt.strip().upper()
    txt = re.sub(r"\s+", " ", txt)
    txt = re.sub(r"[^\w ]", "", txt, flags=re.UNICODE)
    txt = txt.replace("_", " ")
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def _resolve_sheet_name(workbook, configured_name, aliases_map=None):
    aliases_map = aliases_map or {}
    aliases = aliases_map.get(configured_name, [configured_name])
    normalized_to_actual = {}
    sheet_names = getattr(workbook, "sheetnames", None) or getattr(workbook, "sheet_names", lambda: [])()
    for actual in sheet_names:
        normalized_to_actual[_normalize_sheet_name(actual)] = actual

    for alias in aliases:
        n_alias = _normalize_sheet_name(alias)
        if n_alias in normalized_to_actual:
            return normalized_to_actual[n_alias]

    alias_tokens = []
    for alias in aliases:
        n_alias = _normalize_sheet_name(alias)
        tokens = [t for t in n_alias.split(" ") if t]
        # Avoid fuzzy matching for single-word aliases like "ANTEC" to prevent
        # accidental matches such as "ANTEC PSU".
        if len(tokens) >= 2:
            alias_tokens.append(tokens)

    for actual in sheet_names:
        n_actual = _normalize_sheet_name(actual)
        actual_tokens = [t for t in n_actual.split(" ") if t]
        for required_tokens in alias_tokens:
            if all(tok in actual_tokens for tok in required_tokens):
                return actual

    return None


def _transform_five_excel_to_csv_data(file_content_b64):
    if load_workbook is None:
        raise RuntimeError("openpyxl is not installed on server")

    payload = _extract_base64_payload(file_content_b64)
    if not payload:
        raise RuntimeError("Missing file content")

    raw_bytes = base64.b64decode(payload)
    workbook = load_workbook(filename=io.BytesIO(raw_bytes), data_only=True, read_only=True)
    usd_rate = _get_usd_rate()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["supplier_sku", "title", "price", "stock"])
    tabs_summary = []
    total_extracted = 0

    for sheet_name, mapping in FIVE_SHEET_MAPPINGS.items():
        matched_sheet_name = _resolve_sheet_name(workbook, sheet_name, FIVE_SHEET_ALIASES)
        if not matched_sheet_name:
            tabs_summary.append(
                {
                    "tab": sheet_name,
                    "exists": False,
                    "matched_tab": "",
                    "rows_scanned": 0,
                    "extracted": 0,
                }
            )
            continue

        sku_col, title_col, price_col, multiplier = mapping
        sheet = workbook[matched_sheet_name]
        rows_scanned = 0
        extracted = 0

        for row_idx in range(1, sheet.max_row + 1):
            supplier_sku = sheet[f"{sku_col}{row_idx}"].value
            title = sheet[f"{title_col}{row_idx}"].value
            raw_price = sheet[f"{price_col}{row_idx}"].value

            sku_txt = "" if supplier_sku is None else str(supplier_sku).strip()
            title_txt = "" if title is None else str(title).strip()
            raw_price_txt = "" if raw_price is None else str(raw_price).strip()

            if not sku_txt and not title_txt and not raw_price_txt:
                continue

            rows_scanned += 1

            if supplier_sku is None or title is None:
                continue

            base_price = _parse_numeric_price(raw_price)
            if base_price is None or base_price <= 0:
                continue

            adjusted = base_price * float(multiplier)
            if sheet_name == "NOCTUA":
                adjusted = adjusted * usd_rate
            final_price = _calculate_price_from_local_currency(adjusted)
            writer.writerow([str(supplier_sku).strip(), str(title).strip(), str(final_price), "10"])
            extracted += 1

        tabs_summary.append(
            {
                "tab": sheet_name,
                "exists": True,
                "matched_tab": matched_sheet_name,
                "rows_scanned": rows_scanned,
                "extracted": extracted,
            }
        )
        total_extracted += extracted

    return output.getvalue(), {"tabs": tabs_summary, "total_extracted": total_extracted}


def _transform_visual_excel_to_csv_data(file_content_b64):
    if load_workbook is None:
        raise RuntimeError("openpyxl is not installed on server")

    payload = _extract_base64_payload(file_content_b64)
    if not payload:
        raise RuntimeError("Missing file content")

    raw_bytes = base64.b64decode(payload)
    workbook = load_workbook(filename=io.BytesIO(raw_bytes), data_only=True, read_only=True)
    usd_rate = _get_usd_rate()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["supplier_sku", "title", "price", "stock"])
    tabs_summary = []
    total_extracted = 0

    for sheet_name, mapping in VISUAL_SHEET_MAPPINGS.items():
        matched_sheet_name = _resolve_sheet_name(workbook, sheet_name, VISUAL_SHEET_ALIASES)
        if not matched_sheet_name:
            tabs_summary.append(
                {
                    "tab": sheet_name,
                    "exists": False,
                    "matched_tab": "",
                    "rows_scanned": 0,
                    "extracted": 0,
                }
            )
            continue

        sku_col, title_col, price_col = mapping
        sheet = workbook[matched_sheet_name]
        rows_scanned = 0
        extracted = 0

        for row_idx in range(1, sheet.max_row + 1):
            supplier_sku = sheet[f"{sku_col}{row_idx}"].value
            title = sheet[f"{title_col}{row_idx}"].value
            raw_price = sheet[f"{price_col}{row_idx}"].value

            sku_txt = "" if supplier_sku is None else str(supplier_sku).strip()
            title_txt = "" if title is None else str(title).strip()
            raw_price_txt = "" if raw_price is None else str(raw_price).strip()

            if not sku_txt and not title_txt and not raw_price_txt:
                continue

            rows_scanned += 1

            if supplier_sku is None or title is None:
                continue

            base_price_usd = _parse_numeric_price(raw_price)
            if base_price_usd is None or base_price_usd <= 0:
                continue

            local_price = base_price_usd * usd_rate
            final_price = _calculate_price_from_local_currency(local_price)
            writer.writerow([str(supplier_sku).strip(), str(title).strip(), str(final_price), "10"])
            extracted += 1

        tabs_summary.append(
            {
                "tab": sheet_name,
                "exists": True,
                "matched_tab": matched_sheet_name,
                "rows_scanned": rows_scanned,
                "extracted": extracted,
            }
        )
        total_extracted += extracted

    return output.getvalue(), {"tabs": tabs_summary, "total_extracted": total_extracted}


def _images_storage_status(root_path):
    root = root_path or DEFAULT_IMAGES_ROOT
    root = os.path.abspath(root)
    exists = os.path.isdir(root)
    sku_dirs_count = 0
    if exists:
        try:
            sku_dirs_count = len([name for name in os.listdir(root) if os.path.isdir(os.path.join(root, name))])
        except Exception:
            sku_dirs_count = 0
    return {
        "root": root,
        "exists": exists,
        "sku_dirs_count": sku_dirs_count,
    }


def _chunk_list(values, chunk_size):
    for i in range(0, len(values), chunk_size):
        yield values[i:i + chunk_size]


def _build_oscn_substitute_sql_preview(skus):
    if not skus:
        return "SELECT Substitute FROM OSCN WHERE 1 = 0;"

    quoted = []
    for sku in skus:
        safe = str(sku).replace("'", "''")
        quoted.append(f"N'{safe}'")

    values_sql = ", ".join(quoted)
    return f"SELECT Substitute FROM OSCN WHERE Substitute IN ({values_sql});"


def _build_oitm_suppcatnum_sql_preview(skus):
    if not skus:
        return "SELECT SuppCatNum FROM OITM WHERE 1 = 0;"

    quoted = []
    for sku in skus:
        safe = str(sku).replace("'", "''")
        quoted.append(f"N'{safe}'")

    values_sql = ", ".join(quoted)
    return f"SELECT SuppCatNum FROM OITM WHERE SuppCatNum IN ({values_sql});"


def _resolve_sap_supplier_code(mg_supplier_name):
    name = str(mg_supplier_name or "").strip()
    if not name:
        return ""

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT card_code
            FROM sap_suppliers
            WHERE LOWER(TRIM(mg_supplier_name)) = LOWER(TRIM(?))
            LIMIT 1
            """,
            (name,),
        )
        row = cursor.fetchone()
        if not row:
            return ""
        return str(row["card_code"] or "").strip()
    except Exception:
        return ""
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass


def _check_missing_oscn_substitutes(skus, parsed_products=None, supplier_name=""):
    normalized = []
    seen = set()
    for raw in skus or []:
        sku = str(raw or "").strip()
        if not sku:
            continue
        key = sku.upper()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(sku)

    sql_preview = _build_oscn_substitute_sql_preview(normalized)
    result = {
        "checked_count": len(normalized),
        "found_count": 0,
        "found_in_oscn_count": 0,
        "found_in_oitm_count": 0,
        "missing_count": 0,
        "missing_skus": [],
        "sql_preview": sql_preview,
        "sql_preview_oscn": sql_preview,
        "sql_preview_oitm": _build_oitm_suppcatnum_sql_preview(normalized),
        "driver": "",
        "report_path": "",
        "error": "",
    }

    product_map = {}
    for p in parsed_products or []:
        sku = str((p or {}).get("supplier_sku", "")).strip()
        if not sku:
            continue
        k = sku.upper()
        if k not in product_map:
            product_map[k] = {
                "supplier_sku": sku,
                "title": str((p or {}).get("title", "")).strip(),
                "price": float((p or {}).get("price", 0.0) or 0.0),
            }

    if not normalized:
        return result

    conn = None
    try:
        conn, used_driver = _open_sap_odbc_connection()
        result["driver"] = used_driver
        cursor = conn.cursor()

        found_in_oscn_upper = set()
        found_in_oitm_upper = set()
        for chunk in _chunk_list(normalized, 900):
            placeholders = ",".join(["?"] * len(chunk))
            cursor.execute(f"SELECT Substitute FROM OSCN WHERE Substitute IN ({placeholders})", chunk)
            for row in cursor.fetchall():
                val = row[0] if isinstance(row, (list, tuple)) else getattr(row, "Substitute", None)
                txt = str(val or "").strip()
                if txt:
                    found_in_oscn_upper.add(txt.upper())

        for chunk in _chunk_list(normalized, 900):
            placeholders = ",".join(["?"] * len(chunk))
            cursor.execute(f"SELECT SuppCatNum FROM OITM WHERE SuppCatNum IN ({placeholders})", chunk)
            for row in cursor.fetchall():
                val = row[0] if isinstance(row, (list, tuple)) else getattr(row, "SuppCatNum", None)
                txt = str(val or "").strip()
                if txt:
                    found_in_oitm_upper.add(txt.upper())

        found_in_any_upper = found_in_oscn_upper.union(found_in_oitm_upper)
        missing = [sku for sku in normalized if sku.upper() not in found_in_any_upper]
        result["found_in_oscn_count"] = len([sku for sku in normalized if sku.upper() in found_in_oscn_upper])
        result["found_in_oitm_count"] = len([sku for sku in normalized if sku.upper() in found_in_oitm_upper])
        result["found_count"] = len(normalized) - len(missing)
        result["missing_count"] = len(missing)
        result["missing_skus"] = missing[:300]

        if missing:
            os.makedirs(r"C:\TEMP", exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_supplier = str(supplier_name or "UNKNOWN").replace("/", "-").replace("\\", "-").replace(" ", "_")
            report_path = fr"C:\TEMP\OSCN_MISSING_SUBSTITUTES_{safe_supplier}_{ts}.txt"
            report_meta_path = fr"C:\TEMP\OSCN_MISSING_SUBSTITUTES_{safe_supplier}_{ts}.json"
            sap_supplier_code = _resolve_sap_supplier_code(supplier_name)

            with open(report_path, "w", encoding="windows-1255", errors="replace") as f:
                for sku in missing:
                    details = product_map.get(sku.upper(), {})
                    supplier_sku = str(details.get("supplier_sku", sku)).replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()
                    title = str(details.get("title", "")).replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()
                    price = float(details.get("price", 0.0) or 0.0)
                    calc_price = str(int(round(price)))
                    row = [
                        sap_supplier_code,
                        supplier_sku,
                        title,
                        "77",
                        "ציוד היקפי למחשבים",
                        "3",
                        calc_price,
                        "₪",
                    ]
                    f.write("\t".join(row) + "\n")
            with open(report_meta_path, "w", encoding="utf-8") as meta_file:
                json.dump(
                    {
                        "supplier_name": supplier_name,
                        "sap_supplier_code": sap_supplier_code,
                        "checked_count": result["checked_count"],
                        "found_count": result["found_count"],
                        "found_in_oscn_count": result["found_in_oscn_count"],
                        "found_in_oitm_count": result["found_in_oitm_count"],
                        "missing_count": result["missing_count"],
                        "missing_skus": result["missing_skus"],
                        "sql_preview_oscn": result["sql_preview_oscn"],
                        "sql_preview_oitm": result["sql_preview_oitm"],
                        "report_path": report_path,
                    },
                    meta_file,
                    ensure_ascii=False,
                    indent=2,
                )
            result["report_path"] = report_path
            result["report_meta_path"] = report_meta_path
    except Exception as ex:
        result["error"] = str(ex)
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass

    return result

def init_db():
    print(f"[Init] Connecting to database {DB_PATH} to verify schemas...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingestion_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT,
                end_time TEXT,
                mode TEXT,
                total_products INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                skipped_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                incomplete_attributes_count INTEGER DEFAULT 0,
                total_duration REAL DEFAULT 0.0,
                total_chatgpt_wait REAL DEFAULT 0.0,
                categories_summary TEXT,
                status TEXT DEFAULT 'running'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS category_manual_updates (
                mg_id TEXT PRIMARY KEY,
                old_category_code TEXT,
                new_category_code TEXT,
                updated_at TEXT,
                applied INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sap_suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_code TEXT UNIQUE,
                sap_name TEXT,
                mg_supplier_name TEXT,
                updated_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automated_processes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                script_path TEXT,
                interval_value INTEGER DEFAULT 5,
                interval_unit TEXT DEFAULT 'minutes',
                enabled INTEGER DEFAULT 1,
                last_run_at TEXT,
                next_run_at TEXT,
                last_status TEXT,
                last_message TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        _ensure_default_automated_processes(cursor)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS supplier_intake_analysis_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                supplier_name TEXT NOT NULL,
                supplier_sku TEXT,
                title TEXT,
                price REAL,
                stock INTEGER,
                sap_item_code TEXT,
                sap_item_name TEXT,
                sap_on_hand REAL,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_intake_cache_session ON supplier_intake_analysis_cache(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_intake_cache_supplier ON supplier_intake_analysis_cache(supplier_name)")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS supplier_intake_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL UNIQUE,
                supplier_name TEXT NOT NULL,
                total_count INTEGER DEFAULT 0,
                new_count INTEGER DEFAULT 0,
                updated_price_count INTEGER DEFAULT 0,
                unchanged_count INTEGER DEFAULT 0,
                original_file_path TEXT,
                calculated_file_path TEXT,
                mg_new_products_file_path TEXT,
                ingestion_date TEXT,
                source_kind TEXT DEFAULT 'analysis'
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_supplier_intake_history_supplier ON supplier_intake_history(supplier_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_supplier_intake_history_date ON supplier_intake_history(ingestion_date)")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS supplier_field_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_name TEXT NOT NULL,
                supplier_key TEXT NOT NULL UNIQUE,
                tabs_json TEXT NOT NULL DEFAULT '[]',
                category_margins_json TEXT NOT NULL DEFAULT '{}',
                category_import_toggles_json TEXT NOT NULL DEFAULT '{}',
                brand_import_toggles_json TEXT NOT NULL DEFAULT '{}',
                last_sample_file TEXT,
                updated_at TEXT
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_supplier_field_mappings_name ON supplier_field_mappings(supplier_name)")
        _migrate_supplier_field_mappings_legacy_json_to_db_if_needed(cursor)
        _ensure_default_supplier_field_mappings_in_db(cursor)

        # Product sync timeline migration: each product will store last sync datetime.
        cursor.execute("PRAGMA table_info(products)")
        product_cols = {str(row[1]).strip().lower() for row in cursor.fetchall()}
        if "last_sync_at" not in product_cols:
            cursor.execute("ALTER TABLE products ADD COLUMN last_sync_at TEXT")
        if "image_1" not in product_cols:
            cursor.execute("ALTER TABLE products ADD COLUMN image_1 TEXT")
        if "image_2" not in product_cols:
            cursor.execute("ALTER TABLE products ADD COLUMN image_2 TEXT")
        if "image_3" not in product_cols:
            cursor.execute("ALTER TABLE products ADD COLUMN image_3 TEXT")
        if "image_4" not in product_cols:
            cursor.execute("ALTER TABLE products ADD COLUMN image_4 TEXT")
        if "image_5" not in product_cols:
            cursor.execute("ALTER TABLE products ADD COLUMN image_5 TEXT")
        if "is_deleted" not in product_cols:
            cursor.execute("ALTER TABLE products ADD COLUMN is_deleted INTEGER DEFAULT 0")
        if "is_preupload" not in product_cols:
            cursor.execute("ALTER TABLE products ADD COLUMN is_preupload INTEGER DEFAULT 0")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Init] Error creating database tables: {e}")

def col_to_idx(col_str):
    """Convert Excel-style column name (e.g. 'A', 'Z', 'AA', 'IR') to 0-based index."""
    idx = 0
    for char in col_str.upper():
        idx = idx * 26 + (ord(char) - ord('A') + 1)
    return idx - 1


def _detect_csv_delimiter(text):
    sample = str(text or "")
    if not sample:
        return ","
    first_line = sample.splitlines()[0] if sample.splitlines() else sample
    candidates = [",", ";", "\t", "|"]
    best = ","
    best_count = -1
    for d in candidates:
        count = first_line.count(d)
        if count > best_count:
            best = d
            best_count = count
    return best if best_count > 0 else ","


def _resolve_csv_column_index(headers, col_val):
    if not col_val:
        return -1
    col_txt = str(col_val).strip()
    if not col_txt:
        return -1
    if col_txt.isalpha():
        return col_to_idx(col_txt)
    for idx, h in enumerate(headers or []):
        if str(h or "").strip().lower() == col_txt.lower():
            return idx
    return -1


def _normalize_preview_mapping_for_supplier(supplier_name, basic_mappings=None):
    mapping = dict(basic_mappings or {})
    entry = _get_supplier_field_mapping_entry(supplier_name)
    if entry:
        enabled_tabs = [t for t in (entry.get("tabs") or []) if t.get("tab_enabled")]
        chosen_tab = enabled_tabs[0] if enabled_tabs else ((entry.get("tabs") or [None])[0])
        if chosen_tab and isinstance(chosen_tab.get("field_mapping"), dict):
            mapping.update(chosen_tab.get("field_mapping") or {})
    return mapping


def _get_supplier_preview_display_toggles(supplier_name):
    entry = _get_supplier_field_mapping_entry(supplier_name)
    if not entry:
        return {}
    enabled_tabs = [t for t in (entry.get("tabs") or []) if t.get("tab_enabled")]
    chosen_tab = enabled_tabs[0] if enabled_tabs else ((entry.get("tabs") or [None])[0])
    if chosen_tab and isinstance(chosen_tab.get("display_toggles"), dict):
        return dict(chosen_tab.get("display_toggles") or {})
    return {}


def _build_normalized_rows_from_csv_data(csv_data, supplier_name, mappings):
    if not str(csv_data or "").strip():
        return []

    stream = io.StringIO(csv_data)
    reader = csv.reader(stream, delimiter=_detect_csv_delimiter(csv_data))
    try:
        headers = next(reader)
    except StopIteration:
        return []

    merged_mapping = _normalize_preview_mapping_for_supplier(supplier_name, mappings)

    category_idx = _resolve_csv_column_index(headers, merged_mapping.get("category"))
    sub_category_idx = _resolve_csv_column_index(headers, merged_mapping.get("sub_category"))
    sub_sub_category_idx = _resolve_csv_column_index(headers, merged_mapping.get("sub_sub_category"))
    manufacturer_sku_idx = _resolve_csv_column_index(headers, merged_mapping.get("manufacturer_sku") or merged_mapping.get("supplier_sku"))
    supplier_sku_idx = _resolve_csv_column_index(headers, merged_mapping.get("supplier_sku"))
    title_idx = _resolve_csv_column_index(headers, merged_mapping.get("processed_title") or merged_mapping.get("title"))
    raw_price_idx = _resolve_csv_column_index(headers, merged_mapping.get("raw_price") or merged_mapping.get("price"))
    currency_idx = _resolve_csv_column_index(headers, merged_mapping.get("currency"))
    brand_idx = _resolve_csv_column_index(headers, merged_mapping.get("brand"))
    details_idx = _resolve_csv_column_index(headers, merged_mapping.get("details"))
    manufacturer_link_idx = _resolve_csv_column_index(headers, merged_mapping.get("manufacturer_link"))
    notes_idx = _resolve_csv_column_index(headers, merged_mapping.get("notes"))
    availability_idx = _resolve_csv_column_index(headers, merged_mapping.get("availability") or merged_mapping.get("stock"))

    rows = []
    for raw_row in reader:
        if not raw_row:
            continue

        def get_val(idx):
            if idx < 0 or idx >= len(raw_row):
                return ""
            return str(raw_row[idx] or "").strip()

        supplier_sku = get_val(supplier_sku_idx)
        manufacturer_sku = get_val(manufacturer_sku_idx) or supplier_sku
        title = get_val(title_idx)
        raw_price = _parse_numeric_price(get_val(raw_price_idx)) or 0.0
        currency = get_val(currency_idx)
        availability = get_val(availability_idx)
        category = get_val(category_idx)
        sub_category = get_val(sub_category_idx)
        sub_sub_category = get_val(sub_sub_category_idx)
        brand = get_val(brand_idx)
        details = get_val(details_idx)
        manufacturer_link = get_val(manufacturer_link_idx)
        notes = get_val(notes_idx)

        if not supplier_sku and not title and not raw_price:
            continue

        # Intake flow should only include available products from supplier file.
        if not _is_available_status(availability):
            continue

        margin = _get_techno_margin(category, brand)
        needs_margin_decision = margin is None
        if margin is None:
            margin = TECHNO_UNKNOWN_CATEGORY_DEFAULT_MARGIN

        final_price = _calculate_price_with_vat_and_margin(raw_price, margin) if raw_price > 0 else 0

        rows.append({
            "tab_name": "CSV",
            "category": category,
            "sub_category": sub_category,
            "sub_sub_category": sub_sub_category,
            "manufacturer_sku": manufacturer_sku,
            "supplier_sku": supplier_sku,
            "processed_title": title,
            "raw_price": float(raw_price),
            "currency": currency,
            "margin": float(margin),
            "final_price": float(final_price),
            "brand": brand,
            "details": details,
            "notes": notes,
            "availability": availability,
            "manufacturer_link": manufacturer_link,
            "needs_margin_decision": needs_margin_decision,
            "category_key": _category_key(category, sub_category, sub_sub_category),
        })

    return rows

def export_supplier_csv():
    print("[Scheduler] Running daily CSV export...")
    try:
        import csv
        import os
        import sqlite3
        
        # Ensure C:\TEMP exists
        os.makedirs(r"C:\TEMP", exist_ok=True)
        dest_path = r"C:\TEMP\exp_sup.csv"
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Select all valid products where stock > 1 or stock = 9999 (unlimited)
        cursor.execute("""
            SELECT sap_sku, price FROM products
            WHERE is_valid = 1 AND sap_sku IS NOT NULL AND sap_sku != ''
              AND (stock > 1 OR stock = 9999 OR stock = -1)
        """)
        rows = cursor.fetchall()
        
        with open(dest_path, "w", newline="", encoding="windows-1255", errors="replace") as f:
            writer = csv.writer(f)
            for row in rows:
                # 4 fields: SKU, 3, Price, ₪
                writer.writerow([row[0], "3", str(row[1]), "₪"])
                
        conn.close()
        print(f"[Scheduler] Daily CSV export completed successfully: {dest_path} ({len(rows)} products exported)")
    except Exception as e:
        print(f"[Scheduler] Error running daily CSV export: {e}")

last_export_date = None

def daily_exporter_loop():
    global last_export_date
    from datetime import datetime
    import time
    while True:
        try:
            now = datetime.now()
            current_date = now.date()
            # If current time is past 7:00 AM and we haven't run today
            if now.hour >= 7:
                if last_export_date != current_date:
                    export_supplier_csv()
                    last_export_date = current_date
        except Exception as e:
            print(f"[Scheduler] Error in daily exporter loop: {e}")
        time.sleep(60)


def _execute_automated_process(process_row, reason="scheduled"):
    process_id = int(process_row.get("id"))

    with automated_processes_lock:
        if process_id in automated_processes_running:
            return
        automated_processes_running.add(process_id)

    status = "failed"
    message = ""
    started_at = datetime.now()

    try:
        raw_script_path = str(process_row.get("script_path") or "").strip()
        if not raw_script_path:
            raise RuntimeError("script_path is empty")

        if os.path.isabs(raw_script_path):
            script_path = raw_script_path
        else:
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), raw_script_path)

        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script file was not found: {script_path}")

        start_label = started_at.strftime("%Y-%m-%d %H:%M:%S")
        with open(process_log_file, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"\n[Automations] {start_label} running '{process_row.get('name')}' ({reason}) -> {script_path}\n")

        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        with open(process_log_file, "a", encoding="utf-8", errors="replace") as f:
            if result.stdout:
                f.write(result.stdout + ("\n" if not result.stdout.endswith("\n") else ""))
            if result.stderr:
                f.write("[Automations][stderr]\n" + result.stderr + ("\n" if not result.stderr.endswith("\n") else ""))

        status = "success" if result.returncode == 0 else "failed"
        if result.returncode == 0:
            message = "Completed successfully"
        else:
            message = (result.stderr or result.stdout or f"Exit code {result.returncode}").strip()[:1000]
    except Exception as ex:
        status = "failed"
        message = str(ex)[:1000]
        with open(process_log_file, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"[Automations][Error] {message}\n")
    finally:
        finished_at = datetime.now()
        next_run_at = _compute_next_run_at(process_row, finished_at)

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE automated_processes
                SET last_run_at = ?,
                    next_run_at = ?,
                    last_status = ?,
                    last_message = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    finished_at.isoformat(),
                    next_run_at.isoformat(),
                    status,
                    message,
                    finished_at.isoformat(),
                    process_id,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as db_ex:
            print(f"[Automations] Failed to update process {process_id} status: {db_ex}")

        with automated_processes_lock:
            automated_processes_running.discard(process_id)


def _launch_automated_process(process_row, reason="scheduled"):
    t = threading.Thread(target=_execute_automated_process, args=(process_row, reason), daemon=True)
    t.start()


def automated_processes_loop():
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, script_path, interval_value, interval_unit, enabled, next_run_at
                FROM automated_processes
                WHERE enabled = 1
                """
            )
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()

            now = datetime.now()
            for row in rows:
                process_id = int(row.get("id") or 0)
                if process_id <= 0:
                    continue

                with automated_processes_lock:
                    if process_id in automated_processes_running:
                        continue

                next_run = _parse_iso_datetime(row.get("next_run_at"))
                if next_run is None or next_run <= now:
                    _launch_automated_process(row, reason="scheduled")
        except Exception as e:
            print(f"[Automations] Scheduler loop error: {e}")

        time.sleep(30)

class ProductManagerHandler(http.server.SimpleHTTPRequestHandler):
    
    def log_message(self, format, *args):
        # Suppress default request logging to keep console clean
        pass

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # API Endpoints
        if path == "/api/categories":
            self.get_categories()
        elif path == "/api/products":
            self.get_products(query)
        elif path == "/api/brands":
            self.get_brands()
        elif path.startswith("/api/product/"):
            # GET /api/product/<id>
            product_id = path.split("/")[-1]
            self.get_product_details(product_id)
        elif path == "/api/attributes_schema":
            self.get_attributes_schema()
        elif path == "/api/ingestion/status":
            self.get_ingestion_status()
        elif path == "/api/ingestion/logs":
            self.get_ingestion_logs()
        elif path == "/api/desktop-replacement/logs":
            self.get_desktop_replacement_logs()
        elif path == "/api/ingestion/runs":
            self.get_ingestion_runs()
        elif path == "/api/dashboard/stats":
            self.get_dashboard_stats()
        elif path == "/api/audit/results":
            self.get_audit_results()
        elif path == "/api/supplier/ingestions/history":
            self.get_supplier_ingestions_history()
        elif path == "/api/supplier/history/file":
            self.get_supplier_history_file(query)
        elif path == "/api/supplier/intake/complete-sap/status":
            self.get_intake_sap_completion_status(query)
        elif path == "/api/health/version":
            self.get_health_version()
        elif path == "/api/suppliers/contacts":
            self.get_suppliers_contacts()
        elif path == "/api/suppliers/catalog":
            self.get_suppliers_catalog()
        elif path == "/api/sap/suppliers":
            self.get_sap_suppliers()
        elif path == "/api/sap/salespersons":
            self.get_sap_salespersons()
        elif path == "/api/sap/sales-report":
            self.get_sap_sales_report(query)
        elif path == "/api/category/manual/pending":
            self.get_category_manual_pending()
        elif path == "/api/supplier/scripts":
            self.get_supplier_scripts()
        elif path == "/api/supplier/pricelist/scripts":
            self.get_supplier_pricelist_scripts()
        elif path == "/api/supplier/pricelist/field-mappings":
            self.get_supplier_field_mappings(query)
        elif path == "/api/supplier/pricelist/inspect-sample":
            self.inspect_supplier_pricelist_sample(query)
        elif path == "/api/images/storage/status":
            self.get_images_storage_status(query)
        elif path == "/api/images/extraction/config":
            self.get_images_extraction_config()
        elif path == "/api/mg/import/progress":
            self.get_mg_import_progress()
        elif path == "/api/mg/export":
            self.export_mg_csv(query)
        elif path == "/api/reports/errors":
            self.get_reports_errors()
        elif path == "/api/desktop-replacement/resolve":
            self.resolve_desktop_replacement_product(query)
        elif path == "/api/processes":
            self.get_automated_processes()
        elif path.startswith("/api/settings") or path == "/api/supplier/settings":
            self.get_app_settings()
        # Serve static HTML/CSS/JS
        elif path == "/" or path == "/index.html":
            self.serve_file("index.html", "text/html")
        elif path == "/style.css":
            self.serve_file("style.css", "text/css")
        elif path == "/app.js":
            self.serve_file("app.js", "application/javascript")
        else:
            if path.startswith("/api/"):
                self.send_error_response(404, f"Unknown API endpoint: {path}")
                return
            # Default fallback to serve files in current directory or 404
            super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path.startswith("/api/product/") and path.endswith("/update"):
            # POST /api/product/<id>/update
            self.update_product()
        elif path == "/api/parameters/scrape":
            self.start_parameter_scrape()
        elif path == "/api/audit/start":
            self.start_audit()
        elif path == "/api/reports/generate":
            self.start_price_check()
        elif path == "/api/supplier/analyze":
            self.analyze_supplier_csv()
        elif path == "/api/supplier/import":
            self.import_supplier_changes()
        elif path == "/api/supplier/export-5col":
            self.export_supplier_5col_file()
        elif path == "/api/supplier/intake/export-sap" or path.startswith("/api/supplier/intake/export-sap/"):
            self.export_supplier_sap_intake_from_session()
        elif path == "/api/supplier/intake/complete-sap":
            self.complete_intake_sap_skus()
        elif path == "/api/ingestion/start":
            self.start_ingestion()
        elif path == "/api/ingestion/stop":
            self.stop_ingestion()
        elif path == "/api/suppliers/contacts/update":
            self.update_suppliers_contacts()
        elif path == "/api/suppliers/contacts/create":
            self.create_supplier_contact()
        elif path == "/api/sap/suppliers/update":
            self.update_sap_supplier_mapping()
        elif path == "/api/sap/suppliers/create":
            self.create_sap_supplier_mapping()
        elif path == "/api/sap/suppliers/delete":
            self.delete_sap_supplier_mapping()
        elif path == "/api/sap/suppliers/import":
            self.import_sap_suppliers()
        elif path == "/api/category/manual/update":
            self.update_manual_category()
        elif path == "/api/supplier/scripts/update":
            self.update_supplier_script()
        elif path == "/api/supplier/pricelist/scripts/update":
            self.update_supplier_pricelist_script()
        elif path == "/api/supplier/pricelist/inspect-sample":
            self.inspect_supplier_pricelist_sample()
        elif path == "/api/supplier/pricelist/field-mappings/update":
            self.update_supplier_field_mappings()
        elif path == "/api/images/storage/ensure":
            self.ensure_images_storage()
        elif path == "/api/images/extraction/start":
            self.start_images_extraction()
        elif path == "/api/mg/import":
            self.import_mg_csv()
        elif path == "/api/mg/export/full":
            self.export_mg_full_csv()
        elif path == "/api/mg/import/start":
            self.start_mg_import()
        elif path == "/api/supplier/sync":
            self.sync_supplier()
        elif path == "/api/reports/errors/clear":
            self.clear_reports_errors()
        elif path == "/api/supplier/export":
            self.export_supplier_prices()
        elif path == "/api/sap/oscn/export":
            self.export_sap_oscn_sql()
        elif path == "/api/desktop-replacement/scan":
            self.scan_desktop_replacement_candidates()
        elif path == "/api/desktop-replacement/apply":
            self.apply_desktop_replacement_candidates()
        elif path == "/api/desktop-replacement/stop":
            self.stop_desktop_replacement_scan()
        elif path == "/api/sap/sales-report/sheets-sync":
            self.sync_sap_sales_report_to_sheets()
        elif path == "/api/processes/create":
            self.create_automated_process()
        elif path == "/api/processes/update":
            self.update_automated_process()
        elif path == "/api/processes/delete":
            self.delete_automated_process()
        elif path == "/api/processes/run-now":
            self.run_automated_process_now()
        elif path.startswith("/api/settings/update") or path == "/api/supplier/settings/update":
            self.update_app_settings()
        elif path == "/api/products/bulk-action":
            self.bulk_update_products()
        else:
            self.send_error_response(404, "Not Found")

    def _cache_latest_supplier_intake_rows(self, supplier_name, parsed_products):
        supplier = str(supplier_name or "").strip()
        if not supplier:
            return None

        rows = []
        for p in parsed_products or []:
            sku = str((p or {}).get("supplier_sku", "")).strip()
            if not sku:
                continue
            title = str((p or {}).get("title", "")).strip()
            try:
                price = float((p or {}).get("price", 0.0) or 0.0)
            except Exception:
                price = 0.0
            try:
                stock = int((p or {}).get("stock", 0) or 0)
            except Exception:
                stock = 0
            rows.append((sku, title, price, stock))

        if not rows:
            return None

        session_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
        now_txt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO supplier_intake_analysis_cache (
                session_id, supplier_name, supplier_sku, title, price, stock, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [(session_id, supplier, sku, title, price, stock, now_txt, now_txt) for (sku, title, price, stock) in rows],
        )
        conn.commit()
        conn.close()
        return session_id

    def _record_supplier_intake_history(self, session_id, supplier_name, total_count, new_count, updated_price_count, unchanged_count, ingestion_date=None, original_file_path="", calculated_file_path="", mg_new_products_file_path="", source_kind="analysis"):
        session_id = str(session_id or "").strip()
        supplier_name = str(supplier_name or "").strip()
        if not session_id or not supplier_name:
            return

        when_txt = str(ingestion_date or "").strip() or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO supplier_intake_history (
                session_id, supplier_name, total_count, new_count, updated_price_count, unchanged_count,
                original_file_path, calculated_file_path, mg_new_products_file_path, ingestion_date, source_kind
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                supplier_name = excluded.supplier_name,
                total_count = excluded.total_count,
                new_count = excluded.new_count,
                updated_price_count = excluded.updated_price_count,
                unchanged_count = excluded.unchanged_count,
                original_file_path = excluded.original_file_path,
                calculated_file_path = excluded.calculated_file_path,
                mg_new_products_file_path = excluded.mg_new_products_file_path,
                ingestion_date = excluded.ingestion_date,
                source_kind = excluded.source_kind
            """,
            (
                session_id,
                supplier_name,
                int(total_count or 0),
                int(new_count or 0),
                int(updated_price_count or 0),
                int(unchanged_count or 0),
                str(original_file_path or "").strip(),
                str(calculated_file_path or "").strip(),
                str(mg_new_products_file_path or "").strip(),
                when_txt,
                str(source_kind or "analysis").strip() or "analysis",
            ),
        )
        conn.commit()
        conn.close()

    def _backfill_supplier_intake_history_from_cache(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT session_id,
                   supplier_name,
                   COUNT(*) AS total_count,
                   MIN(COALESCE(created_at, updated_at, '')) AS created_at
            FROM supplier_intake_analysis_cache
            WHERE TRIM(COALESCE(session_id, '')) != ''
            GROUP BY session_id, supplier_name
            """
        )
        rows = cursor.fetchall()
        for row in rows:
            cursor.execute("SELECT 1 FROM supplier_intake_history WHERE session_id = ? LIMIT 1", (str(row["session_id"] or "").strip(),))
            if cursor.fetchone():
                continue
            cursor.execute(
                """
                INSERT INTO supplier_intake_history (
                    session_id, supplier_name, total_count, new_count, updated_price_count, unchanged_count,
                    original_file_path, calculated_file_path, mg_new_products_file_path, ingestion_date, source_kind
                ) VALUES (?, ?, ?, 0, 0, 0, '', '', '', ?, 'analysis_cache_backfill')
                """,
                (
                    str(row["session_id"] or "").strip(),
                    str(row["supplier_name"] or "").strip(),
                    int(row["total_count"] or 0),
                    str(row["created_at"] or "").strip() or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
        conn.commit()
        conn.close()

    def _get_latest_intake_session(self, supplier_name):
        supplier = str(supplier_name or "").strip()
        if not supplier:
            return None
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT session_id
            FROM supplier_intake_analysis_cache
            WHERE LOWER(TRIM(supplier_name)) = LOWER(TRIM(?))
            ORDER BY id DESC
            LIMIT 1
            """,
            (supplier,),
        )
        row = cursor.fetchone()
        conn.close()
        return str(row[0]) if row and row[0] is not None else None

    def serve_file(self, filename, content_type):
        candidates = []
        if os.path.isabs(filename):
            candidates.append(filename)
        else:
            candidates.append(os.path.join(BASE_DIR, filename))
            candidates.append(os.path.join(os.getcwd(), filename))
            candidates.append(os.path.join(os.path.dirname(sys.argv[0] or ""), filename))
            # Hard fallback for relocated workspace root on Windows.
            candidates.append(os.path.join(r"C:\PROJECTS\KINGGAMES\king_games_product_manager", filename))

        file_path = None
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                file_path = candidate
                break

        if not file_path:
            checked = [c for c in candidates if c]
            self.send_error_response(404, f"File {filename} not found. Checked: {checked}")
            return
        
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        # Disable caching for easy development
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.end_headers()
        
        with open(file_path, 'rb') as f:
            self.wfile.write(f.read())

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode('utf-8'))

    def get_categories(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Query categories with product counts
            cursor.execute("""
                SELECT c.id, c.name, c.parent, c.is_valid, COUNT(p.mg_id) as count
                FROM categories c
                LEFT JOIN products p ON c.id = p.category_code
                GROUP BY c.id
                ORDER BY c.parent, c.name
            """)
            
            cats = []
            for row in cursor.fetchall():
                cats.append({
                    "id": row[0],
                    "name": row[1],
                    "parent": row[2],
                    "is_valid": row[3],
                    "product_count": row[4]
                })
            
            conn.close()
            self.send_json_response(cats)
        except Exception as e:
            self.send_error_response(500, f"Database error: {e}")

    def get_products(self, query):
        try:
            category = query.get("category", [""])[0]
            brand = query.get("brand", [""])[0]
            search = query.get("search", [""])[0]
            stock_status = query.get("stock_status", [""])[0]
            include_deleted = str(query.get("include_deleted", ["0"])[0] or "0").strip() == "1"
            page = int(query.get("page", [1])[0])
            limit = int(query.get("limit", [50])[0])
            offset = (page - 1) * limit
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""
                                UPDATE category_manual_updates
                                SET applied = 1
                                WHERE applied = 0
                                    AND EXISTS (
                                        SELECT 1 FROM products p
                                        WHERE p.mg_id = category_manual_updates.mg_id
                                            AND p.category_code = category_manual_updates.new_category_code
                                            AND p.sync_flag = 1
                                    )
                        """)
            conn.commit()
            
            # Build query
            where_clauses = []
            params = []
            
            if category:
                where_clauses.append("category_code = ?")
                params.append(category)

            if brand:
                where_clauses.append("brand_code = ?")
                params.append(brand)

            if not include_deleted:
                where_clauses.append("COALESCE(is_deleted, 0) = 0")
                
            if stock_status == "instock":
                where_clauses.append("stock > 0")
            elif stock_status == "outofstock":
                where_clauses.append("stock = 0")
                
            if search:
                where_clauses.append("""
                    (
                        title LIKE ? OR
                        sap_sku LIKE ? OR
                        CAST(mg_id AS TEXT) LIKE ? OR
                        supplier1_sku LIKE ? OR
                        supplier2_sku LIKE ? OR
                        supplier3_sku LIKE ? OR
                        short_desc LIKE ? OR
                        full_desc LIKE ?
                    )
                """)
                for _ in range(8):
                    params.append(f"%{search}%")
                
            where_str = ""
            if where_clauses:
                where_str = "WHERE " + " AND ".join(where_clauses)
                
            # Count total
            cursor.execute(f"SELECT COUNT(*) FROM products {where_str}", params)
            total = cursor.fetchone()[0]
            
            # Get products
            cursor.execute(f"""
                  SELECT p.mg_id, p.title, p.sap_sku, p.price, p.original_price, p.stock, p.category_code, p.brand_code, p.sync_flag, p.is_valid,
                      COALESCE(p.is_deleted, 0), COALESCE(p.is_preupload, 0), COALESCE(p.image_1, ''),
                       cmu.new_category_code, cmu.applied
                FROM products p
                LEFT JOIN category_manual_updates cmu ON cmu.mg_id = p.mg_id AND cmu.applied = 0
                {where_str.replace('category_code', 'p.category_code').replace('title', 'p.title').replace('sap_sku', 'p.sap_sku').replace('mg_id', 'p.mg_id').replace('stock', 'p.stock')}
                LIMIT ? OFFSET ?
            """, params + [limit, offset])
            
            products = []
            for row in cursor.fetchall():
                products.append({
                    "mg_id": row[0],
                    "title": row[1],
                    "sap_sku": row[2],
                    "price": row[3],
                    "original_price": row[4],
                    "stock": row[5],
                    "category_code": row[6],
                    "brand_code": row[7],
                    "sync_flag": row[8],
                    "is_valid": row[9],
                    "is_deleted": int(row[10] or 0),
                    "is_preupload": int(row[11] or 0),
                    "thumb": row[12] or "",
                    "manual_new_category_code": row[13],
                    "manual_category_pending": bool(row[13]) and int(row[14] or 0) == 0
                })
                
            conn.close()
            
            pages = (total + limit - 1) // limit
            self.send_json_response({
                "products": products,
                "total": total,
                "page": page,
                "pages": pages,
                "limit": limit
            })
        except Exception as e:
            self.send_error_response(500, f"Database error: {e}")

    def get_brands(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT DISTINCT TRIM(COALESCE(brand_code, ''))
                FROM products
                WHERE TRIM(COALESCE(brand_code, '')) != ''
                ORDER BY TRIM(COALESCE(brand_code, ''))
                """
            )
            brands = [row[0] for row in cursor.fetchall() if str(row[0] or "").strip()]
            conn.close()
            self.send_json_response({"brands": brands, "count": len(brands)})
        except Exception as e:
            self.send_error_response(500, f"Error getting brands: {e}")

    def get_product_details(self, product_id):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get product details
            cursor.execute("""
                SELECT mg_id, title, zap_title, short_desc, full_desc, extra_info,
                       category_code, sap_sku, price, original_price, stock,
                       brand_code, sync_flag, is_valid,
                       supplier1_name, supplier1_sku, supplier1_price, supplier1_stock,
                       supplier2_name, supplier2_sku, supplier2_price, supplier2_stock,
                       supplier3_name, supplier3_sku, supplier3_price, supplier3_stock,
                       COALESCE(image_1, ''), COALESCE(image_2, ''), COALESCE(image_3, ''), COALESCE(image_4, ''), COALESCE(image_5, ''),
                       COALESCE(is_deleted, 0), COALESCE(is_preupload, 0)
                FROM products
                WHERE mg_id = ?
            """, (product_id,))
            
            prod_row = cursor.fetchone()
            if not prod_row:
                self.send_error_response(404, "Product not found")
                conn.close()
                return
                
            product = {
                "mg_id": prod_row[0],
                "title": prod_row[1],
                "zap_title": prod_row[2],
                "short_desc": prod_row[3],
                "full_desc": prod_row[4],
                "extra_info": prod_row[5],
                "category_code": prod_row[6],
                "sap_sku": prod_row[7],
                "price": prod_row[8],
                "original_price": prod_row[9],
                "stock": prod_row[10],
                "brand_code": prod_row[11],
                "sync_flag": prod_row[12],
                "is_valid": prod_row[13],
                "supplier1_name": prod_row[14],
                "supplier1_sku": prod_row[15],
                "supplier1_price": prod_row[16],
                "supplier1_stock": prod_row[17],
                "supplier2_name": prod_row[18],
                "supplier2_sku": prod_row[19],
                "supplier2_price": prod_row[20],
                "supplier2_stock": prod_row[21],
                "supplier3_name": prod_row[22],
                "supplier3_sku": prod_row[23],
                "supplier3_price": prod_row[24],
                "supplier3_stock": prod_row[25],
                "image_1": prod_row[26],
                "image_2": prod_row[27],
                "image_3": prod_row[28],
                "image_4": prod_row[29],
                "image_5": prod_row[30],
                "is_deleted": int(prod_row[31] or 0),
                "is_preupload": int(prod_row[32] or 0)
            }
            
            # Get populated attributes
            cursor.execute("""
                SELECT attribute_name, attribute_value
                FROM product_attributes
                WHERE product_id = ?
            """, (product_id,))
            
            attrs = {}
            for name, val in cursor.fetchall():
                attrs[name] = val
                
            product["attributes"] = attrs
            conn.close()
            
            self.send_json_response(product)
        except Exception as e:
            self.send_error_response(500, f"Database error: {e}")

    def get_attributes_schema(self):
        try:
            allowed_values = {}
            # Read allowed attributes values from DB tables
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.name, o.option_value
                    FROM cms_parameter_options o
                    JOIN cms_parameters p ON p.id = o.parameter_id
                """)
                for name, val in cursor.fetchall():
                    if name not in allowed_values:
                        allowed_values[name] = []
                    if val not in allowed_values[name]:
                        allowed_values[name].append(val)
                conn.close()
            except Exception as db_err:
                print(f"Error querying allowed values from DB: {db_err}")
                # Fallback to JSON file if DB query fails
                if os.path.exists(ALLOWED_VALUES_PATH):
                    with open(ALLOWED_VALUES_PATH, 'r', encoding='utf-8') as f:
                        allowed_values = json.load(f)
                else:
                    allowed_values = {}
                    
            # Read mappings schema
            if os.path.exists(MAPPING_SCHEMA_PATH):
                with open(MAPPING_SCHEMA_PATH, 'r', encoding='utf-8') as f:
                    mapping_schema = json.load(f)
            else:
                mapping_schema = {"attributes": []}
                
            self.send_json_response({
                "allowed_values": allowed_values,
                "mapping_schema": mapping_schema
            })
        except Exception as e:
            self.send_error_response(500, f"Error reading schema: {e}")

    def resolve_desktop_replacement_product(self, query):
        try:
            product_query = (query.get("query", [""]) or [""])[0].strip()
            if not product_query:
                self.send_error_response(400, "Missing query")
                return
            resolved = desktop_replace.resolve_product_reference(product_query)
            self.send_json_response({"success": True, "product": resolved})
        except Exception as e:
            self.send_error_response(500, f"Resolve error: {e}")

    def scan_desktop_replacement_candidates(self):
        global desktop_scan_running
        try:
            if desktop_scan_running:
                self.send_error_response(409, "Desktop replacement scan is already running")
                return

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            old_query = str(data.get("old_query", "")).strip()
            new_query = str(data.get("new_query", "")).strip()
            desktop_ids = data.get("desktop_ids") or []
            max_pages = int(data.get("max_pages", 5) or 5)

            if not old_query or not new_query:
                self.send_error_response(400, "Missing old_query or new_query")
                return

            desktop_scan_running = True
            desktop_scan_stop_requested.clear()

            with open(process_log_file, "w", encoding="utf-8", errors="replace") as log_fp:
                def write_scan_log(message):
                    ts = time.strftime("%H:%M:%S")
                    line = f"[DesktopScan {ts}] {message}"
                    print(line)
                    try:
                        log_fp.write(line + "\n")
                        log_fp.flush()
                    except Exception:
                        pass

                write_scan_log("Starting desktop replacement dry-run scan...")

                report = desktop_replace.scan_desktop_products_for_replacement(
                    old_query,
                    new_query,
                    target_product_ids=desktop_ids,
                    max_pages=max_pages,
                    logger=write_scan_log,
                    should_stop=desktop_scan_stop_requested.is_set,
                )

                if report.get("stopped"):
                    write_scan_log("Desktop replacement scan stopped by user.")
                elif report.get("load_failed_products"):
                    write_scan_log(
                        f"Desktop replacement scan completed with issues (load_failed={len(report.get('load_failed_products') or [])})."
                    )
                else:
                    write_scan_log("Desktop replacement scan finished successfully.")
            has_issues = bool(report.get("load_failed_products"))
            self.send_json_response({"success": not has_issues, "report": report})
        except Exception as e:
            self.send_error_response(500, f"Desktop replacement scan error: {e}")
        finally:
            desktop_scan_running = False
            desktop_scan_stop_requested.clear()

    def apply_desktop_replacement_candidates(self):
        global desktop_scan_running
        try:
            if desktop_scan_running:
                self.send_error_response(409, "Desktop replacement process is already running")
                return

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            old_query = str(data.get("old_query", "")).strip()
            new_query = str(data.get("new_query", "")).strip()
            desktop_ids = data.get("desktop_ids") or []
            max_pages = int(data.get("max_pages", 5) or 5)

            if not old_query or not new_query:
                self.send_error_response(400, "Missing old_query or new_query")
                return

            desktop_scan_running = True
            desktop_scan_stop_requested.clear()

            with open(process_log_file, "w", encoding="utf-8", errors="replace") as log_fp:
                def write_apply_log(message):
                    ts = time.strftime("%H:%M:%S")
                    line = f"[DesktopScan {ts}] {message}"
                    print(line)
                    try:
                        log_fp.write(line + "\n")
                        log_fp.flush()
                    except Exception:
                        pass

                write_apply_log("Starting desktop replacement APPLY run...")

                report = desktop_replace.run_desktop_products_replacement(
                    old_query,
                    new_query,
                    target_product_ids=desktop_ids,
                    max_pages=max_pages,
                    logger=write_apply_log,
                    should_stop=desktop_scan_stop_requested.is_set,
                    apply_changes=True,
                )

                if report.get("stopped"):
                    write_apply_log("Desktop replacement apply run stopped by user.")
                elif report.get("apply_failed_products") or report.get("load_failed_products") or report.get("verification_failed_products"):
                    write_apply_log(
                        "Desktop replacement apply run completed with issues "
                        f"(applied={len(report.get('applied_products') or [])}, "
                        f"verified={len(report.get('verified_products') or [])}, "
                        f"verify_failed={len(report.get('verification_failed_products') or [])}, "
                        f"apply_failed={len(report.get('apply_failed_products') or [])}, "
                        f"load_failed={len(report.get('load_failed_products') or [])})."
                    )
                elif not report.get("applied_products"):
                    write_apply_log("Desktop replacement apply run finished with no changes to save.")
                else:
                    write_apply_log("Desktop replacement apply run finished successfully.")
            has_issues = bool(
                report.get("load_failed_products")
                or report.get("apply_failed_products")
                or report.get("verification_failed_products")
            )
            self.send_json_response({"success": not has_issues, "report": report})
        except Exception as e:
            self.send_error_response(500, f"Desktop replacement apply error: {e}")
        finally:
            desktop_scan_running = False
            desktop_scan_stop_requested.clear()

    def stop_desktop_replacement_scan(self):
        if not desktop_scan_running:
            self.send_json_response({"success": True, "message": "אין סריקת מחשבים פעילה"})
            return

        try:
            desktop_scan_stop_requested.set()
            with open(process_log_file, "a", encoding="utf-8", errors="replace") as f:
                f.write(f"[DesktopScan {time.strftime('%H:%M:%S')}] [System] Stop requested by user.\n")
            self.send_json_response({"success": True, "message": "בקשת עצירה נשלחה לסריקת המחשבים"})
        except Exception as e:
            self.send_error_response(500, f"Error stopping desktop replacement scan: {e}")

    def get_desktop_replacement_logs(self):
        try:
            if not os.path.exists(process_log_file):
                self.send_json_response({"logs": ""})
                return

            with open(process_log_file, "r", encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()

            desktop_lines = [line for line in all_lines if "[DesktopScan" in line]
            self.send_json_response({"logs": "".join(desktop_lines)})
        except Exception as e:
            self.send_error_response(500, f"Error reading desktop replacement logs: {e}")

    def update_product(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            product_id = data.get("mg_id")
            title = data.get("title")
            sap_sku = data.get("sap_sku")
            price = float(data.get("price", 0.0))
            original_price = float(data.get("original_price", 0.0))
            stock = int(data.get("stock", 0))
            category_code = data.get("category_code")
            sync_flag = int(data.get("sync_flag", 0))
            is_valid = int(data.get("is_valid", 0))
            
            supplier1_name = data.get("supplier1_name", "")
            supplier1_sku = data.get("supplier1_sku", "")
            supplier1_price = float(data.get("supplier1_price", 0.0))
            supplier1_stock = data.get("supplier1_stock", "")
            
            supplier2_name = data.get("supplier2_name", "")
            supplier2_sku = data.get("supplier2_sku", "")
            supplier2_price = float(data.get("supplier2_price", 0.0))
            supplier2_stock = data.get("supplier2_stock", "")
            
            supplier3_name = data.get("supplier3_name", "")
            supplier3_sku = data.get("supplier3_sku", "")
            supplier3_price = float(data.get("supplier3_price", 0.0))
            supplier3_stock = data.get("supplier3_stock", "")

            image_1 = str(data.get("image_1", "") or "").strip()
            image_2 = str(data.get("image_2", "") or "").strip()
            image_3 = str(data.get("image_3", "") or "").strip()
            image_4 = str(data.get("image_4", "") or "").strip()
            image_5 = str(data.get("image_5", "") or "").strip()
            is_deleted = int(data.get("is_deleted", 0) or 0)
            is_preupload = int(data.get("is_preupload", 0) or 0)
            
            # Attributes to update
            attrs = data.get("attributes", {})
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Update product basic info
            cursor.execute("""
                UPDATE products
                SET title = ?, sap_sku = ?, price = ?, original_price = ?, stock = ?,
                    category_code = ?, sync_flag = ?, is_valid = ?,
                    supplier1_name = ?, supplier1_sku = ?, supplier1_price = ?, supplier1_stock = ?,
                    supplier2_name = ?, supplier2_sku = ?, supplier2_price = ?, supplier2_stock = ?,
                                        supplier3_name = ?, supplier3_sku = ?, supplier3_price = ?, supplier3_stock = ?,
                                        image_1 = ?, image_2 = ?, image_3 = ?, image_4 = ?, image_5 = ?,
                                        is_deleted = ?, is_preupload = ?
                WHERE mg_id = ?
            """, (title, sap_sku, price, original_price, stock, category_code, sync_flag, is_valid,
                  supplier1_name, supplier1_sku, supplier1_price, supplier1_stock,
                  supplier2_name, supplier2_sku, supplier2_price, supplier2_stock,
                                    supplier3_name, supplier3_sku, supplier3_price, supplier3_stock,
                                    image_1, image_2, image_3, image_4, image_5,
                                    is_deleted, is_preupload,
                  product_id))
            
            # Delete old attributes and insert new ones
            cursor.execute("DELETE FROM product_attributes WHERE product_id = ?", (product_id,))
            
            attr_inserts = []
            for name, val in attrs.items():
                val_str = str(val).strip()
                if val_str:
                    attr_inserts.append((product_id, name, val_str))
                    
            if attr_inserts:
                cursor.executemany("""
                    INSERT INTO product_attributes (product_id, attribute_name, attribute_value)
                    VALUES (?, ?, ?)
                """, attr_inserts)
                
            conn.commit()
            conn.close()
            
            # Also dynamically update allowed values JSON if the user entered a new value
            # (optional, keeps the schema updated)
            self.send_json_response({"success": True, "message": "המוצר עודכן בהצלחה"})
            
        except Exception as e:
            self.send_error_response(500, f"Error updating product: {e}")

    def bulk_update_products(self):
        try:
            content_length = int(self.headers.get('Content-Length', '0'))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(post_data.decode('utf-8'))

            action = str(data.get("action", "")).strip()
            mg_ids = [str(x).strip() for x in (data.get("mg_ids", []) or []) if str(x).strip()]

            if not mg_ids:
                self.send_error_response(400, "mg_ids is required")
                return

            if action == "queue_upload":
                self.send_json_response({"success": True, "updated": 0, "message": "Placeholder only - no backend action yet"})
                return

            update_sql = None
            if action == "mark_deleted":
                update_sql = "UPDATE products SET is_deleted = 1 WHERE mg_id IN ({})"
            elif action == "set_valid":
                update_sql = "UPDATE products SET is_valid = 1 WHERE mg_id IN ({})"
            elif action == "set_invalid":
                update_sql = "UPDATE products SET is_valid = 0 WHERE mg_id IN ({})"
            elif action == "set_preupload":
                update_sql = "UPDATE products SET is_preupload = 1 WHERE mg_id IN ({})"

            if not update_sql:
                self.send_error_response(400, "Unsupported action")
                return

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            placeholders = ",".join(["?"] * len(mg_ids))
            cursor.execute(update_sql.format(placeholders), mg_ids)
            updated = int(cursor.rowcount or 0)
            conn.commit()
            conn.close()

            self.send_json_response({"success": True, "updated": updated})
        except Exception as e:
            self.send_error_response(500, f"Error updating products in bulk: {e}")

    def get_ingestion_status(self):
        global current_process, process_type
        is_running = False
        if current_process is not None:
            if current_process.poll() is None:
                is_running = True
            else:
                current_process = None
                process_type = None
        
        # Get count of unsynced products
        unsynced_count = 0
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM products WHERE sync_flag = 0")
            unsynced_count = c.fetchone()[0]
            conn.close()
        except Exception:
            pass
            
        self.send_json_response({
            "is_running": is_running,
            "process_type": process_type,
            "unsynced_count": unsynced_count
        })

    def get_ingestion_logs(self):
        logs = ""
        if os.path.exists(process_log_file):
            try:
                with open(process_log_file, "r", encoding="utf-8", errors="replace") as f:
                    logs = f.read()
            except Exception as e:
                logs = f"Error reading log file: {e}"
        self.send_json_response({"logs": logs})

    def get_ingestion_runs(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, start_time, end_time, mode, total_products, success_count, skipped_count, failed_count, incomplete_attributes_count, total_duration, total_chatgpt_wait, categories_summary, status
                FROM ingestion_runs
                ORDER BY start_time DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            
            runs = []
            for r in rows:
                runs.append({
                    "id": r[0],
                    "start_time": r[1],
                    "end_time": r[2],
                    "mode": r[3],
                    "total_products": r[4],
                    "success_count": r[5],
                    "skipped_count": r[6],
                    "failed_count": r[7],
                    "incomplete_attributes_count": r[8],
                    "total_duration": r[9],
                    "total_chatgpt_wait": r[10],
                    "categories_summary": json.loads(r[11]) if r[11] else {},
                    "status": r[12]
                })
            self.send_json_response(runs)
        except Exception as e:
            self.send_error_response(500, f"Error getting runs history: {e}")

    def get_dashboard_stats(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            c.execute(
                """
                SELECT id, name, script_path, enabled, last_run_at, next_run_at, last_status
                FROM automated_processes
                ORDER BY id DESC
                """
            )
            process_rows = c.fetchall()

            with automated_processes_lock:
                running_ids = set(automated_processes_running)

            running_processes = []
            for row in process_rows:
                pid, name, script_path, enabled, last_run_at, next_run_at, last_status = row
                if int(pid or 0) in running_ids:
                    running_processes.append(
                        {
                            "id": pid,
                            "name": name,
                            "script_path": script_path,
                            "last_run_at": last_run_at,
                            "next_run_at": next_run_at,
                            "last_status": last_status,
                            "enabled": bool(enabled),
                        }
                    )

            last_process = None
            last_candidates = [r for r in process_rows if r[4]]
            if last_candidates:
                last_candidates.sort(key=lambda x: str(x[4]), reverse=True)
                row = last_candidates[0]
                last_process = {
                    "id": row[0],
                    "name": row[1],
                    "script_path": row[2],
                    "last_run_at": row[4],
                    "last_status": row[6],
                }

            next_process = None
            next_candidates = [r for r in process_rows if bool(r[3]) and r[5]]
            if next_candidates:
                next_candidates.sort(key=lambda x: str(x[5]))
                row = next_candidates[0]
                next_process = {
                    "id": row[0],
                    "name": row[1],
                    "script_path": row[2],
                    "next_run_at": row[5],
                }

            supplier_catalog = _build_unified_supplier_catalog()
            c.execute("SELECT id, name, interval_days FROM supplier_contacts")
            contact_rows = c.fetchall()
            contacts_map = {
                str(r[1] or "").strip().casefold(): {
                    "id": r[0],
                    "name": str(r[1] or "").strip(),
                    "interval_days": int(r[2] or 14),
                }
                for r in contact_rows
                if str(r[1] or "").strip()
            }

            c.execute(
                """
                SELECT supplier_name, MAX(ingestion_date) AS last_ingestion_date
                FROM supplier_ingestions
                GROUP BY supplier_name
                """
            )
            last_ingestions = c.fetchall()
            last_ing_map = {
                str(r[0] or "").strip().casefold(): str(r[1] or "").strip()
                for r in last_ingestions
                if str(r[0] or "").strip()
            }

            conn.close()

            due_pricelists = []
            now_dt = datetime.now()
            for item in supplier_catalog:
                name = str((item or {}).get("name", "")).strip()
                if not name:
                    continue
                key = name.casefold()
                interval_days = contacts_map.get(key, {}).get("interval_days", 14)
                last_ingestion = last_ing_map.get(key, "")

                reason = "never_ingested"
                days_since = None
                if last_ingestion:
                    try:
                        dt = datetime.strptime(last_ingestion[:19], "%Y-%m-%d %H:%M:%S")
                        diff_days = (now_dt - dt).days
                        days_since = diff_days
                        if diff_days >= 14:
                            reason = "older_than_two_weeks"
                        else:
                            continue
                    except Exception:
                        reason = "invalid_last_ingestion"

                due_pricelists.append(
                    {
                        "supplier": name,
                        "interval_days": interval_days,
                        "last_ingestion_date": last_ingestion or None,
                        "reason": reason,
                        "days_since_last": days_since,
                    }
                )

            today_sales = {
                "documents_count": 0,
                "total_amount": 0.0,
                "by_salesperson": [],
                "error": None,
            }
            sap_conn = None
            try:
                sap_conn, _ = _open_sap_odbc_connection()
                cur = sap_conn.cursor()
                day = datetime.now().strftime("%Y-%m-%d")
                cur.execute(
                    """
                    SELECT o.SlpCode, s.SlpName, COUNT(*) AS docs_count, SUM(o.DocTotalSy) AS total_amount
                    FROM ORDR o
                    LEFT JOIN OSLP s ON s.SlpCode = o.SlpCode
                    WHERE CONVERT(date, o.DocDate) = ?
                      AND o.CANCELED = 'N'
                    GROUP BY o.SlpCode, s.SlpName
                    ORDER BY total_amount DESC
                    """,
                    (day,),
                )
                rows = cur.fetchall()

                total_amount = 0.0
                total_docs = 0
                by_salesperson = []
                for row in rows:
                    docs_count = int(row[2] or 0)
                    amount = float(row[3] or 0.0)
                    total_docs += docs_count
                    total_amount += amount
                    by_salesperson.append(
                        {
                            "slp_code": int(row[0]) if row[0] is not None else None,
                            "slp_name": str(row[1] or "").strip() or "ללא שם",
                            "documents_count": docs_count,
                            "total_amount": amount,
                        }
                    )

                today_sales = {
                    "documents_count": total_docs,
                    "total_amount": total_amount,
                    "by_salesperson": by_salesperson,
                    "error": None,
                }
            except Exception as sap_ex:
                today_sales["error"] = str(sap_ex)
            finally:
                try:
                    if sap_conn is not None:
                        sap_conn.close()
                except Exception:
                    pass

            self.send_json_response(
                {
                    "running_processes": running_processes,
                    "last_process": last_process,
                    "next_process": next_process,
                    "product_agent_active": False,
                    "today_sales": today_sales,
                    "due_pricelists": due_pricelists,
                }
            )

        except Exception as e:
            self.send_error_response(500, f"Error getting dashboard stats: {e}")

    def get_audit_results(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # Ensure the table exists just in case
            c.execute("""
                CREATE TABLE IF NOT EXISTS category_audit (
                    category_code TEXT PRIMARY KEY,
                    category_name TEXT,
                    valid_count INTEGER,
                    invalid_count INTEGER,
                    last_checked TEXT
                )
            """)
            
            c.execute("SELECT category_code, category_name, valid_count, invalid_count, last_checked FROM category_audit")
            rows = c.fetchall()
            conn.close()
            
            results = []
            for r in rows:
                results.append({
                    "code": r[0],
                    "name": r[1],
                    "valid": r[2],
                    "invalid": r[3],
                    "last_checked": r[4]
                })
            self.send_json_response(results)
        except Exception as e:
            self.send_error_response(500, f"Error getting audit results: {e}")

    def start_audit(self):
        global current_process, process_type
        if current_process is not None and current_process.poll() is None:
            self.send_error_response(400, "תהליך אחר כבר רץ ברקע")
            return
            
        try:
            # Clear log file
            with open(process_log_file, "w", encoding="utf-8") as f:
                f.write("[System] Starting Product Validity Audit...\n")
                
            f_log = open(process_log_file, "a", encoding="utf-8")
            
            # Start process
            cmd = [sys.executable, "-u", "audit_cms_products.py"]
            current_process = subprocess.Popen(cmd, stdout=f_log, stderr=subprocess.STDOUT)
            process_type = "audit"
            
            self.send_json_response({"success": True, "message": "בדיקת תקינות מוצרים החלה ברקע"})
        except Exception as e:
            self.send_error_response(500, f"Error starting product audit: {e}")

    def start_price_check(self):
        global current_process, process_type
        if current_process is not None and current_process.poll() is None:
            self.send_error_response(400, "תהליך אחר כבר רץ ברקע")
            return
            
        try:
            # Clear log file
            with open(process_log_file, "w", encoding="utf-8") as f:
                f.write("[System] Starting Price Check and DB Refresh...\n")
                
            f_log = open(process_log_file, "a", encoding="utf-8")
            
            # Start process
            cmd = [sys.executable, "-u", "run_price_check.py"]
            current_process = subprocess.Popen(cmd, stdout=f_log, stderr=subprocess.STDOUT)
            process_type = "price_check"
            
            self.send_json_response({"success": True, "message": "השוואת מחירון החלה ברקע"})
        except Exception as e:
            self.send_error_response(500, f"Error starting price check: {e}")

    def start_parameter_scrape(self):
        global current_process, process_type
        if current_process is not None and current_process.poll() is None:
            self.send_error_response(400, "תהליך אחר כבר רץ ברקע")
            return
            
        try:
            # Clear log file
            with open(process_log_file, "w", encoding="utf-8") as f:
                f.write("[System] Starting Parameter Crawler...\n")
                
            f_log = open(process_log_file, "a", encoding="utf-8")
            
            # Start process
            cmd = [sys.executable, "-u", "scrape_cms_parameters.py"]
            current_process = subprocess.Popen(cmd, stdout=f_log, stderr=subprocess.STDOUT)
            process_type = "crawler"
            
            self.send_json_response({"success": True, "message": "סריקת מאפיינים החלה ברקע"})
        except Exception as e:
            self.send_error_response(500, f"Error starting crawler: {e}")

    def start_ingestion(self):
        global current_process, process_type, active_run_id
        if current_process is not None and current_process.poll() is None:
            self.send_error_response(400, "תהליך אחר כבר רץ ברקע")
            return
            
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            mode = data.get("mode", "all_unsynced") # "all_unsynced" or specific ids comma-separated
            runtime_flags = data.get("runtime_flags", {}) or {}
            
            # Create a run row in DB
            from datetime import datetime
            now_iso = datetime.now().isoformat()
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ingestion_runs (start_time, mode, status, categories_summary)
                VALUES (?, ?, 'running', '{}')
            """, (now_iso, str(mode)))
            run_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            active_run_id = run_id
            
            # Clear log file
            with open(process_log_file, "w", encoding="utf-8") as f:
                f.write(f"[System] Starting Product Ingestion (Mode: {mode}, Run ID: {run_id})...\n")
                
            f_log = open(process_log_file, "a", encoding="utf-8")
            
            # Start process
            cmd = [sys.executable, "-u", "update_products_batch_2.py", mode, "--run_id", str(run_id)]
            if runtime_flags.get("run_headless"):
                cmd.append("--headless")
            if runtime_flags.get("update_sync_flag") is not None:
                cmd.extend(["--set-sup-update", "1" if runtime_flags.get("update_sync_flag") else "0"])
            if runtime_flags.get("update_unlimited") is not None:
                cmd.extend(["--set-unlimited", "1" if runtime_flags.get("update_unlimited") else "0"])
            if runtime_flags.get("update_valid") is not None:
                cmd.extend(["--set-valid", "1" if runtime_flags.get("update_valid") else "0"])
            if runtime_flags.get("preserve_existing_images"):
                cmd.append("--preserve-existing-images")
            if runtime_flags.get("change_category") is False:
                cmd.append("--no-category-change")
            if runtime_flags.get("category_only"):
                cmd.append("--category-only")

            current_process = subprocess.Popen(cmd, stdout=f_log, stderr=subprocess.STDOUT)
            process_type = "ingestion"
            
            self.send_json_response({"success": True, "message": "הזנת מוצרים החלה ברקע", "run_id": run_id})
        except Exception as e:
            self.send_error_response(500, f"Error starting ingestion: {e}")

    def update_manual_category(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            mg_id = str(data.get("mg_id", "")).strip()
            new_category_code = str(data.get("new_category_code", "")).strip()
            if not mg_id or not new_category_code:
                self.send_error_response(400, "mg_id and new_category_code are required")
                return

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT category_code FROM products WHERE mg_id = ?", (mg_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                self.send_error_response(404, "Product not found")
                return

            old_category_code = str(row[0] or "")
            cursor.execute("UPDATE products SET category_code = ?, sync_flag = 0 WHERE mg_id = ?", (new_category_code, mg_id))
            cursor.execute(
                """
                INSERT INTO category_manual_updates (mg_id, old_category_code, new_category_code, updated_at, applied)
                VALUES (?, ?, ?, ?, 0)
                ON CONFLICT(mg_id) DO UPDATE SET
                    old_category_code = excluded.old_category_code,
                    new_category_code = excluded.new_category_code,
                    updated_at = excluded.updated_at,
                    applied = 0
                """,
                (mg_id, old_category_code, new_category_code, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()

            self.send_json_response({
                "success": True,
                "mg_id": mg_id,
                "old_category_code": old_category_code,
                "new_category_code": new_category_code
            })
        except Exception as e:
            self.send_error_response(500, f"Error updating manual category: {e}")

    def get_category_manual_pending(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cmu.mg_id, p.title, cmu.old_category_code, cmu.new_category_code, cmu.updated_at
                FROM category_manual_updates cmu
                JOIN products p ON p.mg_id = cmu.mg_id
                WHERE cmu.applied = 0
                ORDER BY cmu.updated_at DESC
            """)
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            self.send_json_response({"pending": rows, "count": len(rows)})
        except Exception as e:
            self.send_error_response(500, f"Error loading pending manual categories: {e}")

    def import_mg_csv(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            file_path = str(data.get("file_path", "")).strip()
            file_name = str(data.get("file_name", "")).strip() or "uploaded_mg.csv"
            file_content_b64 = str(data.get("file_content_b64", "")).strip()

            csv_stream = None
            source_label = ""
            if file_path:
                if not os.path.exists(file_path):
                    self.send_error_response(404, "MG file was not found")
                    return
                csv_stream = open(file_path, 'r', encoding='cp1255', errors='replace', newline='')
                source_label = file_path
            elif file_content_b64:
                raw_bytes = base64.b64decode(file_content_b64)
                decoded_text = raw_bytes.decode('cp1255', errors='replace')
                csv_stream = io.StringIO(decoded_text)
                source_label = file_name
            else:
                self.send_error_response(400, "file_path or file_content_b64 is required")
                return

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            updated = 0
            skipped = 0
            total_rows = 0
            try:
                reader = csv.reader(csv_stream)
                headers = next(reader, None)
                for row in reader:
                    total_rows += 1
                    if len(row) < 34:
                        skipped += 1
                        continue
                    mg_id = row[0].strip()
                    if not mg_id:
                        skipped += 1
                        continue

                    title = row[1].strip() if len(row) > 1 else ""
                    category_code = row[6].strip() if len(row) > 6 else ""
                    sap_sku = row[8].strip() if len(row) > 8 else ""
                    try:
                        price = float((row[33] or "0").strip() or 0)
                    except Exception:
                        price = 0.0
                    try:
                        original_price = float((row[32] or "0").strip() or 0)
                    except Exception:
                        original_price = 0.0
                    try:
                        stock = int(float((row[30] or "0").strip() or 0))
                    except Exception:
                        stock = 0

                    cursor.execute("""
                        UPDATE products
                        SET title = COALESCE(NULLIF(?, ''), title),
                            category_code = COALESCE(NULLIF(?, ''), category_code),
                            sap_sku = COALESCE(NULLIF(?, ''), sap_sku),
                            price = ?,
                            original_price = ?,
                            stock = ?
                        WHERE mg_id = ?
                    """, (title, category_code, sap_sku, price, original_price, stock, mg_id))

                    if cursor.rowcount > 0:
                        updated += 1
                    else:
                        skipped += 1

                    if total_rows % 1000 == 0:
                        conn.commit()
            finally:
                if csv_stream is not None:
                    csv_stream.close()

            conn.commit()
            conn.close()

            self.send_json_response({
                "success": True,
                "file_path": file_path,
                "file_name": file_name,
                "source": source_label,
                "total_rows": total_rows,
                "updated_existing": updated,
                "skipped": skipped,
                "message": "ייבוא קובץ MG הושלם"
            })
        except Exception as e:
            self.send_error_response(500, f"Error importing MG CSV: {e}")

    def export_mg_csv(self, query):
        try:
            category = query.get("category", [""])[0]
            search = query.get("search", [""])[0]
            out_path = query.get("out_path", [""])[0]
            if not out_path:
                ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                out_path = fr"C:\TEMP\mg_export_{ts}.csv"

            where_clauses = []
            params = []
            if category:
                where_clauses.append("category_code = ?")
                params.append(category)
            if search:
                where_clauses.append("(title LIKE ? OR sap_sku LIKE ? OR mg_id = ?)")
                params.extend([f"%{search}%", f"%{search}%", search])

            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT mg_id, title, zap_title, short_desc, full_desc, extra_info,
                       category_code, '', sap_sku,
                       supplier1_name, supplier1_sku, supplier1_price, supplier1_stock,
                       supplier2_name, supplier2_sku, supplier2_price, supplier2_stock,
                       supplier3_name, supplier3_sku, supplier3_price, supplier3_stock,
                       sync_flag, '', '', '', '', '', '', '',
                       stock, '', original_price, price,
                       '', '', '', '', '', '', '', '', brand_code, '', ''
                FROM products
                {where_str}
                ORDER BY mg_id
            """, params)
            rows = cursor.fetchall()
            conn.close()

            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            headers = [
                "mg_id", "title", "zap_title", "short_desc", "full_desc", "extra_info",
                "category_code", "unused_7", "sap_sku",
                "supplier1_name", "supplier1_sku", "supplier1_price", "supplier1_stock",
                "supplier2_name", "supplier2_sku", "supplier2_price", "supplier2_stock",
                "supplier3_name", "supplier3_sku", "supplier3_price", "supplier3_stock",
                "sync_flag", "c22", "c23", "c24", "c25", "c26", "c27", "c28",
                "stock", "c31", "original_price", "price",
                "c34", "c35", "c36", "c37", "c38", "c39", "c40", "c41", "brand_code", "c43", "c44"
            ]

            with open(out_path, 'w', encoding='windows-1255', errors='replace', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)

            self.send_json_response({
                "success": True,
                "out_path": out_path,
                "rows": len(rows),
                "message": "קובץ ייצוא MG נוצר בהצלחה"
            })
        except Exception as e:
            self.send_error_response(500, f"Error exporting MG CSV: {e}")

    def _mg_export_excel_headers(self, count=266):
        headers = []
        for idx in range(count):
            n = idx + 1
            label = ""
            while n > 0:
                n, rem = divmod(n - 1, 26)
                label = chr(65 + rem) + label
            headers.append(label)
        return headers

    def _bool_to_hebrew(self, value):
        if value is None:
            return ""
        try:
            return "כן" if int(value) == 1 else "לא"
        except Exception:
            text = str(value).strip().lower()
            if text in {"1", "true", "yes", "כן", "v"}:
                return "כן"
            if text in {"0", "false", "no", "לא", "x"}:
                return "לא"
            return ""

    def _stock_to_supplier_flag(self, value):
        try:
            return "כן" if float(value or 0) > 0 else "לא"
        except Exception:
            return ""

    def _build_full_mg_row(self, row):
        values = [""] * 266
        values[0] = str(row["mg_id"] or "")
        values[1] = str(row["title"] or "")
        values[2] = str(row["zap_title"] or "")
        values[4] = str(row["short_desc"] or "")
        values[5] = str(row["full_desc"] or "")
        values[6] = str(row["category_code"] or "")
        values[8] = str(row["sap_sku"] or "")

        values[9] = str(row["supplier1_name"] or "")
        values[10] = str(row["supplier1_sku"] or "")
        values[11] = "" if row["supplier1_price"] is None else str(row["supplier1_price"])
        values[12] = self._stock_to_supplier_flag(row["supplier1_stock"])

        values[13] = str(row["supplier2_name"] or "")
        values[14] = str(row["supplier2_sku"] or "")
        values[15] = "" if row["supplier2_price"] is None else str(row["supplier2_price"])
        values[16] = self._stock_to_supplier_flag(row["supplier2_stock"])

        values[17] = str(row["supplier3_name"] or "")
        values[18] = str(row["supplier3_sku"] or "")
        values[19] = "" if row["supplier3_price"] is None else str(row["supplier3_price"])
        values[20] = self._stock_to_supplier_flag(row["supplier3_stock"])

        values[21] = self._bool_to_hebrew(row["sync_flag"])
        values[30] = "" if row["stock"] is None else str(row["stock"])
        values[32] = "" if row["original_price"] is None else str(row["original_price"])
        values[33] = "" if row["price"] is None else str(row["price"])
        values[42] = str(row["brand_code"] or "")
        values[264] = self._bool_to_hebrew(row["is_valid"])
        return values

    def export_mg_full_csv(self):
        try:
            content_length = int(self.headers.get('Content-Length', '0'))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(post_data.decode('utf-8'))

            mode = str(data.get("mode", "all")).strip() or "all"
            category = str(data.get("category", "")).strip()
            mg_from = str(data.get("mg_from", "")).strip()
            mg_to = str(data.get("mg_to", "")).strip()
            mg_id = str(data.get("mg_id", "")).strip()

            where_clauses = []
            params = []
            if mode == "category":
                if not category:
                    self.send_error_response(400, "category is required")
                    return
                where_clauses.append("category_code = ?")
                params.append(category)
            elif mode == "range":
                if not mg_from or not mg_to:
                    self.send_error_response(400, "mg_from and mg_to are required")
                    return
                where_clauses.append("CAST(mg_id AS INTEGER) BETWEEN CAST(? AS INTEGER) AND CAST(? AS INTEGER)")
                params.extend([mg_from, mg_to])
            elif mode == "single":
                if not mg_id:
                    self.send_error_response(400, "mg_id is required")
                    return
                where_clauses.append("mg_id = ?")
                params.append(mg_id)

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT mg_id, title, zap_title, short_desc, full_desc, extra_info,
                       category_code, sap_sku, price, original_price, stock,
                       brand_code, sync_flag, is_valid,
                       supplier1_name, supplier1_sku, supplier1_price, supplier1_stock,
                       supplier2_name, supplier2_sku, supplier2_price, supplier2_stock,
                       supplier3_name, supplier3_sku, supplier3_price, supplier3_stock
                FROM products
                {where_sql}
                ORDER BY CAST(mg_id AS INTEGER)
            """, params)
            rows = cursor.fetchall()
            conn.close()

            out_path = r"C:\TEMP\PRDS_EXPORT_TO_MG.csv"
            os.makedirs(os.path.dirname(out_path), exist_ok=True)

            headers = self._mg_export_excel_headers(266)
            with open(out_path, 'w', encoding='windows-1255', errors='replace', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for row in rows:
                    writer.writerow(self._build_full_mg_row(row))

            self.send_json_response({
                "success": True,
                "out_path": out_path,
                "rows": len(rows),
                "mode": mode,
                "message": "קובץ ייצוא MG מלא נוצר בהצלחה"
            })
        except Exception as e:
            self.send_error_response(500, f"Error exporting full MG CSV: {e}")

    def stop_ingestion(self):
        global current_process, process_type, active_run_id
        if current_process is None or current_process.poll() is not None:
            self.send_json_response({"success": True, "message": "אין תהליך פעיל ברקע"})
            return
            
        try:
            current_process.terminate()
            time.sleep(1.0)
            if current_process.poll() is None:
                current_process.kill()
                
            current_process = None
            process_type = None
            
            # Update run in DB to terminated
            if active_run_id is not None:
                from datetime import datetime
                now_iso = datetime.now().isoformat()
                try:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT start_time FROM ingestion_runs WHERE id = ?", (active_run_id,))
                    row = cursor.fetchone()
                    duration = 0.0
                    if row and row[0]:
                        try:
                            start_t = datetime.fromisoformat(row[0])
                            duration = (datetime.now() - start_t).total_seconds()
                        except Exception:
                            pass
                        
                    cursor.execute("""
                        UPDATE ingestion_runs
                        SET status = 'terminated', end_time = ?, total_duration = ?
                        WHERE id = ?
                    """, (now_iso, duration, active_run_id))
                    conn.commit()
                    conn.close()
                except Exception as db_ex:
                    print(f"Error updating run status on stop: {db_ex}")
                active_run_id = None
            
            # Append stopped message
            with open(process_log_file, "a", encoding="utf-8") as f:
                f.write("\n[System] Process terminated by user.\n")
                
            self.send_json_response({"success": True, "message": "התהליך נעצר בהצלחה"})
        except Exception as e:
            self.send_error_response(500, f"Error stopping process: {e}")

    def analyze_supplier_csv(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            csv_data = data.get("csv_data", "")
            supplier_name = data.get("supplier_name", "")
            file_name = str(data.get("file_name", "")).strip()
            file_content_b64 = data.get("file_content_b64", "")
            mappings = data.get("mappings", {}) # e.g. {"supplier_sku": "A", "title": "B", "price": "C", "stock": "D"}
            include_oscn_check = bool(data.get("include_oscn_check", True))
            preprocess_only = bool(data.get("preprocess_only", False))
            selected_category_keys = set(str(v).strip() for v in (data.get("selected_category_keys", []) or []) if str(v).strip())
            selected_tabs = set(str(v).strip() for v in (data.get("selected_tabs", []) or []) if str(v).strip())
            category_margin_overrides_raw = dict(data.get("category_margin_overrides", {}) or {})
            extraction_summary = None
            process_type = "manual_csv"

            category_margin_overrides = {}
            for k, v in category_margin_overrides_raw.items():
                try:
                    category_margin_overrides[str(k).strip()] = float(v)
                except Exception:
                    continue

            if file_content_b64:
                entries = _load_supplier_pricelist_scripts_registry()
                process_map = {
                    _normalize_supplier_lookup_key(e.get("supplier", "")): e
                    for e in entries
                    if _normalize_supplier_lookup_key(e.get("supplier", ""))
                }
                process_cfg = process_map.get(_normalize_supplier_lookup_key(supplier_name))

                if process_cfg and process_cfg.get("process_enabled"):
                    process_type = process_cfg.get("process_type", "manual_csv")
                    if process_type == "five_excel_tabs":
                        csv_data, extraction_summary = _transform_five_excel_to_csv_data(file_content_b64)
                        mappings = {
                            "supplier_sku": "A",
                            "title": "B",
                            "price": "C",
                            "stock": "D",
                        }
                    elif process_type == "visual_excel_tabs":
                        csv_data, extraction_summary = _transform_visual_excel_to_csv_data(file_content_b64)
                        mappings = {
                            "supplier_sku": "A",
                            "title": "B",
                            "price": "C",
                            "stock": "D",
                        }
                    elif process_type == "techno_excel_tabs":
                        csv_data, extraction_summary = _transform_techno_excel_to_csv_data(file_content_b64)
                        mappings = {
                            "supplier_sku": "A",
                            "title": "B",
                            "price": "C",
                            "stock": "D",
                        }
                    elif not str(csv_data).strip():
                        self.send_error_response(400, f"Unsupported process_type '{process_type}' for supplier '{supplier_name}'")
                        return
                elif not str(csv_data).strip():
                    self.send_error_response(400, f"No active pricelist process configured for supplier '{supplier_name}' and file '{file_name or 'uploaded file'}'")
                    return
            
            if not str(csv_data).strip():
                self.send_error_response(400, "Empty CSV file")
                return

            normalized_rows = []
            if extraction_summary and isinstance(extraction_summary.get("normalized_rows"), list):
                normalized_rows = extraction_summary.get("normalized_rows")

            if not normalized_rows:
                normalized_rows = _build_normalized_rows_from_csv_data(csv_data, supplier_name, mappings)
                if normalized_rows and not extraction_summary:
                    extraction_summary = {
                        "tabs": [{"tab": "CSV", "matched_tab": "CSV", "exists": True, "rows_scanned": len(normalized_rows), "extracted": len(normalized_rows)}],
                        "total_extracted": len(normalized_rows),
                        "normalized_rows": normalized_rows,
                        "category_tree": _build_supplier_category_tree(normalized_rows),
                        "unique_brands": sorted({str((r or {}).get("brand", "")).strip() for r in normalized_rows if str((r or {}).get("brand", "")).strip()}),
                    }

            if normalized_rows:
                if selected_tabs:
                    normalized_rows = [r for r in normalized_rows if str((r or {}).get("tab_name", "")).strip() in selected_tabs]

                if selected_category_keys:
                    normalized_rows = [
                        r for r in normalized_rows
                        if str((r or {}).get("category_key", "")).strip() in selected_category_keys
                        or str((r or {}).get("category", "")).strip() in selected_category_keys
                    ]

                for row in normalized_rows:
                    key = str((row or {}).get("category_key", "")).strip()
                    if key in category_margin_overrides:
                        margin_val = category_margin_overrides[key]
                        raw_price = float((row or {}).get("raw_price", 0.0) or 0.0)
                        row["margin"] = margin_val
                        row["final_price"] = float(_calculate_price_with_vat_and_margin(raw_price, margin_val))

            resolved_display_toggles = _get_supplier_preview_display_toggles(supplier_name)

            preprocess_payload = {
                "category_tree": extraction_summary.get("category_tree", []) if extraction_summary else [],
                "unique_brands": extraction_summary.get("unique_brands", []) if extraction_summary else [],
                "tabs": extraction_summary.get("tabs", []) if extraction_summary else [],
                "total_rows": len(normalized_rows) if normalized_rows else int(extraction_summary.get("total_extracted", 0) if extraction_summary else 0),
                "preview_rows": (normalized_rows or [])[:500],
                "display_toggles": resolved_display_toggles,
                "diagnostics": {
                    "has_extraction_summary": bool(extraction_summary),
                    "normalized_rows_count": len(normalized_rows),
                    "tabs_detected": len(extraction_summary.get("tabs", []) if extraction_summary else []),
                    "file_name": file_name,
                    "file_b64_length": len(str(file_content_b64 or "")),
                    "csv_length": len(str(csv_data or "")),
                    "process_type": process_type,
                },
            }

            if preprocess_only:
                preprocess_session_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
                self._record_supplier_intake_history(
                    preprocess_session_id,
                    supplier_name,
                    preprocess_payload.get("total_rows", 0),
                    0,
                    0,
                    0,
                    ingestion_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    original_file_path=file_name,
                    source_kind="preprocess_only",
                )
                self.send_json_response({
                    "success": True,
                    "preprocess": preprocess_payload,
                    "extraction_summary": extraction_summary,
                    "display_toggles": resolved_display_toggles,
                })
                return

            import csv
            stream = io.StringIO(csv_data)
            reader = csv.reader(stream, delimiter=_detect_csv_delimiter(csv_data))
            try:
                headers = next(reader)
            except StopIteration:
                self.send_error_response(400, "Empty CSV header")
                return
                
            # Helper to convert Excel column letter or header name to index
            def get_col_index(col_val):
                if not col_val:
                    return -1
                # Check if it's an Excel column letter
                if col_val.isalpha():
                    return col_to_idx(col_val)
                # Try matching by header name
                for idx, h in enumerate(headers):
                    if h.strip().lower() == col_val.strip().lower():
                        return idx
                return -1
                
            sku_idx = get_col_index(mappings.get("supplier_sku"))
            title_idx = get_col_index(mappings.get("title"))
            price_idx = get_col_index(mappings.get("price"))
            stock_idx = get_col_index(mappings.get("stock"))
            availability_idx = get_col_index(mappings.get("availability") or mappings.get("stock"))

            if not normalized_rows and sku_idx == -1:
                self.send_error_response(400, "מיפוי מק''ט ספק הוא חובה!")
                return
                
            # Connect to database to compare
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Retrieve all existing products that have this supplier defined
            # We will match by supplier name and SKU
            cursor.execute("""
                SELECT mg_id, title, price, stock,
                       supplier1_name, supplier1_sku, supplier1_price, supplier1_stock,
                       supplier2_name, supplier2_sku, supplier2_price, supplier2_stock,
                       supplier3_name, supplier3_sku, supplier3_price, supplier3_stock
                FROM products
            """)
            
            db_products = {}
            for row in cursor.fetchall():
                mg_id, title, price, stock = row[0], row[1], row[2], row[3]
                # Index by supplier name + SKU
                for sup_idx in [4, 8, 12]:
                    s_name = row[sup_idx]
                    s_sku = row[sup_idx+1]
                    if s_name and s_sku:
                        db_products[(_normalize_supplier_lookup_key(s_name), s_sku.strip().lower())] = {
                            "mg_id": mg_id,
                            "title": title,
                            "price": price,
                            "stock": stock,
                            "supplier_index": (sup_idx // 4) + 1 # 1, 2 or 3
                        }
                        
            new_products = []
            updated_products = []
            unchanged_count = 0
            parsed_supplier_skus = []
            parsed_products = []

            def _push_parsed_product(s_sku, s_title, s_price, s_stock, extra_row=None):
                parsed_supplier_skus.append(s_sku)
                parsed_product = {
                    "supplier_sku": s_sku,
                    "title": s_title,
                    "price": s_price,
                }
                if isinstance(extra_row, dict):
                    parsed_product.update(extra_row)
                parsed_products.append(parsed_product)

                key = (_normalize_supplier_lookup_key(supplier_name), s_sku.lower())

                if key in db_products:
                    db_prod = db_products[key]
                    mg_id = db_prod["mg_id"]
                    db_title = db_prod["title"]
                    db_price = db_prod["price"]
                    db_stock = db_prod["stock"]

                    has_changes = False
                    changes = {}

                    if abs(db_price - s_price) > 0.01:
                        has_changes = True
                        changes["price"] = {"old": db_price, "new": s_price}

                    db_has_stock = db_stock > 0
                    sup_has_stock = s_stock > 0
                    if db_has_stock != sup_has_stock:
                        has_changes = True
                        changes["stock"] = {"old": db_stock, "new": s_stock}

                    if has_changes:
                        updated_products.append({
                            "mg_id": mg_id,
                            "title": db_title,
                            "supplier_sku": s_sku,
                            "changes": changes,
                            "new_values": {
                                "price": s_price,
                                "stock": s_stock,
                                "supplier_index": db_prod["supplier_index"]
                            },
                            "preview": extra_row or {},
                        })
                    else:
                        return False
                else:
                    new_products.append({
                        "supplier_sku": s_sku,
                        "title": s_title,
                        "price": s_price,
                        "stock": s_stock,
                        "preview": extra_row or {},
                    })
                return True
            
            # Helper to parse price
            def clean_price(val):
                if not val:
                    return 0.0
                val_clean = val.replace("₪", "").replace(",", "").strip()
                try:
                    return float(val_clean)
                except ValueError:
                    return 0.0
                    
            # Helper to parse stock
            def clean_stock(val):
                val_clean = val.strip().lower()
                if val_clean in ["כן", "in stock", "yes", "true", "1", "x"]:
                    return 9999 # Default positive stock (infinite/X)
                if val_clean in ["לא", "out of stock", "no", "false", "0"]:
                    return 0
                try:
                    return int(val_clean)
                except ValueError:
                    return 0
                    
            if normalized_rows:
                for row in normalized_rows:
                    s_sku = str((row or {}).get("supplier_sku", "")).strip()
                    if not s_sku:
                        continue
                    s_title = str((row or {}).get("processed_title", "")).strip()
                    s_price = float((row or {}).get("final_price", 0.0) or 0.0)
                    s_stock = 9999 if _is_available_status((row or {}).get("availability", "")) else 0
                    changed = _push_parsed_product(s_sku, s_title, s_price, s_stock, row)
                    if not changed:
                        unchanged_count += 1
            else:
                for r in reader:
                    if not r or len(r) <= sku_idx:
                        continue
                    s_sku = r[sku_idx].strip()
                    if not s_sku:
                        continue

                    s_title = r[title_idx].strip() if title_idx != -1 and len(r) > title_idx else ""
                    s_price = clean_price(r[price_idx]) if price_idx != -1 and len(r) > price_idx else 0.0
                    s_stock = clean_stock(r[stock_idx]) if stock_idx != -1 and len(r) > stock_idx else 10

                    # Intake flow should only include products that are marked as available.
                    availability_txt = r[availability_idx].strip() if availability_idx != -1 and len(r) > availability_idx else ""
                    if availability_txt:
                        if not _is_available_status(availability_txt):
                            try:
                                if float(availability_txt) <= 0:
                                    continue
                            except Exception:
                                continue
                    elif stock_idx != -1 and s_stock <= 0:
                        continue

                    changed = _push_parsed_product(s_sku, s_title, s_price, s_stock, None)
                    if not changed:
                        unchanged_count += 1
                    
            conn.close()
            intake_session_id = self._cache_latest_supplier_intake_rows(supplier_name, parsed_products)
            if intake_session_id:
                self._record_supplier_intake_history(
                    intake_session_id,
                    supplier_name,
                    len(parsed_products),
                    len(new_products),
                    sum(1 for p in updated_products if "price" in (p.get("changes", {}) or {})),
                    unchanged_count,
                    ingestion_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    original_file_path=file_name,
                    source_kind="analysis",
                )
            oscn_check = _check_missing_oscn_substitutes(parsed_supplier_skus, parsed_products, supplier_name) if include_oscn_check else None
            self.send_json_response({
                "new_products": new_products,
                "updated_products": updated_products,
                "unchanged_count": unchanged_count,
                "extraction_summary": extraction_summary,
                "preprocess": preprocess_payload,
                "preview_rows": parsed_products,
                "intake_session_id": intake_session_id,
                "display_toggles": resolved_display_toggles,
                "oscn_check": oscn_check,
            })
            
        except Exception as e:
            self.send_error_response(500, f"Error analyzing CSV: {e}")

    def export_supplier_5col_file(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            supplier_name = str(data.get("supplier_name", "")).strip()
            requested_session_id = str(data.get("session_id", "") or "").strip()

            if not supplier_name:
                self.send_error_response(400, "supplier_name is required")
                return

            session_id = requested_session_id or self._get_latest_intake_session(supplier_name)
            if not session_id:
                self.send_error_response(400, "לא נמצאה קליטה אחרונה עבור הספק")
                return

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT supplier_sku, title, price
                FROM supplier_intake_analysis_cache
                WHERE session_id = ?
                  AND LOWER(TRIM(supplier_name)) = LOWER(TRIM(?))
                  AND TRIM(COALESCE(supplier_sku, '')) != ''
                ORDER BY id ASC
                """,
                (session_id, supplier_name),
            )
            cached_rows = cursor.fetchall()
            conn.close()

            if not cached_rows:
                self.send_error_response(400, "לא נמצאו שורות קליטה לסשן שנבחר")
                return

            rows = []
            for r in cached_rows:
                sku = str(r[0] or "").strip()
                title = str(r[1] or "").strip()
                try:
                    price_val = int(round(float(r[2] or 0.0)))
                except Exception:
                    price_val = 0
                if not sku or not title or price_val <= 0:
                    continue
                rows.append([supplier_name, sku, title, "", str(price_val)])

            if not rows:
                self.send_error_response(400, "לא נמצאו שורות תקינות לייצוא בקובץ הקליטה")
                return

            os.makedirs(r"C:\TEMP", exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_supplier = supplier_name.replace("/", "-").replace("\\", "-").replace(" ", "_")
            out_path = fr"C:\TEMP\SUPPLIER_MG5_{safe_supplier}_{ts}.csv"

            with open(out_path, "w", newline="", encoding="windows-1255", errors="replace") as f:
                writer = csv.writer(f)
                for row in rows:
                    writer.writerow(row)

            self.send_json_response({
                "success": True,
                "out_path": out_path,
                "rows": len(rows),
                "message": "קובץ ספקים ל-MG (5 שדות) נוצר בהצלחה",
                "session_id": session_id,
            })
        except Exception as e:
            self.send_error_response(500, f"Error generating supplier MG 5-col file: {e}")

    def export_supplier_sap_intake_from_session(self):
        try:
            content_length = int(self.headers.get('Content-Length', '0'))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(post_data.decode('utf-8'))

            supplier_name = str(data.get("supplier_name", "") or "").strip()
            requested_session_id = str(data.get("session_id", "") or "").strip()
            if not supplier_name:
                self.send_error_response(400, "supplier_name is required")
                return

            session_id = requested_session_id or self._get_latest_intake_session(supplier_name)
            if not session_id:
                self.send_error_response(400, "לא נמצאה קליטה אחרונה עבור הספק")
                return

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT supplier_sku, title, price
                FROM supplier_intake_analysis_cache
                WHERE session_id = ?
                  AND LOWER(TRIM(supplier_name)) = LOWER(TRIM(?))
                  AND TRIM(COALESCE(supplier_sku, '')) != ''
                ORDER BY id ASC
                """,
                (session_id, supplier_name),
            )
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                self.send_error_response(400, "לא נמצאו שורות קליטה לסשן שנבחר")
                return

            parsed_supplier_skus = []
            parsed_products = []
            for r in rows:
                s_sku = str(r[0] or "").strip()
                if not s_sku:
                    continue
                s_title = str(r[1] or "").strip()
                try:
                    s_price = float(r[2] or 0.0)
                except Exception:
                    s_price = 0.0
                parsed_supplier_skus.append(s_sku)
                parsed_products.append({
                    "supplier_sku": s_sku,
                    "title": s_title,
                    "price": s_price,
                })

            oscn_check = _check_missing_oscn_substitutes(parsed_supplier_skus, parsed_products, supplier_name)
            self.send_json_response({
                "success": True,
                "supplier_name": supplier_name,
                "session_id": session_id,
                "checked": len(parsed_supplier_skus),
                "oscn_check": oscn_check,
            })
        except Exception as e:
            self.send_error_response(500, f"Error exporting SAP intake from session: {e}")

    def complete_intake_sap_skus(self):
        try:
            content_length = int(self.headers.get('Content-Length', '0'))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(post_data.decode('utf-8'))

            supplier_name = str(data.get("supplier_name", "") or "").strip()
            session_id = str(data.get("session_id", "") or "").strip()
            if not supplier_name:
                self.send_error_response(400, "supplier_name is required")
                return

            if not session_id:
                session_id = self._get_latest_intake_session(supplier_name) or ""
            if not session_id:
                self.send_error_response(400, "לא נמצאה קליטה אחרונה לספק זה")
                return

            job_key = f"{supplier_name.casefold()}::{session_id}"
            with intake_completion_jobs_lock:
                existing = intake_completion_jobs.get(job_key)
                if existing and existing.get("status") in {"queued", "running"}:
                    self.send_json_response({
                        "success": True,
                        "started": False,
                        "job_id": existing.get("job_id"),
                        "supplier_name": supplier_name,
                        "session_id": session_id,
                        "status": existing.get("status"),
                        "progress_pct": int(existing.get("progress_pct", 0) or 0),
                        "message": existing.get("message") or "השלמת מקטים כבר רצה",
                    })
                    return

                job_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
                intake_completion_jobs[job_key] = {
                    "job_id": job_id,
                    "supplier_name": supplier_name,
                    "session_id": session_id,
                    "status": "queued",
                    "progress_pct": 0,
                    "processed": 0,
                    "total": 0,
                    "matched": 0,
                    "unmatched": 0,
                    "message": "התור נוצר, מתחיל עיבוד...",
                    "error": None,
                    "updated_at": datetime.now().isoformat(),
                }

            thread = threading.Thread(
                target=self._run_intake_sap_completion_job,
                args=(job_key, supplier_name, session_id),
                daemon=True,
            )
            thread.start()

            self.send_json_response({
                "success": True,
                "started": True,
                "job_id": job_id,
                "supplier_name": supplier_name,
                "session_id": session_id,
                "status": "queued",
                "progress_pct": 0,
                "message": "השלמת מקטים הופעלה ברקע",
            })
        except Exception as e:
            self.send_error_response(500, f"Error starting SAP SKU completion for intake: {e}")

    def _run_intake_sap_completion_job(self, job_key, supplier_name, session_id):
        conn = None
        sap_conn = None
        try:
            with intake_completion_jobs_lock:
                job = intake_completion_jobs.get(job_key, {})
                job["status"] = "running"
                job["message"] = "שולף מקטי ספק מהקליטה האחרונה..."
                job["updated_at"] = datetime.now().isoformat()
                intake_completion_jobs[job_key] = job

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT DISTINCT TRIM(COALESCE(supplier_sku, ''))
                FROM supplier_intake_analysis_cache
                WHERE session_id = ? AND LOWER(TRIM(supplier_name)) = LOWER(TRIM(?))
                  AND TRIM(COALESCE(supplier_sku, '')) != ''
                """,
                (session_id, supplier_name),
            )
            supplier_skus = [str(r[0] or "").strip() for r in cursor.fetchall() if str(r[0] or "").strip()]
            if not supplier_skus:
                raise ValueError("לא נמצאו מקטי ספק בקליטה האחרונה")

            with intake_completion_jobs_lock:
                job = intake_completion_jobs.get(job_key, {})
                job["total"] = len(supplier_skus)
                job["message"] = f"מתחיל בדיקת {len(supplier_skus)} מקטי ספק מול SAP"
                job["updated_at"] = datetime.now().isoformat()
                intake_completion_jobs[job_key] = job

            sap_conn, _ = _open_sap_odbc_connection()
            sap_cur = sap_conn.cursor()
            sku_to_sap = {}
            chunk_size = 200
            for i in range(0, len(supplier_skus), chunk_size):
                chunk = supplier_skus[i:i + chunk_size]
                placeholders = ",".join(["?"] * len(chunk))
                sql = f"SELECT T0.[ItemCode], T0.[ItemName], T0.[SuppCatNum], T0.[OnHand] FROM OITM T0 WHERE T0.[SuppCatNum] IN ({placeholders})"
                sap_cur.execute(sql, chunk)
                for row in sap_cur.fetchall():
                    supp_cat = str(row[2] or "").strip()
                    if not supp_cat:
                        continue
                    if supp_cat not in sku_to_sap:
                        sku_to_sap[supp_cat] = {
                            "item_code": str(row[0] or "").strip(),
                            "item_name": str(row[1] or "").strip(),
                            "on_hand": float(row[3] or 0.0),
                        }

            now_txt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            matched = 0
            processed = 0
            total = len(supplier_skus)
            for sku in supplier_skus:
                processed += 1
                row = sku_to_sap.get(sku)
                if row:
                    matched += 1
                    cursor.execute(
                        """
                        UPDATE supplier_intake_analysis_cache
                        SET sap_item_code = ?, sap_item_name = ?, sap_on_hand = ?, updated_at = ?
                        WHERE session_id = ?
                          AND LOWER(TRIM(supplier_name)) = LOWER(TRIM(?))
                          AND LOWER(TRIM(supplier_sku)) = LOWER(TRIM(?))
                        """,
                        (row["item_code"], row["item_name"], row["on_hand"], now_txt, session_id, supplier_name, sku),
                    )

                    for idx in (1, 2, 3):
                        cursor.execute(
                            f"""
                            UPDATE products
                            SET sap_sku = ?
                            WHERE LOWER(TRIM(COALESCE(supplier{idx}_name, ''))) = LOWER(TRIM(?))
                              AND LOWER(TRIM(COALESCE(supplier{idx}_sku, ''))) = LOWER(TRIM(?))
                            """,
                            (row["item_code"], supplier_name, sku),
                        )

                progress_pct = int(round((processed / total) * 100)) if total else 100
                with intake_completion_jobs_lock:
                    job = intake_completion_jobs.get(job_key, {})
                    job["processed"] = processed
                    job["matched"] = matched
                    job["unmatched"] = max(total - matched, 0)
                    job["progress_pct"] = progress_pct
                    job["message"] = f"עובד... {processed}/{total} | נמצאו {matched}"
                    job["updated_at"] = datetime.now().isoformat()
                    intake_completion_jobs[job_key] = job

            conn.commit()

            with intake_completion_jobs_lock:
                job = intake_completion_jobs.get(job_key, {})
                job["status"] = "completed"
                job["processed"] = total
                job["matched"] = matched
                job["unmatched"] = max(total - matched, 0)
                job["progress_pct"] = 100
                job["message"] = f"ההשלמה הסתיימה: {matched}/{total} נמצאו ב-SAP"
                job["updated_at"] = datetime.now().isoformat()
                intake_completion_jobs[job_key] = job
        except Exception as e:
            with intake_completion_jobs_lock:
                job = intake_completion_jobs.get(job_key, {})
                job["status"] = "failed"
                job["error"] = str(e)
                job["message"] = f"שגיאה בהשלמת מקטים: {e}"
                job["updated_at"] = datetime.now().isoformat()
                intake_completion_jobs[job_key] = job
        finally:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
            try:
                if sap_conn is not None:
                    sap_conn.close()
            except Exception:
                pass

    def get_intake_sap_completion_status(self, query):
        try:
            supplier_name = str((query.get("supplier_name", [""]) or [""])[0] or "").strip()
            session_id = str((query.get("session_id", [""]) or [""])[0] or "").strip()
            if not supplier_name:
                self.send_error_response(400, "supplier_name is required")
                return
            if not session_id:
                session_id = self._get_latest_intake_session(supplier_name) or ""
            if not session_id:
                self.send_error_response(404, "לא נמצאה קליטה אחרונה לספק זה")
                return

            job_key = f"{supplier_name.casefold()}::{session_id}"
            with intake_completion_jobs_lock:
                job = dict(intake_completion_jobs.get(job_key, {}) or {})

            if not job:
                self.send_json_response({
                    "success": True,
                    "supplier_name": supplier_name,
                    "session_id": session_id,
                    "status": "idle",
                    "progress_pct": 0,
                    "processed": 0,
                    "total": 0,
                    "matched": 0,
                    "unmatched": 0,
                    "message": "טרם הופעלה השלמת מקטים",
                    "error": None,
                })
                return

            job["success"] = True
            self.send_json_response(job)
        except Exception as e:
            self.send_error_response(500, f"Error getting SAP completion status: {e}")

    def import_supplier_changes(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            supplier_name = data.get("supplier_name", "")
            updated_products = data.get("updated_products", [])
            new_products = data.get("new_products", [])
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Commit updates
            for p in updated_products:
                mg_id = p.get("mg_id")
                new_vals = p.get("new_values", {})
                price = new_vals.get("price")
                stock = new_vals.get("stock")
                sup_idx = new_vals.get("supplier_index", 1)
                
                cursor.execute(f"""
                    UPDATE products
                    SET price = ?, stock = ?,
                        supplier{sup_idx}_price = ?, supplier{sup_idx}_stock = ?
                    WHERE mg_id = ?
                """, (price, stock, price, "כן" if stock > 0 else "לא", mg_id))
                
            # Commit new products
            for p in new_products:
                s_sku = p.get("supplier_sku")
                s_title = p.get("title") or f"מוצר חדש {s_sku}"
                s_price = p.get("price")
                s_stock = p.get("stock")
                
                # Check if already exists by SKU to avoid integrity errors
                cursor.execute("SELECT mg_id FROM products WHERE mg_id = ?", (s_sku,))
                if cursor.fetchone():
                    continue
                    
                cursor.execute("""
                    INSERT INTO products (
                        mg_id, title, sap_sku, price, original_price, stock, sync_flag, is_valid,
                        supplier1_name, supplier1_sku, supplier1_price, supplier1_stock
                    ) VALUES (?, ?, ?, ?, ?, ?, 0, 1, ?, ?, ?, ?)
                """, (s_sku, s_title, s_sku, s_price, s_price, s_stock, supplier_name, s_sku, s_price, "כן" if s_stock > 0 else "לא"))
                
            # Record statistics
            unchanged_count = data.get("unchanged_count", 0)
            updated_price_count = sum(1 for p in updated_products if "price" in p.get("changes", {}))
            total_count = len(updated_products) + len(new_products) + unchanged_count
            new_count = len(new_products)
            
            from datetime import datetime
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO supplier_ingestions (supplier_name, total_count, new_count, updated_price_count, unchanged_count, ingestion_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (supplier_name, total_count, new_count, updated_price_count, unchanged_count, now_str))
            
            conn.commit()
            conn.close()
            
            self.send_json_response({"success": True, "message": "הנתונים עודכנו בדאטאבייס בהצלחה!"})
        except Exception as e:
            self.send_error_response(500, f"Error importing data: {e}")

    def get_reports(self):
        try:
            reports_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "daily-price-checker", "reports"))
            if not os.path.exists(reports_dir):
                self.send_json_response([])
                return
            
            files = []
            for f in os.listdir(reports_dir):
                if f.startswith("report_") and f.endswith(".md"):
                    path = os.path.join(reports_dir, f)
                    parts = f.replace("report_", "").replace(".md", "").split("_")
                    display_name = f
                    if len(parts) == 2:
                        date_str = parts[0]
                        time_str = parts[1]
                        if len(date_str) == 8 and len(time_str) == 6:
                            display_name = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]} {time_str[0:2]}:{time_str[2:4]}:{time_str[4:6]}"
                    
                    files.append({
                        "filename": f,
                        "display_name": display_name,
                        "size_bytes": os.path.getsize(path),
                        "created_at": os.path.getmtime(path)
                    })
            
            files.sort(key=lambda x: x["filename"], reverse=True)
            self.send_json_response(files)
        except Exception as e:
            self.send_error_response(500, f"Error listing reports: {e}")

    def get_report_detail(self, query):
        try:
            filename = query.get("filename", [""])[0]
            if not filename or ".." in filename or "/" in filename or "\\" in filename:
                self.send_error_response(400, "Invalid filename")
                return
            
            if not filename.startswith("report_") or not filename.endswith(".md"):
                self.send_error_response(400, "Invalid filename format")
                return
                
            reports_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "daily-price-checker", "reports"))
            path = os.path.join(reports_dir, filename)
            
            if not os.path.exists(path):
                self.send_error_response(404, "Report not found")
                return
                
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                
            self.send_json_response({
                "filename": filename,
                "content": content
            })
        except Exception as e:
            self.send_error_response(500, f"Error reading report: {e}")

    def get_supplier_ingestions_history(self):
        try:
            self._backfill_supplier_intake_history_from_cache()
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id,
                       session_id,
                       supplier_name,
                       total_count,
                       new_count,
                       updated_price_count,
                       unchanged_count,
                       ingestion_date,
                       COALESCE(original_file_path, '') AS original_file_path,
                       COALESCE(calculated_file_path, '') AS calculated_file_path,
                       COALESCE(mg_new_products_file_path, '') AS mg_new_products_file_path,
                       COALESCE(source_kind, 'analysis') AS source_kind
                FROM supplier_intake_history
                ORDER BY ingestion_date DESC, id DESC
                """
            )
            rows = cursor.fetchall()
            history = [dict(r) for r in rows]

            known_sessions = {str((r or {}).get("session_id", "")).strip() for r in history if str((r or {}).get("session_id", "")).strip()}
            cursor.execute(
                """
                SELECT session_id,
                       supplier_name,
                       COUNT(*) AS total_count,
                       MIN(COALESCE(created_at, updated_at, '')) AS ingestion_date
                FROM supplier_intake_analysis_cache
                WHERE TRIM(COALESCE(session_id, '')) != ''
                GROUP BY session_id, supplier_name
                ORDER BY ingestion_date DESC
                """
            )
            live_rows = cursor.fetchall()
            for row in live_rows:
                session_id = str(row["session_id"] or "").strip()
                if not session_id or session_id in known_sessions:
                    continue
                history.append(
                    {
                        "id": None,
                        "session_id": session_id,
                        "supplier_name": str(row["supplier_name"] or "").strip(),
                        "total_count": int(row["total_count"] or 0),
                        "new_count": 0,
                        "updated_price_count": 0,
                        "unchanged_count": 0,
                        "ingestion_date": str(row["ingestion_date"] or "").strip() or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "original_file_path": "",
                        "calculated_file_path": "",
                        "mg_new_products_file_path": "",
                        "source_kind": "live_cache",
                    }
                )

            history.sort(key=lambda r: (str((r or {}).get("ingestion_date", "")), str((r or {}).get("session_id", ""))), reverse=True)
            conn.close()
            self.send_json_response(history)
        except Exception as e:
            self.send_error_response(500, f"Error getting supplier ingestions: {e}")

    def get_health_version(self):
        try:
            mtime = None
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(__file__)).isoformat()
            except Exception:
                mtime = None
            self.send_json_response(
                {
                    "success": True,
                    "api_version": SERVER_API_VERSION,
                    "server_file": os.path.abspath(__file__),
                    "server_mtime": mtime,
                    "pid": os.getpid(),
                }
            )
        except Exception as e:
            self.send_error_response(500, f"Error building health version response: {e}")

    def get_suppliers_contacts(self):
        try:
            supplier_names = {}
            for file_path in (SUPPLIER_PRICELIST_SCRIPTS_PATH, SUPPLIER_SCRIPTS_PATH, SUPPLIER_FIELD_MAPPINGS_PATH):
                try:
                    if not os.path.exists(file_path):
                        continue
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if not isinstance(data, list):
                        continue
                    for row in data:
                        if not isinstance(row, dict):
                            continue
                        name = str(row.get("supplier", "") or "").strip()
                        if name:
                            supplier_names[name.casefold()] = name
                except Exception:
                    continue

            suppliers = []
            for name in sorted(supplier_names.values(), key=lambda x: str(x).casefold()):
                suppliers.append(
                    {
                        "id": None,
                        "name": name,
                        "interval_days": 7,
                        "last_ingestion_date": None,
                        "contact_name": "",
                        "contact_email": "",
                        "template_exists": 0,
                        "pricelist_template_name": "לא הוגדר מיפוי לספק זה",
                    }
                )
            self.send_json_response(suppliers)
        except Exception as e:
            self.send_json_response([])

    def get_suppliers_catalog(self):
        try:
            supplier_catalog = _build_unified_supplier_catalog()
            self.send_json_response({"success": True, "suppliers": supplier_catalog, "count": len(supplier_catalog)})
        except Exception as e:
            self.send_error_response(500, f"Error building suppliers catalog: {e}")

    def get_sap_suppliers(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, card_code, sap_name, mg_supplier_name, updated_at
                FROM sap_suppliers
                ORDER BY sap_name, card_code
            """)
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            self.send_json_response({"suppliers": rows, "count": len(rows)})
        except Exception as e:
            self.send_error_response(500, f"Error loading SAP suppliers: {e}")

    def get_sap_salespersons(self):
        conn = None
        try:
            conn, used_driver = _open_sap_odbc_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SlpCode, SlpName
                FROM OSLP
                ORDER BY SlpName
            """)
            rows = cursor.fetchall()

            salespersons = []
            for r in rows:
                salespersons.append(
                    {
                        "slp_code": int(r[0]) if r[0] is not None else None,
                        "slp_name": str(r[1] or "").strip(),
                    }
                )

            self.send_json_response(
                {
                    "success": True,
                    "driver": used_driver,
                    "salespersons": salespersons,
                    "count": len(salespersons),
                }
            )
        except Exception as e:
            self.send_error_response(500, f"Error loading SAP salespersons: {e}")
        finally:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def get_sap_sales_report(self, query):
        conn = None
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            date_from = str(query.get("date_from", [today])[0] or today).strip()
            date_to = str(query.get("date_to", [today])[0] or today).strip()
            slp_codes_raw = str(query.get("slp_codes", [""])[0] or "").strip()

            datetime.strptime(date_from, "%Y-%m-%d")
            datetime.strptime(date_to, "%Y-%m-%d")

            slp_codes = []
            if slp_codes_raw:
                for token in slp_codes_raw.split(","):
                    token = token.strip()
                    if not token:
                        continue
                    try:
                        slp_codes.append(int(token))
                    except Exception:
                        continue

            conn, used_driver = _open_sap_odbc_connection()
            cursor = conn.cursor()

            where_parts = [
                "CONVERT(date, o.DocDate) BETWEEN ? AND ?",
                "o.CANCELED = 'N'",
            ]
            params = [date_from, date_to]

            if slp_codes:
                placeholders = ",".join(["?"] * len(slp_codes))
                where_parts.append(f"o.SlpCode IN ({placeholders})")
                params.extend(slp_codes)

            where_sql = " AND ".join(where_parts)
            sql = f"""
                SELECT
                    o.DocEntry,
                    o.DocNum,
                    CONVERT(date, o.DocDate) AS DocDate,
                    o.CardCode,
                    o.CardName,
                    o.SlpCode,
                    s.SlpName,
                    o.DocTotalSy,
                    o.DocStatus,
                    o.CANCELED
                FROM ORDR o
                LEFT JOIN OSLP s ON s.SlpCode = o.SlpCode
                WHERE {where_sql}
                ORDER BY o.DocDate DESC, o.DocNum DESC
            """

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            sales_rows = []
            summary_map = {}
            total_gross = 0.0

            for r in rows:
                slp_code_val = int(r[5]) if r[5] is not None else None
                slp_name_val = str(r[6] or "").strip()
                doc_total = float(r[7] or 0.0)
                doc_total_net = round(doc_total / 1.18, 2)

                total_gross += doc_total
                sales_rows.append(
                    {
                        "doc_entry": int(r[0]) if r[0] is not None else None,
                        "doc_num": int(r[1]) if r[1] is not None else None,
                        "doc_date": str(r[2]),
                        "card_code": str(r[3] or "").strip(),
                        "card_name": str(r[4] or "").strip(),
                        "slp_code": slp_code_val,
                        "slp_name": slp_name_val,
                        "doc_total_sy": round(doc_total, 2),
                        "doc_total_sy_net": doc_total_net,
                        "doc_status": str(r[8] or "").strip(),
                        "canceled": str(r[9] or "").strip(),
                    }
                )

                key = (slp_code_val, slp_name_val)
                if key not in summary_map:
                    summary_map[key] = {
                        "slp_code": slp_code_val,
                        "slp_name": slp_name_val,
                        "documents_count": 0,
                        "doc_total_sy_sum": 0.0,
                    }

                summary_map[key]["documents_count"] += 1
                summary_map[key]["doc_total_sy_sum"] += doc_total

            summary = []
            for _, row in sorted(summary_map.items(), key=lambda x: ((x[0][1] or ""), (x[0][0] or 0))):
                gross_val = round(row["doc_total_sy_sum"], 2)
                summary.append(
                    {
                        "slp_code": row["slp_code"],
                        "slp_name": row["slp_name"],
                        "documents_count": row["documents_count"],
                        "doc_total_sy_sum": gross_val,
                        "doc_total_sy_sum_net": round(gross_val / 1.18, 2),
                    }
                )

            total_gross = round(total_gross, 2)
            self.send_json_response(
                {
                    "success": True,
                    "driver": used_driver,
                    "date_from": date_from,
                    "date_to": date_to,
                    "slp_codes": slp_codes,
                    "rows": sales_rows,
                    "summary": summary,
                    "totals": {
                        "documents_count": len(sales_rows),
                        "doc_total_sy_sum": total_gross,
                        "doc_total_sy_sum_net": round(total_gross / 1.18, 2),
                    },
                }
            )
        except ValueError:
            self.send_error_response(400, "date_from/date_to must be in yyyy-mm-dd format")
        except Exception as e:
            self.send_error_response(500, f"Error building SAP sales report: {e}")
        finally:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def sync_sap_sales_report_to_sheets(self):
        conn = None
        try:
            content_length = int(self.headers.get('Content-Length', '0'))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(post_data.decode('utf-8'))

            today = datetime.now().strftime("%Y-%m-%d")
            date_from = str(data.get("date_from", today) or today).strip()
            date_to = str(data.get("date_to", today) or today).strip()
            spreadsheet_id = str(data.get("spreadsheet_id", "") or GOOGLE_SHEETS_SPREADSHEET_ID).strip()
            slp_codes_raw = data.get("slp_codes", [])

            if not spreadsheet_id:
                self.send_error_response(400, "spreadsheet_id is required")
                return

            datetime.strptime(date_from, "%Y-%m-%d")
            datetime.strptime(date_to, "%Y-%m-%d")

            slp_codes = []
            if isinstance(slp_codes_raw, str):
                tokens = slp_codes_raw.split(",")
            elif isinstance(slp_codes_raw, list):
                tokens = slp_codes_raw
            else:
                tokens = []

            for token in tokens:
                val = str(token).strip()
                if not val:
                    continue
                try:
                    slp_codes.append(int(val))
                except Exception:
                    continue

            conn, used_driver = _open_sap_odbc_connection()
            cursor = conn.cursor()

            where_parts = [
                "CONVERT(date, o.DocDate) BETWEEN ? AND ?",
                "o.CANCELED = 'N'",
            ]
            params = [date_from, date_to]

            if slp_codes:
                placeholders = ",".join(["?"] * len(slp_codes))
                where_parts.append(f"o.SlpCode IN ({placeholders})")
                params.extend(slp_codes)

            where_sql = " AND ".join(where_parts)
            sql = f"""
                SELECT
                    o.DocEntry,
                    o.DocNum,
                    CONVERT(date, o.DocDate) AS DocDate,
                    o.CardCode,
                    o.CardName,
                    o.SlpCode,
                    s.SlpName,
                    o.DocTotalSy,
                    o.DocStatus,
                    o.CANCELED
                FROM ORDR o
                LEFT JOIN OSLP s ON s.SlpCode = o.SlpCode
                WHERE {where_sql}
                ORDER BY o.DocDate DESC, o.DocNum DESC
            """

            cursor.execute(sql, params)
            source_rows = cursor.fetchall()

            summary_map = {}

            for r in source_rows:
                doc_total = float(r[7] or 0.0)
                slp_code_val = int(r[5]) if r[5] is not None else None
                slp_name_val = str(r[6] or "").strip()

                key = (slp_code_val, slp_name_val)
                if key not in summary_map:
                    summary_map[key] = {
                        "slp_code": slp_code_val,
                        "slp_name": slp_name_val,
                        "documents_count": 0,
                        "doc_total_sy_sum": 0.0,
                    }
                summary_map[key]["documents_count"] += 1
                summary_map[key]["doc_total_sy_sum"] += doc_total

            # Update the exact target grid requested by the user:
            # DATA sheet, starting at row 7, columns:
            # B = salesperson name, C = orders count, D = total orders (DocTotalSy sum)
            data_values = []
            for _, row in sorted(summary_map.items(), key=lambda x: ((x[0][1] or ""), (x[0][0] or 0))):
                gross_val = round(row["doc_total_sy_sum"], 2)
                net_val = gross_val / 1.18
                data_values.append([
                    row["slp_name"],
                    _format_int_with_thousands(row["documents_count"]),
                    _format_int_with_thousands(net_val),
                ])

            sheets_service = _open_google_sheets_service()
            spreadsheet_meta = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            target_title = None
            sheets = spreadsheet_meta.get("sheets", [])

            # 1) Prefer exact gid from provided sheet URL.
            for s in sheets:
                props = s.get("properties", {})
                if int(props.get("sheetId", -1)) == GOOGLE_SHEETS_TARGET_GID:
                    target_title = props.get("title")
                    break

            # 2) Fallback by title matching DATA (case-insensitive).
            if not target_title:
                for s in sheets:
                    props = s.get("properties", {})
                    title = str(props.get("title") or "").strip()
                    if title.lower() == "data":
                        target_title = title
                        break

            if not target_title:
                raise RuntimeError("Target sheet tab was not found (gid/data)")

            if data_values:
                sheets_service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=f"{target_title}!B7:D10000",
                    valueInputOption="USER_ENTERED",
                    body={"values": data_values},
                ).execute()

            self.send_json_response({
                "success": True,
                "spreadsheet_id": spreadsheet_id,
                "date_from": date_from,
                "date_to": date_to,
                "rows_written": len(data_values),
                "message": "Sales report synced to DATA!B7:D",
            })
        except ValueError:
            self.send_error_response(400, "date_from/date_to must be in yyyy-mm-dd format")
        except Exception as e:
            self.send_error_response(500, f"Error syncing sales report to Google Sheets: {e}")
        finally:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def get_automated_processes(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, script_path, interval_value, interval_unit, enabled,
                       last_run_at, next_run_at, last_status, last_message,
                       created_at, updated_at
                FROM automated_processes
                ORDER BY
                    CASE WHEN name = ? THEN 0 ELSE 1 END,
                    id DESC
                """
                ,
                (DEFAULT_GOOGLE_PROCESS_NAME,)
            )
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()

            with automated_processes_lock:
                running_ids = set(automated_processes_running)

            for row in rows:
                row["enabled"] = bool(row.get("enabled"))
                row["is_running"] = int(row.get("id") or 0) in running_ids

            self.send_json_response({"success": True, "processes": rows, "count": len(rows)})
        except Exception as e:
            self.send_error_response(500, f"Error loading automated processes: {e}")

    def create_automated_process(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(post_data.decode("utf-8"))

            name = str(data.get("name", "")).strip()
            script_path = str(data.get("script_path", "")).strip()
            interval_unit = _normalize_interval_unit(data.get("interval_unit", "minutes"))
            interval_value = _validate_interval(data.get("interval_value", 5), interval_unit)
            enabled = 1 if bool(data.get("enabled", True)) else 0

            if not name:
                self.send_error_response(400, "name is required")
                return
            if not script_path:
                self.send_error_response(400, "script_path is required")
                return

            now = datetime.now()
            next_run_at = (now + timedelta(seconds=_interval_to_seconds(interval_value, interval_unit))).isoformat() if enabled else None

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO automated_processes
                (name, script_path, interval_value, interval_unit, enabled, next_run_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, script_path, interval_value, interval_unit, enabled, next_run_at, now.isoformat(), now.isoformat()),
            )
            new_id = cursor.lastrowid
            conn.commit()
            conn.close()

            self.send_json_response({"success": True, "id": new_id})
        except sqlite3.IntegrityError:
            self.send_error_response(400, "Process name already exists")
        except ValueError as ve:
            self.send_error_response(400, str(ve))
        except Exception as e:
            self.send_error_response(500, f"Error creating automated process: {e}")

    def update_automated_process(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(post_data.decode("utf-8"))

            process_id = data.get("id")
            if not process_id:
                self.send_error_response(400, "id is required")
                return

            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM automated_processes WHERE id = ?", (process_id,))
            existing = cursor.fetchone()
            if not existing:
                conn.close()
                self.send_error_response(404, "Process was not found")
                return

            name = str(data.get("name", existing["name"])).strip()
            script_path = str(data.get("script_path", existing["script_path"])).strip()
            interval_unit = _normalize_interval_unit(data.get("interval_unit", existing["interval_unit"]))
            interval_value = _validate_interval(data.get("interval_value", existing["interval_value"]), interval_unit)
            enabled = 1 if bool(data.get("enabled", bool(existing["enabled"]))) else 0

            if not name:
                conn.close()
                self.send_error_response(400, "name is required")
                return
            if not script_path:
                conn.close()
                self.send_error_response(400, "script_path is required")
                return

            now = datetime.now()
            next_run_at = existing["next_run_at"]
            if enabled:
                next_run_at = (now + timedelta(seconds=_interval_to_seconds(interval_value, interval_unit))).isoformat()
            else:
                next_run_at = None

            cursor.execute(
                """
                UPDATE automated_processes
                SET name = ?,
                    script_path = ?,
                    interval_value = ?,
                    interval_unit = ?,
                    enabled = ?,
                    next_run_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (name, script_path, interval_value, interval_unit, enabled, next_run_at, now.isoformat(), process_id),
            )
            conn.commit()
            conn.close()

            self.send_json_response({"success": True})
        except sqlite3.IntegrityError:
            self.send_error_response(400, "Process name already exists")
        except ValueError as ve:
            self.send_error_response(400, str(ve))
        except Exception as e:
            self.send_error_response(500, f"Error updating automated process: {e}")

    def delete_automated_process(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(post_data.decode("utf-8"))

            process_id = data.get("id")
            if not process_id:
                self.send_error_response(400, "id is required")
                return

            with automated_processes_lock:
                if int(process_id) in automated_processes_running:
                    self.send_error_response(400, "Cannot delete process while it is running")
                    return

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM automated_processes WHERE id = ?", (process_id,))
            deleted = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted == 0:
                self.send_error_response(404, "Process was not found")
                return

            self.send_json_response({"success": True})
        except Exception as e:
            self.send_error_response(500, f"Error deleting automated process: {e}")

    def run_automated_process_now(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(post_data.decode("utf-8"))

            process_id = data.get("id")
            if not process_id:
                self.send_error_response(400, "id is required")
                return

            with automated_processes_lock:
                if int(process_id) in automated_processes_running:
                    self.send_error_response(400, "Process is already running")
                    return

            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, script_path, interval_value, interval_unit, enabled, next_run_at
                FROM automated_processes
                WHERE id = ?
                """,
                (process_id,),
            )
            row = cursor.fetchone()
            conn.close()

            if not row:
                self.send_error_response(404, "Process was not found")
                return

            _launch_automated_process(dict(row), reason="manual")
            self.send_json_response({"success": True})
        except Exception as e:
            self.send_error_response(500, f"Error running process: {e}")

    def update_sap_supplier_mapping(self):
        try:
            content_length = int(self.headers.get('Content-Length', '0'))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(post_data.decode('utf-8'))

            row_id = data.get("id")
            card_code = str(data.get("card_code", "")).strip()
            sap_name = str(data.get("sap_name", "")).strip()
            mg_supplier_name = str(data.get("mg_supplier_name", "")).strip()
            if not row_id and not card_code:
                self.send_error_response(400, "id or card_code is required")
                return

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            if row_id:
                cursor.execute(
                    "UPDATE sap_suppliers SET mg_supplier_name = ?, sap_name = COALESCE(NULLIF(?, ''), sap_name), updated_at = ? WHERE id = ?",
                    (mg_supplier_name, sap_name, datetime.now().isoformat(), row_id),
                )
            else:
                cursor.execute(
                    "UPDATE sap_suppliers SET mg_supplier_name = ?, sap_name = COALESCE(NULLIF(?, ''), sap_name), updated_at = ? WHERE card_code = ?",
                    (mg_supplier_name, sap_name, datetime.now().isoformat(), card_code),
                )
            conn.commit()
            conn.close()
            self.send_json_response({"success": True})
        except Exception as e:
            self.send_error_response(500, f"Error updating SAP supplier mapping: {e}")

    def create_sap_supplier_mapping(self):
        try:
            content_length = int(self.headers.get('Content-Length', '0'))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(post_data.decode('utf-8'))

            card_code = str(data.get("card_code", "")).strip()
            sap_name = str(data.get("sap_name", "")).strip()
            mg_supplier_name = str(data.get("mg_supplier_name", "")).strip()
            if not card_code:
                self.send_error_response(400, "card_code is required")
                return

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sap_suppliers (card_code, sap_name, mg_supplier_name, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(card_code) DO UPDATE SET
                    sap_name = excluded.sap_name,
                    mg_supplier_name = excluded.mg_supplier_name,
                    updated_at = excluded.updated_at
            """, (card_code, sap_name, mg_supplier_name, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            self.send_json_response({"success": True})
        except Exception as e:
            self.send_error_response(500, f"Error creating SAP supplier mapping: {e}")

    def delete_sap_supplier_mapping(self):
        try:
            content_length = int(self.headers.get('Content-Length', '0'))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(post_data.decode('utf-8'))

            row_id = data.get("id")
            card_code = str(data.get("card_code", "")).strip()
            if not row_id and not card_code:
                self.send_error_response(400, "id or card_code is required")
                return

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            if row_id:
                cursor.execute("DELETE FROM sap_suppliers WHERE id = ?", (row_id,))
            else:
                cursor.execute("DELETE FROM sap_suppliers WHERE card_code = ?", (card_code,))
            conn.commit()
            conn.close()
            self.send_json_response({"success": True})
        except Exception as e:
            self.send_error_response(500, f"Error deleting SAP supplier mapping: {e}")

    def import_sap_suppliers(self):
        try:
            content_length = int(self.headers.get('Content-Length', '0'))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(post_data.decode('utf-8'))

            file_path = str(data.get("file_path", "")).strip()
            file_content_b64 = str(data.get("file_content_b64", "")).strip()
            file_name = str(data.get("file_name", "")).strip() or "sap_suppliers.csv"

            stream = None

            def decode_csv_bytes(raw_bytes):
                for enc in ("utf-8-sig", "cp1255"):
                    try:
                        return raw_bytes.decode(enc)
                    except Exception:
                        continue
                return raw_bytes.decode("utf-8", errors="replace")

            if file_path:
                if not os.path.exists(file_path):
                    self.send_error_response(404, "SAP suppliers file was not found")
                    return
                with open(file_path, "rb") as bf:
                    raw_bytes = bf.read()
                stream = io.StringIO(decode_csv_bytes(raw_bytes))
            elif file_content_b64:
                raw_bytes = base64.b64decode(file_content_b64)
                decoded_text = decode_csv_bytes(raw_bytes)
                stream = io.StringIO(decoded_text)
            else:
                self.send_error_response(400, "file_path or file_content_b64 is required")
                return

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            imported = 0
            skipped = 0
            try:
                reader = csv.reader(stream)
                headers = next(reader, None)
                if not headers:
                    self.send_error_response(400, "File has no headers")
                    return

                headers_l = [str(h or "").strip().lower() for h in headers]
                card_idx = -1
                name_idx = -1
                mg_idx = -1
                for i, h in enumerate(headers_l):
                    if h in {"cardcode", "card_code", "supplier_code", "card code", "קוד כרטיס", "קוד ספק", "קוד"}:
                        card_idx = i
                    if h in {"cardname", "sap_name", "supplier_name", "card name", "name", "שם כרטיס", "שם ספק sap", "שם ספק"}:
                        name_idx = i
                    if h in {
                        "mg_supplier_name", "mg name", "mg_supplier", "mg supplier",
                        "supplier_name_mg", "supplier mg", "mg",
                        "שם ספק במערכת mg", "שם ספק במערכתmg", "שם ספק mg", "שם ספק בmg", "שם ספק mg במערכת",
                        "שם ספק במערכת mg", "שם ספק במערכת mg "
                    }:
                        mg_idx = i

                if card_idx == -1 or name_idx == -1:
                    self.send_error_response(400, "Missing required columns CardCode/CardName")
                    return

                for row in reader:
                    if not row or len(row) <= max(card_idx, name_idx):
                        skipped += 1
                        continue
                    card_code = str(row[card_idx] or "").strip()
                    sap_name = str(row[name_idx] or "").strip()
                    mg_supplier_name = ""
                    if mg_idx != -1 and len(row) > mg_idx:
                        mg_supplier_name = str(row[mg_idx] or "").strip()
                    if not card_code:
                        skipped += 1
                        continue

                    cursor.execute("""
                        INSERT INTO sap_suppliers (card_code, sap_name, mg_supplier_name, updated_at)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(card_code) DO UPDATE SET
                            sap_name = excluded.sap_name,
                            mg_supplier_name = CASE
                                WHEN excluded.mg_supplier_name IS NOT NULL AND TRIM(excluded.mg_supplier_name) != '' THEN excluded.mg_supplier_name
                                ELSE sap_suppliers.mg_supplier_name
                            END,
                            updated_at = excluded.updated_at
                    """, (card_code, sap_name, mg_supplier_name, datetime.now().isoformat()))
                    imported += 1

                conn.commit()
            finally:
                if stream is not None:
                    stream.close()
                conn.close()

            self.send_json_response({
                "success": True,
                "imported": imported,
                "skipped": skipped,
                "file_name": file_name,
            })
        except Exception as e:
            self.send_error_response(500, f"Error importing SAP suppliers: {e}")

    def export_sap_oscn_sql(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT card_code, mg_supplier_name
                FROM sap_suppliers
                WHERE mg_supplier_name IS NOT NULL AND TRIM(mg_supplier_name) != ''
            """)
            mapping_rows = cursor.fetchall()
            mg_to_card = {}
            for r in mapping_rows:
                mg_name = str(r["mg_supplier_name"] or "").strip().lower()
                if mg_name:
                    mg_to_card[mg_name] = str(r["card_code"] or "").strip()

            cursor.execute("""
                SELECT mg_id, sap_sku, is_valid, stock,
                       supplier1_name, supplier1_sku, supplier1_price,
                       supplier2_name, supplier2_sku, supplier2_price,
                       supplier3_name, supplier3_sku, supplier3_price
                FROM products
                WHERE is_valid = 1
            """)
            products = cursor.fetchall()
            conn.close()

            tsv_lines = []
            total_rows = 0
            missing_mappings = []

            for p in products:
                item_code = str(p["sap_sku"] or "").strip()
                if not item_code:
                    continue

                for idx in (1, 2, 3):
                    sup_name = str(p[f"supplier{idx}_name"] or "").strip()
                    sup_sku = str(p[f"supplier{idx}_sku"] or "").strip()

                    if not sup_name or not sup_sku:
                        continue

                    card_code = mg_to_card.get(sup_name.lower())
                    if not card_code:
                        missing_mappings.append({"mg_id": p["mg_id"], "supplier_name": sup_name})
                        continue

                    item_code_safe = item_code.replace("\t", " ").replace("\r", " ").replace("\n", " ")
                    sup_sku_safe = sup_sku.replace("\t", " ").replace("\r", " ").replace("\n", " ")
                    card_code_safe = str(card_code).replace("\t", " ").replace("\r", " ").replace("\n", " ")
                    tsv_lines.append(f"{item_code_safe}\t{sup_sku_safe}\t{card_code_safe}")
                    total_rows += 1

            out_path = r"C:\TEMP\OSCN_SUPPLIER_SUBSTITUTES.tsv"
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="windows-1255", errors="replace", newline="") as f:
                f.write("ItemCode\tSubstitute\tCardCode\n")
                for line in tsv_lines:
                    f.write(line + "\n")

            self.send_json_response({
                "success": True,
                "out_path": out_path,
                "rows": total_rows,
                "missing_mappings": missing_mappings[:50],
                "missing_mappings_count": len(missing_mappings),
                "message": "OSCN TAB file generated",
            })
        except Exception as e:
            self.send_error_response(500, f"Error generating OSCN TAB file: {e}")

    def get_supplier_scripts(self):
        try:
            supplier_catalog = _build_unified_supplier_catalog()
            scripts = _merge_supplier_image_scripts_with_catalog(_load_supplier_scripts_registry(), supplier_catalog)
            self.send_json_response(
                {
                    "scripts": scripts,
                    "summary": _build_supplier_image_scripts_summary(scripts),
                    "images_storage": _images_storage_status(DEFAULT_IMAGES_ROOT),
                }
            )
        except Exception as e:
            self.send_error_response(500, f"Error loading supplier scripts: {e}")

    def get_supplier_pricelist_scripts(self):
        try:
            supplier_catalog = _build_unified_supplier_catalog()
            scripts = _merge_pricelist_scripts_with_catalog(_load_supplier_pricelist_scripts_registry(), supplier_catalog)
            self.send_json_response({"scripts": scripts, "supplier_catalog": supplier_catalog})
        except Exception as e:
            self.send_error_response(500, f"Error loading supplier pricelist scripts: {e}")

    def get_supplier_field_mappings(self, query):
        try:
            supplier = str((query.get("supplier", [""]) or [""])[0] or "").strip()
            entries = _load_supplier_field_mappings_registry()
            if supplier:
                supplier_key = _normalize_supplier_lookup_key(supplier)
                entries = [
                    e
                    for e in entries
                    if _normalize_supplier_lookup_key(e.get("supplier_key", "") or e.get("supplier", "")) == supplier_key
                ]
                entry = None
                if entries:
                    entries.sort(key=lambda x: str((x or {}).get("updated_at", "")), reverse=True)
                    entry = entries[0]
                self.send_json_response({"entry": entry})
                return
            self.send_json_response({"entries": entries})
        except Exception as e:
            self.send_error_response(500, f"Error loading supplier field mappings: {e}")

    def inspect_supplier_pricelist_sample(self, query=None):
        try:
            if query is not None:
                data = {
                    "supplier_name": str((query.get("supplier_name", [""]) or [""])[0] or ""),
                    "file_name": str((query.get("file_name", [""]) or [""])[0] or ""),
                    "csv_data": str((query.get("csv_data", [""]) or [""])[0] or ""),
                    "file_content_b64": str((query.get("file_content_b64", [""]) or [""])[0] or ""),
                    "sample_file_path": str((query.get("sample_file_path", [""]) or [""])[0] or ""),
                }
            else:
                content_length = int(self.headers["Content-Length"])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode("utf-8"))

            supplier_name = str(data.get("supplier_name", "")).strip()
            file_name = str(data.get("file_name", "")).strip()
            csv_data = str(data.get("csv_data", "") or "")
            file_content_b64 = data.get("file_content_b64", "")
            sample_file_path = str(data.get("sample_file_path", "") or "").strip()

            if not supplier_name:
                self.send_error_response(400, "supplier_name is required")
                return

            tabs = []
            preprocess = None

            process_cfg = None
            entries = _load_supplier_pricelist_scripts_registry()
            process_map = {
                _normalize_supplier_lookup_key(e.get("supplier", "")): e
                for e in entries
                if _normalize_supplier_lookup_key(e.get("supplier", ""))
            }
            process_cfg = process_map.get(_normalize_supplier_lookup_key(supplier_name))
            process_type = str((process_cfg or {}).get("process_type", "manual_csv") or "manual_csv")

            if not file_content_b64 and sample_file_path and os.path.exists(sample_file_path):
                raw_bytes = open(sample_file_path, "rb").read()
                file_content_b64 = "data:application/octet-stream;base64," + base64.b64encode(raw_bytes).decode("ascii")
                if not file_name:
                    file_name = os.path.basename(sample_file_path)

            if not file_content_b64 and process_cfg:
                cfg_path = str(process_cfg.get("sample_file_path", "") or "").strip()
                if cfg_path and os.path.exists(cfg_path):
                    raw_bytes = open(cfg_path, "rb").read()
                    file_content_b64 = "data:application/octet-stream;base64," + base64.b64encode(raw_bytes).decode("ascii")
                    if not file_name:
                        file_name = os.path.basename(cfg_path)

            if file_content_b64:
                payload = _extract_base64_payload(file_content_b64)
                raw_bytes = base64.b64decode(payload) if payload else b""
                if raw_bytes and raw_bytes.startswith(b"PK") and load_workbook is not None:
                    wb = load_workbook(filename=io.BytesIO(raw_bytes), data_only=True, read_only=True)
                    tabs = [str(n) for n in (wb.sheetnames or [])]
                elif raw_bytes and xlrd is not None:
                    wb = xlrd.open_workbook(file_contents=raw_bytes)
                    tabs = [str(n) for n in wb.sheet_names()]

            if not tabs and csv_data.strip():
                tabs = ["CSV"]

            if process_type == "techno_excel_tabs" and file_content_b64:
                transformed_csv, extraction_summary = _transform_techno_excel_to_csv_data(file_content_b64)
                preprocess = {
                    "total_rows": int(extraction_summary.get("total_extracted", 0)),
                    "category_tree": extraction_summary.get("category_tree", []),
                    "unique_brands": extraction_summary.get("unique_brands", []),
                    "preview_rows": extraction_summary.get("normalized_rows", [])[:500],
                }
                if not tabs:
                    tabs = [str((t or {}).get("matched_tab") or (t or {}).get("tab") or "") for t in extraction_summary.get("tabs", []) if str((t or {}).get("matched_tab") or (t or {}).get("tab") or "").strip()]

            default_mapping = {
                "category": "A",
                "brand": "B",
                "sub_category": "C",
                "sub_sub_category": "D",
                "processed_title": "E",
                "manufacturer_sku": "F",
                "supplier_sku": "F",
                "details": "G",
                "manufacturer_link": "H",
                "currency": "J",
                "raw_price": "K",
                "notes": "N",
                "availability": "P",
            }

            field_keys = [
                "category",
                "sub_category",
                "sub_sub_category",
                "manufacturer_sku",
                "supplier_sku",
                "processed_title",
                "raw_price",
                "currency",
                "brand",
                "details",
                "manufacturer_link",
                "notes",
                "availability",
            ]
            import_defaults = {k: True for k in field_keys}
            display_defaults = {k: k in {
                "category",
                "sub_category",
                "sub_sub_category",
                "manufacturer_sku",
                "supplier_sku",
                "processed_title",
                "raw_price",
                "currency",
                "availability",
                "manufacturer_link",
            } for k in field_keys}

            tab_configs = []
            for tab_name in tabs:
                tab_configs.append(
                    {
                        "tab_name": tab_name,
                        "tab_enabled": True,
                        "field_mapping": dict(default_mapping),
                        "import_toggles": dict(import_defaults),
                        "display_toggles": dict(display_defaults),
                    }
                )

            existing = _get_supplier_field_mapping_entry(supplier_name)
            if existing and isinstance(existing.get("tabs"), list) and existing.get("tabs"):
                by_name = {str((t or {}).get("tab_name", "")).strip(): t for t in existing.get("tabs", [])}
                merged_tabs = []
                for cfg in tab_configs:
                    tab_name = str(cfg.get("tab_name", "")).strip()
                    if tab_name in by_name:
                        merged_tabs.append(_normalize_tab_field_mapping(by_name[tab_name]))
                    else:
                        merged_tabs.append(cfg)
                tab_configs = merged_tabs

            self.send_json_response(
                {
                    "success": True,
                    "supplier_name": supplier_name,
                    "file_name": file_name,
                    "process_type": process_type,
                    "tabs": tab_configs,
                    "preprocess": preprocess,
                }
            )
        except Exception as e:
            self.send_error_response(500, f"Error inspecting supplier sample: {e}")

    def update_supplier_field_mappings(self):
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode("utf-8"))

            supplier = str(data.get("supplier", "")).strip()
            if not supplier:
                self.send_error_response(400, "supplier is required")
                return
            supplier_key = _normalize_supplier_lookup_key(supplier)
            if not supplier_key:
                self.send_error_response(400, "supplier is invalid")
                return

            tabs = data.get("tabs", [])
            if not isinstance(tabs, list):
                self.send_error_response(400, "tabs must be an array")
                return

            category_margins = dict(data.get("category_margins", {}) or {})
            category_import_toggles = dict(data.get("category_import_toggles", {}) or {})
            brand_import_toggles = dict(data.get("brand_import_toggles", {}) or {})
            last_sample_file = str(data.get("last_sample_file", "")).strip()

            normalized_tabs = [_normalize_tab_field_mapping(t) for t in tabs]
            now_iso = datetime.now().isoformat()

            entries = _load_supplier_field_mappings_registry()
            idx = -1
            for i, row in enumerate(entries):
                row_key = _normalize_supplier_lookup_key(row.get("supplier_key", "") or row.get("supplier", ""))
                if row_key == supplier_key:
                    idx = i
                    break

            entry = {
                "supplier": supplier,
                "supplier_key": supplier_key,
                "tabs": normalized_tabs,
                "category_margins": category_margins,
                "category_import_toggles": category_import_toggles,
                "brand_import_toggles": brand_import_toggles,
                "last_sample_file": last_sample_file,
                "updated_at": now_iso,
            }

            if idx >= 0:
                entries[idx] = entry
            else:
                entries.append(entry)

            _save_supplier_field_mappings_registry(entries)
            self.send_json_response({"success": True, "entry": entry})
        except Exception as e:
            self.send_error_response(500, f"Error updating supplier field mappings: {e}")

    def get_app_settings(self):
        try:
            self.send_json_response(_load_app_settings())
        except Exception as e:
            self.send_error_response(500, f"Error loading app settings: {e}")

    def update_app_settings(self):
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode("utf-8"))
            updated = _save_app_settings(data)
            self.send_json_response({"success": True, "settings": updated})
        except ValueError as ex:
            self.send_error_response(400, str(ex))
        except Exception as e:
            self.send_error_response(500, f"Error updating app settings: {e}")

    def update_supplier_pricelist_script(self):
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode("utf-8"))

            supplier = str(data.get("supplier", "")).strip()
            if not supplier:
                self.send_error_response(400, "supplier is required")
                return

            entries = _load_supplier_pricelist_scripts_registry()
            entry = None
            for row in entries:
                if str(row.get("supplier", "")).strip().lower() == supplier.lower():
                    entry = row
                    break

            if entry is None:
                entry = {
                    "supplier": supplier,
                    "process_enabled": False,
                    "process_type": "manual_csv",
                    "process_script_path": "",
                    "sample_file_path": "",
                    "notes": "",
                }
                entries.append(entry)

            if "process_enabled" in data:
                entry["process_enabled"] = bool(data.get("process_enabled"))

            if "process_type" in data:
                process_type = str(data.get("process_type", "manual_csv")).strip() or "manual_csv"
                if process_type not in ["manual_csv", "five_excel_tabs", "visual_excel_tabs", "techno_excel_tabs"]:
                    self.send_error_response(400, "process_type must be one of: manual_csv, five_excel_tabs, visual_excel_tabs, techno_excel_tabs")
                    return
                entry["process_type"] = process_type

            if "process_script_path" in data:
                entry["process_script_path"] = str(data.get("process_script_path", "")).strip()

            if "sample_file_path" in data:
                entry["sample_file_path"] = str(data.get("sample_file_path", "")).strip()

            if "notes" in data:
                entry["notes"] = str(data.get("notes", "")).strip()

            _save_supplier_pricelist_scripts_registry(entries)
            self.send_json_response({"success": True, "entry": entry})
        except Exception as e:
            self.send_error_response(500, f"Error updating supplier pricelist script: {e}")

    def update_supplier_script(self):
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode("utf-8"))

            supplier = str(data.get("supplier", "")).strip()
            if not supplier:
                self.send_error_response(400, "supplier is required")
                return

            entries = _load_supplier_scripts_registry()
            entry = None
            for row in entries:
                if row.get("supplier") == supplier:
                    entry = row
                    break

            if entry is None:
                entry = {
                    "supplier": supplier,
                    "has_image_extractor": False,
                    "use_enabled": False,
                    "loader_script_path": "",
                    "images_download_dir": DEFAULT_IMAGES_ROOT,
                }
                entries.append(entry)

            if "has_image_extractor" in data:
                entry["has_image_extractor"] = bool(data.get("has_image_extractor"))
            if "use_enabled" in data:
                entry["use_enabled"] = bool(data.get("use_enabled"))
            if "loader_script_path" in data:
                entry["loader_script_path"] = str(data.get("loader_script_path", "")).strip()
            if "images_download_dir" in data:
                entry["images_download_dir"] = str(data.get("images_download_dir", DEFAULT_IMAGES_ROOT)).strip() or DEFAULT_IMAGES_ROOT

            _save_supplier_scripts_registry(entries)
            self.send_json_response({"success": True, "entry": entry})
        except Exception as e:
            self.send_error_response(500, f"Error updating supplier script: {e}")

    def get_images_storage_status(self, query):
        try:
            root = query.get("root", [DEFAULT_IMAGES_ROOT])[0]
            self.send_json_response(_images_storage_status(root))
        except Exception as e:
            self.send_error_response(500, f"Error getting images storage status: {e}")

    def ensure_images_storage(self):
        try:
            root = DEFAULT_IMAGES_ROOT
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                content_length = 0

            if content_length > 0:
                data = json.loads(self.rfile.read(content_length).decode("utf-8"))
                root = str(data.get("root", DEFAULT_IMAGES_ROOT)).strip() or DEFAULT_IMAGES_ROOT

            os.makedirs(root, exist_ok=True)
            status = _images_storage_status(root)
            self.send_json_response({"success": True, "storage": status})
        except Exception as e:
            self.send_error_response(500, f"Error ensuring images storage: {e}")

    def get_images_extraction_config(self):
        try:
            supplier_catalog = _build_unified_supplier_catalog()
            scripts = _merge_supplier_image_scripts_with_catalog(_load_supplier_scripts_registry(), supplier_catalog)
            enabled = [
                s for s in scripts
                if s.get("has_image_extractor") and s.get("use_enabled") and s.get("script_file_exists")
            ]
            self.send_json_response({
                "suppliers": enabled,
                "summary": _build_supplier_image_scripts_summary(scripts),
                "images_storage": _images_storage_status(DEFAULT_IMAGES_ROOT),
            })
        except Exception as e:
            self.send_error_response(500, f"Error loading image extraction config: {e}")

    def get_mg_import_progress(self):
        try:
            if os.path.exists(MG_IMPORT_PROGRESS_PATH):
                with open(MG_IMPORT_PROGRESS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {
                    "processed": 0,
                    "total": 0,
                    "updated": 0,
                    "skipped": 0,
                    "errors": 0,
                    "in_stock": 0,
                    "out_of_stock": 0,
                    "valid": 0,
                    "invalid": 0,
                    "current_product": "",
                    "completed": False,
                }
            self.send_json_response(data)
        except Exception as e:
            self.send_error_response(500, f"Error loading MG import progress: {e}")

    def start_mg_import(self):
        global current_process, process_type
        if current_process is not None and current_process.poll() is None:
            self.send_error_response(400, "תהליך אחר כבר רץ ברקע")
            return

        try:
            content_length = int(self.headers.get('Content-Length', '0'))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(post_data.decode('utf-8'))

            file_path = str(data.get("file_path", "")).strip()
            file_name = str(data.get("file_name", "")).strip() or "uploaded_mg.csv"
            file_content_b64 = str(data.get("file_content_b64", "")).strip()

            if file_path:
                if not os.path.exists(file_path):
                    self.send_error_response(404, "MG file was not found")
                    return
                source_path = file_path
            elif file_content_b64:
                os.makedirs(r"C:\Temp", exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                source_path = os.path.join(r"C:\Temp", f"mg_import_upload_{ts}.csv")
                raw_bytes = base64.b64decode(file_content_b64)
                with open(source_path, "wb") as f:
                    f.write(raw_bytes)
            else:
                self.send_error_response(400, "file_path or file_content_b64 is required")
                return

            progress_seed = {
                "processed": 0,
                "total": 0,
                "updated": 0,
                "skipped": 0,
                "errors": 0,
                "in_stock": 0,
                "out_of_stock": 0,
                "valid": 0,
                "invalid": 0,
                "current_product": "",
                "file_name": file_name,
                "source": source_path,
                "completed": False,
            }
            os.makedirs(os.path.dirname(MG_IMPORT_PROGRESS_PATH), exist_ok=True)
            with open(MG_IMPORT_PROGRESS_PATH, "w", encoding="utf-8") as f:
                json.dump(progress_seed, f, ensure_ascii=False, indent=2)

            job_payload = {
                "file_path": source_path,
                "progress_path": MG_IMPORT_PROGRESS_PATH,
            }
            os.makedirs(os.path.dirname(MG_IMPORT_JOB_PATH), exist_ok=True)
            with open(MG_IMPORT_JOB_PATH, "w", encoding="utf-8") as f:
                json.dump(job_payload, f, ensure_ascii=False, indent=2)

            with open(process_log_file, "w", encoding="utf-8") as f:
                f.write("[System] Starting MG import process...\n")
                f.write(f"[System] Source: {source_path}\n")

            f_log = open(process_log_file, "a", encoding="utf-8")
            cmd = [sys.executable, "-u", "mg_import_runner.py", "--job", MG_IMPORT_JOB_PATH]
            current_process = subprocess.Popen(cmd, stdout=f_log, stderr=subprocess.STDOUT)
            process_type = "mg-import"

            self.send_json_response({
                "success": True,
                "message": "ייבוא MG הופעל ברקע",
                "source": source_path,
                "file_name": file_name,
            })
        except Exception as e:
            self.send_error_response(500, f"Error starting MG import: {e}")

    def start_images_extraction(self):
        global current_process, process_type
        if current_process is not None and current_process.poll() is None:
            self.send_error_response(400, "תהליך אחר כבר רץ ברקע")
            return

        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            selected_suppliers = data.get("selected_suppliers", [])
            sku_list = data.get("sku_list", [])

            if not selected_suppliers or not isinstance(selected_suppliers, list):
                self.send_error_response(400, "selected_suppliers list is required")
                return
            if not sku_list or not isinstance(sku_list, list):
                self.send_error_response(400, "sku_list list is required")
                return

            images_root = str(data.get("images_root", DEFAULT_IMAGES_ROOT)).strip() or DEFAULT_IMAGES_ROOT
            os.makedirs(images_root, exist_ok=True)

            job_payload = {
                "selected_suppliers": [str(s).strip() for s in selected_suppliers if str(s).strip()],
                "sku_list": [str(s).strip() for s in sku_list if str(s).strip()],
                "images_root": images_root,
            }

            os.makedirs(os.path.dirname(IMAGE_EXTRACTION_JOB_PATH), exist_ok=True)
            with open(IMAGE_EXTRACTION_JOB_PATH, "w", encoding="utf-8") as f:
                json.dump(job_payload, f, ensure_ascii=False, indent=2)

            with open(process_log_file, "w", encoding="utf-8") as f:
                f.write("[System] Starting supplier image extraction process...\n")
                f.write(f"[System] Suppliers: {', '.join(job_payload['selected_suppliers'])}\n")
                f.write(f"[System] SKUs queued: {len(job_payload['sku_list'])}\n")

            f_log = open(process_log_file, "a", encoding="utf-8")
            cmd = [sys.executable, "-u", "supplier_image_extraction_runner.py", "--job", IMAGE_EXTRACTION_JOB_PATH]
            current_process = subprocess.Popen(cmd, stdout=f_log, stderr=subprocess.STDOUT)
            process_type = "image-extraction"

            self.send_json_response({
                "success": True,
                "message": "תהליך חילוץ תמונות הופעל בהצלחה",
                "queued_skus": len(job_payload["sku_list"]),
                "selected_suppliers": job_payload["selected_suppliers"],
                "images_root": images_root,
            })
        except Exception as e:
            self.send_error_response(500, f"Error starting image extraction: {e}")

    def update_suppliers_contacts(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            sup_id = data.get("id")
            interval_days = int(data.get("interval_days", 7))
            contact_name = data.get("contact_name", "")
            contact_email = data.get("contact_email", "")
            template_exists = int(data.get("template_exists", 1))
            
            integration_type = data.get("integration_type", "ידני")
            pull_files = data.get("pull_files", "לא מיושם")
            sync_active = data.get("sync_active", "כבוי")
            login_email = data.get("login_email", "")
            login_password = data.get("login_password", "")
            selector_email = data.get("selector_email", "")
            selector_password = data.get("selector_password", "")
            selector_submit = data.get("selector_submit", "")
            selector_download_btn = data.get("selector_download_btn", "")
            selector_checkbox_1 = data.get("selector_checkbox_1", "")
            selector_checkbox_2 = data.get("selector_checkbox_2", "")
            selector_checkbox_3 = data.get("selector_checkbox_3", "")
            selector_checkbox_4 = data.get("selector_checkbox_4", "")
            selector_checkbox_5 = data.get("selector_checkbox_5", "")
            selector_download_excel = data.get("selector_download_excel", "")
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE supplier_contacts
                SET interval_days = ?, contact_name = ?, contact_email = ?, template_exists = ?,
                    integration_type = ?, pull_files = ?, sync_active = ?,
                    login_email = ?, login_password = ?,
                    selector_email = ?, selector_password = ?, selector_submit = ?,
                    selector_download_btn = ?, selector_checkbox_1 = ?, selector_checkbox_2 = ?,
                    selector_checkbox_3 = ?, selector_checkbox_4 = ?, selector_checkbox_5 = ?,
                    selector_download_excel = ?
                WHERE id = ?
            """, (interval_days, contact_name, contact_email, template_exists,
                  integration_type, pull_files, sync_active,
                  login_email, login_password,
                  selector_email, selector_password, selector_submit,
                  selector_download_btn, selector_checkbox_1, selector_checkbox_2,
                  selector_checkbox_3, selector_checkbox_4, selector_checkbox_5,
                  selector_download_excel, sup_id))
            conn.commit()
            conn.close()
            
            self.send_json_response({"success": True})
        except Exception as e:
            self.send_error_response(500, f"Error updating supplier contact: {e}")

    def create_supplier_contact(self):
        try:
            content_length = int(self.headers.get('Content-Length', '0'))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(post_data.decode('utf-8'))

            name = str(data.get("name", "") or "").strip()
            if not name:
                self.send_error_response(400, "supplier name is required")
                return

            try:
                interval_days = int(data.get("interval_days", 7) or 7)
            except Exception:
                interval_days = 7
            if interval_days < 1:
                interval_days = 1

            contact_name = str(data.get("contact_name", "") or "").strip()
            contact_email = str(data.get("contact_email", "") or "").strip()
            try:
                template_exists = int(data.get("template_exists", 0) or 0)
            except Exception:
                template_exists = 0

            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id
                FROM supplier_contacts
                WHERE LOWER(TRIM(name)) = LOWER(TRIM(?))
                LIMIT 1
                """,
                (name,),
            )
            exists_row = cursor.fetchone()
            if exists_row:
                conn.close()
                self.send_error_response(409, "supplier already exists")
                return

            cursor.execute(
                """
                INSERT INTO supplier_contacts (name, interval_days, contact_name, contact_email, template_exists)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, interval_days, contact_name, contact_email, template_exists),
            )
            new_id = cursor.lastrowid
            conn.commit()
            conn.close()

            self.send_json_response({
                "success": True,
                "id": new_id,
                "name": name,
                "message": "הספק נוסף בהצלחה",
            })
        except Exception as e:
            self.send_error_response(500, f"Error creating supplier contact: {e}")

    def get_reports_errors(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, product_id, product_title, error_type, description, created_at
                FROM product_errors
                ORDER BY created_at DESC
            """)
            rows = cursor.fetchall()
            errors = [dict(r) for r in rows]
            conn.close()
            self.send_json_response(errors)
        except Exception as e:
            self.send_error_response(500, f"Error getting product errors: {e}")

    def clear_reports_errors(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM product_errors")
            conn.commit()
            conn.close()
            self.send_json_response({"success": True})
        except Exception as e:
            self.send_error_response(500, f"Error clearing product errors: {e}")

    def export_supplier_prices(self):
        try:
            export_supplier_csv()
            self.send_json_response({"success": True, "message": "קובץ exp_sup.csv נוצר בהצלחה בנתיב C:\\TEMP!"})
        except Exception as e:
            self.send_error_response(500, f"Error exporting prices: {e}")

    def get_supplier_history_file(self, query):
        try:
            file_path = query.get("path", [None])[0]
            if not file_path:
                self.send_error_response(400, "Path is required")
                return
            
            clean_path = os.path.abspath(file_path)
            if not (clean_path.lower().startswith("c:\\temp\\history")):
                self.send_error_response(403, "Access Denied")
                return
                
            if not os.path.exists(clean_path):
                self.send_error_response(404, "File not found")
                return
                
            with open(clean_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
                
            self.send_json_response({
                "path": file_path,
                "filename": os.path.basename(file_path),
                "content": content
            })
        except Exception as e:
            self.send_error_response(500, f"Error reading history file: {e}")

    def sync_supplier(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            supplier_name = str(data.get("supplier_name", "")).strip()
            if not supplier_name:
                self.send_error_response(400, "supplier_name is required")
                return

            script_by_supplier = {
                "מור לוי": "auto_run_morlevi.py",
                "טכנו": "auto_run_techno.py",
                "אמטל": "auto_run_amtel.py",
                "בנדא": "auto_run_benda.py",
                "פייב": "auto_run_five.py",
                "איסטרוניקס": "auto_run_eastronics.py",
                "סי-דאטה": "auto_run_cdata.py",
                "אסוס ROG": "auto_run_asus_rog.py",
            }

            script_name = script_by_supplier.get(supplier_name)
            if not script_name:
                self.send_error_response(400, f"No sync script mapping defined for supplier: {supplier_name}")
                return

            script_candidates = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "helper_scripts", "supplier_sync", script_name),
                os.path.join(r"C:\Temp", script_name),
            ]

            script_path = None
            for candidate in script_candidates:
                if os.path.exists(candidate):
                    script_path = candidate
                    break

            if not script_path:
                self.send_error_response(
                    400,
                    f"Sync script file was not found for supplier '{supplier_name}'. Expected one of: {script_candidates}"
                )
                return
                
            def run_sync():
                start_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    with open(process_log_file, "a", encoding="utf-8", errors="replace") as f:
                        f.write(f"\n[Sync] {start_ts} Starting supplier sync for '{supplier_name}' with script: {script_path}\n")

                    ret = subprocess.run([sys.executable, script_path], capture_output=True, text=True, encoding="utf-8", errors="replace")

                    with open(process_log_file, "a", encoding="utf-8", errors="replace") as f:
                        if ret.stdout:
                            f.write(ret.stdout + ("\n" if not ret.stdout.endswith("\n") else ""))
                        if ret.stderr:
                            f.write("[Sync][stderr]\n" + ret.stderr + ("\n" if not ret.stderr.endswith("\n") else ""))
                        end_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"[Sync] {end_ts} Supplier sync finished for '{supplier_name}' with exit code {ret.returncode}\n")
                except Exception as ex:
                    with open(process_log_file, "a", encoding="utf-8", errors="replace") as f:
                        f.write(f"[Sync][Error] Supplier sync crashed for '{supplier_name}': {ex}\n")
                
            t = threading.Thread(target=run_sync)
            t.daemon = True
            t.start()
            
            self.send_json_response({
                "success": True,
                "message": "סנכרון ברקע הופעל בהצלחה.",
                "supplier_name": supplier_name,
                "script_path": script_path
            })
        except Exception as e:
            self.send_error_response(500, f"Error starting sync: {e}")

if __name__ == "__main__":
    init_db()
    handler = ProductManagerHandler
    
    # Allow restarting server on same port immediately without waiting
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    
    # Daily CSV exporter disabled on request; keep the function available for manual recovery only.
    print("[Scheduler] Daily CSV exporter thread disabled.")

    t2 = threading.Thread(target=automated_processes_loop, daemon=True)
    t2.start()
    print("[Scheduler] Started automated processes scheduler thread.")
    
    with socketserver.ThreadingTCPServer(("", PORT), handler) as httpd:
        print(f"Product Manager Web Server running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server...")
            sys.exit(0)
