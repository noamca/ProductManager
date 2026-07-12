# King Games Automation Manager

This folder contains the duplicated automation project for KING-GAMES product operations.

## Project Structure

- `king_games_product_manager/`
  - Main local dashboard + API server + automation scripts.
  - Core entrypoint: `server.py`.
  - Main database: `products.db`.
- `daily-price-checker/`
  - Daily CSV comparison and report generation.
- Root helper scripts and debug artifacts
  - Legacy and one-off scripts for extraction, checks, and debugging.

## What This System Does

1. Product directory management (categories, products, attributes).
2. Supplier CSV analysis/import (new/updated/unchanged products).
3. Supplier mapping management, preprocess/category-margin flow, and MG/SAP supplier intake exports.
4. Supplier image extraction management with per-supplier script status and local image download orchestration.
5. CMS ingestion automation via Selenium + Chrome DevTools remote debugging.
6. Parameter/options scraping from CMS and schema mapping updates.
7. Daily price checks and markdown reports.

## Development Traceability (Live)

From now on, every development request and implementation must be logged here as a new versioned entry with a date:

- Version format: `vYYYYMMDD-XX`
- Each new change gets its own dated entry
- Every code fix or behavior change must also increment the running app/API version without asking first.

- `LIVE_DEVELOPMENT_HISTORY.md` (human-readable full history)
- `LIVE_DEVELOPMENT_HISTORY.jsonl` (machine-readable log)

### Current Version Entries

- `v20260709-01` | `2026-07-09`
  - Raised runtime version to `v0.10`.
  - Added a new Reports submenu screen: `מוצרים שחזרו לספק`.
  - Added backend endpoint `GET /api/sap/returned-products` that runs the SAP SQL report query for open supplier returns from the last 3 months.
  - Added text search on the new screen across all returned fields and dynamic table rendering of the query result set.

- `v20260708-03` | `2026-07-08`
  - Completed full end-to-end validation on runtime `v0.09`.
  - Verified the supplier intake `5-column MG` export flow works without SAP-SKU completion requirement.
  - Performed a real API run (`analyze` + `export-5col`) and verified actual file creation under `C:\TEMP` with no error response.
  - Validated generated CSV format and encoding on disk: exactly 5 columns per row, with the 4th column empty, encoded as `Windows-1255`.

- `v20260708-02` | `2026-07-08`
  - Raised runtime version to `v0.09`.
  - Added the new supplier intake button `הכנת קובץ ספקים ל MG` to the main intake action row (not only in the preprocess modal).
  - Placed exactly between `התחל ניתוח מחירון` and `יצירת קובץ ל SAP` as requested.
  - Wired the new button to export the 5-column MG suppliers CSV from processed intake session data.

- `v20260708-01` | `2026-07-08`
  - Raised runtime version to `v0.08`.
  - Added a new supplier intake action button in the preprocess mapping modal, placed immediately after the blue "התחל עיבוד" button: `הכנת קובץ ספקים ל MG`.
  - Implemented immediate MG supplier export in true 5-column format from processed intake session rows (same processed data flow used by SAP intake export).
  - Export format is CSV in `Windows-1255` encoding with exactly: `ספק, מקט, תיאור, עמודה ריקה, מחיר מחושב`.

- `v20260707-09` | `2026-07-07`
  - Added a verified technical Python scripts map to this README.
  - Documented which scripts are definitely linked at runtime (entrypoints/subprocess workers), which scripts are reusable modules, and which are mostly one-off analysis/inspection utilities.
  - Added explicit certainty levels for "in active flow" vs "utility/debug" script groups.

- `v20260707-08` | `2026-07-07`
  - Raised runtime version to `v0.07`.
  - Hardened supplier intake preview rendering by returning `display_toggles` from the analyze/preprocess API response itself, so the preview table now follows the supplier's saved display settings even when local mapping state is stale.

- `v20260707-07` | `2026-07-07`
  - Raised runtime version to `v0.06`.
  - Fixed supplier intake preview table rendering so saved `display_toggles` now actually control visible columns, filters, and table headers for suppliers such as מור לוי.

- `v20260707-06` | `2026-07-07`
  - Raised runtime version to `v0.05`.
  - Fixed supplier import file-selection robustness so choosing the same pricelist file again still triggers loading, and analyze falls back to the current file input when state was not populated yet.

- `v20260707-05` | `2026-07-07`
  - Raised runtime version to `v0.04`.
  - Established project rule: every fix or code change increments version automatically without requiring explicit approval.

