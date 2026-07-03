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
3. CMS ingestion automation via Selenium + Chrome DevTools remote debugging.
4. Parameter/options scraping from CMS and schema mapping updates.
5. Daily price checks and markdown reports.

## Quick Start

### 1) Open terminal in project manager folder

```powershell
cd C:\Users\USER\OneDrive\Documents\Projects\Kinggames\king_games_product_manager
```

### 2) (Recommended) Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3) Install Python dependencies

This repository does not include a dependency lock file, so install the known required packages:

```powershell
pip install selenium pillow requests
```

If you run scripts that parse/edit HTML in future, also install:

```powershell
pip install beautifulsoup4 lxml
```

### 4) Run the local dashboard server

```powershell
python server.py
```

Then open:

- `http://127.0.0.1:8000`

## Runtime Components

- UI: `index.html`, `style.css`, `app.js` (served by `server.py`).
- API: endpoints under `/api/*` in `server.py`.
- DB: SQLite (`products.db`) with products, categories, attributes, ingestion runs, supplier history, contacts.
- Browser automation:
  - `browser_manager.py`
  - `update_products_batch_2.py`
  - `scrape_cms_parameters.py`
  - `run_price_check.py`

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