- `v20260707-04` | `2026-07-07`
  - Moved supplier field mappings from legacy file storage to DB-backed persistence with normalized supplier-key lookup and legacy JSON migration support.
  - Added CSV delimiter auto-detection in supplier intake flows and restored visible intake preview rows in the import UI.
  - Enforced available-only supplier intake processing and changed MG supplier export flow to generate a full 266-column MG file with the first identifier column left blank for new products.
  - Added supplier creation directly from the supplier management screen and improved long-running preprocess/apply UX with progress overlay, percentage feedback, and lighter result rendering.
  - Reworked supplier image extraction management to merge against the unified supplier catalog and show real runtime status (`ready`, `missing_file`, `disabled`, `not_configured`) based on actual script-file existence.
  - Added dedicated supplier intake history screen under the Suppliers menu and switched it to read from a real `supplier_intake_history` table populated from actual intake-analysis sessions instead of only final import records.

- `v20260707-03` | `2026-07-07`
  - Enlarged supplier edit popup to 80% screen width with improved internal scrolling so all fields are reachable.
  - Reworked supplier tab-field mapping UI into true tabbed navigation (one selected tab at a time), with a full-tab `tab_enabled` toggle inside each selected tab.

- `v20260707-02` | `2026-07-07`
  - Added runtime identity endpoint `GET /api/health/version` for deterministic verification of the active server instance.
  - Added unified supplier catalog endpoint `GET /api/suppliers/catalog` that merges suppliers from contacts, pricelist scripts, image scripts, field mappings, and SAP mappings.
  - Unified supplier process retrieval so import supplier options are populated from a canonical catalog and missing process rows are auto-filled as `manual_csv` defaults.
  - Updated UI app version badge to `v0.03` and ensured supplier edit modal loads pricelist process data before rendering sample path/mapping controls.

- `v20260707-01` | `2026-07-07`
  - Added VAT setting to system settings and wired pricing flow to apply VAT before margin.
  - Added supplier/tab field-mapping infrastructure and preprocess modal flow for supplier pricelist ingestion.
  - Moved supplier pricelist mapping management into the supplier edit popup, including sample file upload, tab mapping, category margin controls, and brand toggles.
  - Removed the full intake rows table from the import screen per updated UI requirement.

Canonical launcher for the main app:

- `START_MAIN_MANAGER.bat`

## Quick Start

### 1) Open terminal in the project folder

```powershell
cd C:\Projects\KINGGAMES
```

### 2) (Recommended) Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3) Install Python dependencies

Install the required Python packages:

```powershell
pip install -r requirements.txt
```

If you want to install only the core runtime pieces manually, use:

```powershell
pip install selenium pillow requests beautifulsoup4 lxml pyodbc google-api-python-client google-auth openpyxl xlrd==2.0.1
```

### 4) Run the system

Preferred launcher:

```powershell
.\START_MAIN_MANAGER.bat
```

If you want to run the main app directly from the project manager folder:

```powershell
cd C:\Projects\KINGGAMES\king_games_product_manager
python server.py
```

Then open:

- `http://127.0.0.1:8000`

### 5) What should be running

For normal operation, the important components are:

- `START_MAIN_MANAGER.bat` to launch the main dashboard/server stack.
- `king_games_product_manager\server.py` as the local API and UI server.
- `products.db` as the main SQLite database.

For supplier or price workflows, run the specific script from the same environment only when needed. Examples include `run_price_check.py`, `process_google_prices_update.py`, `process_google_prices_update_clone.py`, `mg_import_runner.py`, and `scrape_cms_parameters.py`.

## Runtime Components

- UI: `index.html`, `style.css`, `app.js` (served by `server.py`).
- API: endpoints under `/api/*` in `server.py`.
- DB: SQLite (`products.db`) with products, categories, attributes, ingestion runs, supplier contacts, supplier intake analysis cache, supplier intake history, supplier field mappings, and SAP supplier mappings.
- Browser automation:
  - `browser_manager.py`
  - `update_products_batch_2.py`
  - `scrape_cms_parameters.py`
  - `run_price_check.py`

## Python Scripts Map (Verified)

This project contains many Python files. They are not all part of the same runtime path.

### A) Definitely linked in active runtime flow (high certainty)

- Main entrypoint:
  - `king_games_product_manager/server.py`
  - launched by `START_MAIN_MANAGER.bat` -> `king_games_product_manager/start_local_product_manager_server.bat`
- Worker scripts launched by `server.py` via subprocess:
  - `audit_cms_products.py`
  - `run_price_check.py`
  - `scrape_cms_parameters.py`
  - `update_products_batch_2.py`
  - `mg_import_runner.py`
  - `supplier_image_extraction_runner.py`
- Supplier automation mapping invoked by `server.py` (if configured and files exist):
  - `auto_run_morlevi.py`, `auto_run_techno.py`, `auto_run_amtel.py`, `auto_run_benda.py`, `auto_run_five.py`, `auto_run_eastronics.py`, `auto_run_cdata.py`, `auto_run_asus_rog.py`

### B) Reusable internal modules (imported by other local scripts)

- `replace_desktop_tree_component.py`
  - imported by `server.py`.
- `browser_manager.py`
  - imported by `run_price_check.py` and related tests.
- `image_resolver.py`
  - imported by `supplier_image_extraction_runner.py` and related tests.

### C) The large script set you asked about (`analyze_categories.py` ... `write_category_options.py`)

Most files in this range are utility/debug/inspection scripts, typically run manually and not auto-launched by `server.py`.

- Analysis utilities (`analyze_*.py`):
  - Example: `analyze_categories.py`, `analyze_csv.py`, `analyze_to_file.py`.
- Inspection utilities (`inspect_*.py`):
  - DB/UI probes and reverse engineering helpers.
- Validation utilities (`check_*.py`):
  - Form fields, ports, saves, TinyMCE behavior checks.
- One-off data/scripts (`find_*`, `decode_*`, `dump_*`, `update_product_*`, etc.):
  - Targeted experiments, ad-hoc fixes, historical debugging.
- Selenium helper probes like `write_category_options.py`:
  - typically manual interaction scripts, not background workers.

### D) What is certain vs uncertain

- Certain (high confidence):
  - Which script is main runtime entrypoint (`server.py`).
  - Which scripts are launched by server subprocess calls.
  - Which local modules are imported by other local Python files.
- Less certain without runtime telemetry/git recency analysis:
  - Whether every utility/debug script is still actively used today.
  - Historical one-off scripts that may no longer be part of current operations.

### E) Practical rule of thumb

- If a script is referenced by `server.py`, launcher BATs, or scheduler config: treat as production flow.
- If a script is only `inspect_*`, `check_*`, `analyze_*`, or `test_*`: treat as manual utility unless explicitly wired into server/launcher/task flow.

## Supplier Workflows

- Supplier management:
  - Add suppliers directly from the UI.
  - Edit contact/integration metadata from the supplier modal.
- Supplier import:
  - Analyze supplier pricelists with DB-backed field mappings.
  - Preprocess categories/tabs before applying the import.
  - Intake analysis keeps real session history in `supplier_intake_history`.
  - Availability filtering keeps only products marked available.
- Supplier exports:
  - SAP intake export is session-based.
  - MG export from supplier intake generates a 266-column MG-format file with blank first identifier for new products.
- Supplier images:
  - Image extraction uses a supplier-image registry merged with the unified supplier catalog.
  - Only suppliers with an enabled extractor and an existing loader script are considered runnable.

## Supplier Screens

- `ניהול ספקים`
  - Supplier list, reminder state, contact/integration editing, and direct supplier creation.
- `קליטת מחירון ספק`
  - CSV/Excel supplier intake analysis, preprocess modal, mapping controls, SAP completion flow, and MG export.
- `חילוץ תמונות ספקים`
  - Supplier image extractor registry, runtime script availability status, SKU input, and live log polling.
- `הסטוריית קליטות ספקים`
  - Dedicated screen for actual supplier intake-analysis sessions loaded from `supplier_intake_history`.

## Critical Security Notes

This codebase currently contains hardcoded credentials and absolute user-specific paths in some scripts.

Before moving to shared production usage:

1. Move credentials to environment variables.
2. Create a central config file for all paths.
3. Restrict local server access to localhost only.
4. Rotate any credentials that were committed in scripts.

## Operational Flow

1. Start `server.py`.
2. Use dashboard tabs to:
   - inspect/update products,
   - run supplier ingestion analysis/import,
  - manage supplier contacts, mappings, and image-extraction capabilities,
  - review supplier intake history sessions,
   - start ingestion/crawler background tasks,
   - review logs and runs.
3. Run `run_price_check.py` (directly or from UI action) to refresh prices and generate reports.

## Common Files to Check While Debugging

- `process_run.log` (current background process output)
- `products.db` (current data state)
- `allowed_attribute_values.json` and `mapping_schema.json` (attribute schema/mapping)
- `../daily-price-checker/reports/` (generated markdown reports)

## Suggested Next Hardening Steps

1. Add `.env` support and remove inline credentials.
2. Add `requirements.txt` pinned versions.
3. Add startup validator script (`python doctor.py`) for DB, browser, and path checks.
4. Add backup/export script for `products.db` before ingestion runs.
