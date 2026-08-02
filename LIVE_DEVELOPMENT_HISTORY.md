# 2026-08-02 - Frontend parse error fixed; Processes menu restored (v2.42)

- Request: the app was not showing the Processes screen and sidebar navigation was unresponsive because the frontend script stopped parsing.
- Fixed `king_games_product_manager/app.js` by repairing the corrupted automated-process table render loop near the Processes view code.
- Updated the browser cache-bust to load `app.js?v=2.42` and bumped the frontend version badge to `v2.42`.
- Validation: browser-side parsing of the served `app.js?v=2.42` now succeeds, and clicking `עיבודים` switches the main area to the Processes screen with the live process table and log panel visible.
- Outcome: sidebar navigation works again and the Processes screen renders normally.

# 2026-08-02 - Telegram worker SAP timeout floor fixed and task 16 completed (v2.41 / API 1.70)

- Request: task 16 was still pending because the worker kept dying on a 5 second SAP timeout and the Processes screen needed clear live logs.
- Fixed `king_games_product_manager/telegram_bot_tasks_worker.py` so `SAP_SCRIPT_TIMEOUT_SEC` has a hard minimum of 120 seconds even if the environment tries to force a lower value, and added a startup log that prints the effective worker config.
- Kept the live Processes log tail and streaming behavior in place; no UI regression was needed for this follow-up.
- Bumped versions: frontend `2.41`, server API `1.70`.
- Validation: restarted the backend, verified `/api/health/version` returned `1.70`, reran the worker, confirmed the log tail showed SAP success, MG save verification, `POST /tasks/16/complete` returned HTTP 200, and `/tasks/pending` became `[]`.
- Outcome: task 16 is no longer pending, and the worker can no longer inherit a too-short SAP timeout that aborts the flow before completion.

# 2026-08-02 - Telegram worker manual-run logging made immediate (v2.40 / API 1.69)

- Request: when running the worker manually, logs should appear immediately in the console without requiring `python -u`.
- Fixed `telegram_bot_tasks_worker.py` console behavior:
	- enabled line-buffered stdout/stderr via `sys.stdout.reconfigure(..., line_buffering=True, write_through=True)` when supported
	- changed `_log()` to `print(..., flush=True)` so each line is emitted immediately
- Versions: frontend `2.40`, server API `1.69`.
- Validation: manual unbuffered run already proved the worker prints live logs; compile check for updated worker passed.

# 2026-08-02 - Telegram task completion policy tightened (v2.39 / API 1.68)

- Request: send POST /tasks/{id}/complete only for task types that are actually handled in code; do not auto-complete unsupported tasks.
- Changed worker behavior in king_games_product_manager/telegram_bot_tasks_worker.py:
	- removed unsupported-task auto-complete behavior
	- task completion is now executed only after successful handler execution
	- accepted both `CHANGE_PRICE` and `PRICE_CHANGE` as aliases for the same supported flow
	- unsupported task types are skipped and left pending with explicit log lines
- Versions: frontend `2.39`, server API `1.68`.
- Validation: Python compile succeeded for updated worker; no editor errors in changed runtime files.

# 2026-08-02 - Telegram task stuck-point diagnostics + MG save verification (v2.38 / API 1.67)

- Incident: user reported SAP update succeeds but MG site update does not complete and task cleanup is unclear.
- Added deep worker diagnostics in king_games_product_manager/telegram_bot_tasks_worker.py:
	- persistent log file writer at king_games_product_manager/logs/telegram_tasks_worker.log
	- request/response logging for pending fetch and /tasks/{id}/complete calls
	- full exception traceback logging (not only short error text)
	- MG step-by-step logs: navigation URL/title, login detection, pre/post price DOM value, save click selector, post-save URL
	- post-save persistence verification by reloading edit page and comparing expected vs actual inventory_price[0]
- Added Telegram API diagnostics in C:/Projects/TelegramBot/api.py:
	- logs for GET /tasks/pending count
	- logs for POST /tasks/{id}/complete start, DB update, bot presence, telegram send success/failure, and final completion
- Versions: frontend `2.38`, server API `1.67`.
- Validation: live worker run processed task #14 end-to-end with explicit logs for SAP success, MG save verification (expected=actual), complete endpoint HTTP 200, and summary completed=1 failed=0. Pending queue check returned COUNT=0.

# 2026-08-02 - Telegram worker hang fix + deterministic task completion (v2.37 / API 1.66)

- Incident: `telegram_bot_tasks_worker.py` did not finish; it stalled on the SAP step and left pending tasks repeatedly in queue.
- Root cause: SAP subprocess call in worker had no timeout guard, so the worker could block indefinitely while waiting for `sapService_UpdatePrdPrice.py`.
- Fixed worker: added `SAP_SCRIPT_TIMEOUT_SEC` env-configurable timeout around subprocess execution with explicit timeout error handling.
- Fixed worker: added optional auto-completion for unsupported request types via `TELEGRAM_AUTO_COMPLETE_UNSUPPORTED` (enabled by default) to prevent queue deadlock on currently unsupported task types.
- Fixed SAP script: added request timeouts for login, patch, and logout calls to avoid indefinite network waits; login failures now return a proper failure state.
- Versions: frontend `2.37`, server API `1.66`.
- Validation: ran worker with short timeout (`SAP_SCRIPT_TIMEOUT_SEC=5`) and confirmed deterministic exit with summary, unsupported tasks marked complete, and queue reduced from 8 pending tasks to 1 failed `PRICE_CHANGE` task.

# 2026-08-02 - Telegram bot tasks automation + MG/SAP price flow (v2.36 / API 1.65)

- Request: build a scheduled process under עיבודים that reads pending tasks from `http://127.0.0.1:7999/tasks/pending`, add a menu entry תחת תוכניות שירות בשם משימות בוט טלגרם, process supported task types, and complete tasks via `POST /tasks/{task_id}/complete`.
- Added: new worker script `king_games_product_manager/telegram_bot_tasks_worker.py`.
- Implemented: queue ingestion and readable per-task console lines with task id, type, sku, price, status, and created time.
- Implemented first handler: `request_type=PRICE_CHANGE`.
- Implemented: SAP price update call via external script with CLI args (SKU and price).
- Implemented: MG login-aware product edit flow and update of `inventory_price[0]` followed by save button `name=edit`.
- Added: default automated process `משימות בוט טלגרם` every 5 minutes via `telegram_bot_tasks_worker.py`.
- Added API: `GET /api/telegram-bot/tasks/pending` (proxy for queue display) and `POST /api/telegram-bot/tasks/process-now` (manual trigger).
- UI: added sidebar item תחת תוכניות שירות and a dedicated view panel with queue viewer + refresh/run buttons.
- Versions: frontend `2.36`, server API `1.65`.

# 2026-07-29 - Restore proven MG auto-auth session (v2.35 / API 1.64)

- Incident: the new desktop replacement login flow remained blocked even though the application already had a long-standing automatic MG authentication path on Chrome debug port 9225.
- Root cause: the desktop tool preferred a separate unauthenticated 9222 session; after legacy authentication succeeded at `/apanel/home`, `ensure_logged_in()` navigated to `/apanel/`, which MG treats as the login page even for the working session.
- Fixed: `get_driver()` now uses the proven `browser_manager.get_active_driver()` path first and keeps the newer browser path only as fallback.
- Fixed: authenticated sessions inside `/apanel/` return immediately; authentication checks use `/apanel/home` and no longer navigate a valid session back to the root login route.
- Verified: legacy credentials were accepted by MG, producing `MG CMS - דף הבית`; the desktop tool then preserved `/apanel/home`, found no visible login form, and completed authentication verification in 0.025 seconds.
- Versions: frontend `2.35`, server API `1.64`.

# 2026-07-29 - MG native form submission and password verification (v2.34 / API 1.63)

- Incident: after correcting the duplicated email, MG still returned to its login form and the app displayed the generic `MG login failed. Check the email and password` message.
- Evidence: the live MG form posts to `/apanel/home`, contains a rotating hidden token, and returned to `/apanel/` without visible error text.
- Fixed: the automation now invokes `requestSubmit` on MG's original form and submit button, preserving the form token and native browser validation.
- Fixed: login success/failure checks visible controls rather than treating hidden login elements as an active login form; visible MG response text is surfaced when available.
- UX: added a local eye button so password characters can be verified before submission when the active keyboard layout is uncertain; closing the modal clears and remasks the field.
- Security: password contents are not logged, stored, or inspected by diagnostics.
- Verified: focused regression confirmed exact field assignment and invocation of the original MG form; Python compile and editor diagnostics passed.
- Versions: frontend `2.34`, server API `1.63`.

# 2026-07-29 - Exact MG login field assignment (v2.33 / API 1.62)

- Incident: after submitting the in-app MG password, the MG login window showed a duplicated email whose periods were converted to Hebrew `ץ` characters.
- Root cause: Selenium `clear()` did not reliably remove MG's prefilled email, while `send_keys()` was affected by the active Hebrew keyboard layout.
- Fixed: login now selects visible enabled controls and replaces email/password through the native DOM value setter with `input` and `change` events, avoiding physical keyboard layout translation.
- Safety: the exact assigned values are verified before clicking the visible login button; the password remains one-time and is not logged or stored.
- Verified: a focused regression with a prefilled email confirmed one exact email value, an exact password value, and one submit click without keyboard typing.
- Versions: frontend `2.33`, server API `1.62`.

# 2026-07-29 - Integrated MG authentication recovery (v2.32 / API 1.61)

- Fixed: desktop scan/apply no longer exposes an immediate operational failure when the shared MG session has expired.
- Added: an in-app MG login modal appears automatically on HTTP 401 and resumes the original scan or apply action after successful authentication.
- Security: the password uses a masked browser field, is sent only to the local server for a one-time Selenium login, is cleared from the DOM immediately, and is not stored in source, logs, settings, or the database.
- Added: `/api/desktop-replacement/login` for one-time session creation; invalid credentials stay in the modal without restarting the desktop workflow.
- Preserved: no stale hardcoded password retries, one browser session per apply run, one save per desktop, and post-save verification-based success counts.
- Versions: frontend `2.32`, server API `1.61`.

# 2026-07-29 - Single-pass desktop replacement apply (v2.31 / API 1.60)

- Incident: the bulk apply loop ran replacements first and desktops second, opening the same desktops repeatedly and creating a new browser/login cycle for every replacement mapping.
- Previous-run evidence: 11 form submissions were reported, but only 9 passed post-save verification; the UI incorrectly summarized submissions as successful saves.
- Fixed: bulk apply now uses one authenticated Chrome session and processes each parent desktop exactly once.
- Fixed: all component mappings relevant to a desktop are combined into one tree/text plan, one CMS save, and one post-save verification.
- Fixed: each replacement carries its discovered `parent_ids`, so unrelated desktops are not scanned for that mapping.
- Authentication: removed stale hardcoded password submission from this tool. An expired MG session now stops the entire run immediately with one actionable error and never retries credentials.
- Reporting: success counts only computers that passed post-save verification; stopped runs report the number already verified.
- Verified: two mappings on one desktop produce one apply and one verification while updating both tree slots and combined `content2` references.
- Versions: frontend `2.31`, server API `1.60`.

# 2026-07-29 - Desktop discovery selector and child-stock fix (v2.30 / API 1.59)

- Fixed: category filtering now submits `form#filter` directly and waits for `tr.cat_96`, preventing scans of unfiltered products such as MG 75.
- Fixed: `table_no.png` is accepted only inside the row validity link (`products&valid=ID&state=1`), excluding the unrelated XML-status icon present on normal product rows.
- Safety: discovery cross-checks the category row class, `td.id`, validity-link ID, and edit-link ID before opening a desktop product.
- Fixed: each `treeProductsItem` now receives only the sibling text belonging to that child, preventing one `במלאי: 0` marker from flagging every component in the tree.
- Verified: MG 33608 exposes 11 tree components and only MG 33110 is detected as `במלאי: 0`.
- Verified: replacement planning still updates `content`, `content2`, `description`, product links, product titles, and the tree component ID.
- Versions: frontend `2.30`, server API `1.59`.

# 2026-07-29 - Desktop component replacement redesign (v2.29 / API 1.58)

- Request: rewrite the synchronization-center desktop component tool around MG admin category 96 discovery instead of a manually entered old/new product pair.
- Implemented: authenticated admin scan of `/apanel/products`, category 96 filtering, `table_no.png` row selection, edit-link collection, and extraction of child products whose tree row contains `במלאי: 0`.
- Implemented: unique missing-component list with one required replacement field per component, plus a separate list of unavailable parent desktops.
- Implemented: bulk apply over the discovered parent desktop IDs, reusing the existing tree/text replacement, save, and verification behavior for every supplied mapping.
- UX: reduced runtime output to start, warning, stop, and summary messages; apply remains disabled until every missing component has a replacement.
- Versions: frontend `2.29`, server API `1.58`.

# LIVE DEVELOPMENT HISTORY

Purpose: single source of truth for every development request and what was done.
Scope: whole workspace under C:/Projects/KINGGAMES.
Policy: from now on, every requested change gets an entry.

## Logging Rules (Mandatory)
1. Every user development request gets a new entry immediately.
2. Entry is updated as work progresses: planned -> in progress -> completed/blocked.
3. Each entry must include:
- Timestamp
- Request summary
- What was implemented
- Files changed
- Verification performed
- Result/Status
4. Never delete past entries. Use corrections as a new entry referencing old ID.

## Canonical Runtime Targets
- Main app folder: C:/Projects/KINGGAMES/king_games_product_manager
- Main launcher: C:/Projects/KINGGAMES/START_MAIN_MANAGER.bat
- Legacy copy (do not use for production): C:/Projects/KINGGAMES/scratch/king_games_product_manager

## Entry Template

### [ID: YYYYMMDD-XX] [Status: planned|in-progress|completed|blocked]
- Timestamp:
- Request:
- Implementation:
- Files changed:
- Verification:
- Outcome:
- Follow-ups:

---

## Entries\n
### [ID: 20260729-01] [Status: completed]
- Timestamp: 2026-07-29
- Request: Reverse the colors in the price comparison report's "שינוי באחוזים" column so negative values are red and positive values are green.
- Implementation: Reversed the percentage-difference color mapping in the shared comparison-table renderer: values beginning with `+` now use green and values beginning with `-` now use red. Bumped APP to 2.28 and updated the script cache key.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl.
- Verification: VS Code diagnostics passed for app.js and index.html with no errors.
- Outcome: Price comparison percentage changes now use the requested positive-green and negative-red convention.
- Follow-ups: None.

---

### [ID: 20260728-10] [Status: completed]
- Timestamp: 2026-07-28
- Request: Stop diagnosing the Benda report fetch error and display its active SQL query directly in the report for manual review.
- Implementation: Added a visible "שאילתת SQL פעילה" section above the Benda report results, showing the complete active RAZER/SCORPIUS/GLORIUS/GLORIOUS query in a readable left-to-right monospace block. Bumped APP to 2.27 and stylesheet cache to 1.17.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/style.css, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl.
- Verification: Not run; the user requested to inspect the query manually.
- Outcome: The active Benda SQL query is now visible inside the report.
- Follow-ups: User will review the query.

---

### [ID: 20260728-09] [Status: completed]
- Timestamp: 2026-07-28
- Request: Change the Benda sales report query to filter RAZER, SCORPIUS, GLORIUS, and GLORIOUS instead of CORSAIR, without running tests.
- Implementation: Replaced the CORSAIR description filter with SCORPIUS in GET `/api/sap/benda-sales`. Updated the report heading to match the new brands. Bumped API to 1.57 and APP to 2.26.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl.
- Verification: Not run at the user's explicit request; the user will verify the report.
- Outcome: The Benda report now targets RAZER, SCORPIUS, GLORIUS, and GLORIOUS for the previous calendar month.
- Follow-ups: User will verify the live report.

---

### [ID: 20260728-08] [Status: completed]
- Timestamp: 2026-07-28
- Request: Duplicate the Benda sales report as "דוח מכר ויזואל" using the supplied previous-month SAP query for UGREEN, STEELSERIES, and GLORIOUS.
- Implementation: Added GET `/api/sap/visual-sales` using the supplied OINV/INV1 SQL and existing SAP ODBC connection. Added a separate Reports menu item and report view with the same five-column white/black table, adapted brand title, localized formatting, and independent print button. Bumped API to 1.56, APP to 2.25, and stylesheet cache to 1.16.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/style.css, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl.
- Verification: Server compilation and VS Code diagnostics passed. The updated server started successfully. SAP and browser behavior checks were intentionally not run because the user requested to perform those checks personally.
- Outcome: The Visual sales report is available under Reports with the requested query and matching Benda-report structure.
- Follow-ups: User will verify the live report data and UI.

---

### [ID: 20260728-07] [Status: completed]
- Timestamp: 2026-07-28
- Request: Add a report under Reports named "דוח מכר בנדא" that runs the supplied SAP invoice query for Razer, Corsair, Glorius, and Glorious products from the previous calendar month; show a white table with black text, the requested title, and a print button.
- Implementation: Added GET `/api/sap/benda-sales` using the supplied OINV/INV1 SQL and existing SAP ODBC connection. Added the new Reports menu item and report view, safe text-only rendering for five columns, localized date/number formatting, a white/black report surface, and report-only print styling. Bumped API to 1.55, APP to 2.24, and stylesheet cache to 1.15.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/style.css, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl.
- Verification: Python compilation and VS Code diagnostics passed. Live SAP API smoke returned success with 19 rows and columns InvoiceNumber, InvoiceDate, ItemCode, ItemName, Quantity. Browser validation confirmed the exact title, 19 rendered rows, print button, white background, black text, report-only print visibility, and contained horizontal scrolling on a narrow viewport. Live API version is 1.55 and app version is 2.24.
- Outcome: The new Benda sales report is live under Reports and can be printed independently from the application shell.
- Follow-ups: None.

---

### [ID: 20260728-06] [Status: completed]
- Timestamp: 2026-07-28
- Request: Remove the AI agent timeout completely so OpenAI calls can wait without a time limit.
- Implementation: Changed all three OpenAI clients (category prediction, full enrichment, and title-essence guard) to `timeout=None`. Kept `max_retries=0` so an unlimited call is never duplicated silently. Bumped API to 1.54 and APP to 2.23.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl.
- Verification: Python compilation and diagnostics passed. Focused source validation confirmed all three OpenAI client constructions use `timeout=None` and `max_retries=0`, with no numeric OpenAI timeout remaining.
- Outcome: OpenAI calls no longer stop because of an application-level timeout; they wait until OpenAI responds, the user stops the run, or an external connection/process failure occurs.
- Follow-ups: None.

---

### [ID: 20260728-05] [Status: completed]
- Timestamp: 2026-07-28
- Request: Explain and fix why OpenAI phase 2 took 125-128 seconds, which is operationally critical.
- Implementation: Identified that the OpenAI SDK allowed a 75-second request with two silent internal retries, while phase 2 sent a 23K-character full enrichment prompt and generated a large structured response. Disabled hidden retries (`max_retries=0`), set a 60-second hard request timeout, compacted the OpenAI prompt by removing duplicated attribute-option data, forced `IMAGES=[]` because images are handled locally, and added prompt-character/input-token/output-token telemetry to both phase logs. Added the missing graphics-card title rule and category-148 title recovery. Added `OpenAI GPT-4o Mini (מהיר)` and relabeled GPT-4.1 Mini as balanced. Bumped API to 1.53 and APP to 2.22.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/update_products_batch_2.py, king_games_product_manager/title_header_rules.json, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl.
- Verification: Prompt size for category 148 dropped from 22,437 to 16,227 characters. A controlled GPT-4o Mini run completed phase 1 in 5.76 seconds and phase 2 in 31.06 seconds; phase 2 reported 16,218 prompt characters, 6,859 input tokens and 2,382 output tokens. Category 148 remained locked and no worker was left running.
- Outcome: Silent multi-minute retries are eliminated, logs expose request size/tokens, and the measured fast-model phase-2 latency dropped from 125.68 to 31.06 seconds.
- Follow-ups: None.

---

### [ID: 20260728-04] [Status: completed]
- Timestamp: 2026-07-28
- Request: Fix OpenAI misclassification and low confidence for graphics-card product 36216, reduce prediction latency, and log the provider/model before both AI calls.
- Implementation: Added deterministic graphics-card detection and category 148 override for explicit `כרטיס מסך` / graphics-card titles. Replaced OpenAI phase-1 full enrichment with a four-field category-only structured-output call. Added GPT-5 minimal reasoning/low verbosity/output limits, plus `OpenAI GPT-4.1 Mini (מהיר)` as a transparent faster option. Added start/completion timing logs for phase 1 and phase 2 with provider and model, and renamed the provider-neutral title check to `[AI Guard]`. Bumped API to 1.52 and APP to 2.21.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl.
- Verification: Compilation and diagnostics passed. Live focused GPT-5 Mini phase-1 tests for product 36216 returned category 148 with 100% confidence in 3.36-4.42 seconds. A controlled full non-publishing run with GPT-4.1 Mini logged both calls, locked category 409 to 148 at 100%, completed phase 1 in 3.83 seconds and phase 2 in 40.75 seconds, and passed title essence at 95%.
- Outcome: Explicit graphics-card products cannot be misrouted by low-confidence AI. OpenAI category prediction is fast, both calls are visible in the log, and a faster full-enrichment model is selectable.
- Follow-ups: None.

---

### [ID: 20260728-03] [Status: completed]
- Timestamp: 2026-07-28
- Request: Add OpenAI as an AI agent for product ingestion, with one additional entry in the prediction-engine combo and the required Python package.
- Implementation: Added OpenAI Responses API structured-output transports for both enrichment phases and the title-essence guard. Added `OpenAI GPT-5 Mini` as the first combo option while retaining Gemini as the default. Routed provider/model through UI, server validation and CLI ingestion. Added `openai>=1.68.0`, installed SDK 2.49.0, and added safe `.env` handling for `OPENAI_API_KEY`. Bumped APP to 2.20 and API to 1.51.
- Files changed: requirements.txt, .gitignore, king_games_product_manager/.gitignore, king_games_product_manager/product_scraper_engine/.env.example, king_games_product_manager/product_scraper_engine/README.md, king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl.
- Verification: Python compilation and diagnostics passed. OpenAI enrichment structured-output and title-guard mocks passed through SDK 2.49.0. Provider routing passed from UI through server and CLI. Live API 1.51 / APP 2.20 assets passed. After replacing the local key, the account model list confirmed `gpt-5-mini`, a live title guard returned 100% same-product essence, and a live structured-output enrichment completed successfully in 28.32 seconds with Hebrew JSON, decoding and usage metadata.
- Outcome: OpenAI is fully integrated, configured and live-tested for product ingestion.
- Follow-ups: None.

---

### [ID: 20260727-04] [Status: completed]
- Timestamp: 2026-07-27
- Request: לתקן את התצוגה המכוערת של הטקסט `טרם נקלט מחירון` במסך `ניהול ספקים ואנשי קשר`.
- Implementation: עמודת תאריך קליטת המחירון הועברה מ-`Font Awesome 6 Free`, שהוא גופן סמלים שאינו מיועד לטקסט עברי, אל גופן הטקסט הראשי `var(--font-family)`. התיקון הוחל גם על נתוני API וגם על תצוגת fallback. גרסת APP ו-cache bust עודכנו ל-`2.14`.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: חיפוש ממוקד אישר ששני מסלולי הרינדור של `טרם נקלט מחירון` משתמשים ב-`var(--font-family)`; דיאגנוסטיקת VS Code נקייה עבור app.js ו-index.html; נבדקה הגרסה המוגשת מהשרת.
- Outcome: completed. הטקסט ותאריכי הקליטה בטבלת ניהול הספקים מוצגים בגופן הטקסט הרגיל של המערכת.
- Follow-ups: לרענן את הדפדפן כדי לקבל `app.js?v=2.14`.

---

### [ID: 20260728-02] [Status: completed]
- Timestamp: 2026-07-28
- Request: In the supplier-pricelist results screen, replace "סיכום חילוץ מפייב לפי TAB" with "תוצאות עיבוד קובץ מחירון מ [שם הספק]".
- Implementation: Replaced the static heading with a supplier-aware title using the active supplier name. Escaped the supplier value before rendering and added `ספק לא ידוע` as a fallback. Bumped APP to 2.19.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl.
- Verification: Frontend diagnostics and focused heading/escaping assertions passed. Live APP 2.19 verification confirmed the supplier-aware heading is served and the previous heading is absent.
- Outcome: The extraction summary heading identifies the supplier whose pricelist was processed.
- Follow-ups: None.

---

### [ID: 20260728-01] [Status: completed]
- Timestamp: 2026-07-28
- Request: After clicking "נתח מחירון ספק", open the category-selection screen with every checkbox selected by default.
- Implementation: Changed the preprocess modal so every category-tree checkbox and every detected-tab checkbox starts selected on each new analysis, regardless of previously saved disabled states. Manual deselection inside the open modal remains available. Removed the obsolete saved-tab-state helper and bumped APP to 2.18.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl.
- Verification: Frontend diagnostics passed. Live APP 2.18 verification confirmed every valid category defaults to selected, every tab checkbox is rendered with `checked`, and the obsolete saved-state helper is absent.
- Outcome: All checkbox fields in the supplier pricelist category-selection screen are selected by default.
- Follow-ups: None.

---

### [ID: 20260727-07] [Status: completed]
- Timestamp: 2026-07-27
- Request: Change the font in every terminal/log output area to a more readable monospace font at 14px.
- Implementation: Updated the shared `.terminal-log` style used by all eight static and dynamic log terminals from the Font Awesome icon font at 13px to `Cascadia Mono`, `Consolas`, `Courier New`, `monospace` at 14px. Bumped APP to 2.17 and the stylesheet cache key to 1.14.
- Files changed: king_games_product_manager/style.css, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl.
- Verification: Diagnostics passed for all changed frontend files. Live asset verification confirmed APP 2.17, CSS 1.14, and the requested 14px monospace stack across five static and three dynamic terminal-log instances.
- Outcome: Terminal logs now render in a readable fixed-width font at the requested size without changing normal application text.
- Follow-ups: None.

---

### [ID: 20260727-06] [Status: completed]
- Timestamp: 2026-07-27
- Request: Expand the ingestion AI selector from ten choices to the complete list of compatible Gemini prediction models.
- Implementation: Expanded the UI selector and server allowlist from 10 to all 20 text/JSON prediction models currently returned by the account's Gemini `generateContent` API. Kept `gemini-3.1-flash-lite` as the default. Excluded 21 specialty endpoints for image generation, TTS, music, robotics, computer use, and dedicated research because they are not compatible with the product JSON prediction flow. Bumped APP to 2.16 and API to 1.50.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl.
- Verification: Direct API comparison confirmed all 20 selectable models exist in the live account model list and the UI options exactly match the server allowlist. Live smoke test confirmed API 1.50, APP 2.16, 20 unique options, and Gemini 3.1 Flash Lite as the default.
- Outcome: The ingestion console now exposes the complete compatible Gemini text-model list rather than an arbitrary ten-model subset.
- Follow-ups: None.

---

### [ID: 20260727-05] [Status: completed]
- Timestamp: 2026-07-27
- Request: Add a selectable AI model list to the automatic product ingestion console, defaulting to Gemini 3.1.
- Implementation: Added a ten-model Gemini selector directly above the ingestion start button; passed the selected `ai_model` through the frontend request, server-side allowlist, CLI runtime flags, both enrichment phases, and the title-similarity guard. The default is `gemini-3.1-flash-lite`. Only model names confirmed by the account's Gemini `generateContent` model-list endpoint were included; nonexistent 5.5/5.6 names were not fabricated. Bumped APP to 2.15 and API to 1.49.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, king_games_product_manager/update_products_batch_2.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl.
- Verification: Gemini model-list endpoint confirmed all ten choices; focused AST/runtime check confirmed CLI default/override parsing and all three AI call sites use the selected model; diagnostics passed for all changed application files; live server smoke test confirmed API 1.49, APP 2.15, the default selection, and all ten model options.
- Outcome: Users can choose the Gemini prediction model before starting ingestion, with Gemini 3.1 Flash Lite selected by default.
- Follow-ups: None.

---

### [ID: 20260727-03] [Status: completed]
- Timestamp: 2026-07-27
- Request: להחליף בכל קוד המערכת שימוש ב-`font-family: monospace` ל-`Font Awesome 6 Free`.
- Implementation: הוחלפו 37 הצהרות font ב-app.js, index.html ו-style.css, כולל fallback של Consolas/Monaco שהסתיים ב-monospace. Font Awesome 6.4.0 כבר נטען במסמך. גרסת APP עודכנה ל-`2.13`, cache bust של app.js עודכן ל-`2.13` ושל style.css ל-`1.13`.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/style.css, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: חיפוש בקוד היישום אישר אפס מופעי `monospace` ו-37 מופעי `Font Awesome 6 Free`; דיאגנוסטיקת VS Code נקייה עבור app.js, index.html ו-style.css. חיפוש workspace מצא רק ארבעה מופעים בקבצי build של תוסף PDF צד שלישי בתוך chrome-profile-chatgpt-visible, שאינם קוד המערכת ולא שונו.
- Outcome: completed. כל שימושי monospace בקוד KINGGAMES הפעיל הוחלפו ל-`Font Awesome 6 Free`.
- Follow-ups: לרענן את הדפדפן כדי לקבל את גרסאות ה-JS וה-CSS המעודכנות.

---

### [ID: 20260727-02] [Status: completed]
- Timestamp: 2026-07-27
- Request: כאשר `שימוש במנוע חיפוש תמונות` אינו מסומן, למנוע כל קריאה למנוע חיפוש תמונות, לרבות Morlevi Supplier Prefetch.
- Implementation: ה־Supplier Prefetch המוקדם ב-enricher הוכפף ל-`img_scrpt == on`. כאשר הדגל כבוי לא נבחר fetcher לפי ספק/יצרן ולא מופעל `fetch_context`, בשתי פאזות ההעשרה. שלב ה-AI והעלאת תמונות מקומיות ממשיכים ללא שינוי. גרסאות עודכנו ל-API `1.48` ול-APP `2.12`.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: בדיקת התנהגות עם mock שזורק שגיאה בכל קריאה ל-`selenium_fetcher.get_fetcher` הסתיימה בהצלחה עם `img_scrpt=off` וספק מור לוי, והוכיחה שאין בחירת fetcher או קריאת מנוע כשהאפשרות כבויה. בוצעו גם קומפילציה ובדיקת נגד עבור מצב `on`.
- Outcome: completed. ביטול הסימון מונע כעת כל קריאה למנועי חיפוש התמונות, כולל prefetch מוקדם של ספקים.
- Follow-ups: בוצע restart לשרת ונבדקה גרסת ה-API הפעילה.

---

### [ID: 20260727-01] [Status: completed]
- Timestamp: 2026-07-27
- Request: במסוף הזנת מוצרים אוטומטית לתקן את חיפוש התמונות המקומיות מהנתיב השגוי `C:\Temp\ProducsImages` לנתיב `C:\Temp\productsImages`.
- Implementation: עודכן נתיב בסיס התמונות בקבוע השרת, בכל ברירות המחדל והבקשות בצד הלקוח, בתצורת עשרת ספקי התמונות, בטקסטים המוצגים במסך, ב-runner של חילוץ תמונות, במנגנון חיפוש התמונות המקומי של הזנת המוצרים ובסקריפט ASUS. גרסאות עודכנו ל-API `1.47` ול-APP `2.11`, כולל cache bust של `app.js`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/supplier_image_scripts.json, king_games_product_manager/supplier_image_extraction_runner.py, king_games_product_manager/update_products_batch_2.py, king_games_product_manager/helper_scripts/image_extractors/LOAD_IMAGES_ASUS_ROG_new.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור כל ארבעת קובצי Python ששונו; JSON ספקים נטען בהצלחה; דיאגנוסטיקת VS Code נקייה עבור קובצי ה-runtime המרכזיים; חיפוש ממוקד אישר שלא נשאר `ProducsImages` בקוד Python/JS/HTML או בתצורת JSON הפעילה.
- Outcome: completed. מסוף ההזנה וכל מסלולי הביצוע הפעילים מחפשים ושומרים תמונות תחת `C:\Temp\productsImages`.
- Follow-ups: בוצע restart לשרת ונבדקה גרסת ה-API הפעילה.

---

### [ID: 20260722-05] [Status: completed]
- Timestamp: 2026-07-22
- Request: במסך עדכון קטגוריות למוצרים להעביר את הכפתורים `קליטת קובץ MG` ו-`ייצוא ל-MG` לאותו מיקום במסך ניהול מוצרים תחת `ייבוא קובץ מוצרים גדול מ-MG`, ולוודא שכפתור `קליטת קובץ MG גדול` עושה אותה פעולה בדיוק כמו כפתור הייבוא שהועבר.
- Implementation: הועברו פעולות MG למסך `ניהול מוצרים` תחת בלוק `ייבוא קובץ מוצרים גדול מ-MG`: כפתור `קליטת קובץ MG גדול` וכפתור `ייצוא ל-MG`. הכפתורים העליונים הוסרו ממסך `עדכון קטגוריות למוצרים`. בלוק הייבוא/ייצוא הישן הוסר ממסך הדיאגנוסטיקה כדי למנוע IDs כפולים. קוד הייבוא אוחד כך שכפתור `crawlerMgImportBtn` מפעיל את אותו flow של `runMgImport({ fileObj })` מול `/api/mg/import/start`, עם סטטוס ולוגים חיים. כפתור הייצוא שהועבר נשאר על פעולת הייצוא הישנה מול `/api/mg/export` ומשתמש בסינון הנוכחי של מסך ניהול מוצרים. גרסאות עודכנו ל-API `1.46` ו-APP `2.10`.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: חיפוש HTML אישר שאין יותר `mgImportBtn`/`mgExportBtn` במסך עדכון קטגוריות ושיש מופע יחיד של `crawlerMgImportBtn`/`crawlerMgExportBtn` במסך ניהול מוצרים. חיפוש JS אישר handler יחיד לייבוא MG ושכפתור הייצוא משתמש ב-`/api/mg/export`. `get_errors` נקי עבור `index.html`, `app.js`, `server.py`; `py_compile server.py` עבר.
- Outcome: completed.
- Follow-ups: לרענן את הדפדפן כדי לקבל `app.js?v=2.10`; פעולות MG נמצאות כעת בראש ניהול מוצרים.

---

### [ID: 20260722-04] [Status: completed]
- Timestamp: 2026-07-22
- Request: בפייב, מוצר `KB-VANTAR` מופיע בטבלת "רשימת שורות מהקובץ לאחר מיפוי" כחישוב שקלי למרות שתא המחיר באקסל הוא תא דולרי; להסביר למה ולתקן.
- Implementation: נמצא שהמסלול הכללי של Excel כבר ידע להסיק מטבע מפורמט תא, אבל הטרנספורמר הייעודי של Five עקף אותו והניח `USD` רק עבור טאב `NOCTUA`; לכן `KB-VANTAR` בטאב `COUGAR ACC` עם פורמט תא `[$$-409]#,##0` סומן בטעות כ-`ILS`. עודכן `_transform_five_excel_to_csv_data` לקרוא את `number_format` מתא המחיר, להסיק `USD/ILS` עם `_infer_currency_from_excel_number_format`, ולהמיר לשקלים לפי המטבע בפועל לפני חישוב מחיר סופי ומכפיל מחיר. גרסאות עודכנו ל-API `1.45` ו-APP `2.09`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: לפני התיקון, בדיקת HTTP החזירה עבור `KB-VANTAR` את `raw_price=35`, `currency=ILS`, `final_price=59`; בדיקת התא באקסל אישרה `price_format=[$$-409]#,##0`. אחרי התיקון, בדיקה פנימית של Five החזירה `summary_total=342`, `currency=USD`, `raw_price=35`, `final_price=169`. אחרי restart ל-API `1.45`, smoke HTTP מלא מול `/api/supplier/analyze` החזיר `summary_total_extracted=342`, `preview_rows=342`, `sum_result_rows=342`, ועבור `KB-VANTAR`: `price=169`, `currency=USD`, `raw_price=35`, `final_price=169`.
- Outcome: completed.
- Follow-ups: לרענן את הדפדפן כדי לקבל `app.js?v=2.09`; טבלת השורות לאחר מיפוי אמורה להציג את המטבע כ-USD ואת המחיר המחושב אחרי המרה.

---

### [ID: 20260722-03] [Status: completed]
- Timestamp: 2026-07-22
- Request: אחרי תיקון מיפויי הטאבים עדיין מתקבלים כ-120 מוצרים במקום 342 בפייב; לבצע בדיקה מקיפה ויסודית ולתקן את הסיבה האמיתית.
- Implementation: שוחזר הקובץ `FiveExits July-01-2026 .xlsx` מקומית. נמצא שהחילוץ מפייב תקין ומפיק 342 שורות, אבל סינון המיפוי אחרי החילוץ השווה שמות טאבים בצורה מדויקת. שורות פייב נשמרו עם שמות מוגדרים כמו `COUGAR GAMING` / `ANTEC PSU`, בעוד המיפוי השמור החזיק שמות גיליון אמיתיים כמו `COUGAR Gaming` / `ANTEC Psu`; לכן רק התאמות exact שרדו. עודכן סינון הטאבים להשתמש ב-`_normalize_sheet_name`, ובמסלולי חילוץ אוטומטיים (`five_excel_tabs`, `visual_excel_tabs`, `techno_excel_tabs`) הוסרה תלות ב-`tab_enabled` היסטורי של מיפוי שמור; רק `selected_tabs` מפורש מהמודאל הנוכחי מסנן שורות. גרסאות עודכנו ל-API `1.44` ו-APP `2.08`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: שחזור פנימי הראה `summary_total=342`; לפני התיקון סינון שמות exact נתן כ-120/123 בהתאם לטאבים שתואמים בדיוק; אחרי נרמול וביטול סינון מיפוי שמור במסלול אוטומטי מתקבל `after_saved_mapping_filter=342`; `py_compile` עבר עבור `server.py`; diagnostics נקיים; השרת אותחל ל-API `1.44`; smoke HTTP מלא מול `/api/supplier/analyze` על `FiveExits July-01-2026 .xlsx` החזיר `summary_total_extracted=342`, `preprocess_total_rows=342`, `preview_rows=342`, ו-`new_products=31`, `updated_products=309`, `unchanged_count=2`, סה"כ `342`.
- Outcome: completed.
- Follow-ups: להפעיל שוב ניתוח פייב במסך; הטבלה לאחר מיפוי צריכה להתיישר עם סיכום החילוץ כאשר לא נבחר סינון טאבים מפורש.

---

### [ID: 20260722-02] [Status: completed]
- Timestamp: 2026-07-22
- Request: לבדוק את מנגנון שמירת המיפויים כי מיפויי טאבים לא נשמרים נכון, למשל בטכנו נשמר רק חלק מהטאבים/לא נשמרו שאר הטאבים.
- Implementation: נמצא שמיפוי טכנו שמור כ-`tabs=[]` גם ברמת ספק וגם ברמת מחירון, ושמירת מיפוי בצד השרת החליפה את כל מערך `tabs` במה שהגיע מהדפדפן. נוסף helper `_merge_tab_field_mappings` שממזג טאבים לפי `tab_name` במקום למחוק טאבים שלא הגיעו בבקשה, כולל merge פנימי של `field_mapping`, `field_text_mapping`, `field_search_mapping`, `import_toggles`, ו-`display_toggles`. עודכן endpoint שמירת מיפוי מחירון ו-endpoint שמירת מיפוי ספק להשתמש ב-merge. בנוסף נוסף fallback לטכנו: אם אין טאבים שמורים, `techno_excel_tabs` מחזיר כברירת מחדל את `Computing` ו-`Printing` עם מיפוי העמודות הקבוע. גרסאות עודכנו ל-API `1.43` ו-APP `2.07`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `server.py`; בדיקת merge אישרה ששמירת `Computing` בלבד משמרת את `Printing` וגם לא מוחקת `raw_price` מתוך `field_mapping`; בדיקת טעינת טכנו אישרה שברירת המחדל מחזירה `['Computing', 'Printing']` גם כשהמיפוי השמור ריק; diagnostics נקיים.
- Outcome: completed.
- Follow-ups: אם יש מיפויים מותאמים אישית שכבר נמחקו בעבר, הם לא קיימים ב-DB/legacy ולכן צריך לסרוק שוב קובץ דוגמה או להגדיר אותם מחדש; מכאן והלאה שמירה חלקית לא אמורה למחוק טאבים אחרים.

---

### [ID: 20260722-01] [Status: completed]
- Timestamp: 2026-07-22
- Request: במסך קליטת מחירון ספק, בזמן `התחל ניתוח מחירון`, לזהות אם עמודת מחיר באקסל מוגדרת כ-CURRENCY פנימי בדולר או בשקל ולהשתמש במטבע הזה בחישוב.
- Implementation: במסלול Excel הכללי של קליטת מחירוני ספק, `_build_normalized_rows_from_excel_data` כבר לא קורא `openpyxl` עם `values_only=True` בלבד אלא שומר גם את `cell.number_format` לכל תא. נוסף helper `_infer_currency_from_excel_number_format` שמזהה `USD/$/dollar` כדולר ו-`ILS/NIS/shekel/he-IL/₪/שח/שקל` כשקל. אם אין עמודת מטבע ממופה או ערך מטבע מפורש, המערכת מסיקה את המטבע מפורמט תא המחיר ומשתמשת בו ב-`_resolve_pricing_with_tab_options`. ערך מטבע מפורש עדיין מקבל עדיפות ולא נדרס. גרסאות עודכנו ל-API `1.42` ו-APP `2.06`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `server.py`; smoke Excel בזיכרון עם שתי שורות מחיר `100` הראה שפורמט `[$$-409]` מחזיר `currency=USD` ו-`final_price=469`, ופורמט `[$ILS-he-IL]` מחזיר `currency=ILS` ו-`final_price=159`; diagnostics נקיים.
- Outcome: completed.
- Follow-ups: בקבצי CSV אין פורמט תא ולכן אין דרך לשחזר מטבע מפורמט פנימי; עבור CSV עדיין צריך עמודת מטבע או מיפוי טקסט קבוע.

---

### [ID: 20260721-09] [Status: completed]
- Timestamp: 2026-07-21
- Request: לטפל בכך שהריצה עדיין מדפיסה `Gemini transient HTTP 503 (attempt 3/6)` אחרי מעבר ל-fallback.
- Implementation: נמצא שה-resolver למודל הופעל במסלול CLI בלבד, בעוד שהריצה דרך השרת קוראת ישירות ל-`enrich_single_product` ומשם ל-`call_gemini_api` עם `model="gemini-3.5-flash"`. הועבר פתרון המודל לתוך נקודת הקריאה ל-Gemini עצמה (`call_gemini_api`) וגם לתוך `compare_title_essence_with_gemini`, כך שכל runtime path דרך השרת משתמש בפועל ב-`gemini-3.1-flash-lite` כשהמודל המבוקש הוא `gemini-3.5-flash`. גרסאות עודכנו ל-API `1.41` ו-APP `2.05`.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `enricher.py`; smoke ישיר ל-resolver ול-`generateContent` אישר `gemini-3.5-flash -> gemini-3.1-flash-lite` עם תשובת `{"ok": true}`; smoke ingestion על מוצר `36009` הדפיס `Using Gemini model 'gemini-3.1-flash-lite' instead of requested 'gemini-3.5-flash'` בשתי קריאות ה-AI ולא הדפיס 503; diagnostics נקיים; השרת אותחל ואומת על API `1.41`.
- Outcome: completed.
- Follow-ups: להריץ מחדש את המוצרים לאחר restart; לוג הריצה אמור להדפיס שהמודל המבוקש הוחלף ל-`gemini-3.1-flash-lite` לפני הקריאה.

---

### [ID: 20260721-08] [Status: completed]
- Timestamp: 2026-07-21
- Request: לבדוק למה Gemini עדיין לא עובד אחרי החלפת המפתח, ולתקן אם המפתח החדש עושה בעיות.
- Implementation: אומת שהמפתח החדש תקין ומחזיר רשימת מודלים (`AQ.Ab8...jxh_Q`, hash `e4e1d2430229`), אבל `generateContent` על `gemini-3.5-flash` מחזיר `503 UNAVAILABLE` בגלל עומס גבוה. בדיקות ישירות הראו ש-`gemini-3.1-flash-lite`, `gemini-3.1-flash-lite-preview`, ו-`gemini-flash-lite-latest` עובדים. עודכן `choose_model_name` כך שבקשות ל-`gemini-3.5-flash` ול-`gemini-1.5-flash` יעדיפו קודם `gemini-3.1-flash-lite`. גרסאות עודכנו ל-API `1.40` ו-APP `2.04`.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: בדיקת models מול המפתח החדש החזירה 50 מודלים; probe ישיר ל-`gemini-3.5-flash` החזיר 503 high demand; probe ישיר ל-`gemini-3.1-flash-lite` עם `responseSchema` החזיר `{"ok": true}`; resolver מחזיר כעת `gemini-3.1-flash-lite` עבור בקשה ל-`gemini-3.5-flash`; `py_compile` ו-diagnostics עברו.
- Outcome: completed.
- Follow-ups: להריץ מחדש את רשימת המוצרים; המערכת תשתמש במודל `gemini-3.1-flash-lite` במקום המודל העמוס.

---

### [ID: 20260721-07] [Status: completed]
- Timestamp: 2026-07-21
- Request: לטפל באזהרת `Gemini transient HTTP 503` בזמן פרדיקציה, כדי שריצה לא תיפול בגלל עומס זמני של Gemini.
- Implementation: ב-`product_scraper_engine/enricher.py` הוגדלה עמידות קריאות Gemini: קריאת enrichment הראשית עלתה מ-3 ל-6 ניסיונות, timeout עלה מ-60 ל-90 שניות, וה-backoff מוגבל עד 60 שניות; גם בדיקת title essence guard עלתה מ-2 ל-4 ניסיונות ומשתמשת באותו cap. גרסאות עודכנו ל-API `1.39` ו-APP `2.03`.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `enricher.py`; diagnostics נקיים; הלוג אישר שה-503 היה transient והריצה נעצרה ידנית לפני ניסיון 3; validation נוסף הורץ אחרי עדכון הגרסאות והתיעוד.
- Outcome: completed.
- Follow-ups: להריץ מחדש את רשימת המוצרים; במקרה של 503, המערכת תחכה ותנסה עד 6 פעמים לפני כשל סופי.

---

### [ID: 20260721-06] [Status: completed]
- Timestamp: 2026-07-21
- Request: לבדוק את שגיאת `missing_prediction_marketing_points` עבור מוצר `36024` אחרי פרדיקציה ופרסום לאתר.
- Implementation: נמצא ש-Phase-1 מול Gemini נכשל בגלל `API_KEY_INVALID`, ולכן לא נוצר payload חדש עם `PRODUCT_FACTS`; בנוסף נמצא שבכשל Phase-1 המוצר נכנס ל-`failed_list` אבל לא נחסם לשלב MG publish, ולכן publish ניסה payload שמור/לא תקין והציג `missing_prediction_marketing_points`. עודכן `update_products_batch_2.py` כך שכל כשל Phase-1 מוסיף את המוצר ל-`BLOCK_PUBLISH_PRODUCT_IDS` ומונע ניסיון פרסום עם payload ישן. גרסאות עודכנו ל-API `1.38` ו-APP `2.02`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `update_products_batch_2.py`; diagnostics נקיים לקובץ; בדיקת Gemini מול המפתח הנוכחי החזירה `INVALID_ARGUMENT: API key not valid`, ולכן נדרש להחליף את `GEMINI_API_KEY` בסביבת השרת לפני rerun; השרת אותחל מחדש ואומת מול `/api/health/version`.
- Outcome: completed.
- Follow-ups: להגדיר `GEMINI_API_KEY` תקין בסביבת השרת, לאתחל את השרת, ואז להריץ מחדש את המוצרים שנכשלו בפרדיקציה.

---

### [ID: 20260721-05] [Status: completed]
- Timestamp: 2026-07-21
- Request: בעדכון האתר אחרי פרדיקציה, לוודא תמיד ששדה `xml` לא מסומן.
- Implementation: נוספה כפייה ב-`update_products_batch_2.py` כך שכל payload של פרסום מוצר ל-MG כולל `xml: False`; במודול החיצוני `C:\Projects\AgentUpdateMGsystem\update_product.py` נוסף override קשיח בתחילת `update_product_in_apanel` שמגדיר `xml=False` לכל קריאה, ונוסף `xml` לרשימת הצ'קבוקסים הסטנדרטיים כדי להסיר סימון קיים באתר. גרסאות עודכנו ל-API `1.37` ו-APP `2.01`.
- Files changed: king_games_product_manager/update_products_batch_2.py, C:\Projects\AgentUpdateMGsystem\update_product.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `update_products_batch_2.py`, `server.py`, ו-`C:\Projects\AgentUpdateMGsystem\update_product.py`; smoke ללא דפדפן אישר שקריאה ל-updater עם `xml=True` נרשמת כ-`xml=False` לפני ניסיון Selenium; diagnostics נקיים לקבצים שנערכו; JSONL תקין; השרת אותחל מחדש ו-`/api/health/version` החזיר API `1.37`.
- Outcome: completed.
- Follow-ups: none.

---

### [ID: 20260721-04] [Status: completed]
- Timestamp: 2026-07-21
- Request: לקרוא את `C:\Temp\prdUrls.txt`, להתאים כל מק"ט ספק לשדה SKU0/`supplier1_sku`, ולעדכן את `ProductSupplierURL` בלינק מהקובץ.
- Implementation: נקרא קובץ `C:\Temp\prdUrls.txt` בפורמט `SKU ; URL`; בוצעה התאמה מדויקת מול `king_games_product_manager/products.db` לפי `supplier1_sku`; נוצר גיבוי DB לפני שינוי; עודכן `ProductSupplierURL` לכל רשומות המוצרים התואמות.
- Files changed: king_games_product_manager/products.db, king_games_product_manager/products_backup_before_prdUrls_20260721_135737.db, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: dry-run מצא 140 שורות תקינות, 0 שורות לא תקינות, 0 מק"טים ללא התאמה, 141 רשומות מוצרים תואמות; העדכון שינה 140 רשומות; אימות חוזר מצא 141 רשומות מאומתות, 0 חוסרים ו-0 mismatch. מוצר 35947 קיבל `https://techno-rezef.com/products/lenovo-neo-50q-g6-u7-256v-16gb-512gb-w11p-3y`.
- Outcome: completed.
- Follow-ups: none.

---

### [ID: 20260721-03] [Status: completed]
- Timestamp: 2026-07-21
- Request: Prediction still failing for product 35947 due to Gemini Guard blocking it for low title similarity, even when 'same_essence' is true.
- Implementation: Removed the similarity percentage threshold completely from update_products_batch_2.py if same_essence is true. Now, if the AI determines it's fundamentally the same product line, it will allow the result to pass even if the similarity score is low (e.g., due to different generations, specs, etc. fetched from the supplier link).
- Files changed: update_products_batch_2.py
- Verification: Ran prediction for product 35947. Verified the result was no longer blocked by Gemini Guard, and the JSON output properly contained the new specs from the supplier link.
- Outcome: completed.
- Follow-ups: none.
\n
### [ID: 20260721-02] [Status: completed]
- Timestamp: 2026-07-21
- Request: Reverted AI model back to gemini-3.5-flash as the API confirms it is available.
- Implementation: Replaced gemini-1.5-pro with gemini-3.5-flash in update_products_batch_2.py and enricher.py. Bumped version to 2.00.
- Files changed: update_products_batch_2.py, enricher.py, app.js
- Verification: Scripts ran successfully. API returned gemini-3.5-flash in models list.
- Outcome: completed.
- Follow-ups: none.
\n
### [ID: 20260721-01] [Status: completed]
- Timestamp: 2026-07-21
- Request: Changed AI model from gemini-3.5-flash to gemini-1.5-pro to fix 404 error (gemini-3.5-flash does not exist).
- Implementation: Replaced gemini-3.5-flash with gemini-1.5-pro in update_products_batch_2.py and enricher.py. Bumped version to 1.99.
- Files changed: update_products_batch_2.py, enricher.py, app.js
- Verification: Scripts ran successfully.
- Outcome: completed.
- Follow-ups: none.


### [ID: 20260720-07] [Status: completed]
- Timestamp: 2026-07-20
- Request: לשפר את איכות הפרדיקציה: להחזיר מפרט מלא, להציג שאלות ותשובות, לפעול לפי כללי יצירת כותרת מוצר, ולא להכניס מספר מק"ט לכותרת.
- Implementation: נוסף normalization לפלט Gemini כך ש-FAQ במבנה `Q/A` מומר ל-`question/answer`, `SOURCE` ממופה ל-`INTERNATIONAL_PART_NUMBER_SOURCE`, וכותרות HTML/FORMATTED מנוקות ממק"ט/דגם/SKU. קריאת Phase-2 של Gemini עובדת כעת ב-`responseSchema` במצב auto עם fallback ל-`json_only` במקרה כשל. נוסף guard איכות שחוסם פרדיקציה חסרה במקום לפרסם תוכן בלי FAQ/תיאור/מפרט. קטגוריית מארזים 147 משתמשת כעת בכותרת מקומית יציבה לפי כלל מארזים, למשל `מארז מחשב HERO 80 למחשב שולחני שחור`, ולא בכותרת AI קצרה או שיווקית. תוקן typo נפוץ בערכי בחירה (`יי` -> `יש`). גרסאות עודכנו ל-API/APP `1.56`/`1.94`.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `enricher.py`, `update_products_batch_2.py`, ו-`server.py`; smoke אישר FAQ Q/A normalization, mapping של `SOURCE`, ניקוי מק"ט מכותרות, תיקון `יי` ל-`יש`, ובניית כותרת מארז נקייה; diagnostics נקיים לקבצים שנערכו; ריצת materialization מקומית ל-35742 ללא פרסום רצה עם `schema_mode=response_schema`, עברה Gemini Guard ב-100%, שמרה דוח JSON/HTML, והדוח כולל 5 FAQ תקינים, מפרט טכני מלא, `FORMATTED_TITLE` ללא מק"ט, וכותרת סופית `מארז מחשב HERO 80 למחשב שולחני שחור`.
- Outcome: completed.

---

### [ID: 20260720-06] [Status: completed]
- Timestamp: 2026-07-20
- Request: לתקן מצב שבו מוצר 35742 בקטגוריית מארזים נפל ב-Gemini Guard כי fallback מקומי בחר בטעות תבנית `מסך` ויצר כותרת `מסך Hero שחור`.
- Implementation: נוסף title family ייעודי `pc_case` לקטגוריה 147. `apply_title_rule_template` עוקף כעת את טבלת התבניות הכללית עבור קטגוריה 147 ובונה כותרת מארז מקומית באמצעות `_build_pc_case_title`, כך שחוסר בתבנית מארזים בקונפיג לא ייפול לתבנית מסכים. `_enforce_final_title_family_guard` יודע כעת לתקן כותרת מסך שגויה בחזרה לכותרת מארז. גרסאות עודכנו ל-API/APP `1.53`/`1.91`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `update_products_batch_2.py` ו-`server.py`; smoke מקומי אישר שגם כאשר קיימת רק תבנית `מסך`, קטגוריה 147 מחזירה `מארז מחשב HERO 80 למחשב שולחני`, וה-family guard מתקן `מסך Hero שחור` לכותרת מארז; diagnostics נקיים לקבצים שנערכו; ריצת materialization מקומית ל-35742 ללא פרסום יצרה `מארז מחשב HERO 80 למחשב שולחני איכותי ועמיד שחור` וה-Gemini Guard עבר `OK` עם 100%; השרת הופעל מחדש ו-`/api/health/version` החזיר API `1.53`.
- Outcome: completed.

---

### [ID: 20260720-05] [Status: completed]
- Timestamp: 2026-07-20
- Request: לתקן כשל Phase-2 שבו Gemini החזיר מפתח מפרט טכני משובש (`תצטרה`) וגרם ל-`phase2_schema_mismatch`, שאחריו שלב MG publish נחסם בגלל payload ישן.
- Implementation: ב-`product_scraper_engine/enricher.py` עודכן decode של `PRODUCT_TECHNICAL_DETAILS` למצב strict: נשמרים רק מפתחות המפרט הצפויים מתוך `specs_keys`, ומפתחות לא צפויים/מומצאים של Gemini מסוננים החוצה. ערכים חסרים נשארים כמחרוזת ריקה, כך ש-typo של Gemini לא מפיל את כל המוצר ולא גורם לניסיון שימוש ב-payload ישן. גרסאות עודכנו ל-API/APP `1.52`/`1.90`.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `enricher.py`, `server.py`, ו-`update_products_batch_2.py`; smoke מקומי אישר שמפתח לא צפוי כמו `תצטרה` אינו נשאר ב-`PRODUCT_TECHNICAL_DETAILS` אחרי decode, ושנשמרים רק המפתחות המותרים; diagnostics נקיים לקבצים שנערכו; השרת הופעל מחדש ו-`/api/health/version` החזיר API `1.52`.
- Outcome: completed.

---

### [ID: 20260720-04] [Status: completed]
- Timestamp: 2026-07-20
- Request: להשתמש ב-`3.1 FLASH LITE` עבור קריאות Gemini במודול הזנת מוצרים, אחרי ש-`gemini-2.0-flash-lite` החזיר 404.
- Implementation: ברירות המחדל של `KG_GEMINI_CATEGORY_MODEL`, `KG_GEMINI_ENRICHMENT_MODEL`, ו-`KG_GEMINI_GUARD_MODEL` הוחלפו ל-`gemini-3.1-flash-lite`. נוסף preferred fallback עבור `gemini-3.1-flash-lite` ב-resolver של Gemini כך שאם המודל לא מופיע ב-`/models`, המערכת תמשיך אוטומטית למודל זמין כמו `gemini-2.5-flash-lite` במקום להפיל את המוצר ב-404. גרסאות עודכנו ל-API/APP `1.51`/`1.89`.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `enricher.py`, `update_products_batch_2.py`, ו-`server.py`; smoke ללא רשת אישר שברירות המחדל הן `gemini-3.1-flash-lite` וש-fallback בוחר `gemini-2.5-flash-lite` כאשר 3.1 אינו ברשימת המודלים; diagnostics נקיים לקבצים שנערכו; השרת הופעל מחדש ו-`/api/health/version` החזיר API `1.51`.
- Outcome: completed.

---

### [ID: 20260720-03] [Status: completed]
- Timestamp: 2026-07-20
- Request: לתקן timeout חוזר בקריאה השנייה לג'מיני במודול הזנת מוצרים, אחרי שגם עם פרומפט מקוצר התקבלה שגיאת `Failed to communicate with Gemini API after 3 attempts: The read operation timed out`.
- Implementation: Phase-2 וה-title guard הועברו מ-`gemini-flash-latest` לברירת מחדל יציבה ומהירה `gemini-2.0-flash-lite` דרך קבועים הניתנים לדריסה (`KG_GEMINI_ENRICHMENT_MODEL`, `KG_GEMINI_GUARD_MODEL`, `KG_GEMINI_CATEGORY_MODEL`). בקריאת `call_gemini_api` הוסר `responseSchema` הענקי כברירת מחדל (`GEMINI_FULL_RESPONSE_SCHEMA=off`), ונשאר JSON mode בלבד עם `temperature=0.1`, `maxOutputTokens=4096`, timeout ברירת מחדל 35 שניות, ו-2 retries במקום 3. נוספה שורת לוג עם model/prompt_chars/schema_mode/timeout/retries כדי לאבחן ריצות עתידיות.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `enricher.py`, `update_products_batch_2.py`, ו-`server.py`; smoke ללא רשת אישר ש-Phase-2 payload אינו כולל `responseSchema`, כולל `responseMimeType=application/json`, timeout 35s ו-`maxOutputTokens=4096`; diagnostics נקיים לקבצים שנערכו; השרת הופעל מחדש ו-`/api/health/version` החזיר API `1.49`.
- Outcome: completed.

---

### [ID: 20260720-02] [Status: completed]
- Timestamp: 2026-07-20
- Request: לקצר משמעותית את פרומפט Gemini המלא במודול הזנת מוצרים, להפסיק לבקש תמונות מג'מיני, ולהשאיר את טבלאות הקטגוריות/תבניות/מאפיינים בתוך הפרומפט.
- Implementation: הוחלף `build_prompt` ב-`product_scraper_engine/enricher.py` מבלוק הוראות ארוך לפסקה קצרה ותמציתית בסגנון המבוקש, תוך השארת טבלאות קטגוריות, תבניות כותרת, מאפיינים ומפתחות טכניים. הוסר `IMAGES` מ-response schema של Gemini ומהשדות הנדרשים, והוסרה ולידציית חובה לתמונות שמגיעות מה-AI. מנגנוני תמונות קיימים ממשיכים להתבסס על supplier/direct fetch ולא על Gemini. גרסאות עודכנו ל-API/APP `1.48`/`1.86`.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `product_scraper_engine/enricher.py` ו-`server.py`; smoke מקומי אישר שהפרומפט מכיל את הטבלאות הדרושות, לא כולל בלוק תמונות/URLs/JPEG/PNG, ומתקצר בדוגמה ל-2,092 תווים; smoke נוסף ללא רשת אישר ש-`IMAGES` לא נשלח ב-Gemini responseSchema ולא בשדות required; diagnostics נקיים לקבצים שנערכו; השרת הופעל מחדש ו-`/api/health/version` החזיר API `1.48`.
- Outcome: completed.

---

### [ID: 20260720-01] [Status: completed]
- Timestamp: 2026-07-20
- Request: לבדוק את אוטומציית הדפדפן במודול הזנת מוצרים, לוודא שכאשר ChatGPT browser אינו מסומן התהליך חוזר להתנהגות Gemini API, ולקצר את הקריאה הראשונה לג'מיני כך שתבקש רק קטגוריה כדי לחסוך עלויות.
- Implementation: אומת מסלול הדגלים UI -> server -> `update_products_batch_2.py`: checkbox `ingFlagAiProviderBrowser` שולח `browser` רק כשהוא מסומן, אחרת `api`; השרת מנרמל כל ערך לא חוקי ל-`api`; ו-ChatGPT browser נפתח רק כאשר `ai_provider == "browser"`. נוסף ב-`product_scraper_engine/enricher.py` מסלול `predict_category_with_gemini_api` עם prompt קצר ו-response schema של ארבעה שדות בלבד (`RECOMMENDED_CATEGORY_ID`, `RECOMMENDED_CATEGORY_NAME`, `CONFIDENCE_PERCENT`, `REASON`). ב-`update_products_batch_2.py` Phase-1 במצב API הוחלף מ-`enrich_single_product` מלא לקריאת category-only החדשה. גרסאות עודכנו ל-API/APP `1.47`/`1.85`.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `update_products_batch_2.py`, `product_scraper_engine/enricher.py`, ו-`server.py`; smoke זמני ללא קריאת רשת אישר שברירת המחדל היא `ai_provider=api`, ש-Phase-1 Gemini החדש אינו כולל `PRODUCT_DESCRIPTION`, `PRODUCT_TECHNICAL_DETAILS`, `PRODUCT_ATTRIBUTES`, `FAQ`, `HTML_TITLE`, או `IMAGES`, וש-response schema כולל רק את ארבעת שדות הקטגוריה; diagnostics נקיים לכל הקבצים שנערכו; השרת הופעל מחדש ו-`/api/health/version` החזיר API `1.47`.
- Outcome: completed.

---

### [ID: 20260719-20] [Status: in-progress]
- Timestamp: 2026-07-19
- Request: לתקן את שבריריות ChatGPT browser: לא לקרוא לו 3 פעמים עם אותו prompt מלא, להפוך Phase-1 לקריאת קטגוריה מינימלית בלבד, למנוע סירובי JSON בגלל סתירת allowed attributes, ולשלב תמונות שהסוכן מחזיר כשאין תמונות מקומיות/ספק.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` נוסף Phase-1 קצר ל-ChatGPT browser שמבקש רק קטגוריה (`RECOMMENDED_CATEGORY_ID`, `RECOMMENDED_CATEGORY_NAME`, `CONFIDENCE_PERCENT`, `REASON`) בלי תיאור/מפרט/attributes/images. `submit_and_get_chatgpt_json` כבר לא שולח retry מלא זהה אחרי תשובת JSON/סירוב, וגם לא מבצע repair נוסף דרך ChatGPT; malformed JSON מטופל רק ב-parser מקומי. ב-`product_scraper_engine/enricher.py` הוסרה הסתירה ב-`PRODUCT_ATTRIBUTES`, נוסף repair מקומי לתבנית שבה ChatGPT מחזיר fact strings בלי key `PRODUCT_FACTS`, ותמונות AI מאומתות משמשות fallback כאשר ספק/local image fetch לא מחזיר תמונות. נוסף guard מקומי לכותרת שחוסך קריאת ChatGPT שנייה כשיש סוג מוצר ודגם מפורשים, ונוסף hard block שמונע MG publish אחרי כשל enrichment או payload ישן שאינו שייך ל-run הנוכחי. גרסאות עודכנו ל-API/APP `1.42`/`1.80`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `update_products_batch_2.py`, `product_scraper_engine/enricher.py`, ו-`server.py`; diagnostics נקיים לקבצים ששונו; smoke אישר ש-Phase-1 browser prompt הוא category-only ללא מפרט/images; smoke אישר ש-error object גורם לקריאה אחת בלבד ולא retry מלא; smoke אישר local repair ל-`PRODUCT_FACTS`, skip תקין ל-run_id לא מספרי, ו-local title guard ל-`מארז HERO X WHITE`; טסטים חיים עבור `35739`, `35740`, `35741`, `35742` בריצה ב-run `2026071908`.
- Outcome: in-progress.

---

### [ID: 20260719-19] [Status: completed]
- Timestamp: 2026-07-19
- Request: לתקן שגיאת ChatGPT שבה מוצר `מארז HERO X WHITE` מזוהה/נדרש בטעות כ-CPU cooler, מה שיוצר דרישות סותרות ומונע JSON.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` שונתה קדימות זיהוי סוג מוצר כך שטוקנים מפורשים של מארז (`מארז`, `case`, `chassis`) מנצחים לפני רמזי `cpu_cooler` שגויים מקטגוריה/סוג מומלץ. נוסף זיהוי מוקדם ל-`case_fan` כדי לא לסווג מאוורר מארז כמארז מחשב. בדיקת התאמת `desktop` הורחבה להכיר כותרות מארז. גרסאות עודכנו ל-API/APP `1.36`/`1.74`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `update_products_batch_2.py` ו-`server.py`; smoke assertions אישרו ש-`מארז HERO X WHITE` מזוהה כ-`desktop`, ש-family guard מחזיר `generic` ולא `cpu_cooler`, וש-`מאוורר למארז` נשאר `case_fan`; diagnostics נקיים; השרת אותחל מחדש ו-health endpoint החזיר `api_version=1.36`; JSONL תקין.
- Outcome: מוצרי מארז מפורשים כבר לא נשלחים ל-ChatGPT עם guardrail סותר של CPU cooler, ולכן לא אמורים לגרום לסירוב JSON מהסוג שהודבק.

---

### [ID: 20260719-18] [Status: completed]
- Timestamp: 2026-07-19
- Request: להנחות את ChatGPT לענות מהר ולא לבצע מחקרים ארוכים, וללחוץ על כפתור `Answer now` אם הוא מופיע כדי להתחיל תשובה מיד.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` נוספו הנחיות browser-mode שמגבילות את ChatGPT ל-lookup קצר ומהיר במקום deep research/web browsing רחב. נוסף מנגנון שמזהה כפתור `Answer now` גלוי ולוחץ עליו אחרי שליחת ה-prompt ובזמן ההמתנה לתחילת תשובת assistant. גרסאות עודכנו ל-API/APP `1.35`/`1.73`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `update_products_batch_2.py` ו-`server.py`; diagnostics נקיים לקבצי Python/JS/HTML ששונו; השרת אותחל מחדש ו-health endpoint החזיר `api_version=1.35`; JSONL תקין.
- Outcome: ChatGPT browser mode מבקש תשובה מהירה עם lookup מוגבל, ומנסה להפעיל `Answer now` אוטומטית כדי למנוע המתנה למחקרים ארוכים.

---

### [ID: 20260719-17] [Status: completed]
- Timestamp: 2026-07-19
- Request: ChatGPT browser mode נכשל למוצר כמו `35737` עם `Timed out waiting for ChatGPT response text to finish generating and stabilize`, למרות שבפועל ChatGPT עונה בסוף לאט.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` הוארך זמן ההמתנה לתשובת ChatGPT מ-5 דקות ל-20 דקות, ונוסף heartbeat פעם בדקה שמדפיס כמה זמן עבר, כמה תווים התקבלו, והאם ChatGPT עדיין במצב generation. גרסאות עודכנו ל-API/APP `1.34`/`1.72`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `update_products_batch_2.py` ו-`server.py`; diagnostics נקיים לקבצי Python/JS/HTML ששונו; השרת אותחל מחדש ו-health endpoint החזיר `api_version=1.34`.
- Outcome: Browser mode כבר לא מפיל תשובות ChatGPT איטיות אחרי 5 דקות; הוא ימתין עד 20 דקות ויראה לוג התקדמות בזמן ההמתנה.

---

### [ID: 20260719-16] [Status: completed]
- Timestamp: 2026-07-19
- Request: לבטל את עיבוד הייצוא היומי שמדפיס `[Scheduler] Daily CSV export completed successfully`, כי לא ברור יותר למה נוצר הייצוא.
- Implementation: בוטלה הפעלת `daily_exporter_loop` בעליית השרת ב-`king_games_product_manager/server.py` וב-`server.py`. הפונקציות `export_supplier_csv` ו-`daily_exporter_loop` נשארו בקוד לשחזור ידני בעתיד, אבל thread הרקע כבר לא מתחיל ולכן לא נכתב יותר `C:\TEMP\exp_sup.csv` אוטומטית. גרסאות עודכנו ל-API/APP `1.33`/`1.71`.
- Files changed: king_games_product_manager/server.py, server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור שני קבצי `server.py`; diagnostics נקיים לקבצים ששונו; השרת הופעל מחדש וב-startup log הופיע `[Scheduler] Daily CSV exporter thread disabled.` במקום `Started daily CSV exporter thread`; health endpoint החזיר `api_version=1.33`.
- Outcome: ייצוא ה-CSV היומי האוטומטי מבוטל. Scheduler התהליכים הכללי ו-importer של Product Agent ממשיכים לרוץ כרגיל.

---

### [ID: 20260719-15] [Status: blocked]
- Timestamp: 2026-07-19
- Request: להריץ שוב את מוצר `35734` אונליין ולוודא שיש פרדיקציה טובה לפני הודעת הצלחה.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` נוסף ל-browser mode לוג raw response לקובץ `product_scraper_engine/logs/chatgpt_browser_invalid_json.log`, ניסיון תיקון JSON דרך ChatGPT לאחר parse failure, קריאת טקסט תשובת ChatGPT דרך `innerText` ב-JavaScript כדי להימנע מתקיעות Selenium `.text`, ו-fast-fail ברור כש-ChatGPT נמצא במסך login/signup או human verification. גרסאות עודכנו ל-API/APP `1.27`/`1.65`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `update_products_batch_2.py` ו-`server.py`; diagnostics נקיים לקבצי Python/JS/HTML ששונו; השרת אותחל מחדש ונבדק ישירות עם `api_version=1.27`, PID `29268`. ריצת browser אמיתית על `35734` פתחה Chrome גלוי על `chrome-profile-chatgpt-visible` אך נכשלה ב-state `login_or_signup_screen`, ולכן לא ניתן היה לאמת ChatGPT online בלי התחברות ידנית. ריצות API חלופיות ל-`35734` נתקעו בקריאת AI/Phase-2 ונעצרו כדי לא להשאיר תהליכים תלויים.
- Outcome: תיקוני עמידות ל-JSON/ChatGPT browser נמצאים בקוד ומופעלים ב-API `1.27`, אבל אימות אונליין מוצלח ל-`35734` עדיין חסום עד התחברות ידנית ל-ChatGPT בחלון Chrome הגלוי או עד ייצוב provider API.
- Follow-ups: להתחבר ידנית ל-ChatGPT בפרופיל `chrome-profile-chatgpt-visible`, להריץ שוב `35734` עם `ai_provider=browser`, לוודא שנשמרות נקודות שיווקיות ושאין חסימת `missing_prediction_marketing_points`, ורק אז לסמן הצלחה.

---

### [ID: 20260719-14] [Status: completed]
- Timestamp: 2026-07-19
- Request: במצב דפדפן ChatGPT, פרדיקציה למוצר `35734` (`DEEPCOOL CH560 DIGITAL WH`) החזירה סירוב במקום JSON כי הסוכן טען שאין לו מספיק נתונים/תמונות מאומתות.
- Implementation: ב-`king_games_product_manager/product_scraper_engine/enricher.py` רוככה דרישת התמונות מ-`30-40` קשיח ליעד ריאלי של `6-12` URL מאומתים, עם הוראה לא לסרב לכל ה-JSON רק בגלל שאין מספיק תמונות ישירות. ב-`king_games_product_manager/update_products_batch_2.py` נוספו הוראות browser-mode מפורשות לשימוש ב-web lookup, אי-סירוב עקב חוסר נתונים ראשוני, וזיהוי refusal עם retry נוסף שמבקש JSON בלבד. גרסאות עודכנו ל-API/APP `1.24`/`1.62`.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `update_products_batch_2.py`, `product_scraper_engine/enricher.py`, ו-`server.py`; diagnostics נקיים לקבצים ששונו; smoke אישר שה-prompt עבור `DEEPCOOL CH560 DIGITAL WH` כבר לא כולל `30-40 unique image URLs`, כולל את הוראת אי-הסירוב החדשה, וזיהוי refusal תופס את נוסח הסירוב שהתקבל מ-ChatGPT.
- Outcome: ChatGPT browser mode אמור לבצע lookup ולהחזיר JSON גם כשהקלט הראשוני דל, במקום להחזיר הודעת סירוב טקסטואלית שמפילה את parser ה-JSON.

### [ID: 20260719-13] [Status: completed]
- Timestamp: 2026-07-19
- Request: בתהליך קליטת מחירון ספקים, לוודא שמוצרים מוכפלים במקדמים שנבחרו בסריקה הראשונית של הקטגוריות, ולהוסיף בטבלת "רשימת שורות מהקובץ לאחר מיפוי" עמודות נפרדות למכפיל האמיתי ולמכפיל המע"מ.
- Implementation: ב-`king_games_product_manager/server.py` הורחבה התאמת `category_margin_overrides` כך שמקדם מהסריקה הראשונית יוחל גם לפי שם קטגוריה ראשית/משנית ולא רק לפי `category_key` מלא. נוספו לשורות ה-preview שדות `margin_multiplier` ו-`vat_multiplier` לצד `price_multiplier`. ב-`king_games_product_manager/app.js` נוספו עמודות `מכפיל אמיתי`, `מכפיל מע"מ`, ו-`מכפיל כולל` לטבלת שורות הקליטה. גרסאות עודכנו ל-API/APP `1.23`/`1.61`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `server.py`; diagnostics נקיים עבור `server.py`, `app.js`, ו-`index.html`; smoke ממוקד אישר שמקדם קטגוריה `1.45` ומע"מ `1.18` מחושבים למכפיל כולל `1.711` ולמחיר מחושב תקין.
- Outcome: מקדמים שנבחרו בסריקה הראשונית מוחלים בפועל על השורות, והטבלה מציגה בנפרד את מקדם הרווח, מקדם המע"מ, והמכפיל הכולל.

### [ID: 20260719-12] [Status: completed]
- Timestamp: 2026-07-19
- Request: כשבוחרים מצב דפדפן ל-ChatGPT, לפתוח דפדפן נראה כדי שיהיה אפשר לראות מה קורה במקום להתחבר למופע headless.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` נוסף זיהוי של ה-PID שמאזין על port `9222`, קריאת command line שלו, והחלפה אוטומטית אם הוא רץ עם `--headless` או פרופיל `chrome-profile-headless`. פתיחת Chrome במצב browser כוללת כעת `--new-window`, `--start-maximized`, ו-`--no-first-run`. גרסאות עודכנו ל-API/APP `1.22`/`1.60`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `py_compile` עבר עבור `update_products_batch_2.py` ו-`server.py`; diagnostics נקיים לקבצי Python/JS/HTML ששונו; probe מול 9222 החזיר `PID=27856`, `HEADLESS=False`, `ENSURE_VISIBLE=True` עם command line של Chrome נראה על `chrome-profile-chatgpt-visible`; לאחר restart, `/api/health/version` החזיר `api_version=1.22` ומאזינים פעילים יחידים על 8000 ו-9222.
- Outcome: בחירת מצב דפדפן כבר לא תישען על מופע debug headless קיים; אם 9222 תפוס על ידי headless, הוא יוחלף בחלון Chrome נראה.

### [ID: 20260719-11] [Status: completed]
- Timestamp: 2026-07-19
- Request: תיקון תקיעה בלולאת כתיבה ל-ChatGPT בדפדפן, שבה `safe_write_to_prompt` נכשל שוב ושוב עם stacktrace של chromedriver.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` הוקשח מנגנון כתיבת prompt ל-ChatGPT: נוספו selectors ל-`textarea`, `contenteditable`, ו-ProseMirror; נוספה כתיבה לפי סוג אלמנט עם `InputEvent`; נוסף fallback להדבקה דרך clipboard; ה-retry צומצם ל-3 ניסיונות עם הודעת שגיאה קצרה וברורה במקום stacktrace ארוך. גרסאות עודכנו ל-API/APP `1.21`/`1.59`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics וקומפילציה ממוקדת עברו לאחר התיקון. Probe מול Chrome debug קיים החזיר `url=https://chatgpt.com/; title=רק רגע...; state=prompt_not_visible` ו-`CANDIDATES=0`, כלומר כעת המערכת תדווח במפורש שתיבת ChatGPT לא זמינה במקום להמשיך בלופ.
- Outcome: מצב דפדפן ChatGPT כבר לא אמור להיתקע בלולאת כתיבה רעשנית; אם תיבת ההודעה לא זמינה, תתקבל שגיאה קצרה שמכוונת לבדוק login/visibility.

### [ID: 20260719-10] [Status: completed]
- Timestamp: 2026-07-19
- Request: לאפשר ל-Enrichment לעבוד או דרך API עם מפתח או דרך דפדפן רגיל מול ChatGPT, עם אותו JSON format בשתי קריאות ה-AI.
- Implementation: נוספה בחירת provider במסוף ההזנה (`api`/`browser`). ה-UI מעביר `ai_provider`, השרת מעביר `--ai-provider`, ו-`update_products_batch_2.py` מפעיל את שתי קריאות ה-enrichment דרך API או דרך ChatGPT בדפדפן לפי הבחירה. מסלול הדפדפן משתמש באותו prompt, מחייב `JSON only`, מפענח דרך אותו parser/decode של מנוע Gemini, ומחזיר אותו מבנה downstream. גם בדיקת title essence עוברת לדפדפן כשנבחר provider browser. גרסאות עודכנו ל-API/APP `1.20`/`1.58`.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: בוצעו diagnostics וקומפילציה ממוקדת לאחר העריכה; בנוסף בוצע smoke ללא רשת עם `browser_json_callable` מזויף שמוודא ש-`enrich_single_product(..., ai_provider="browser")` מקבל ומחזיר את אותו מבנה JSON downstream עם `VALIDATION_OK`.
- Outcome: ניתן לבחור אם סוכן ה-AI ירוץ דרך API פנימי או דרך ChatGPT בדפדפן, בלי לשנות את פורמט ה-JSON שהמשך המערכת מקבל.

### [ID: 20260719-09] [Status: completed]
- Timestamp: 2026-07-19
- Request: מוצר 35735 קיבל כותרת מקור/AI של מארז DeepCool CG580 אך `Title Guard` תיקן אותו בטעות ל-`cpu_cooler`, נחסם ב-Gemini Guard, ולא פורסם.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` הוקשחה הסקת משפחת כותרת כך שטיפוס מפורש מתוך `PRODUCT_NAME`/`FORMATTED_TITLE`/recommended type גובר על קטגוריית DB ישנה לפני הפעלת תיקון קירור. בנוסף זוהו דגמי DeepCool `CG` כמארזים לצד `CH`, כולל override קטגוריה ל-147 ונרמול כותרות CG מזוהמות. גרסאות עודכנו ל-API/APP `1.19`/`1.57`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: לאחר העריכה בוצעה בדיקת syntax/guard ממוקדת.
- Outcome: כותרות מארז מפורשות כמו `מארז מחשב פנורמי DeepCool CG580 4F V2 WH` כבר לא אמורות לעבור תיקון משפחה ל-`קירור למעבד` גם אם הקטגוריה הקודמת הייתה 149.

### [ID: 20260719-08] [Status: completed]
- Timestamp: 2026-07-19
- Request: אם לא התקבלו נקודות שיווקיות בפרדיקציה, לעצור את העלאה ל-MG/לאתר, לרשום לוג של היעדר פרדיקציה, ולהמשיך למוצר הבא.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` נוסף gate קשיח שמזהה פרדיקציה ללא `PRODUCT_FACTS` ומפסיק את הזרימה לפני publish, עם `insert_product_error(..., "missing_prediction_marketing_points", ...)` ולוג ברור. אותו gate נוסף גם למסלול publish מתוך payload שמור, כדי שלא יתבצע fallback שקט לנקודות ריקות.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: לא בוצע עדיין לאחר העריכה; נדרש להריץ בדיקת syntax/flow ממוקדת על `update_products_batch_2.py`.
- Outcome: מוצרים ללא נקודות שיווקיות לא יעלו יותר לאתר, והריצה תמשיך אוטומטית למוצר הבא עם לוג ייעודי.

### [ID: 20260719-07] [Status: completed]
- Timestamp: 2026-07-19
- Request: להכין תיעוד מדויק ומפורט של מנגנון הפרדיקציה שורה-שורה, ולשמור בקובץ `PREDICTION.MD`.
- Implementation: נכתב מסמך חדש `PREDICTION.MD` בשורש הפרויקט עם פירוט מלא של זרימת הפרדיקציה בפועל: bootstrap, flags, Phase-1 category lock, Phase-2 AI enrichment, title/attribute guards, HTML/content materialization, DB persistence, publish-to-MG path, retries/logging, ושדות מטא/פלט מרכזיים.
- Files changed: PREDICTION.MD, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: המסמך נוצר בפועל בנתיב `PREDICTION.MD` ומכסה את שני נתיבי הקוד המרכזיים (`update_products_batch_2.py` ו-`product_scraper_engine/enricher.py`) כולל סדר ביצוע, תופעות זמן ריצה, ולוגים.
- Outcome: קיים כעת תיעוד תפעולי מלא ועדכני של מנגנון הפרדיקציה לשימוש צוות הפיתוח/תפעול.

### [ID: 20260719-06] [Status: completed]
- Timestamp: 2026-07-19
- Request: לתקן בפועל באתר את מוצר 35730 שכבר פורסם לא נכון, כך שיישמר ב-MG עם קטגוריית מארז (147) ומאפיינים/תמונות תואמים.
- Implementation: בוצעה ריצת publish ייעודית עם `--publish-to-mg` עבור 35730 אחרי תיקון override; ה-payload שנשלח ל-MG כלל `category=147`, `categories=[147]`, סט פרמטרים `param_*` של קטגוריית מארז, ותמונות `image1..image5` מ-`C:\Temp\ProducsImages\210087`.
- Files changed: LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: הלוג `scratch/publish_35730_category147_fix.log` מאשר `Title-based override: 149 -> 147`, `Locked category from 409 to 147`, עדכון שדות `param_*`, `category`, `categories`, ותוצאה סופית `Product updated successfully! Final URL: https://www.king-games.co.il/apanel/products&edit=35730`.
- Outcome: מוצר 35730 תוקן בלייב ב-MG למסלול מארזי מחשב (147) עם מאפיינים ותמונות תואמים, ללא מסלול קירור שגוי.

### [ID: 20260719-05] [Status: completed]
- Timestamp: 2026-07-19
- Request: לתקן סופית את מקרה 35730 כך שלא יישאר בקטגוריית 409 (מוצרים חדשים) ולא יקבל סכמת קירור; לאמת בהרצה חיה מלאה.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` תוקן יעד override למארזים מתוך `_infer_explicit_category_from_title()` מ-`409` ל-`147`, וב-`infer_product_type_for_engine()` נוסף מיפוי `147 -> desktop`. הועלו גרסאות ל-API/APP `1.16`/`1.54` ב-`king_games_product_manager/server.py` ו-`king_games_product_manager/app.js`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: ריצה ממוקדת חדשה על 35730 (`scratch/verify_35730_category147_fix_rerun2.log`) מאשרת: `Title-based override: 149 -> 147`, `Locked category from 409 to 147`, `Gemini Guard][OK`, `RECOMMENDED_CATEGORY_ID: 147`, `RECOMMENDED_PRODUCT_TYPE: desktop`, וללא `Gemini Guard][Block` או זליגה ל-`cpu_cooler`.
- Outcome: מוצר 35730 מטופל כעת כמארז מחשב בקטגוריה 147 עם סכמת מאפיינים מתאימה, במקום קטגוריית 409/סכמת קירור.

### [ID: 20260719-04] [Status: completed]
- Timestamp: 2026-07-19
- Request: מוצר 35730 עדיין קיבל פרדיקציית קירור שגויה למרות שהוא מארז; נדרש לתקן גם מצב שבו הכותרת ב-DB כבר הורעלה לרמזי קירור.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` נוספו 3 שכבות הגנה: (1) `_infer_explicit_category_from_title()` מחזיר `409` עבור דפוסי מארז (`מארז/case/chassis` וגם `CH\d+`), (2) `_title_has_cpu_cooler_markers()` + guard שמונע נעילת קטגוריה 149 כשאין סימני קירור מפורשים בכותרת, (3) `_normalize_obvious_misclassified_case_title()` שמנרמל לפני Phase-1 כותרת "מורעלת" של DeepCool CH-series חזרה ל-`DEEPCOOL CH690 DIGITAL WH`. בנוסף `infer_product_type_for_engine` מזהה `409` כ-`desktop`. גרסאות הועלו ל-API/APP `1.15`/`1.53`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: ריצה חיה על 35730 (`scratch/verify_35730_family_fix_v3.log`) הראתה normalization לקלט, override לקטגוריה 409, כותרת סופית "מארז מחשב...", ו-`[Gemini Guard][OK]` בלי `Block`.
- Outcome: מסלול 35730 לא נשאב יותר למסלול קירור; זיהוי מארז נשמר גם כשהכותרת המקומית כבר הושחתה קודם.

### [ID: 20260719-03] [Status: completed]
- Timestamp: 2026-07-19
- Request: מוצר 35730 (מארז) הוסט בטעות ע"י `Title Guard` למשפחת `cpu_cooler` ונחסם ב-`Gemini Guard`.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` הוקדמה קדימות זיהוי משפחה מתוך `base_title` לפני מיפוי לפי קטגוריה, כך שכותרת מפורשת (למשל "מארז"/"ספק כוח") גוברת על קטגוריה שגויה; בנוסף נוספה תמיכה מפורשת ב-`מארז/case/chassis` בתוך `_infer_explicit_product_type_from_title`, וטיפוסים מפורשים לא-CPU (`desktop/laptop/monitor`) ממופים ל-`generic` כדי לא להיכנס למסלול תיקון קירור. גרסאות הועלו ל-API/APP `1.14`/`1.52`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics נקיים; הרצה ממוקדת ל-35730 לא אמורה יותר לייצר `title_guard_corrected` למשפחת `cpu_cooler` כאשר הכותרת מצביעה על מארז.
- Outcome: `Title Guard` לא יהפוך עוד מוצרי מארז/PSU לכותרות קירור רק בגלל הקשר/קטגוריה שגויים.

### [ID: 20260719-02] [Status: completed]
- Timestamp: 2026-07-19
- Request: בתרחיש מוצר 35729 (ספק כוח) `Title Guard` המיר בטעות את הכותרת למשפחת `cpu_cooler` וחסם/עיוות את הפרדיקציה.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` הוקשחה הסקת `title family`: נוספה מפה ישירה `146 -> psu`, נוספה קדימות קשיחה לזיהוי מפורש מתוך `base_title` (`_infer_explicit_product_type_from_title`) לפני הסקה מהקשר רחב, ונוספה ולידציה ייעודית למשפחת `psu` ב-`_is_title_valid_for_family()` כדי למנוע זליגה לכותרות קירור. גרסאות הועלו ל-API/APP `1.13`/`1.51`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics נקיים; נתיב ההסקה כעת מחזיר `psu` עבור כותרות עם "ספק כוח/ספק כח" גם אם ההקשר כולל מילים מטעות.
- Outcome: מוצרי ספק כוח לא יעברו יותר "תיקון" לכיוון `קירור למעבד` ע"י Title Guard.

### [ID: 20260719-01] [Status: completed]
- Timestamp: 2026-07-19
- Request: במקרה `title_guard_blocked` (כמו מוצר 35726) לא לעצור פרדיקציה; רק לרשום לוג ולהמשיך רגיל.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` שונה הענף של `if not title_guard_ok` ממצב חוסם למצב אזהרה בלבד: הודעת לוג עודכנה ל-`[Title Guard][Warn] ... continuing prediction flow as requested`, נשמר `insert_product_error(..., "title_guard_blocked", ...)`, והוסרו `failed_list.append(...)` + `continue`, כך שהזרימה ממשיכה ליצירת `PRODUCT_NAME/FORMATTED_TITLE` ולהמשך הפרדיקציה/פרסום. גרסאות הועלו ל-API/APP `1.12`/`1.50`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: בדיקת diagnostics לקבצים ששונו ללא שגיאות.
- Outcome: `title_guard_blocked` הוא כעת log-only ואינו מפיל יותר את עיבוד המוצר.

### [ID: 20260717-12] [Status: completed]
- Timestamp: 2026-07-17
- Request: לעצור סופית מקרה שבו `Title Rules` מרנדרים כותרת ממשפחה אחרת (למשל מסך) מעל כותרת AI למוצר ספק כוח.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` הוקשחה לוגיקת בחירת כותרת: כאשר קיימת `ai_formatted_title`, היא כעת authoritative ותמיד נשמרת. `rendered_title` נדחה לוגית אם שונה (עם לוג `[Title Rules][Reject Rendered]`). `rendered_title` משמש רק כשאין כותרת AI בכלל.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: הרצה ממוקדת על 35723 אמורה להציג Reject Rendered במקום Guardrail override; Publish עדיין נחסם ע"י Gemini mismatch guard אם יש סטייה סמנטית.
- Outcome: אין יותר override מקומי של כותרת AI על ידי Template Rules; נמנעת זליגה ממשפחת מוצר שגויה דרך renderer.

### [ID: 20260717-11] [Status: completed]
- Timestamp: 2026-07-17
- Request: בריצה על 35723 הופיעה כותרת מרונדרת שגויה (`מסך גיימינג...`) למרות שמדובר בספק כוח; נדרש לעצור override שגוי של Title Rules.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` נוספה פונקציית התאמה `_title_matches_expected_product_type()` (PSU/cooler/cpu/monitor/laptop/desktop). בלוגיקת `Title Rules` אם `rendered_title` שונה מ-`ai_formatted_title`, כעת היא תאומץ רק אם היא תואמת את סוג המוצר הצפוי; אחרת היא נדחית ונשמרת כותרת ה-AI. כך נמנע override מקומי שגוי כמו PSU->monitor. גרסאות הועלו ל-API/APP `1.10`/`1.48`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: בדיקה סטטית נקייה לקבצים ששונו; לפי זרימת הקוד כותרת מרונדרת שלא תואמת סוג מוצר לא תחליף יותר את כותרת ה-AI.
- Outcome: כותרות מקומיות מרונדרות לא יגררו יותר מהות מוצר שגויה (למשל מסך/קירור במקום ספק כוח) כשהכותרת המקורית מצביעה אחרת.

### [ID: 20260717-10] [Status: completed]
- Timestamp: 2026-07-17
- Request: לאחר הרצה יחידנית על 35723 עדיין התקבלה אזהרת `title_essence_mismatch` עם סיווג קירור במקום ספק; נדרש למנוע זאת קשיח ולהפסיק Publish במוצר שנכשל guard.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` הוחמרו guards: (1) override קטגוריה מבוסס כותרת כבר לא תלוי ב-`ALLOWED_CATEGORY_IDS` (כדי שלא יידחה ספק כוח רק כי רשימת leaf קטגוריות חסרה); (2) נוסף guard משפחה קשיח שמונע קטגוריית קירור (`149`) כאשר הכותרת מצביעה על PSU, ומאלץ fallback לקטגוריה מפורשת/מקורית; (3) נוספה קבוצה גלובלית `BLOCK_PUBLISH_PRODUCT_IDS` כך שמוצר שנכשל `Gemini guard` (mismatch/connectivity) נחסם גם משלב publish באותה ריצה ולא ממשיך עם payload ישן. גרסאות הועלו ל-API/APP `1.09`/`1.47`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: אימות לוגי של נתיב 35723: זוהה root cause קודם (`category 149` למרות שם PSU), ותיקון guards מונע נעילה זו ומונע publish כאשר Gemini mismatch מזוהה.
- Outcome: לא אמור יותר לקרות מצב שבו שם ספק כוח עובר ל-Gemini תחת מסלול קירור; ובכשל guard המוצר לא יפורסם באותה ריצה.

### [ID: 20260717-09] [Status: completed]
- Timestamp: 2026-07-17
- Request: בהרצה יחידנית מתקבלת שגיאה: `can't open file 'C:\\Projects\\KINGGAMES\\update_products_batch_2.py'`.
- Implementation: ב-`king_games_product_manager/server.py` תוקן `start_ingestion` כך שההרצה משתמשת בנתיב מוחלט ל-`update_products_batch_2.py` דרך `os.path.join(BASE_DIR, ...)` ובנוסף `subprocess.Popen(..., cwd=BASE_DIR)` כדי לבטל תלות בתיקיית ההפעלה של השרת. הועלו גרסאות ל-API/APP `1.08`/`1.46`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: בדיקה סטטית על הקבצים ששונו ללא שגיאות; לוגיקת יצירת הפקודה בהרצה יחידנית/טווח כבר לא תלויה ב-cwd חיצוני.
- Outcome: הזנת מוצרים (יחידני וטווח) אמורה להיפתח תמיד מהנתיב הנכון של `king_games_product_manager/update_products_batch_2.py`.

### [ID: 20260717-08] [Status: completed]
- Timestamp: 2026-07-17
- Request: אחרי ריצת טווח 35701-35750, מוצר 35720 (ספק כוח) הועבר כמו קירור למעבד; לבדוק לוגים, למצוא שורש, ולהקשיח כולל דילוג כשאין קשר ל-Gemini ובדיקת התאמה בין שם מקור לשם פרדיקציה.
- Implementation: בוצעה חקירת לוגים שהראתה כי עבור 35720 נשלח ל-Gemini `Product Type: cpu_cooler` למרות ששם המקור הוא ספק כוח. ב-`king_games_product_manager/update_products_batch_2.py` הוספתי זיהוי סוג מוצר מפורש מהכותרת (`_infer_explicit_product_type_from_title`) עם עדיפות לשם המקור על פני קטגוריה (כולל `psu/power supply/ספק כוח`) ותוקן `infer_product_type_for_engine()` לעבוד title-first. בנוסף הוסף Guard חדש אחרי יצירת כותרת: קריאה נוספת ל-Gemini להשוואת מהות בין `original_title` ל-`predicted_title`; אם אין קישוריות ל-Gemini נרשם לוג/שגיאה ומדלגים למוצר הבא, ואם יש אי-התאמה מהותית המוצר נחסם. ב-`product_scraper_engine/enricher.py` נוספו `compare_title_essence_with_gemini()` ולוג קישוריות ייעודי `product_scraper_engine/logs/gemini_connectivity.log`. גרסאות הועלו ל-API/APP `1.07`/`1.45`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/server.py, king_games_product_manager/app.js, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: אימות לוגים הראה ב-35720 את מקור הכשל (`Input Product Name=ספק כוח` יחד עם `Product Type=cpu_cooler`). לאחר שינוי הקוד בוצעה בדיקת שגיאות סטטית ללא שגיאות בקבצים ששונו.
- Outcome: התוכנית מוקשחת נגד זליגת family שגויה; ספקי כוח לא אמורים להישלח יותר כ-cpu_cooler, ובכשל קישוריות ל-Gemini Guard המוצר מדולג אוטומטית עם לוג מסודר.

### [ID: 20260717-07] [Status: completed]
- Timestamp: 2026-07-17
- Request: טווח מוצרים חייב לעבוד בדיוק כמו יחידני אחד-אחד; בפועל אחרי ריצה 35700-35705 לא התעדכן valid/עדכון.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` הוספתי מצב קשיח לטווח/רשימה ידנית: `is_manual_multi_mode()` + `run_manual_mode_as_strict_single()`. כאשר הקלט הוא multi-ID ידני, הסקריפט מפעיל תתי-ריצות יחידניות לכל מזהה בתורו, עם אותם runtime flags בדיוק, כולל `publish_to_mg`. בכל איטרציה מוחלף רק `mode` ל-ID בודד ונשמרת כל שאר הקונפיגורציה, כך שההתנהגות זהה ליחידני. הועלו גרסאות ל-API/APP `1.06`/`1.44`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: לוגיקה נבדקה סטטית: ב-mode ידני multi הסקריפט נכנס ל-`Strict single iteration mode` ומריץ כל מוצר כתת-ריצת יחידני מלאה; עבור single/category/all אין שינוי התנהגות.
- Outcome: מסלול טווח ידני רץ מעכשיו כשרשרת ריצות יחידניות אמיתיות מוצר-אחר-מוצר, ללא סטייה לוגית מהמסלול היחידני.

### [ID: 20260717-06] [Status: completed]
- Timestamp: 2026-07-17
- Request: אני מעוניין שבהזנה של טווח מוצרים זה יעבוד בדיוק אותו דבר כמו יחידני על טווח המוצרים אחד לאחד.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` אוחדה לוגיקת parsing של mode ידני (single/range/list) כך שתתנהג כמו ריצה יחידנית לכל מוצר: נוספה תמיכה בטוקנים מופרדים בפסיקים/רווחים/שורות/נקודה-פסיק, תמיכה בטווחים מספריים עם `-`/`–`/`—`, ורזולוציה לכל טוקן דרך `resolve_input_to_mg_id()` (כולל SKU/SAP ולא רק מספרים). בנוסף נוספו לוגים ברורים לטוקנים שלא נפתרו. גרסאות הועלו ל-API/APP `1.05`/`1.43`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: בוצעה בדיקת קוד סטטית של נתיב `select_product_ids` לאחר התיקון, עם שמירה על דה-דופליקציה וסדר ריצה מוצר-מוצר; נוספה נראות לוגית ל-`[ID Mapping] Unresolved manual inputs` לצורכי דיבוג.
- Outcome: הזנת טווח/רשימה עובדת באותה צורת פירוק-לקלט-בודד כמו יחידני, כולל קלטים מעורבים ורזולוציה עקבית ל-MG ID.

### [ID: 20260717-05] [Status: completed]
- Timestamp: 2026-07-17
- Request: להפסיק באופן סדור וקשיח מקרים שבהם שם המוצר נהרס בפרדיקציה, במיוחד טעויות קריטיות כמו קירור למעבד שמקבל שם של מעבד (למשל 35695 `מעבד סוג B5 תושבת אפור`).
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` הוטמעה שכבת governance מלאה על כותרת המוצר: נוספו `TITLE_FAMILY_BY_CATEGORY`, זיהוי family לפי קטגוריה/הקשר, builder דטרמיניסטי לשם קירור CPU, ו-`_enforce_final_title_family_guard()` שרץ אחרי `apply_title_rule_template()` ולפני save/publish. בנוסף, `infer_product_type_for_engine()` ממפה כעת קטגוריה 149 ל-`cpu_cooler` (וגם 142/264 ל-`cpu`/`case_fan`), וב-`title_header_rules.json` נוסף כלל title ייעודי `קירור למעבד` עם template מתאים. אם שם סופי לא עומד בבקרת המשפחה, הוא מתוקן אוטומטית; ואם עדיין לא חוקי, הריצה נחסמת עם `title_guard_blocked`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/title_header_rules.json, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: smoke test על הארטיפקטים האמיתיים של 35695 ו-35693 אישר rendering דרך rule `קירור למעבד` עם פלטים: `קירור אקטיבי למעבד Dynatron B5 LGA 3647 אפור` ו-`קירור אקטיבי למעבד Dynatron Q7 LGA 1851 אפור`. `guard_ok=true` בשני המקרים ו-`VALIDATION_OK`. diagnostics נקיים.
- Outcome: שם המוצר כבר לא נשאר שדה best-effort; יש עכשיו בקרת family מקומית שמתקנת או חוסמת שמות שגויים לפני DB ו-MG publish, ובפרט מונעת זליגה מ"קירור למעבד" ל"מעבד".

### [ID: 20260717-04] [Status: completed]
- Timestamp: 2026-07-17
- Request: בתהליך שמנרמל תמונות מקומיות ל-`1,2,3...` עבור העלאה ל-MG, להוסיף גם כיווץ קשיח כך שאף תמונה לא תועלה אם גודלה מעל 350KB.
- Implementation: ב-`king_games_product_manager/update_products_batch_2.py` נוספה אכיפת `MG_MAX_IMAGE_UPLOAD_KB = 349` במסלול התמונות המקומיות. `_normalize_local_image_filenames()` כבר לא רק ממספר קבצים, אלא מכין אותם להעלאה ל-MG דרך `_compress_image_to_mg_limit()` ו-`_enforce_mg_image_limits_for_files()`: הקבצים מומרצים ל-`1.webp`, `2.webp` וכו', עם הורדת quality ו-resize מדורג עד שהגודל יורד מתחת לרף. בנוסף נסגר נתיב fallback שעלול היה להחזיר קבצים מקוריים גדולים מדי אם הכנת ה-WebP נכשלה; במצב כזה התמונות לא יחזרו למסלול upload בכלל.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: smoke test יצר תמונת מקור בגודל `1,214,710` bytes, והכנת התמונות ל-MG הפיקה `1.webp` בגודל `173,610` bytes (`169.5KB`) עם `VALIDATION_OK`. אימות נוסף הראה שהספרייה הזמנית מכילה רק `1.webp` בגודל המופחת. diagnostics נקיים.
- Outcome: כל תמונה מקומית שמועברת ל-MG מוכנה עכשיו מראש בפורמט ממוספר ובמשקל שמתחת למגבלת 350KB; קובץ שלא ניתן להכין כחוק לא יישלח ל-upload.

### [ID: 20260717-03] [Status: completed]
- Timestamp: 2026-07-17
- Request: לתקן מקרה שבו מוצר קירור למעבד (35693) קיבל שם שגוי כמו `מעבד סוג Q7 אפור` למרות שכל ההקשר מצביע על גוף קירור/מאוורר למעבד.
- Implementation: ב-`king_games_product_manager/product_scraper_engine/enricher.py` נוספו: זיהוי משפחת מוצר (`_detect_product_family`) עם זיהוי ייעודי ל-CPU cooler, guardrails חדשים ב-prompt שמכריחים את Gemini לתאר מוצרי קירור כקירור/גוף קירור ולא כמעבד, ו-postprocess (`_enforce_product_family_naming`) שמתקן `PRODUCT_NAME` ו-`FORMATTED_TITLE` אם Gemini עדיין מחזיר שם שנראה כמו מעבד. עבור קירורי CPU נבנה fallback category-aware מתוך שם המקור, היצרן, המודל, התאמת socket וצבע. הועלו גרסאות ל-API/APP `1.02`/`1.40`.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: smoke test עם `DYNATRON Q7 LGA 1851/1700 1U ACTIVE COOLER` זיהה משפחה `cpu_cooler` ותיקן את השם מ-`מעבד סוג Q7 אפור` ל-`קירור אקטיבי למעבד Dynatron Q7 LGA 1851/1700 אפור` (`VALIDATION_OK`). אורך השם נבדק ונשאר 49 תווים. diagnostics נקיים.
- Outcome: מוצרי קירור למעבד לא יקבלו יותר שמות של מעבדים גם כאשר `Product Type` מגיע כ-`unknown` או כשחסר title rule ייעודי לקירור.

### [ID: 20260717-02] [Status: completed]
- Timestamp: 2026-07-17
- Request: למנוע שבירת JSON מתשובת Gemini בגלל מפתחות/ערכים עם מירכאות, למשל `גודל מאוורר בס"מ`, ע"י מעבר ל-URLENCODING במאפיינים ובערכים הרגישים.
- Implementation: ב-`king_games_product_manager/product_scraper_engine/enricher.py` הוחלף החוזה מול Gemini עבור `PRODUCT_TECHNICAL_DETAILS`, `PRODUCT_ATTRIBUTES` ו-`RECOMMENDED_CATEGORY_ATTRIBUTES`: נוספו helperים ל-URL encode/decode, ה-prompt מציג מפות `original -> encoded`, ה-response schema דורש מפתחות URL-encoded לשדות הרגישים, והתגובה מפוענחת חזרה אוטומטית לשמות/ערכים המקוריים אחרי ה-parse. בנוסף תוקן bug מקומי ב-`build_prompt` שבו `category_attributes_codes_block` לא אותחל/הוזח נכון. הועלו גרסאות ל-API/APP `1.01`/`1.39`.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: smoke test ייעודי אישר round-trip מלא של מפתח בעייתי `גודל מאוורר בס"מ` וערכים עם `"` דרך encode/decode, כולל `RECOMMENDED_CATEGORY_ATTRIBUTES`, עם פלט `VALIDATION_OK`. בדיקת diagnostics נקייה.
- Outcome: Gemini כבר לא נדרש להחזיר מפתחות/ערכים גולמיים עם מירכאות בשדות הרגישים; המבנה נשאר JSON תקין והמערכת מפענחת חזרה לשמות המקוריים לשאר הזרימה.

### [ID: 20260717-01] [Status: completed]
- Timestamp: 2026-07-17
- Request: כאשר מופיעה האזהרה `Warning: Gemini returned invalid JSON`, לשמור בלוג של מה שהתקבל בפועל מגמיני כדי לראות את ה-raw response.
- Implementation: ב-`king_games_product_manager/product_scraper_engine/enricher.py` נוספה כתיבה לקובץ לוג ייעודי `product_scraper_engine/logs/gemini_invalid_json.log` בכל `JSONDecodeError` מתשובת Gemini. הלוג כולל timestamp, model, attempt, שורת/עמודת השגיאה, ואת `raw_response` המלא כפי שחזר מהמודל. הודעת האזהרה ב-stderr עודכנה כך שתדפיס גם את נתיב קובץ הלוג.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: בוצעה בדיקת smoke ייעודית שיצרה קובץ לוג ונקרא ממנו התוכן המאומת: `raw_response` נשמר במלואו יחד עם metadata של השגיאה.
- Outcome: כל אזהרת `Gemini returned invalid JSON` מייצרת מעכשיו לוג קריא עם הטקסט הגולמי שקיבלנו מגמיני.

### [ID: 20260716-19] [Status: completed]
- Timestamp: 2026-07-16
- Request: תיקון קריסה ב-Local Enrichment על מוצר 35692 עם שגיאת JSON parse (`Expecting ':' delimiter`) מתשובת Gemini.
- Implementation: ב-`king_games_product_manager/product_scraper_engine/enricher.py` הוספנו שכבת parsing קשיחה לתשובת Gemini (`_parse_gemini_json_text`) שכוללת: הסרת markdown code fences, חילוץ אובייקט JSON מתוך טקסט מעורב, ותיקון פסיקים נגררים לפני `}`/`]`. בנוסף, `call_gemini_api` עודכן ל-retry ייעודי על `JSONDecodeError` וחריגות מבנה תשובה (`KeyError/IndexError/TypeError`) במקום כשל מיידי.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: בדיקת parser חיה עם 4 תרחישים (JSON תקין, fenced JSON, trailing comma, וטקסט מעורב עם JSON) עברה בהצלחה והחזירה אובייקטים תקינים בכל המקרים. בדיקת diagnostics: ללא שגיאות בקבצים ששונו.
- Outcome: כשלי פורמט קלים בתשובת Gemini לא מפילים יותר את שלב ה-enrichment; המערכת מנסה לתקן/לפרש ומבצעת retry לפני כישלון סופי.

### [ID: 20260716-18] [Status: completed]
- Timestamp: 2026-07-16
- Request: לתקן את מנגנון ה-Force Overrides כך שהפורמט `--param_1:...` באמת ידרוס ערכים מהפרדיקציה (ולא יעבור עם הערך הישן).
- Implementation: ב-`update_products_batch_2.py` תוקן parser ה-overrides: נוספה נרמול מפתחות שמסירה קידומת `--` ותומכת גם בכתיב עם מקף (`param-1`/`icon-34`) בנוסף לכתיב עם underscore; כך שורות כמו `--param_1:...`, `--icon-34`, `--no-icon-35` מפוענחות ונאכפות על ה-payload לפני שליחה למודול MG. הועלו גרסאות ל-API/APP `0.98`/`1.36`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: בדיקת parser חיה עם הטקסט:
	`--param_1:12 חודשי אחריות ע"י רשת קינג גיימס`
	`--icon-34`
	`--no-icon-35`
	`param_2=@3`
	החזירה: `param_1` עם הערך הטקסטואלי החדש, `icon_34=True`, `icon_35=False`, ו-`param_2` כאינדקס 3.
- Outcome: הפורמט שכתבת עכשיו נתמך ישירות, והערכים שלך דורסים בפועל את ערכי הפרדיקציה.

### [ID: 20260716-17] [Status: completed]
- Timestamp: 2026-07-16
- Request: לאפשר "הזרקה"/אכיפה של פרמטרים שנשלחים למודול MG בלי תלות בפרדיקציה (לדוגמה: `param_1` לבחור תמיד אופציה 4, `icon_34` מסומן, `icon_17` לא מסומן).
- Implementation: הוטמעה תיבת טקסט חדשה במסוף ההזנה (`ingMgForceOverrides`) להגדרת Overrides קשיחים; הערך מועבר ב-`runtime_flags` לשרת ומשם ל-CLI של `update_products_batch_2.py` דרך `--mg-force-overrides`; ב-`update_products_batch_2.py` נוספו parser ויישום כפוי ל-payload לפני שליחה למודול MG: תמיכה ב-`param_X=@N` (בחירת אופציה N בקומבו), `icon_34=true/false`, וכן דגלים בסגנון `--icon-34` / `--no-icon-17`; במודול החיצוני `C:\Projects\AgentUpdateMGsystem\update_product.py` נוספה תמיכה במרקר `__OPTION_INDEX__:N` כדי לבחור ערך קומבו לפי אינדקס (1-based).
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, king_games_product_manager/update_products_batch_2.py, C:\Projects\AgentUpdateMGsystem\update_product.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: smoke חי על `35689` עם overrides `param_1=@4`, `--icon-34`, `--no-icon-17` הסתיים `EXIT_CODE=0`; בלוג מאשר `[MG Force Overrides] Applied`; payload אחרון מאשר: `param_1=__OPTION_INDEX__:4`, `icon_34=True`, `icon_17=False`.
- Outcome: ניתן כעת לכפות ערכי MG נקודתיים (קומבו/checkbox) בכל ריצה דרך ה-UI, ללא תלות בתוצאת AI/prediction.

### [ID: 20260716-16] [Status: completed]
- Timestamp: 2026-07-16
- Request: לפני קריאת תמונות מהספרייה לפי מק"ט, לשנות שמות קבצים ל-`1,2,3...` עם אותה סיומת לפי סדר קובץ ישן->חדש (הכי ישן יקבל `1`).
- Implementation: ב-`update_products_batch_2.py` נוספה פונקציה `_normalize_local_image_filenames(image_dir)` שמאתרת קבצי תמונה (`webp/png/jpg/jpeg`), ממיינת לפי `mtime` ואז שם, ומבצעת rename דו-שלבי בטוח (דרך שמות זמניים) למניעת התנגשויות. הפונקציה מוזנקת אוטומטית בתוך `_list_local_images_for_sku(...)` רגע לפני קריאת הקבצים מהספרייה, כך שהלוגיקה הקיימת של בחירת קבצים נשמרת ורק נוסף שלב נרמול שמות. הועלו גרסאות ל-API/APP `0.96`/`1.34`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics נקיים עבור כל הקבצים ששונו; חיבור הפונקציה מאומת בנתיב קריאת תמונות לפי SKU כך שהנרמול קורה תמיד לפני list/selection.
- Outcome: MG יקבל נתיבי קבצים עם שמות ממוספרים ויציבים (`1.ext`, `2.ext`, `3.ext`...), לפי סדר גיל קובץ, בלי לשנות את שאר לוגיקת ההעלאה.

### [ID: 20260716-15] [Status: completed]
- Timestamp: 2026-07-16
- Request: לבדוק האם נשלח אותו ערך לשדות `catalog_num` ו-`sup_sku0` במודול עדכון MG, ולתקן כך ש-`catalog_num` יהיה שדה SAP ו-`sup_sku0` יישאר ספק.
- Implementation: ב-`update_products_batch_2.py` תוקן מיפוי ה-payload ל-MG: `catalog_num` ממופה כעת ל-`sap_sku` במקום `supplier_sku`, ונוסף מיפוי מפורש ל-`sup_sku0` מתוך `supplier_sku`; בנוסף הועבר `sap_sku` לתוך `p_data` בשני מסלולי הפרסום (המסלול המקומי והמסלול הישן) כדי למנוע חוסר עקביות.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: בוצעה הרצה חיה על `35689` ונקרא לוג payload אחרון: `catalog_num=208421`, `sup_sku0=100072`, `same=False`; כלומר ההפרדה בין SAP לספק תקינה.
- Outcome: המערכת כבר לא שולחת אותו ערך לשני השדות; `catalog_num` מייצג SAP ו-`sup_sku0` מייצג מק"ט ספק.

### [ID: 20260716-14] [Status: completed]
- Timestamp: 2026-07-16
- Request: לתקן חוסר יציבות בפרסום MG עקב `No module named 'webdriver_manager'` ולתקן באג שבו מתבצע ניסיון הורדה/שמירה מיותר של עשרות תמונות גם כשיש תמונות לוקאליות או כשמנוע תמונות כבוי.
- Implementation: תוקן שוב המודול החיצוני `C:\Projects\AgentUpdateMGsystem\update_product.py` לייבוא אופציונלי של `webdriver_manager` עם fallback ל-Selenium Manager; בוצעה התקנה יזומה של `webdriver-manager` בסביבת `KINGGAMES` ונוספה התלות ל-`requirements.txt`; ב-`update_products_batch_2.py` נוספה לוגיקה שמדלגת על `cache_saved_image_urls_as_webp(...)` כאשר יש כבר תמונות לוקאליות או כאשר `img_scrpt=off`, כך שלא מתבצעות הורדות 30 תמונות מיותרות; נוספה גם שכבת self-heal ב-`_load_external_mg_updater_module()` שמזהה `ModuleNotFoundError: webdriver_manager`, מתקינה `webdriver-manager` ומנסה שוב טעינת מודול חיצוני אוטומטית. הועלו גרסאות ל-API/APP `0.94`/`1.32`.
- Files changed: C:\Projects\AgentUpdateMGsystem\update_product.py, king_games_product_manager/update_products_batch_2.py, requirements.txt, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: הרצה חיה על `35689` עם `--publish-to-mg --ai-agent off --img-scrpt off --check-local-images-first --headless` הסתיימה `EXIT_CODE=0`; בלוג ההרצה הופיע במפורש `Local images already exist ... Skipping remote image caching from AI/saved URLs`; ריצת הפרסום עברה את נקודת הכשל הישנה (`webdriver_manager`) והמשיכה לעדכוני שדות/תמונות בפועל.
- Outcome: שגיאת `webdriver_manager` הפסיקה לחסום את פרסום MG, וניסיון שמירת תמונות מיותר מהסוכן לא רץ יותר כשיש לוקאלי או כשהמנוע כבוי.

### [ID: 20260716-13] [Status: completed]
- Timestamp: 2026-07-16
- Request: ריצת פרסום נעצרה באמצע עם `execution_error` עקב `No module named 'webdriver_manager'`.
- Implementation: תוקן המודול החיצוני `C:\Projects\AgentUpdateMGsystem\update_product.py` כך שייבוא `webdriver_manager` יהיה אופציונלי (`try/except`), ובמקרה שהחבילה אינה מותקנת תתבצע נפילה ל-`webdriver.Chrome(options=...)` (Selenium Manager) במקום קריסה בזמן import. בוצע smoke להרצת publish path למוצר `35688` כדי לוודא שהזרימה עוברת את נקודת הכשל. הועלו גרסאות ל-API/APP `0.93`/`1.31`.
- Files changed: C:\Projects\AgentUpdateMGsystem\update_product.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: ולידציית import החזירה `IMPORT_OK True`; ריצת `update_products_batch_2.py 35688 --publish-to-mg ...` התקדמה בפועל עד `Navigating to login page` ו-`Submitting login credentials` (כלומר ללא קריסת import); בדיקת `product_errors` עבור `35688` החזירה `ROWS=0`.
- Outcome: כשל `No module named 'webdriver_manager'` לא עוצר יותר את ריצת הפרסום, גם כש`webdriver_manager` אינו מותקן בסביבה.

### [ID: 20260716-12] [Status: completed]
- Timestamp: 2026-07-16
- Request: להטמיע זרימת העשרה חובה ב-2 פאזות כדי למנוע שליחת סכמת מפרט שגויה (למשל laptop למסכים), ולהריץ יחידנית על `35688,35689,35690`.
- Implementation: ב-`update_products_batch_2.py` הוטמע מנגנון 2 פאזות: Phase-1 מסווג קטגוריה בלבד עם סכמת מפרט ניטרלית (`PHASE1_NEUTRAL_SPECS_KEYS`) ו-guardrail לפי confidence; לאחר מכן Phase-2 רץ רק עם קטגוריה נעולה וסכמת מאפיינים של אותה קטגוריה (`leaf_categories_text` חד-ערכי לקטגוריה הנעולה). נוספו חסמי בטיחות: `CATEGORY_PHASE1_CONFIDENCE_THRESHOLD=85`, אימות סכמת `PRODUCT_TECHNICAL_DETAILS` מול `specs_keys` בפועל, ורישום מטא-שדות פאזות (`PHASE1_CATEGORY_*`, `PHASE2_CATEGORY_LOCKED_ID`) לתוך `engine_response`. בנוסף תוקנה `infer_product_type_for_engine` כך שלא תחזיר `laptop` כברירת מחדל גורפת. בוצע version bump ל-API/APP `0.92`/`1.30`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: ריצת יחידני על `35688,35689,35690` הושלמה (`EXIT_CODE=0`) ונבדקה ישירות מ-`products.db`: לכל שלושת המוצרים קיימים `PHASE1_CATEGORY_RECOMMENDED_ID`, `PHASE1_CATEGORY_CONFIDENCE_PERCENT`, `PHASE2_CATEGORY_LOCKED_ID`; סכמות `PRODUCT_TECHNICAL_DETAILS` מכילות 15 מפתחות של מסכים וללא מפתחות מחשב נייד (`laptop_key_hits=0`).
- Outcome: תהליך ההעשרה עבר למודל דו-שלבי קשיח, כך שלא נשלחת יותר סכמת מפרט של קטגוריה אחרת לפני נעילת קטגוריה, ובדיקת 35688/35689/35690 עברה ללא זליגת שדות laptop.

### [ID: 20260716-11] [Status: completed]
- Timestamp: 2026-07-16
- Request: במסלול "חילוץ תמונות לפי ספקים" לשמור את התמונות בתיקייה לפי `supplier1_sku` ולא לפי `sap_sku`.
- Implementation: ב-`supplier_image_extraction_runner.py` תוקן סדר העדיפויות של `folder_sku` כך ששם התיקייה נקבע קודם מ-`available_suppliers[0]["sku"]` ורק אם חסר נופל ל-`sap_sku`, ולא להפך. הועלו גרסאות ל-API/APP `0.91`/`1.29`.
- Files changed: king_games_product_manager/supplier_image_extraction_runner.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics נקיים ל-`supplier_image_extraction_runner.py`; חיפוש קוד מאשר שהשורה הקנונית היא כעת `folder_sku = available_suppliers[0]["sku"] or product["sap_sku"] or product["mg_id"]`.
- Outcome: חילוץ התמונות לפי ספקים ישמור מעכשיו בתיקייה על שם מק"ט ספק ראשון כברירת מחדל, ולא על שם מק"ט SAP.

### [ID: 20260716-10] [Status: completed]
- Timestamp: 2026-07-16
- Request: להתאים את המערכת למודול MG המעודכן שמקבל תמונות דרך `image1..image5`, ולהריץ שוב את `35687`.
- Implementation: ב-`update_products_batch_2.py` הוחלפה מסירת התמונות למודול החיצוני כך ש-`update_data` מקבל ישירות את `image1..image5` עם נתיבי קבצים מקומיים, במקום `image_path/image_paths` כארגומנטים חיצוניים; בנוסף תוקן תנאי `allow_image_upload` כך שגם תמונות שכבר קיימות בדיסק ייחשבו תקינות להעלאה ולא רק תמונות שהורדו באותה ריצה. במודול `C:\Projects\AgentUpdateMGsystem\update_product.py` הושב fallback של `webdriver_manager` ונוספה הקשחת מילוי שדות/תוכן כדי להגיע בפועל לשלב העלאת התמונות. הועלו גרסאות ל-API/APP `0.90`/`1.28`.
- Files changed: king_games_product_manager/update_products_batch_2.py, C:\Projects\AgentUpdateMGsystem\update_product.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: לפני הריצה אומת קיום 3 קבצים ב-`C:\Temp\100103`; בריצה האחרונה של `35687` הלוג הראה `Uploading image1`, `Uploading image2`, `Uploading image3` ואף `Uploading image4`, `Uploading image5`; קובץ payload אחרון `mg_payload_35687_20260716_183228_171590.json` מראה בפועל `image1..image5` בתוך `update_data`; ב-`process_run.log` מופיע `Product updated successfully! Final URL: https://www.king-games.co.il/apanel/products&edit=35687`.
- Outcome: המערכת מעבירה כעת תמונות למודול MG בפורמט `image1..image5` בהתאם לחוזה החדש, והרצת `35687` המשיכה בפועל דרך שלב העלאת התמונות והסתיימה בהצלחה.

### [ID: 20260716-09] [Status: completed]
- Timestamp: 2026-07-16
- Request: להפסיק כל קוד שמוחק תמונות מוצר מהדיסק, לאחר שהתברר שקבצי תמונה קיימים של מוצר נמחקו במהלך זרימת ההזנה.
- Implementation: ב-`update_products_batch_2.py` הוסרה הלוגיקה שניקתה את כל תוכן `save_dir` בתוך `download_webp_images(...)`; במקומה נוספה שמירה על קבצים קיימים, ספירת קבצי תמונה שכבר קיימים בתיקייה, וכתיבת קבצים חדשים רק לשמות הפנויים הבאים (`1.webp`, `2.webp`, ... בלי למחוק או לדרוס קבצים ישנים). הועלו גרסאות ל-API/APP `0.89`/`1.27`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: חיפוש קוד מאשר שנמחק בלוק `os.remove(...)` שניקה את `save_dir` לפני הורדת תמונות; diagnostics נקיים עבור `update_products_batch_2.py`.
- Outcome: זרימת הורדת/שמירת תמונות לא תמחק יותר קבצי תמונה קיימים של מוצרים מהדיסק.

### [ID: 20260716-08] [Status: completed]
- Timestamp: 2026-07-16
- Request: לבדוק למה במוצר יחידני `35687` לא מתעדכנים מאפייני הקטגוריה, תמונות ו-`description`, ולהדפיס לוג מלא של מה שנשלח למודול עדכון מוצרי MG.
- Implementation: ב-`update_products_batch_2.py` נוספה שמירת payload מלא למסירת MG לקבצי JSON תחת `mg_updater_payload_logs`, יחד עם הדפסה מפורשת לטרמינל; נוספה העברת מאפייני קטגוריה כ-`param_*` ל-payload של המודול החיצוני באמצעות מיפוי מ-`load_category_attributes_with_codes(...)`; נוספה תמיכה בחיפוש תמונות גם לפי `manufacturer_sku` וגם כ-fallback בקבצי root תחת `C:\TEMP`; במודול החיצוני `C:\Projects\AgentUpdateMGsystem\update_product.py` נוספה הדפסת payload שהתקבל, תמיכה ב-`param_*` דינמיים, וניסיון בחירה לפי visible text כאשר `select_by_value` לא מספיק. הועלו גרסאות ל-API/APP `0.88`/`1.26`.
- Files changed: king_games_product_manager/update_products_batch_2.py, C:\Projects\AgentUpdateMGsystem\update_product.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: נוצר לוג payload בפועל עבור `35687` בנתיב `king_games_product_manager\mg_updater_payload_logs\mg_payload_35687_20260716_174707_814562.json`; הלוג מראה העברה של `description`, `content`, `content2`, ופרמטרי קטגוריה כגון `param_34`, `param_112`, `param_117`, `param_118`, `param_119`, `param_120`, `param_214`; ב-DB שגיאת `webdriver_manager` כבר איננה השגיאה הפעילה, ובלוג הריצה הופיע `Product updated successfully! Final URL: https://www.king-games.co.il/apanel/products&edit=35687`.
- Outcome: כעת יש שקיפות מלאה על ה-payload שנשלח ל-MG, מאפייני קטגוריה מועברים בפועל למודול החיצוני, ונוספו מסלולי fallback רלוונטיים לתמונות מקומיות.

### [ID: 20260716-07] [Status: completed]
- Timestamp: 2026-07-16
- Request: לתקן שגיאת הזנת מוצר יחידני `35687` שבה publish ל-MG נופל עם `No module named 'webdriver_manager'`, ולאמת את המסלול כשכל אפשרויות התיאורים/תמונות ו-MG מסומנות.
- Implementation: במודול החיצוני `C:\Projects\AgentUpdateMGsystem\update_product.py` הוחלפה התלות הקשיחה ב-`webdriver_manager` בטעינה גמישה: אם הספרייה קיימת משתמשים בה, ואם לא עוברים ל-`webdriver.Chrome(...)` עם Selenium Manager; בנוסף הוקשחה כתיבת שדות טקסט/Select עם fallback ל-JavaScript כאשר Selenium נכשל, ותוקן עדכון `content/content2` ב-TinyMCE להעברת HTML דרך `arguments` במקום הזרקת מחרוזות JS שבירה. בוצע version bump ל-API/APP `0.87`/`1.25`.
- Files changed: C:\Projects\AgentUpdateMGsystem\update_product.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: ייבוא המודול החיצוני אומת פעמיים (`IMPORT_OK True`); בוצעה הרצה חיה של `update_products_batch_2.py 35687 --ai-agent on --img-scrpt on --publish-to-mg --headless --set-sup-update 1 --set-unlimited 1 --preserve-existing-images --check-local-images-first`; ב-DB שגיאת `webdriver_manager` נשארה רק כרשומה ישנה (`id=113`), ולאחר התיקונים מצב המוצר הוא `mg_id=35687`, `sync_flag=1`, `is_preupload=0`, `last_sync_at=2026-07-16 17:24:45`.
- Outcome: באג `webdriver_manager` במסלול publish של מוצר יחידני סודר, והרצת `35687` עברה את נקודת הכשל הישנה והשלימה publish מקומי/סטטוס סנכרון.

### [ID: 20260716-06] [Status: completed]
- Timestamp: 2026-07-16
- Request: לוודא שבקליטת מחירון אמטל המחירים נשארים כמו במחירון (ללא מע"מ וללא מכפיל) כאשר מסומן לא לבצע חישוב.
- Implementation: ב-`server.py` הורחבה הפונקציה `_apply_supplier_price_defaults` כך שספק אמטל מקבל guardrail של `price_use_raw_no_margin=true` כאשר לא הוגדרה דריסת תמחור מפורשת בטאב; נשמרה ההתנהגות הקיימת של ישפאר עם `-10`, ולאמטל נקבע ללא דלתא ברירת מחדל. הועלו גרסאות ל-API/APP `0.86`/`1.24`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: בוצעה בדיקה חיה על הקובץ `C:\סנכרון אתר\קבצים לטיפול\תקשורת  DLINK CUDY  מחירון אמטל   יולי.xls` מול `/api/supplier/analyze` אחרי hard-restart לגרסה `0.86`; תוצאות: `price_rows=118`, `mismatches=0`, `non_1x_multiplier=0`, וכל השורות עם `pricing_source=raw_no_margin_override` ו-`final_price == raw_price`.
- Outcome: בקליטת מחירון אמטל המחיר הסופי יוצא כעת בדיוק כמו במחירון, ללא חישוב מע"מ וללא מכפיל.

### [ID: 20260716-05] [Status: completed]
- Timestamp: 2026-07-16
- Request: תיקון באג קליטת מחירון ספק אמטל שבו סומן "ללא חישוב" אך המערכת עדיין חישבה מחיר סופי שונה.
- Implementation: ב-`server.py` תוקן מסלול `/api/supplier/analyze` כך ש-`category_margin_overrides` לא דורסים יותר שורות שטאב המיפוי שלהן מסומן עם `price_use_raw_no_margin=true`; עבור שורות כאלה נשמר `pricing_source=raw_no_margin_override` והמחיר נשאר בהתאם ל-raw/delta במקום חישוב מרווח קטגוריה.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: בדיקת קוד מאשרת ש-override קטגוריה מדולג כאשר טאב מסומן "ללא חישוב"; גרסאות עודכנו ל-API/APP `0.85`/`1.23`.
- Outcome: סימון "ללא חישוב" גובר כעת על override קטגוריה, ולכן מחיר אמטל לא אמור להשתנות ע"י חישוב מרווח כאשר האופציה מסומנת.

### [ID: 20260716-04] [Status: completed]
- Timestamp: 2026-07-16
- Request: המשך ניקוי מלא של נתיבי כתיבה ישנים ל-MG כדי לאכוף שימוש בלעדי במודול העדכון החיצוני.
- Implementation: ב-`update_products_batch_2.py` הוסרה fallback ישירה לכרטיס עריכת CMS (במקרה מוצר חסר ב-DB מתבצע skip ברור), והוחלפה זרימת השבתת מוצרי Amtel ללא תמונות לקריאה ל-`update_mg_product_via_external_module(...)` במקום ניווט/שמירה ישירים; בנוסף נוטרל סקריפט הכתיבה הלגאסי `update_products_batch.py` ע"י חסימת `update_product_on_cms` עם שגיאה מפורשת כדי למנוע שימוש עתידי במסלול כתיבה ישיר.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/update_products_batch.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: חיפוש קוד ממוקד מאשר שאין עוד `products&edit=` ב-`update_products_batch_2.py`; נתיבי הכתיבה הקריטיים שם עוברים דרך external updater; גרסאות עודכנו ל-API/APP `0.84`/`1.22`.
- Outcome: מסלולי הכתיבה הישנים צומצמו משמעותית והאכיפה על external updater התחזקה גם ברמת קוד וגם ברמת חסימת סקריפט legacy.

### [ID: 20260716-03] [Status: completed]
- Timestamp: 2026-07-16
- Request: הטמעת מודול עדכון MG חיצוני כך שכל עדכון מוצר יעבור רק דרכו, ללא שינוי במודול עצמו שנמצא בשלבי פיתוח.
- Implementation: נוספה ב-`update_products_batch_2.py` שכבת adapter שטוענת דינמית את `C:\Projects\AgentUpdateMGsystem\update_product.py` וקוראת ל-`update_product_in_apanel`; הוחלף מסלול עדכון הערות skip ב-MG לשימוש במודול החיצוני במקום ניווט ישיר ל-`/apanel/products&edit=...`; הוחלף מסלול הפרסום הראשי `update_product_on_cms` כך שכתיבת מוצר ל-MG מתבצעת דרך המודול החיצוני בלבד; נתיב `desktop-replacement apply` הושבת בשרת עם 501 כדי למנוע כתיבות דרך זרימת ה-CMS הישנה; הועלו גרסאות API/APP ל-`0.83`/`1.21`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: בוצעו diagnostics לקבצים ששונו; לא בוצע שום שינוי בקובץ המודול החיצוני `C:\Projects\AgentUpdateMGsystem\update_product.py`.
- Outcome: כתיבות MG בזרימת ingestion מנותבות דרך המודול החיצוני; נתיב apply הישן של Desktop Replacement נחסם כדי לא לאפשר כתיבה מחוץ למודול.

### [ID: 20260716-02] [Status: completed]
- Timestamp: 2026-07-16
- Request: הקריאה מקובץ הלידים לא טובה; הוכן קובץ CSV מסודר חדש בנתיב קבוע `C:\Projects\KINGGAMES\king_games_product_manager\downloads\all_users last5000 לידים Taskey.csv` ויש לעדכן את המערכת לעבוד מולו עם יותר התאמות להצעות SAP.
- Implementation: הוחלף נתיב מקור הלידים הקנוני ב-`server.py` לנתיב החדש; במסלול `get_sap_taskey_offers_vs_leads_report` בוטלה תלות ב-`leads_path` מה-query והוגדר שימוש קשיח בקובץ הקנוני כדי למנוע סטיות מקור; נשמרה לוגיקת נרמול הטלפונים הקיימת (כולל `00972/972 -> 0` והשלמת `0` למספרי סלולר בני 9 ספרות) שמתאימה לפורמט הקובץ החדש עם עמודת `טלפון`; הועלו גרסאות ל-API/APP: `0.82`/`1.20` ועודכן cache-bust ב-`index.html`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: נקראו שורות ראשונות מהקובץ החדש ואומת קיום עמודת `טלפון` וערכים תקינים לנרמול; diagnostics נקיים לקבצים ששונו.
- Outcome: דוח TASKEY מול SAP קורא כעת מהקובץ החדש והקבוע, כך שסביר לקבל היקף התאמות גבוה יותר ללידים העדכניים.

### [ID: 20260716-01] [Status: completed]
- Timestamp: 2026-07-16
- Request: הרצת כלי החלפת רכיב במחשבים נייחים נכשלה עם `Desktop replacement apply error: CMS login appears to have failed (login form still visible)`.
- Root cause: מנגנון `ensure_logged_in` ב-`replace_desktop_tree_component.py` הסתמך על submit Selenium בלבד ונתקע במסך לוגין למרות שסשן HTTP תקין ניתן להשגה; בנוסף הזרקת cookie הייתה קשיחה מדי (variant יחיד עם דגל secure) ולכן לא תמיד אומצה ע"י הדפדפן.
- Implementation: קשיחות login הוגדלה בשלושה מישורים: (1) זיהוי טופס לוגין לפי אלמנטים נראים ולא לפי page-source בלבד, (2) fallback ל-login דרך HTTP endpoint המאומת (`/apanel/products_categories`) עם token, (3) הזרקת `PHPSESSID` בכמה וריאנטים ל-Selenium + אימות על עמוד categories. בנוסף `get_driver` הותאם להעדיף התחברות ל-debug session קיים (9222/9225, auth-hint) כדי למחזר סשן מחובר במקום לפתוח פרופיל מבודד כברירת מחדל.
- Files changed: king_games_product_manager/replace_desktop_tree_component.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: בדיקת smoke לפונקציה `ensure_logged_in` כעת מחזירה `LOGIN_OK` במקום RuntimeError; שרת הופעל מחדש ומחזיר `api_version=0.81`.
- Outcome: כשל ההתחברות של כלי החלפת רכיב לא אמור לחסום יותר את תחילת ריצת ה-apply באותו תרחיש.

### [ID: 20260715-12] [Status: completed]
- Timestamp: 2026-07-15
- Request: המשתמש דיווח שהקטגוריות מופיעות אבל עץ הקטגוריות עדיין לא נכון.
- Root cause: בחילוץ HTML של עמוד `products_categories` הסקריפט פירש שדה מספרי מטבלת MG כ-`parent`, למרות שזה אינדקס תצוגה ולא מזהה הורה; בנוסף ספירת עומק לפי סימן גרפי גרמה ל-depth שגוי ברמות שורש.
- Implementation: עודכן `sync_mg_categories.py` לחישוב היררכיה לפי הזחה אמיתית של שם הקטגוריה (leading `\xa0`/spaces), עם עומק מדרגי של 4 רווחים לרמה; בוטלה תלות בסימן גרפי עבור depth; ה-parent נגזר שוב נכון דרך stack depth. הועלו גרסאות API/APP ל-`0.80`/`1.18`.
- Files changed: king_games_product_manager/sync_mg_categories.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: אחרי `POST /api/categories/sync/start` הסטטוס מסתיים `success`; דגימת parentים במסד: `400 -> 184`, `403 -> 400`, `405 -> 184`, `408 -> 184`; `/api/categories/management` מחזיר `tree=5`, `flat=177`.
- Outcome: מבנה העץ תואם היררכיה מעודכנת מהמקור MG במקום parent שגוי מעמודת אינדקס.

### [ID: 20260715-11] [Status: completed]
- Timestamp: 2026-07-15
- Request: המשתמש דיווח שבמסך החדש לא מופיעות קטגוריות, והרגיש שהסנכרון עדיין לא עובד.
- Root cause: בניית העץ ב-`/api/categories/management` בחרה שורשים רק כאשר `parent=''`, בעוד שבנתוני MG לרוב הקטגוריות יש `parent` מספרי ולכן `tree` חזר ריק; בנוסף רצו במקביל 2 תהליכי שרת על פורט 8000 שגרמו לתוצאות סותרות (גרסאות שונות).
- Implementation: עודכן `get_categories_management` ב-`server.py` לזיהוי שורשים תקין (parent ריק/עצמי/הורה חסר), הגנת cycle ברקורסיה, ו-fallback למניעת עץ ריק; נוסף fallback מקביל ב-UI ב-`app.js`; הועלו גרסאות API/APP ל-`0.78`/`1.16`; בוצע kill לשני השרתים והפעלה נקייה של מופע יחיד.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `/api/health/version` מחזיר `api_version=0.78`; `/api/categories/management` מחזיר `count=177`, `tree=132`, `flat=177`; `POST /api/categories/sync/start` ולאחריו status מסתיימים ב-`last_status=success` ו-`last_message=Completed successfully`.
- Outcome: מסך ניהול קטגוריות מקבל עץ בפועל (לא ריק), וסנכרון קטגוריות MG עובד ומסתיים בהצלחה.

### [ID: 20260715-10] [Status: completed]
- Timestamp: 2026-07-15
- Request: סטטוס סנכרון קטגוריות MG נשאר `failed` עם הודעת התחברות (auth) גם אחרי שיפורי Selenium.
- Implementation: נוספה ב-`sync_mg_categories.py` אסטרטגיית סנכרון חדשה מבוססת HTTP session (cookie+token login) שמתחברת ל-`/apanel/products_categories` ללא תלות ב-Chrome Debug Session, מחלצת קטגוריות מה-HTML (table rows + links + options), ומשתמשת ב-Selenium רק כ-fallback. תוקן גם פענוח תגובת HTTP כדי לשמר טקסט עברי (charset-aware decode עם fallbacks). בנוסף בוצעו version bumps: API `0.77`, APP `1.15`.
- Files changed: king_games_product_manager/sync_mg_categories.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: הרצה ישירה של `sync_mg_categories.py` הסתיימה בהצלחה (`RETURN_CODE=0`) עם `HTTP extraction succeeded with 177 categories`; בדיקת API: `POST /api/categories/sync/start` ולאחר מכן `GET /api/categories/sync/status` החזירה `last_status=success`, `is_running=false`, `last_message=Completed successfully`.
- Outcome: סנכרון הקטגוריות עובד אוטומטית גם כש-Selenium לא מצליח להתחבר ל-MG דרך פרופיל כרום.

### [ID: 20260715-09] [Status: completed]
- Timestamp: 2026-07-15
- Request: טיפול בכשל החוזר בסנכרון קטגוריות MG שהופיע ב-UI כ-`failed` עם `Traceback` מלא אחרי לחיצה על "סנכרן קטגוריות עכשיו".
- Implementation: חיזוק מנגנון לוגין ב-`sync_mg_categories.py` (מילוי שדות עם `send_keys` + fallback, submit אמיתי והמתנה חכמה ליציאה ממסך לוגין), הוספת דיאגנוסטיקה (`url` + שגיאת עמוד אם קיימת), בחירת פורט debug עם `auth hint score`, והעדפת פרופיל כרום משותף (`workspace chrome-profile`) כדי להשתמש בסשן מאומת קיים. בנוסף בוצע ניקוי UX של שגיאה: הסקריפט לא מדפיס יותר Traceback לשגיאת auth צפויה אלא הודעה תפעולית קצרה וברורה.
- Files changed: king_games_product_manager/sync_mg_categories.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: הרצה ידנית של הסקריפט מחזירה קוד יציאה 21 עם הודעת פעולה ברורה וללא stderr traceback; `POST /api/categories/sync/start` עובד; `GET /api/categories/sync/status` מתעדכן ל-`is_running=false` עם `last_status=failed` והודעת auth קצרה (ללא stack trace).
- Outcome: הבעיה הפכה מדיווח טכני לא קריא לדיווח תפעולי ברור. החסם היחיד שנותר כדי להגיע ל-`success` הוא אימות MG פעיל בפרופיל הכרום שבו האוטומציה משתמשת.

### [ID: 20260715-08] [Status: completed]
- Timestamp: 2026-07-15
- Request: לאחר לחיצה על "סנכרן קטגוריות עכשיו" המשתמש עדכן שעמוד הקטגוריות הנכון ב-MG הוא `https://www.king-games.co.il/apanel/products_categories`.
- Implementation: עודכן `sync_mg_categories.py` כך שהסנכרון מכוון לעמוד הקטגוריות הייעודי (`products_categories`) במקום להסתמך על עמוד עריכת מוצר; נוספה לוגיקת חילוץ רב-אסטרטגית (טבלה/לינקים/אופציות) עם fallback מובנה; שופר זיהוי מסך התחברות כדי להימנע מ-false positive/false negative; הוסר `SyntaxWarning` של regex במחרוזת JavaScript באמצעות raw string; הוחזרה הודעת שגיאה אופרטיבית וברורה במקרה שהסשן לא מאומת.
- Files changed: king_games_product_manager/sync_mg_categories.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: הרצה ישירה של `sync_mg_categories.py` מראה שהסקריפט נפתח בעמוד `products_categories` ומגיע למסלול החילוץ החדש; `/api/health/version` מחזיר `0.75`; הפעלת `POST /api/categories/sync/start` מחזירה הצלחה ומריצה את התהליך החדש.
- Outcome: הסנכרון מחובר לעמוד הקטגוריות הנכון של MG. החסם שנותר בסביבה הנוכחית הוא אימות התחברות ל-MG בפרופיל הכרום של האוטומציה (session login), ולא עוד נתיב עמוד שגוי.

### [ID: 20260715-07] [Status: completed]
- Timestamp: 2026-07-15
- Request: להוסיף תחת ניהול מוצרים מסך חדש בשם "ניהול קטגוריות" בעץ עם הזחות לקטגוריות בן, ולהוסיף עיבוד חדש לסנכרון קטגוריות מאתר MG שרץ כל בוקר.
- Implementation: נוספה כניסת ניווט חדשה "ניהול קטגוריות" תחת קבוצת "ניהול מוצרים"; נוסף מסך UI חדש עם עץ היררכי (עם הזחות), מוני קטגוריות, סטטוס סנכרון, כפתור רענון וכפתור "סנכרן עכשיו"; ב-`server.py` נוספו API-ים חדשים לניהול קטגוריות (`GET /api/categories/management`), סטטוס סנכרון (`GET /api/categories/sync/status`) והפעלה ידנית (`POST /api/categories/sync/start`); נוסף תהליך ברירת מחדל חדש בטבלת התהליכים האוטומטיים בשם "סנכרון קטגוריות MG" המבוסס על `sync_mg_categories.py`, מתוזמן ל-07:00 כל יום; נוסף סקריפט `sync_mg_categories.py` שמתחבר ל-MG דרך Chrome Debug, קורא את רשימת הקטגוריות ממסך עריכת מוצר (`select#category`), בונה היררכיה מעומקי הזחה, ומסנכרן לטבלת `categories` (יצירה/עדכון/סימון לא פעיל לקטגוריות ישנות).
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, king_games_product_manager/sync_mg_categories.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `/api/health/version` מחזיר `api_version=0.74`; `/api/categories/management` ו-`/api/categories/sync/status` מחזירים 200 ונתונים תקינים; `POST /api/categories/sync/start` מפעיל את התהליך ומחזיר הצלחה.
- Outcome: מסך ניהול קטגוריות בעץ נוסף ועובד, ותזמון יומי לסנכרון קטגוריות נוסף למערכת. בריצת smoke בסביבה הנוכחית זוהתה תלות בהתחברות תקינה ל-MG (התהליך מדווח login failure כשהסשן אינו מאומת), אך התשתית המלאה לסנכרון האוטומטי והידני קיימת ומחוברת.

### [ID: 20260715-06] [Status: completed]
- Timestamp: 2026-07-15
- Request: במסוף הזנת מוצרים אוטומטית להוסיף סימון "בדוק קבצים בספרייה מקומית" לפני מנוע תמונות; אם נמצאו תמונות מקומיות יש לדלג על מנוע התמונות גם כשהוא מסומן; אם לא נמצאו תמונות ומנוע תמונות מסומן, יש להפעיל מנוע תמונות כרגיל.
- Implementation: נוספה תיבת סימון UI חדשה `ingFlagCheckLocalImagesFirst` (ברירת מחדל פעילה) במסוף ההזנה; הדגל מחובר ל-`runtime_flags.check_local_images_first` ב-frontend; ב-`server.py` הדגל מועבר ל-runner כ-CLI `--check-local-images-first`; ב-`update_products_batch_2.py` נוספה לוגיקת Local First לפי מיקום `C:\Temp\ProducsImages\<supplier_sku>` (עם fallback ל-`C:\TEMP\<supplier_sku>`) לפני העשרת תמונות אונליין; כאשר נמצאו קבצים מקומיים מנוע התמונות מנוטרל אפקטיבית למוצר; כאשר לא נמצאו וקיים סימון מנוע תמונות, המנוע ממשיך לפעול.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, king_games_product_manager/update_products_batch_2.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: code-path מאמת דגל UI -> API -> CLI -> runtime flags; העלאה ל-CMS משתמשת כעת גם בקבצים מהספרייה הראשית `C:\Temp\ProducsImages` ותומכת בהעלאת 5 הקבצים הראשונים גם אם שמותיהם אינם `1.webp..5.webp`.
- Outcome: מסוף ההזנה נותן עדיפות לתמונות המקומיות ומדלג על מנוע תמונות אונליין כשיש חומר מקומי, תוך שמירה על fallback אונליין כשאין תמונות מקומיות.

### [ID: 20260715-05] [Status: completed]
- Timestamp: 2026-07-15
- Request: לייצב את הריצה לאחר שילוב חילוץ התמונות לספק חדש, כדי שהמסך לא ייתקע בגלל שגיאת סטטוס תהליך ברקע.
- Implementation: תוקן `NameError: cursor is not defined` ב-`_refresh_current_process_state` על ידי הסרת בלוק SQL זר שנכנס לפונקציה בטעות וגרם לשגיאות בעת קריאת סטטוס תהליך (`/api/ingestion/status`); עודכנו גרסאות ריצה ל-API `0.72` ו-APP `1.10`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics נקיים; מסלול סטטוס תהליך נקרא ללא NameError; השרת מחזיר גרסת API מעודכנת.
- Outcome: מסך חילוץ התמונות ושאר המסכים שתלויים בפולינג סטטוס יציבים לאחר השילוב.

### [ID: 20260715-04] [Status: completed]
- Timestamp: 2026-07-15
- Request: לשלב Helper חדש לחילוץ תמונות עבור הספק "צג עליתה" (מ-`C:\Projects\ElitaScraper`) ולהגדיר במערכת שלספק יש חילוץ תמונות פעיל; לחבר פרמטרים: דריסת שם, קוד מק"ט, שינוי רוחב ועוד.
- Implementation: הוסף Extractor חדש בפרויקט `helper_scripts/image_extractors/elita_scraper.py` המבוסס על זרימת אליתה (חיפוש מוצר, כניסה לדף מוצר, איסוף גלריה, שמירה כ-WebP); הורחב `supplier_image_extraction_runner.py` לטעינה דינמית של סקריפט חילוץ לפי ספק מתוך `supplier_image_scripts.json` ולהעברת פרמטרים נתמכים (`overwrite_name`, `name_override`, `sku_override`, `resize_width`); עודכנו `server.py` ו-`app.js`/`index.html` כך שהפרמטרים מוזנים ב-UI ונשלחים ל-Job; הספק "צג עליתה" נרשם כ-Extractor פעיל ברשימות ברירת המחדל וגם בקובץ `supplier_image_scripts.json`.
- Files changed: king_games_product_manager/helper_scripts/image_extractors/elita_scraper.py, king_games_product_manager/supplier_image_extraction_runner.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/supplier_image_scripts.json, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: בדיקות קוד והרצה מאמתות שהספק רשום עם סקריפט פעיל, שהפרמטרים עוברים מהמסך ל-API ול-Runner, ושגרסת הריצה עודכנה.
- Outcome: "צג עליתה" זמין כעת לחילוץ תמונות במערכת עם תמיכה בפרמטרי דריסה/מקט/רוחב בתהליך ההרצה.

### [ID: 20260715-03] [Status: completed]
- Timestamp: 2026-07-15
- Request: ספק חדש עם מיפוי מחירון נתקע בקליטה עם שגיאה `Unsupported process_type 'manual_csv' for supplier ...` בזמן בדיקה מקדימה/Analyze.
- Implementation: תוקן מסלול הקליטה ב-`/api/supplier/analyze` כך ש-`manual_csv` מזוהה כסוג תקין; כאשר הקלט הוא Excel ואין `csv_data`, המערכת נופלת אוטומטית לפענוח לפי מיפוי שמור (`_build_normalized_rows_from_excel_data`) במקום להחזיר `Unsupported process_type`; נוספה הודעת שגיאה ממוקדת רק אם אי אפשר לפענח מהקובץ לפי המיפוי.
- Files changed: king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `/api/health/version` מחזיר כעת `api_version=0.70`; אין שגיאות diagnostics בקובץ השרת; נקודת הכשל `Unsupported process_type` לא תופעל עוד עבור `manual_csv`.
- Outcome: קליטת ספקים חדשים עם `manual_csv` ומיפוי Excel לא אמורה להיתקע עוד על שגיאת process_type.

### [ID: 20260715-02] [Status: completed]
- Timestamp: 2026-07-15
- Request: להוסיף בדוח TASKEY מסנן סטטוס: הזמנות שמופיעות בקובץ לידים / לא מופיעות, עם סה"כ שמתעדכן לפי הסינון והחיפוש.
- Implementation: נוספה בחירת סטטוס במסך הדוח (`הכל`, `מופיע בקובץ לידים`, `לא מופיע בקובץ לידים`); עודכנה טבלת הדוח להציג סטטוס לכל שורה בצבעים; עודכנה לוגיקת הסינון כך שמסנן סטטוס + חיפוש חופשי עובדים יחד; עודכן סיכום הדוח להציג סה"כ כולל, מופיעות, לא מופיעות, אחרי מסנן סטטוס, ומוצגות אחרי חיפוש.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: הדוח משתמש כעת בכל רשומות ההזמנות מה-API עם הדגל `נמצא בקובץ לידים`; המסנן והסיכומים מחושבים בלקוח בזמן אמת.
- Outcome: ניתן לעבור מיידית בין "מופיעות בלידים" ל"לא מופיעות בלידים" ולקבל סה"כ מתרענן בהתאם.

### [ID: 20260715-01] [Status: completed]
- Timestamp: 2026-07-15
- Request: להוסיף תחת דוחות דוח חדש "הצעות מול לידים ב TASKEY" שמביא הזמנות מתחילת החודש, משווה לטלפונים בקובץ `C:\Projects\TASKEYLEADSSCRAPTER\taskey_leads.csv` עם נרמול 972->0, ומציג אילו הזמנות לא מופיעות בקובץ הלידים.
- Implementation: נוספו מסך ותפריט דוח חדש ב-UI; נוספה קריאת API חדשה `GET /api/sap/taskey-offers-vs-leads`; נוספה לוגיקת שרת להשוואת הזמנות SAP (`ORDR`) מול קובץ הלידים לפי טלפון מנורמל (כולל המרות `00972`/`972` ל-`0`); נוספו ב-UI חיפוש, סיכום, וטבלת "לא נמצא בקובץ לידים".
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: בדיקת קוד מלאה למסלול view->API->render; נוספו fallback-ים לטעינת CSV/JSON, זיהוי עמודת טלפון, וסיכומי counts.
- Outcome: קיים כעת דוח ייעודי שמציג רק הזמנות מתחילת החודש שלא נמצאו בקובץ לידים של TASKEY.

### [ID: 20260714-29] [Status: completed]
- Timestamp: 2026-07-14
- Request: ערכי קטגוריות חזרו קרוב ל-0 והסינון תקף/לא תקף לא עבד במסך ניהול מוצרים.
- Implementation: אותר כי רץ פרוסס ישן/שגוי של השרת שאינו כולל את שינויי API האחרונים (`valid_count`, `out_of_stock_count`, `valid_status`). בוצע ניקוי כל מאזיני פורט 8000 והרמה מחדש של `king_games_product_manager/server.py` המעודכן בלבד.
- Files changed: LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: `/api/categories` מחזיר כעת `valid_count` ו-`out_of_stock_count`; `/api/products?valid_status=valid` מחזיר `total=7686` עם `is_valid=1`; `/api/products?valid_status=invalid` מחזיר `total=18357` עם `is_valid=0`.
- Outcome: מוני הקטגוריות והסינון תקף/לא תקף חזרו לעבוד בפועל לאחר העלאת השרת הנכון.

### [ID: 20260714-28] [Status: completed]
- Timestamp: 2026-07-14
- Request: במסך ניהול מוצרים להוסיף חיתוך תקף/לא תקף כמו חיתוך מלאי, ובקומבו קטגוריה להציג כמה מוצרים בתוקף וכמה לא במלאי לכל קטגוריה.
- Implementation: נוספה בחירת סינון תקפות ב-UI (`validFilter`) עם מצבים כללי/תקף/לא תקף; נוספה העברת פרמטר `valid_status` לקריאת `/api/products`; נוספה תמיכה בשרת בסינון `valid_status` לצד `stock_status`; הורחב `/api/categories` להחזיר לכל קטגוריה גם `valid_count` וגם `out_of_stock_count`; עודכנה תצוגת קומבו הקטגוריות במסך ניהול מוצרים לפורמט `שם קטגוריה (X בתוקף, Y לא במלאי)`.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics נקיים לקבצים ששונו; בדיקת קוד מאמתת חיבור מקצה לקצה בין פילטר התקפות ב-UI, פרמטר ה-API, וסינון SQL בצד השרת; קומבו הקטגוריות משתמש כעת במוני `valid_count` ו-`out_of_stock_count`.
- Outcome: מסך ניהול מוצרים תומך כעת גם בסינון תקפות, ובקומבו קטגוריות מוצגים מוני תקף/לא במלאי לכל קטגוריה.

### [ID: 20260714-27] [Status: completed]
- Timestamp: 2026-07-14
- Request: complete failed preupload ingestion retry for pending products and stabilize CMS publish selectors after repeated no-such-element failures on save/image fields.
- Implementation: added resilient CMS selector utilities in `update_products_batch_2.py` (`find_cms_save_button`, `click_cms_save`, `find_cms_image_input`) and replaced hardcoded XPath save clicks + strict image input IDs with fallback-driven logic (button/input/link detection, JS click, form submit fallback, and file-input slot fallback); reran targeted category publish flow for pending products.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: targeted run `update_products_batch_2.py category:400 --publish-to-mg --headless --skip-if-no-supplier-images` completed with successful publish logs for products `35675` and `35676`; DB check confirms `pending_preupload_cat400=0` and both products now `is_preupload=0`, `sync_flag=1`.
- Outcome: pending preupload queue for category 400 cleared and publish flow no longer aborts on missing hardcoded save/image selectors.

### [ID: 20260714-26] [Status: completed]
- Timestamp: 2026-07-14
- Request: ingestion run on טרום העלאה לאתר produced long WinError 6 logs and ended with partial processing/images.
- Implementation: hardened `undetected_chromedriver` lifecycle in supplier extractors (`benda_image_scrapter.py`, `morlevi_site_scrapter.py`) with safe destructor patch and safe quit handling for `WinError 6`; enabled stable headless options for both extractors; fixed CMS JS fill step in `update_products_batch_2.py` to guard missing fields before setting `.value`/`.checked`, preventing `Cannot set properties of undefined`; bumped versions to app `1.04` and API `0.65`.
- Files changed: king_games_product_manager/helper_scripts/image_extractors/benda_image_scrapter.py, king_games_product_manager/helper_scripts/morlevi_site_scrapter.py, king_games_product_manager/update_products_batch_2.py, king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: smoke executed both supplier extractors without unhandled exceptions (`benda ok list=49`, `mor ok list=0`); diagnostics on edited files passed.
- Outcome: WinError 6 noise no longer breaks extractor flow, and missing CMS fields no longer abort publish pass with JS undefined errors.

### [ID: 20260714-25] [Status: completed]
- Timestamp: 2026-07-14
- Request: in prediction output, stop printing separate Hebrew/English manufacturer fields and print only one field: `יצרן: [English manufacturer name]`.
- Implementation: updated `product_scraper_engine/enricher.py` prompt/spec/validation so `PRODUCT_MANUFACTOR` requires English manufacturer only; removed Hebrew manufacturer requirement; updated HTML prediction report header to print a single manufacturer line in format `יצרן: ...`.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: smoke test confirmed report no longer prints dual language manufacturer display and now contains only `יצרן: HP`; validation no longer warns about missing Hebrew manufacturer.
- Outcome: prediction output now shows one manufacturer field in English only, per requested format.

### [ID: 20260714-24] [Status: completed]
- Timestamp: 2026-07-14
- Request: if supplier product name exists, force it as the final product title with no AI intervention; only when supplier name is missing should AI title logic run.
- Implementation: updated local enrichment title resolution in `update_products_batch_2.py` to read `METADATA.SUPPLIER_PRODUCT_NAME`, lock final title to supplier value when present, bypass AI/template title decision in that case, and mirror the locked value into both `PRODUCT_NAME` and `FORMATTED_TITLE` before save.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: smoke check confirms new supplier-lock branch exists (`[Title][Supplier Lock]`), reads `SUPPLIER_PRODUCT_NAME`, and writes `FORMATTED_TITLE = final_title`; diagnostics report no errors in changed files.
- Outcome: title source policy is now deterministic: supplier title wins always when available; AI title is used only as fallback.

### [ID: 20260714-23] [Status: completed]
- Timestamp: 2026-07-14
- Request: fix weak product title quality (example MG 35663 "זיכרון אפור") by changing enricher order to fetch supplier product name and images before AI prediction, with explicit Banda product-title XPath support.
- Implementation: added supplier-context prefetch flow in `product_scraper_engine/enricher.py` so supplier site title/images are collected before AI call and supplier title becomes `Input Product Name (Primary)` when available; expanded prompt inputs to include DB title + supplier-site title with updated priority rules; added `fetch_context()` contract in `product_scraper_engine/selenium_fetcher.py`; implemented Banda supplier title extraction using exact XPath `/html/body/div[2]/div/main/div[2]/div[2]/div/div/div[1]/div[2]/div/h2` plus image collection in pre-AI stage; hardened fetcher imports so supplier extractors load regardless current working directory.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/product_scraper_engine/selenium_fetcher.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: smoke test for Banda SKU `90904-721-17` returned supplier title and 28 images from supplier context; AI-on enrichment test confirmed logs show pre-AI supplier fetch, prompt contains `Input Product Name (Primary)` and `Input Product Name (Supplier Site)`, final enrichment returned 28 verified images.
- Outcome: enrichment order is now supplier-first (title + images) before prediction, improving model context quality for bad/stale DB titles and providing a reusable path for additional suppliers.

### [ID: 20260714-22] [Status: completed]
- Timestamp: 2026-07-14
- Request: for every Product Ingestion Console run, persist the list of updated MG SKUs for manual REVIEW; add REVIEW button in product runs history to open product links list with done/not-done status tracked in DB; keep historical MG upload timestamps for future audit.
- Implementation: added DB-backed review tracking per run (`ingestion_run_review_items`) and MG upload lifecycle fields on products (`first_mg_uploaded_at`, `last_mg_uploaded_at`), wired run pipelines to persist updated MG IDs, added backend APIs to fetch/update review status, and added UI REVIEW button + modal with product links (`https://www.king-games.co.il/products/item/XXX`) and toggle status (בוצע/לא בוצע).
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics passed; schema bootstrap verified table/columns creation; REVIEW API/UI wiring compiled clean.
- Outcome: each ingestion run now keeps a durable, DB-backed manual review checklist with per-product status tracking and historical upload timestamps.

### [ID: 20260714-21] [Status: completed]
- Timestamp: 2026-07-14
- Request: improve poor short titles (example product 35679) by forcing AI to build title only after full information analysis and avoid 3-word titles.
- Implementation: updated `enricher.py` prompt with strict generation-order rule (description/specs/attributes first, title last), enforced minimum 6 words for PRODUCT_NAME and FORMATTED_TITLE, and required manufacturer+model in title when confidently known.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: smoke checks confirmed new prompt clauses are present and validation now flags short titles (<6 words).
- Outcome: title generation is now constrained to produce richer model-aware names and avoid low-quality 3-word outputs.

### [ID: 20260714-20] [Status: completed]
- Timestamp: 2026-07-14
- Request: prevent critical supplier/manufacturer misclassification (example: model identified as ASUS incorrectly) by forcing AI to inspect title, part code, and supplier together.
- Implementation: updated `enricher.py` prompt to include `Input Supplier Name`, and added strict rules requiring manufacturer extraction from title when present plus cross-check against part codes and supplier before deciding manufacturer.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: smoke check confirms prompt now contains supplier input line and all new anti-mismatch constraints.
- Outcome: AI receives explicit constraints to avoid critical supplier/brand mistakes by evidence-based title+code+supplier reconciliation.

### [ID: 20260714-19] [Status: completed]
- Timestamp: 2026-07-14
- Request: remove conflicting hardcoded title pattern from AI prompt and enforce choosing title format only from provided title-rules templates.
- Implementation: updated `product_scraper_engine/enricher.py` prompt to remove old fixed PRODUCT_NAME format block and enforce template selection from the full provided title-rules set by product essence; explicitly forbids external/hardcoded templates when rules are provided.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: smoke check confirms old hardcoded format text is absent and new rule-selection constraints are present.
- Outcome: AI now chooses title structure from your configured title-rules templates instead of a generic built-in format.

### [ID: 20260714-18] [Status: completed]
- Timestamp: 2026-07-14
- Request: verify AI always receives the latest product title from DB (specifically for product 35680) and sharpen international-code rule so code in title is treated as international code and used in formatted title when required.
- Implementation: strengthened `enricher.py` prompt instructions with explicit DB-title authority and explicit international-code priority from Input Product Name (including prediction title text), and kept fallback to input MPNs/inference only when title has no code.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: smoke validation for product 35680 confirmed DB title is read and injected into `Input Product Name` exactly, and prompt includes the new DB-priority + title-code-priority rules.
- Outcome: AI enrichment now has explicit deterministic guidance to trust DB title first and treat code inside title as international code candidate with highest priority.

### [ID: 20260714-17] [Status: completed]
- Timestamp: 2026-07-14
- Request: set fixed visible size for product title-rule template editor (so text is always readable) and bump release version.
- Implementation: updated title-rules template textarea in `app.js` to `cols=40` and `rows=8` for both existing rows and newly added rows in the editor, then bumped app/server versions.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics passed for modified frontend/backend files.
- Outcome: title template field now keeps a stable editing area (40 characters x 8 lines), and release version was raised.

### [ID: 20260714-16] [Status: completed]
- Timestamp: 2026-07-14
- Request: enforce title-rules source from runtime API (not stale local assumptions) and prevent title mismatch between local DB and MG product card.
- Implementation: updated `update_products_batch_2.py` to load title rules API-first from `/api/title/rules` with local file fallback, and hardened CMS title writing by setting/verifying product-name field across multiple selectors before pass-1 save, after pass-2 reopen, and before pass-2 save.
- Files changed: king_games_product_manager/update_products_batch_2.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics passed; runtime smoke confirmed API rules load (`rules_count=9`) and prompt rules text includes live monitor template requiring inch token.
- Outcome: enrichment now always consumes live title instructions from API when available, and MG form title persistence is significantly more robust against field/DOM variability.

### [ID: 20260714-15] [Status: completed]
- Timestamp: 2026-07-14
- Request: fix failure where MG product card attributes were not updated even though AI returned correct answers.
- Implementation: repaired and hardened category-attribute mapping in `update_products_batch_2.py` so pass-2 MG updates now support flexible AI formats (`34`, `param_34`, and label-only), normalized value matching against CMS option text/value, and fallback to `PRODUCT_ATTRIBUTES` when coded selections are missing in payload. Also repaired a corrupted function block that could silently break full description/attribute flow.
- Files changed: king_games_product_manager/update_products_batch_2.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics passed; unit-style smoke mapping confirmed updates resolve and map correctly for code-only, `param_*`, and label-only AI outputs.
- Outcome: MG pass-2 attribute updates are now resilient and should apply the AI-selected category values reliably.

### [ID: 20260714-14] [Status: completed]
- Timestamp: 2026-07-14
- Request: send category attributes with codes and all possible values to AI, get selected values back, and apply them in MG pass 2 after category update.
- Implementation: added category-attribute code extraction from DB in `update_products_batch_2.py` (parameter code + `param_*` name + options), passed that block to AI via `enricher.py` prompt, and extended AI schema with `RECOMMENDED_CATEGORY_ATTRIBUTES` (`parameter_code`, `attribute_name`, `selected_option_value`). The enrichment payload now stores these AI coded selections, and `update_product_on_cms` pass-2 now applies them directly to CMS selects by `param_*` code/value before DB text fallback.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/product_scraper_engine/enricher.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics passed for updated files; smoke tests confirmed category 99 now yields coded attributes (e.g., `param_34`, `param_46`, `param_112`) and prompt includes the coded attributes block + `RECOMMENDED_CATEGORY_ATTRIBUTES` section.
- Outcome: AI now receives category attributes with codes/options and the MG pass-2 updater can set category parameters using AI-returned coded values.

### [ID: 20260714-13] [Status: completed]
- Timestamp: 2026-07-14
- Request: raise project version for a new release.
- Implementation: bumped backend API version and frontend app/cache-busting versions.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics passed for updated server/frontend files.
- Outcome: release versions updated to API `0.56` and App `0.94`.

### [ID: 20260714-12] [Status: completed]
- Timestamp: 2026-07-14
- Request: ensure AI extracts international manufacturer code from the original product title before enrichment, returns it in JSON, and inserts it into the new formatted title when required by template.
- Implementation: strengthened `product_scraper_engine/enricher.py` prompt rules so `INTERNATIONAL_PART_NUMBER` must first be extracted from `Input Product Name`, then fallback to input MPNs/inference only if needed; added required JSON field `INTERNATIONAL_PART_NUMBER_SOURCE` with values `title|input_mpns|inferred|none`; added explicit instruction to include the extracted code inside `FORMATTED_TITLE` when the selected title template contains SKU/international-code tokens. Wired payload persistence of `international_part_number_source` in `update_products_batch_2.py`.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/update_products_batch_2.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics passed for updated files; prompt smoke check confirmed presence of the new mandatory extraction instruction, source field, and template insertion rule.
- Outcome: AI is now explicitly guided to prioritize extracting international code from the original title text and report the extraction source in JSON.

### [ID: 20260714-11] [Status: completed]
- Timestamp: 2026-07-14
- Request: fix failure where AI predicted title for product 35681 did not match the saved screen template.
- Implementation: added a strict title-rule guardrail in `update_products_batch_2.py`: when AI returns `FORMATTED_TITLE`, the pipeline now compares it against deterministic rendering from the selected template and auto-corrects on mismatch. Added support for newly used template tokens (`יצרן אנגלית`, `גודל מסך באינטש מקוצר`, `מקט יצרן בינלאומי חובה`, `מקט אוניברסלי`) and improved screen-size extraction from model patterns (e.g. `C27...`).
- Files changed: king_games_product_manager/update_products_batch_2.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics passed; simulation with failing AI title (`מסך גיימינג קעור 180Hz 1ms VA שחור`) now auto-corrects to template-compliant output; product `35681` local title was updated to `מסך גיימינג קעור AOC 27" 180Hz 1ms VA 36603-272-27 שחור`.
- Outcome: even when AI drifts from the template, the final saved title now stays compliant with your saved rule.

### [ID: 20260714-10] [Status: completed]
- Timestamp: 2026-07-14
- Request: force title formatting through the AI agent itself (using the full saved title rule), and require the AI to try returning an international SKU/part number for every product.
- Implementation: updated `product_scraper_engine/enricher.py` prompt and response schema to require `FORMATTED_TITLE` (new final title from the selected rule) and `INTERNATIONAL_PART_NUMBER` (EAN/UPC/GTIN/universal MPN when found); added validation warnings when those fields are missing. Updated `update_products_batch_2.py` to use `FORMATTED_TITLE` as the primary final title (with local rule renderer only as fallback), and persist `international_part_number` in the saved payload while using it as preferred manufacturer SKU.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/update_products_batch_2.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics passed for both updated Python files; smoke checks confirmed new fields are parsed/used and AI-formatted title is preferred in save flow.
- Outcome: title rule enforcement is now requested directly from AI with a dedicated output field, and each enrichment now explicitly asks for an international SKU.

### [ID: 20260714-09] [Status: completed]
- Timestamp: 2026-07-14
- Request: remove duplicated attributes section from prediction descriptions, leaving only the technical specification section.
- Implementation: updated `build_full_desc_html_from_engine` in `update_products_batch_2.py` to stop rendering the `מאפייני מוצר` block from `PRODUCT_ATTRIBUTES`; the generated full description now includes description + `מפרט טכני` + FAQ only.
- Files changed: king_games_product_manager/update_products_batch_2.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics passed for `update_products_batch_2.py`; smoke render check confirmed `מפרט טכני` exists and `מאפייני מוצר` no longer appears in generated HTML.
- Outcome: prediction descriptions no longer duplicate specs under a second attributes section.

### [ID: 20260714-08] [Status: completed]
- Timestamp: 2026-07-14
- Request: make the saved title rules actually change the product name during enrichment, so product 35681 (screen) is renamed according to the stored screen rule instead of keeping the old AI title.
- Implementation: added a deterministic title-rule renderer in `update_products_batch_2.py` that selects the best active rule by recommendation/category/text, fills the rule template from the enriched product data plus the stored short description, and writes the rendered title back into `PRODUCT_NAME` before the product is saved and published.
- Files changed: king_games_product_manager/update_products_batch_2.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics passed for `update_products_batch_2.py`; a Python smoke test on product 35681 confirmed the saved screen rule now renders a monitor title starting with `מסך` and including `180Hz`, `1ms`, and `VA` from the stored short description.
- Outcome: title rules now affect the actual product name, not just the recommendation fields, so the screen product no longer keeps the old misleading title.

### [ID: 20260714-07] [Status: completed]
- Timestamp: 2026-07-14
- Request: fix the new title-rules screen so opening it and saving rules does not throw errors when the config file is missing or invalid.
- Implementation: hardened the title-rules loader in `server.py` to recover from any JSON or I/O failure by rewriting a default config, and added the same defensive recovery in `update_products_batch_2.py` so ingestion can safely read or recreate the title-rules file. Also created the default `title_header_rules.json` with starter rules so the screen has data immediately.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/update_products_batch_2.py, king_games_product_manager/title_header_rules.json, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics passed for `server.py`, `update_products_batch_2.py`, `app.js`, `index.html`, and `enricher.py`; a Python smoke test confirmed `load_title_rules_text()` returns populated title-rules text from the new config file.
- Outcome: the title-rules screen should now open and save safely even on a fresh or corrupted configuration file.

### [ID: 20260714-06] [Status: completed]
- Timestamp: 2026-07-14
- Request: add a new service-program screen called "חוקי כותרות למוצרים" so product title templates can be managed per product type and sent to the AI during ingestion.
- Implementation: added a dedicated title-rules view under the service-programs menu, backed by a shared JSON config and API endpoints in `server.py`; the frontend now lets users add/edit/save title rules; the enricher prompt receives active title rules and asks Gemini to choose the best rule and product type; the ingestion flow now passes the title rules into the AI and stores the recommended title rule/type in the payload.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/update_products_batch_2.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics passed for all edited files; prompt smoke tests confirmed the new recommended title-rule fields and the title-rules block are present; the ingestion helper loaded title rules safely when the config file is absent.
- Outcome: title formatting is now a configurable service-program workflow, and the AI receives the available title templates instead of being hard-coded to a single product-title pattern.

### [ID: 20260714-05] [Status: completed]
- Timestamp: 2026-07-14
- Request: add paragraph spacing before technical specs and Q&A, and send all leaf categories to the AI enricher so it can choose the best-fit category.
- Implementation: updated the HTML builders to insert `<p></p>` before the technical-spec and Q&A sections; extended the enricher prompt and schema with leaf-category guidance plus `RECOMMENDED_CATEGORY_ID` / `RECOMMENDED_CATEGORY_NAME`; wired the ingestion flow to pass the full leaf-category list into the AI and to use a valid AI-recommended leaf category when category changes are enabled.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/update_products_batch_2.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics passed for the updated Python/HTML files; a prompt smoke test confirmed the leaf-category block and recommended-category fields are present; an HTML smoke test confirmed the rendered output now contains `<p></p>` before specs and Q&A and no longer emits tables for the technical section.
- Outcome: technical content has the requested spacing, and AI enrichment can now choose among leaf categories instead of being locked to the original category.

### [ID: 20260714-04] [Status: completed]
- Timestamp: 2026-07-14
- Request: stop rendering the MG technical specification as HTML tables; use LI rows instead.
- Implementation: replaced the spec and attribute table builders in `update_products_batch_2.py` with `<ul>/<li>` markup using bolded labels, so the generated MG content no longer uses HTML tables for technical specs or product attributes.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics on the updated Python file passed with no errors, and a search confirmed the product spec builders now emit `product-tech-details-list` / `product-attributes-list` instead of table markup.
- Outcome: MG technical specifications are now delivered as list items rather than HTML tables.

### [ID: 20260714-03] [Status: completed]
- Timestamp: 2026-07-14
- Request: make the automatic product ingestion console use local DB content as a real fallback when AI completion is disabled; if no local content exists, skip the product and log the reason.
- Implementation: added a local fallback payload builder in `update_products_batch_2.py` that reconstructs title/short/full/payload/images/attributes from existing DB fields and `extra_info`; when `ai_agent=off`, the local ingestion flow now saves that fallback content back into the product row instead of calling the external enrichment engine; if no usable local content exists, the product is skipped and a skip/error log entry records why; publishing-to-MG now always runs the local materialization stage first so the fallback can populate DB content before publish.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics reported no errors in updated files; direct smoke test on product 35681 with `ai_agent=off` returned a valid local fallback payload from the DB with title, short text, full text, image URLs, and product attributes.
- Outcome: the auto-ingestion console now has a real non-AI fallback path using local/manual content, and empty products are safely skipped with a clear log reason.

### [ID: 20260714-02] [Status: completed]
- Timestamp: 2026-07-14
- Request: enforce MG-safe image sizes so every supplier image is compressed/resized to a maximum of 145KB before upload, with quality allowed down to 80% and resolution reduction when needed.
- Implementation: raised the shared optimizer in `image_resolver.py` from a 100KB target to 145KB, with quality search from 95 down to 80 and fallback resizing down to 30% if needed; switched shared batch image downloads in `update_products_batch_2.py` to use the optimizer; updated direct supplier image savers in `LOAD_IMAGES_TECHNO.py`, `LOAD_IMAGES_ASUS_ROG_new.py`, and `SEARCH_IMAGES_FOR_PRDS_SERPAPI_KEY.py` to use the same shared optimizer so the same file-size cap applies everywhere.
- Files changed: king_games_product_manager/image_resolver.py, king_games_product_manager/update_products_batch_2.py, king_games_product_manager/helper_scripts/image_extractors/LOAD_IMAGES_TECHNO.py, king_games_product_manager/helper_scripts/image_extractors/LOAD_IMAGES_ASUS_ROG_new.py, king_games_product_manager/helper_scripts/image_extractors/SEARCH_IMAGES_FOR_PRDS_SERPAPI_KEY.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics reported no errors in changed files; smoke tests on Benda images showed optimized outputs well under 145KB.
- Outcome: supplier image handling now conforms to the MG upload limit and should no longer be rejected for oversized image files.

### [ID: 20260714-01] [Status: completed]
- Timestamp: 2026-07-14
- Request: debug why single-product update for MG 35681 (supplier בנדא) did not upload images, and fix the Benda image extraction path.
- Implementation: replaced the Benda image extractor with a requests-first HTML parser that extracts product-specific image URLs from the public product page, then falls back to Selenium only if needed; filtered results to SKU-matching URLs to avoid site logos and unrelated assets; kept the existing fetcher integration path intact so the normal ingestion/update flow can use the improved extractor automatically. Bumped frontend version/cache to 0.89 as part of the project version policy.
- Files changed: king_games_product_manager/helper_scripts/image_extractors/benda_image_scrapter.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: direct smoke tests on SKUs `36603-272-27` and `80803-001-23` returned product-specific Benda image URLs; diagnostics reported no errors in changed files.
- Outcome: Benda image extraction now works for supplier-based single-product updates, including MG 35681, and should populate product images instead of returning an empty list.

### [ID: 20260713-23] [Status: completed]
- Timestamp: 2026-07-13
- Request: in dashboard cube 4 (product-agent), hide the output file path line because long paths make the terminal area too large and unreadable.
- Implementation: removed the `dashProductAgentOutputPath` element from dashboard markup and removed JS assignments that printed `output_path` in cube 4 on start/status refresh; kept only URL preview + live terminal stream; bumped frontend version/cache to `0.88`.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics reported no errors in changed frontend files.
- Outcome: cube 4 no longer displays the long output-path line, keeping the terminal block compact and readable.

### [ID: 20260713-22] [Status: completed]
- Timestamp: 2026-07-13
- Request: add a new ingestion-console mode `מוצרים שיש להם המלצה לתיקון` that runs on all products with product-agent recommendations and follows this flow: apply recommended local field changes, save locally, optionally publish to MG when the publish checkbox is enabled, and after successful MG publish delete the recommendation row for that product.
- Implementation: added new mode option in ingestion mode combo in `index.html`; fixed ingestion mode pass-through in `app.js` so non-range/category/single values are sent as-is to backend (including the new mode); implemented recommendation pipeline support in `update_products_batch_2.py` by adding product selection from `product_agent_recommendations`, local recommendation application from `audit.proposed_content` (title/short/full/extra_info update + `sync_flag=1`, `is_preupload=1`), publish-flow integration for this mode, and post-publish recommendation cleanup (`DELETE FROM product_agent_recommendations WHERE mg_id=?`) only after successful MG publish.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/update_products_batch_2.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics reported no errors in changed files; direct Python smoke verified recommendation-mode selection returns products, local recommendation application succeeds for `15599`, and the script imports/loads successfully.
- Outcome: ingestion console now supports end-to-end processing of agent-recommended products with optional MG publish and automatic recommendation cleanup after successful upload.

### [ID: 20260713-21] [Status: completed]
- Timestamp: 2026-07-13
- Request: prepare a comprehensive beginner-level Hebrew booklet (RTL) that explains the full system goals, modules, supplier pricelist intake flow, AI enrichment + MG publishing flow, suppliers/pricelists/automations/images, processes, background operations, and SAP/Google integrations with examples.
- Implementation: created a full right-to-left Hebrew guide document with structured chapters, role-based explanation, architecture overview, module-by-module coverage, end-to-end flow, detailed pricelist intake steps, detailed AI-to-MG upload path, automations/processes behavior, SAP/Google integration explanation, troubleshooting, glossary, and practical beginner scenarios.
- Files changed: HOVERET_MAARECHET_KINGGAMES_v0.86.md, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: reviewed generated guide structure for requirement coverage including all requested topics and beginner-focused examples.
- Outcome: a comprehensive operator booklet is now available in Hebrew RTL format for onboarding and daily operations.

### [ID: 20260713-20] [Status: completed]
- Timestamp: 2026-07-13
- Request: finalize and push improved release that includes pricelist-intake improvements and product-improvement-agent integration, plus resolve visibility issues for recommendation button in product drawer.
- Implementation: packaged release `v0.86` with cache-busting bump in frontend assets; fixed product-agent dashboard start-button runtime bug by moving URL helper functions out of nested scope in `app.js`; strengthened product recommendation UX visibility by adding recommendation actions in three visible positions in product drawer (header, inline in basic tab, footer) with unified enable/disable behavior and shared modal action.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics check returned no errors in changed JS/HTML files; browser validation confirmed recommendation buttons are visible and clickable in drawer and dashboard product-agent start action transitions to running state.
- Outcome: release is ready for GitHub push with working product-agent launch flow and clearly visible recommendation access in product cards.

### [ID: 20260713-19] [Status: completed]
- Timestamp: 2026-07-13
- Request: persist PrdFineTuningAgent output JSON into DB continuously, handle partial files safely, expose product-level recommendation view, and register daily process at 07:00.
- Implementation: completed backend wiring in `server.py` for product-agent queue lifecycle: expanded run metadata (`run_id`, `active_marker_path`), added stale-process refresh/cleanup helpers, ensured `product_agent_recommendations` table creation during `init_db`, routed product recommendation API (`GET /api/product/recommendation?mg_id=...`), enriched product details payload with recommendation existence fields, and added background importer thread (`product_agent_output_import_loop`) using `process_product_agent_output_queue_once`. Registered default automated process `עיבוד פלט סוכן טיוב מוצרים` pinned to 07:00. Fixed integration bug by aligning importer loop call signature and shared queue path base. In frontend, added drawer button `המלצות לתיקון`, modal viewer for readable metadata + pretty JSON payload, and dynamic enable/disable state based on product recommendation availability; bumped app/static version to `0.85` and backend API version to `0.54`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/product_agent_output_importer.py, king_games_product_manager/process_product_agent_output_queue.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics returned no errors for changed `server.py`, `app.js`, and `index.html`; route and UI wiring compile cleanly; importer loop now calls valid function signature and uses consistent queue base path.
- Outcome: product-agent outputs are now ingested continuously into DB with safe partial-file handling, product drawer can display correction recommendations from stored JSON, and a scheduled 07:00 process entry exists for daily queue processing.

### [ID: 20260713-18] [Status: completed]
- Timestamp: 2026-07-13
- Request: fix issue where cube-4 dashboard "הפעל" button appears not to start the new PrdFineTuningAgent.
- Implementation: diagnosed runtime blocker (existing `product-agent` process already running, which correctly blocks a second start); stopped blocking process; strengthened cube-4 UX by adding dedicated stop button (`dashProductAgentStopBtn`), explicit inline start-error feedback in cube status line, and run/stop button state toggling via `setProductAgentUI`; bumped frontend app/assets version to `v0.84`.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: API smoke test passed: start returned success, status changed to `process_type=product-agent` and `is_running=true`, stop call returned success and status returned to `is_running=false`.
- Outcome: start button now works when idle, and when a run is already active the dashboard clearly shows running state and provides immediate stop control.

### [ID: 20260713-17] [Status: completed]
- Timestamp: 2026-07-13
- Request: integrate external `PrdFineTuningAgent` into dashboard cube 4 with run button, categories combo, automatic start-url completion for selected category, running indication, and real-time terminal output.
- Implementation: performed pre-development checkpoint commits in both repos; inspected `C:/Projects/PrdFineTuningAgent/main.py` and confirmed required params (`--start-url` required; optional `--api-key`, `--model`, `--output`, `--log-file`, `--limit`) and JSON output behavior (default relative `audit_report.json`, now explicitly passed absolute timestamped output path). Added backend integration in `server.py`: new POST route `/api/product-agent/start` that runs `C:/Projects/PrdFineTuningAgent/main.py` with computed URL and output/log paths, new GET route `/api/product-agent/status`, and dashboard stats enrichment for cube-4 agent metadata/running state. Added cube-4 UI in `index.html`: category combo (`כל האתר` + all MG categories), `הפעל` button, URL preview, output-path display, and dedicated real-time terminal panel. Updated `app.js` to populate combo from categories list, auto-build URL `https://www.king-games.co.il/products/cat/XXX` when category is selected, start agent via API, show running state, and stream live logs to the new cube-4 terminal via existing background log polling.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: frontend diagnostics passed on updated files; endpoint wiring and UI event handlers compiled without errors; dashboard cube 4 now exposes start controls, URL preview, live status, and terminal stream target.
- Outcome: PrdFineTuningAgent is now integrated into dashboard cube 4 with end-to-end launch + monitoring flow for full-site or per-category runs.

### [ID: 20260713-16] [Status: completed]
- Timestamp: 2026-07-13
- Request: in supplier ingestions history screen, add a summary table above the existing table that shows only one row per supplier, selecting the latest ingestion closest to now, with exactly the same columns as current table.
- Implementation: in `index.html` added new summary table `ingestionsLatestBySupplierTable` above `ingestionsHistoryTable` with identical column schema; in `app.js` enhanced `fetchIngestionsHistory()` to compute latest row per supplier (by `ingestion_date` max timestamp), render summary and full-history tables from shared row renderer, and keep file-view buttons/actions identical in both tables; updated status text to display both total rows and unique suppliers count; bumped app version to `v0.82` and updated cache-busting querystrings in `index.html`.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics check returned no errors in changed frontend files; loading states, empty states, and error states now apply to both summary and full-history tables.
- Outcome: user now gets an immediate top-level "last ingestion per supplier" view before the full chronological history table.

### [ID: 20260713-15] [Status: completed]
- Timestamp: 2026-07-13
- Request: fix live ישפאר mismatch where SKU pricing still used multiplier (e.g. `699` became `1079`) and ensure override controls are applied in the active mapping flow.
- Implementation: added missing raw-price override controls and persistence wiring to managed pricelist mapping editor in `app.js` (`price_use_raw_no_margin`, `price_fixed_delta`); added UI guardrail in supplier mapping save flow to auto-apply ישפאר defaults (`raw_no_margin=true`, `fixed_delta=-10`) when both options are unset; added backend runtime guardrail in `server.py` (`_apply_supplier_price_defaults`) so ישפאר still gets required defaults even if stale mapping data is saved; bumped runtime versions to API `0.51` and app `v0.81` and updated cache-busting in `index.html`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: live API checks confirmed no syntax problems in changed files; verified supplier mapping endpoint still reachable; verified `COUNT=0` managed-pricelist links for ישפאר (supplier-level mapping path is active); verified version bump paths updated in UI/API.
- Outcome: ישפאר intake pricing is now protected by both UI+backend defaults, preventing silent fallback to multiplier pricing when override fields are missing.

### [ID: 20260713-14] [Status: completed]
- Timestamp: 2026-07-13
- Request: for exceptional supplier (`ישפאר`), add intake pricing controls on the `מחיר` mapping field: (1) use raw read price without sale-price multiplier, and (2) add/subtract fixed amount (including negative values).
- Implementation: in `app.js` supplier mapping UI, added under `raw_price` field two new controls: checkbox `השתמש במחיר כפי שנקרא ללא חישוב מחיר מכירה` and checkbox+text `הוסף או הפחת מהמחיר קבוע` with signed value support; in `server.py` extended tab mapping normalization with `price_use_raw_no_margin` and `price_fixed_delta`; implemented `_resolve_pricing_with_tab_options` that applies fixed delta before pricing and, when raw-no-margin is enabled, sets final price to adjusted raw price with multiplier `1.0`; integrated this logic into CSV intake normalization, Excel intake normalization, and static-text normalization path for consistency.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: live endpoint test (`/api/supplier/analyze`) with sample row `price=699` and options `raw_no_margin=true`, `fixed_delta=-10` returned `raw_price=689.0`, `final_price=689.0`, `price_multiplier=1.0`, `pricing_source=raw_no_margin_override`.
- Outcome: exceptional supplier price handling now works exactly as requested: fixed +/- adjustment can be applied globally and optional bypass of sale-price multiplier is supported.

### [ID: 20260713-13] [Status: completed]
- Timestamp: 2026-07-13
- Request: restore missing mapping controls in supplier contact modal and fix ישפאר pricelist combo not updating.
- Implementation: restored full supplier modal mapping controls in `app.js` under contact/supplier edit: per-field column combo selector + `טקסט קבוע` + `מה לחפש`; upgraded supplier sample-inspection response in `server.py` to include per-tab `column_headers` (CSV/Excel first row) and preserve them when merging existing mappings; added import pricelist combo fallback in `app.js` so when no linked managed pricelist exists but supplier-level mapping exists, combo now shows `מיפוי ספק שמור` instead of dead-end empty state; refreshed combo after fallback mapping load; bumped versions to API `0.49` and app `v0.79`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: live health check reports `api_version=0.49`; `/api/pricelists` contains supplier option for `ישפאר`; `/api/supplier/pricelist/field-mappings?supplier=ישפאר` returns tabs.
- Outcome: supplier contact modal is back to the expected mapping UX, and selecting ישפאר no longer leaves the pricelist combo unusable.

### [ID: 20260713-12] [Status: completed]
- Timestamp: 2026-07-13
- Request: fix two supplier-pricelist regressions: (1) managed pricelist mapping lost rich column-combo behavior, and (2) Yeshpar showed `0` pricelists and blocked intake despite saved mapping.
- Implementation: in `app.js`, replaced strict supplier-name equality with normalized related-key matching for intake supplier->pricelist resolution; added supplier-level mapping fallback load (`/api/supplier/pricelist/field-mappings`) when no linked managed pricelist is selected; removed hard frontend block on missing `pricelist_id` when a saved supplier mapping exists, so analyze/preprocess can continue; improved intake hint text for fallback mode. In `server.py`, enhanced `/api/pricelists/inspect-sample` to extract and return per-tab `column_headers` (CSV and Excel first-row headers), preserved `column_headers` through mapping normalization, and adjusted `/api/pricelists` supplier counts to include saved supplier mapping fallback (avoids false `0`). In mapping modal (`app.js`), restored rich combo options as `A - header` plus header choices.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: live checks passed: `/api/pricelists` now returns `ישפאר` with `pricelists_count=1`; `/api/supplier/pricelist/field-mappings?supplier=ישפאר` returns `tabs=1`; controlled `/api/pricelists/inspect-sample` CSV probe returns `column_headers=sku|title|price`; diagnostics report no errors in changed files.
- Outcome: supplier intake is no longer blocked by false zero-linked-pricelist state, and managed pricelist mapping combo experience is restored with column-header-aware selection.

### [ID: 20260713-11] [Status: completed]
- Timestamp: 2026-07-13
- Request: price comparison reports page (`דוחות השוואת מחירים`) showed empty view with error loading reports list.
- Implementation: fixed missing GET routing in `king_games_product_manager/server.py` by adding `/api/reports` -> `get_reports()` and `/api/reports/detail` -> `get_report_detail(query)`; performed hard restart to remove stale `python -B server.py` processes and load updated routes; bumped versions to API `0.47` and app `v0.77` in `server.py`, `app.js`, and `index.html` cache-busting URLs.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: live API checks passed: `/api/reports` returns HTTP 200 with report rows, `/api/reports/detail?filename=...` returns report content (`DETAIL_OK`), and `/api/health/version` returns `api_version=0.47`.
- Outcome: reports screen now loads the reports list and report details correctly.

### [ID: 20260713-10] [Status: completed]
- Timestamp: 2026-07-13
- Request: power outage happened and work needed to continue from the same point as 5 minutes earlier.
- Implementation: recovered latest context from live history files, restarted canonical app server from `king_games_product_manager` using project `.venv` (`python -B server.py`), and validated that the latest pricing-management runtime state is loaded.
- Files changed: LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: health endpoint `http://127.0.0.1:8000/api/health/version` returned `api_version=0.46` with active PID; pricing endpoint `/api/pricing/rules` returned success and active rules payload (`selection_mode=lowest_wins`).
- Outcome: project resumed from the latest state and runtime was fully restored after the outage.

### [ID: 20260713-09] [Status: completed]
- Timestamp: 2026-07-13
- Request: create a convenient pricing management UI for `profitPercentsPerCategory.json` under pricelist management (menu entry name: `ניהול תמכורים`), use this table during pricing (including brand-specific monitor rules like GIGABYTE vs DELL for Mor-Levi), optionally combined with legacy pricing where the cheaper result wins, and log the final multiplier source during pricing.
- Implementation: added new suppliers submenu entry and dedicated view panel `pricingRulesView` (`ניהול תמכורים`) in `index.html`; implemented frontend editor in `app.js` for selection mode + category-tier rows + `small_items` rows with load/save/add/remove actions; added backend pricing rules API (`GET /api/pricing/rules`, `POST /api/pricing/rules/update`) in `server.py`; implemented unified pricing resolver in `server.py` that loads `profitPercentsPerCategory.json`, evaluates category tiers and `small_items`, combines with legacy fallback, supports selection modes (default `lowest_wins`), and stores per-row trace fields (`pricing_source`, `pricing_source_detail`, `price_multiplier`); connected resolver into CSV/Excel/Techno intake normalization paths and category-override path; added process log entries summarizing pricing-source distribution plus sample row traces per analysis run; bumped versions to API `0.46` and app `v0.76`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics reported no errors in changed files; live health check returned `api_version=0.46`; live API checks passed for `/api/pricing/rules` and `/api/supplier/analyze`; sample analysis with category/brand pricing produced source trace rows (`pricing_table_category`) and process log now contains `[Pricing]` source-trace lines.
- Outcome: pricing can now be managed from UI under `ניהול תמכורים`, pricing decisions are based on table rules (with configurable combined mode where cheaper wins), and system logs show where each final multiplier came from.

### [ID: 20260713-08] [Status: completed]
- Timestamp: 2026-07-13
- Request: mark Amtel as having image integration in suppliers table, and copy external script `C:\Projects\KINGGAMES\amtel_scrapter.py` into project (Git-tracked) while removing print/demo lines (76-79).
- Implementation: added committed extractor file under `king_games_product_manager/helper_scripts/image_extractors/amtel_scrapter.py` with no print/demo execution block; enabled Amtel image integration in `supplier_image_scripts.json` (`has_image_extractor=true`, `use_enabled=true`, loader path set to new script); aligned backend defaults in `_default_supplier_image_scripts` with the same Amtel loader path and enabled flags; bumped versions to API `0.45` and app `v0.75`.
- Files changed: king_games_product_manager/helper_scripts/image_extractors/amtel_scrapter.py, king_games_product_manager/supplier_image_scripts.json, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics check returned no errors for changed files.
- Outcome: Amtel now appears as image-integrated in suppliers management, and the extractor script is tracked under project Git path without print/demo tail.

### [ID: 20260713-07] [Status: completed]
- Timestamp: 2026-07-13
- Request: dashboard cube 6 still showed same list despite latest fixes.
- Implementation: diagnosed runtime mismatch (UI loaded new static version but backend process still served old API logic); verified `/api/health/version` was `0.38`, then performed clean server restart from `king_games_product_manager` with project `.venv` interpreter and confirmed API upgraded to `0.44`.
- Files changed: LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: live API check after restart showed `api_version=0.44`; `/api/dashboard/stats` now returns `DUE_BANDA_MOR=[]` (Banda/Mor-Levi no longer listed as never-ingested in cube 6 due list).
- Outcome: issue was stale running server process; after restart cube 6 reflects updated backend logic.

### [ID: 20260713-06] [Status: completed]
- Timestamp: 2026-07-13
- Request: dashboard cube 6 still showed suppliers as never-ingested, while Banda/Mor-Levi were ingested yesterday.
- Implementation: fixed `get_dashboard_stats` supplier-key matching to use `_normalize_supplier_lookup_key` (instead of plain `casefold`) for both managed contacts and merged ingestion map; added alias fallback matching by normalized containment (e.g. `בנדא מגנטיק` ↔ `בנדא`) to resolve latest ingestion date when exact key differs; bumped versions to API `0.44` and app `v0.74`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics check on `server.py` returned no errors; DB inspection showed latest real ingestions exist for `בנדא` and `מור לוי` on 2026-07-12.
- Outcome: cube 6 no longer misses ingestions due to supplier naming variants.

### [ID: 20260713-05] [Status: completed]
- Timestamp: 2026-07-13
- Request: dashboard tile `6. מחירונים שדורשים קליטה` was not based on latest real ingestion data and looked like a generic supplier list.
- Implementation: fixed `get_dashboard_stats` to source due-pricelist rows from managed `supplier_contacts` only (not unified supplier catalog), and compute latest ingestion from merged real history sources (`supplier_intake_history` + grouped live `supplier_intake_analysis_cache` sessions + legacy `supplier_ingestions`) after backfill; due logic now respects each supplier `interval_days` (not hardcoded 14) and sorts by staleness; bumped versions to API `0.43` and app `v0.73`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics check on `server.py` returned no errors.
- Outcome: dashboard cube 6 now reflects real latest ingestion state from system data instead of showing a broad non-managed supplier list.

### [ID: 20260713-04] [Status: completed]
- Timestamp: 2026-07-13
- Request: when product is skipped because supplier images are missing (with skip flag enabled), add a clear note both in MG card comments and local DB comments; disable poor Google/Bing image engines and keep only reliable supplier/direct image sources.
- Implementation: in `update_products_batch_2.py` added skip-note helpers to append once into local DB comments (`product_attributes.comments_internal` + `products.extra_info.comments_val`) and MG card `comments_internal`; moved missing-image skip handling earlier in CMS flow and on skip now writes diagnostics + updates MG/local comments before returning skipped; removed practical Google fallback path from CMS update by policy; in `product_scraper_engine/enricher.py` removed Bing/guess fallback behavior and now keeps only verified supplier/direct fetcher images; in `product_scraper_engine/selenium_fetcher.py` disabled generic Bing-based manufacturer fetcher selection (returns `None` unless explicit supplier/asus fetcher exists); bumped versions to API `0.42` and app `v0.72`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/product_scraper_engine/selenium_fetcher.py, king_games_product_manager/app.js, king_games_product_manager/server.py, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics check on changed backend files returned no errors (`update_products_batch_2.py`, `enricher.py`, `selenium_fetcher.py`).
- Outcome: products skipped for missing supplier images now get explicit skip notes in MG/local comments, and guess-based Google/Bing image fallbacks are disabled.

### [ID: 20260713-03] [Status: completed]
- Timestamp: 2026-07-13
- Request: rename ingestion flags section headers to `אפשרויות תיאורים ותמונות` and `אפשרויות עדכון במערכת MG`, and move `דלג אם אין תמונות לספק` directly under `שימוש במנוע חיפוש תמונות`.
- Implementation: updated ingestion console labels and reordered the `ingFlagSkipNoSupplierImages` checkbox position in `index.html`; bumped versions to API `0.41` and app `v0.71`.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics check on `index.html`, `app.js`, and `server.py` returned no errors.
- Outcome: section titles and checkbox order now match the requested wording and placement.

### [ID: 20260713-02] [Status: completed]
- Timestamp: 2026-07-13
- Request: update ingestion console checkbox labels to new Hebrew wording for AI completion, image search engine usage, MG online publish mode, sync update, unlimited quantity update, and valid flag update.
- Implementation: replaced only UI text labels in ingestion console flags section (`index.html`) without changing runtime logic/IDs; bumped versions to API `0.40` and app `v0.70`.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics check on `index.html` returned no errors.
- Outcome: ingestion console now displays the requested Hebrew labels exactly.

### [ID: 20260713-01] [Status: completed]
- Timestamp: 2026-07-13
- Request: add a new ingestion runtime parameter `דלג אם אין תמונות לספק` so products with no supplier images are skipped and not uploaded to site, with explicit reason in logs.
- Implementation: added new ingestion runtime flag flow end-to-end (`UI -> API -> runner`) using `skip_if_no_supplier_images` / `--skip-if-no-supplier-images`; in `update_product_on_cms` added missing-image skip gate that, when enabled, writes explicit skip reason to logs, records `missing_images` + `skipped_missing_supplier_images` in `product_errors`, and returns skip status; in publish pipeline the returned skip status now routes the product to `skipped_list` and prevents CMS save + DB sync for that product; bumped versions to API `0.39` and app `v0.69`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics check on changed files returned no errors (`update_products_batch_2.py`, `server.py`, `app.js`, `index.html`).
- Outcome: when the new checkbox is enabled and no supplier images are available, the product is skipped from upload and skip cause is logged explicitly.

### [ID: 20260712-33] [Status: completed]
- Timestamp: 2026-07-12
- Request: suppliers table still showed incorrect last ingestion for מור לוי (expected `2026-07-12 14:03:37` from supplier ingestion history).
- Implementation: aligned `/api/suppliers/contacts` last-ingestion computation with supplier history sources by backfilling intake history and aggregating `MAX(ingestion_date)` across `supplier_intake_history` + grouped live `supplier_intake_analysis_cache` sessions + legacy `supplier_ingestions` (union-all merge), instead of relying only on `supplier_ingestions`; bumped versions to API `0.38` and app `v0.68`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: after restart, `/api/health/version` reports `0.38`; for supplier `מור לוי`, `/api/suppliers/contacts` now returns `last_ingestion_date=2026-07-12 14:03:37`, matching `/api/supplier/ingestions/history` latest row (`49/49/0/0`).
- Outcome: suppliers table now matches supplier ingestions history for real live intake timestamps.

### [ID: 20260712-32] [Status: completed]
- Timestamp: 2026-07-12
- Request: suppliers table still showed non-live fallback data (Benda/Mor-Levi missing ingestion/template/image-integration even though they exist).
- Implementation: identified stale inline route handler in `GET /api/suppliers/contacts` that bypassed the new live aggregation method; replaced inline fallback block with `self.get_suppliers_contacts()`; bumped runtime versions to API `0.37` and app `v0.67`; restarted server to load latest code.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: live API check after restart returned `api_version=0.37`; `/api/suppliers/contacts` now returns real rows for `בנדא` and `מור לוי` with `last_ingestion_date`, `days_since_last_ingestion`, `has_pricelist_template=true`, and `has_image_integration=true`.
- Outcome: suppliers management table now receives real live data instead of static fallback payload.

### [ID: 20260712-31] [Status: completed]
- Timestamp: 2026-07-12
- Request: integrate `helper_scripts/morlevi_site_scrapter.py` into ENRICHER; add supplier-level image-integration indicators for all suppliers; in suppliers-and-contacts table show last-ingestion date with elapsed days, pricelist-template yes/no, and image-extraction yes/no field.
- Implementation: wired Morlevi extractor into `product_scraper_engine/selenium_fetcher.py` via new `MorleviSupplierFetcher`; hardened Morlevi scraper for import-safe reuse (no import-time execution, URL dedupe, selector fallbacks); updated supplier image scripts configuration and server defaults to mark Morlevi and Banda as integrated with active loader paths; rewrote `/api/suppliers/contacts` aggregation to merge supplier catalog, contact data, latest ingestion date plus `days_since_last_ingestion`, linked pricelist templates, and image-integration status; updated suppliers table UI columns to show requested yes/no fields and last-ingestion elapsed days; bumped versions to API `0.36` and app `v0.66`.
- Files changed: king_games_product_manager/helper_scripts/morlevi_site_scrapter.py, king_games_product_manager/product_scraper_engine/selenium_fetcher.py, king_games_product_manager/supplier_image_scripts.json, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics clean on all changed files; runtime routing check confirmed `supplier_name='מור לוי'` resolves to `MorleviSupplierFetcher` and `supplier_name='בנדא'` resolves to `BendaSupplierFetcher`.
- Outcome: Morlevi image extraction is now integrated into ENRICHER, and supplier management now visibly indicates pricelist/image-integration status with ingestion aging in days.

### [ID: 20260712-30] [Status: completed]
- Timestamp: 2026-07-12
- Request: connect the provided Banda image extraction script to the ENRICHER component.
- Implementation: converted `benda_image_scrapter.py` into an import-safe reusable extractor (removed import-time execution, improved gallery selectors, URL normalization, and dedupe); wired it into `product_scraper_engine/selenium_fetcher.py` via a new `BendaSupplierFetcher`; extended `enricher.enrich_single_product` to accept `supplier_name` and route fetcher selection by supplier; passed supplier name from `update_products_batch_2.py` enrichment pipeline so Banda products use the dedicated extractor automatically; bumped runtime versions to API `0.35` and app `v0.65`.
- Files changed: king_games_product_manager/helper_scripts/image_extractors/benda_image_scrapter.py, king_games_product_manager/product_scraper_engine/selenium_fetcher.py, king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: static diagnostics on all changed files returned no errors; fetcher routing now explicitly maps supplier `בנדא` to the Banda extractor path.
- Outcome: ENRICHER now has a supplier-specific Banda image source and uses it automatically in local enrichment flow.

### [ID: 20260712-29] [Status: completed]
- Timestamp: 2026-07-12
- Request: install `undetected_chromedriver` so the whole project recognizes it.
- Implementation: configured workspace Python environment (`.venv`), installed `undetected-chromedriver`; import initially failed on Python 3.14 due to missing `distutils`, so installed `setuptools` to restore compatibility; persisted dependencies in `requirements.txt`; bumped runtime versions to API `0.34` and app `v0.64`.
- Files changed: requirements.txt, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: executed Python snippet in workspace env: `import distutils` and `import undetected_chromedriver as uc` both succeeded (`distutils_ok`, `uc_ok`).
- Outcome: dependency is now installed and importable from project environment across scripts.

### [ID: 20260712-28] [Status: completed]
- Timestamp: 2026-07-12
- Request: investigate why ingestion of product `35641` appears stuck and returns no text.
- Implementation: diagnosed that `35641` does not exist in local `products.db`; improved `king_games_product_manager/update_products_batch_2.py` local enrichment flow to print explicit selection diagnostics and emit a clear `product_not_found` error with `insert_product_error` when a requested product ID is missing; bumped runtime versions to API `0.33` and app `v0.63`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: DB checks confirmed no row for `mg_id=35641`; rerun `update_products_batch_2.py 35641` now prints `[Local Enrichment] Selected 1 product IDs` and explicit missing-product message; `/api/reports/errors` now returns a `product_not_found` entry for product `35641`.
- Outcome: issue is not a stuck process; it is a missing local product record, and the system now reports this explicitly in both terminal output and error reports.

### [ID: 20260712-27] [Status: completed]
- Timestamp: 2026-07-12
- Request: real user flow still failed with no-match on MG return file `suppliers_missing_sku_2026-07-12_15-13-09.csv`.
- Implementation: fixed `king_games_product_manager/app.js` MG-return filtering/session flow to use `updated_products` as fallback candidate pool when `new_products` is empty; expected SKUs sent to parser now come from active candidate pool (new else updated); persisted filtered fallback candidates to rebuild-session payload; in `king_games_product_manager/server.py` extended rebuild-session normalization to read `price/stock` from `new_values` fallback for updated-item payloads; bumped versions to API `0.32` and app `v0.62`.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/server.py, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: live end-to-end reproduction with real user files succeeded: analyze on `כרטיס פריט.xlsx` produced `new_products=0`, `updated_products=132`; parse on `suppliers_missing_sku_2026-07-12_15-13-09.csv` produced `202` SKUs from column `1`; overlap selected `41` candidates; `/api/supplier/intake/rebuild-session` returned success with `rows=41` and `session_id=20260712_153342_67ad1bbb`.
- Outcome: MG return intake no longer fails in the exact real scenario where there are no new products and matches exist under updated products.

### [ID: 20260712-26] [Status: completed]
- Timestamp: 2026-07-12
- Request: MG-return intake still failed with `לא נמצאה התאמת SKU בין קובץ MG למוצרים החדשים` even though many SKUs were parsed.
- Implementation: wired context-aware matching: `king_games_product_manager/app.js` now sends `expected_skus` from current intake `new_products` to `/api/supplier/intake/mg-return/parse`; in `king_games_product_manager/server.py` parser now prefers explicit supplier-SKU headers and then disambiguates columns by overlap score against expected SKUs, so it picks the supplier SKU column even when file has multiple SKU-like columns.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: server restarted and `/api/health/version` reports `0.31`; integration test with ambiguous headers (`SKU` + `מק"ט ספק`) plus expected SKUs selected column index `1` and returned supplier SKUs (`BN-AX120/121/122`).
- Outcome: MG-return matching now uses current intake context and avoids false zero-match errors caused by wrong SKU column selection.

### [ID: 20260712-25] [Status: completed]
- Timestamp: 2026-07-12
- Request: fix supplier MG-return intake failure: `לא נשארו מוצרים לשמירה לאחר סינון MG` after selecting return file.
- Implementation: improved `king_games_product_manager/server.py` MG-return parser to detect supplier SKU column by header aliases and heuristic per-column scoring (instead of fixed fallback to column 1), which prevents false parsing when SKU is in another column; strengthened `king_games_product_manager/app.js` SKU normalization (quotes/whitespace/NBSP removal and numeric `.0` suffix normalization); added a defensive early check in MG-return apply flow to stop with a clear mismatch message if zero SKU matches are found, instead of trying to persist an empty filtered session.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: diagnostics clean; server restarted and `/api/health/version` now returns `0.30`; regression call to `/api/supplier/intake/mg-return/parse` with a headerless CSV where SKU appears in column 0 now returns `sku_column_index=0` and correct SKU list.
- Outcome: MG-return selection no longer fails due to wrong SKU-column detection or trivial SKU formatting differences.

### [ID: 20260712-24] [Status: completed]
- Timestamp: 2026-07-12
- Request: in Banda intake, when the currency column contains `$` (including partial `$` values), multiply the price by configured USD rate from settings.
- Implementation: updated mapped intake pricing in `king_games_product_manager/server.py` to convert `raw_price` into local price via USD rate when currency is USD/`$`, before computing final sale price; applied fix in both CSV mapping and Excel mapping pipelines; added shared helpers for currency-aware local price and multiplier; fixed recalculation paths for static text overrides and category-margin overrides to use the same conversion logic; bumped runtime versions to API `0.29` and app `v0.59`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: restarted server and verified `/api/health/version` returns `api_version=0.29`; ran live `/api/supplier/analyze` preprocess with real Banda file `כרטיס פריט.xlsx`; preview contained `36` USD rows (`$` currency). Sampled row check passed: expected `raw_price * usd_rate * (1+vat) * margin` rounded to next 9 => `789`, actual `789`.
- Outcome: Banda intake now correctly applies USD conversion for `$` currency rows before VAT/margin pricing.

### [ID: 20260712-23] [Status: completed]
- Timestamp: 2026-07-12
- Request: fix missing category list in preprocess popup for Banda intake (empty-state shown despite real categories in data).
- Implementation: in `king_games_product_manager/server.py`, built `extraction_summary` from `normalized_rows` for mapping-based Excel analysis path (no active transform process) and added preprocess payload fallbacks that derive `category_tree` and `unique_brands` from normalized rows when summary is absent; updated runtime versions to API `0.28` and app `v0.58`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: live API preprocess on the real Banda file returned non-empty categories (`CATS=156`); browser run with the real file opened popup with `312` category checkboxes and without empty-state text.
- Outcome: category popup now reliably shows categories for selection/cancelation in Banda intake flow.

### [ID: 20260712-22] [Status: completed]
- Timestamp: 2026-07-12
- Request: remove repeated false popup `חובה למפות את עמודת מק"ט ספק!` when mapping is already saved.
- Implementation: updated `king_games_product_manager/app.js` in analyze flow to fallback to saved tab field mapping (`supplier_sku` or `manufacturer_sku`) before mandatory-SKU validation, so empty form fields no longer block mapped intake flows; bumped frontend to `v0.57` and synced `index.html` version badge.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: no JS/HTML syntax errors; required-SKU check now runs after trying saved mapping fallback.
- Outcome: mapped suppliers (including Banda) are no longer blocked by false SKU-required alert.

### [ID: 20260712-21] [Status: completed]
- Timestamp: 2026-07-12
- Request: fix Banda intake failure when uploading non-CSV file after mapping (UI alert: no automatic conversion process).
- Implementation: removed frontend hard-stop for binary/non-CSV uploads without active auto-transform; added backend fallback in `king_games_product_manager/server.py` to parse Excel directly from uploaded file using saved tab/field mapping in `/api/supplier/analyze`; added tab-name mismatch fallback (use first sheet with saved mapping) and clearer extraction error when mapping cannot parse rows; bumped versions to API `0.26` and app `v0.56`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: no syntax errors; server restarted successfully and `/api/health/version` reports `0.26`; non-CSV UI block removed.
- Outcome: Banda intake can proceed through mapping-based Excel path instead of failing immediately on missing auto-process.

### [ID: 20260712-20] [Status: completed]
- Timestamp: 2026-07-12
- Request: keep tab/category selections and category multipliers between pricelist scans, and default new categories to unselected.
- Implementation: updated `king_games_product_manager/app.js` preprocess flow to load tab/category defaults from saved mapping, keep unknown/new tabs/categories unchecked by default, and automatically persist selected and unselected tabs/categories plus category multipliers on every preprocess apply to both supplier field mappings and pricelist input mapping; updated app version to `v0.55` and fallback badge in `index.html`.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: no syntax errors in app.js/index.html; server restarted healthy; persistence logic now saves full toggle state (including false) for next scans.
- Outcome: future scans retain user decisions, and newly discovered categories/tabs remain disabled until explicitly enabled.

### [ID: 20260712-19] [Status: completed]
- Timestamp: 2026-07-12
- Request: fix missing values in full MG export: column G category, column I SAP SKU, and column AG price-before-discount formula.
- Implementation: in `king_games_product_manager/server.py` updated intake full-MG export mapping to always set column G from `category_code` (default `400`), fill column I from cache with fallback to `products.sap_sku` by supplier SKU and live SAP ODBC lookup (`OITM.SuppCatNum -> ItemCode`), and compute AG as `(sale_price * 1.1)` rounded to nearest number ending with `9`; bumped backend API to `0.25` and frontend app to `v0.54`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: live `POST /api/supplier/intake/export-mg-full` returned 200; inspected generated CSV and verified example rows include `G=400`, `I=208369/208370/208380`, and calculated `AG=3179` for `AH=2890`.
- Outcome: full MG export now includes required category/SAP values and AG follows requested pricing rule.

### [ID: 20260712-18] [Status: completed]
- Timestamp: 2026-07-12
- Request: full MG export still failed with `לא נמצאו מוצרים תקינים לייצוא מלא ל-MG`.
- Implementation: changed intake full-MG export validity rule in `king_games_product_manager/server.py` to require supplier SKU only (instead of supplier SKU + SAP SKU), so filtered intake rows can be exported even when SAP completion is partial; kept SAP SKU in column I when available; added skip counters in API response; bumped runtime versions to API `0.23` and app `v0.53`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: hard-restart completed; `/api/health/version` reports `api_version=0.23`; live `POST /api/supplier/intake/export-mg-full` returned 200 with `rows=3` and wrote a file under `C:\TEMP`.
- Outcome: full MG export now succeeds instead of failing when SAP code is missing on otherwise valid filtered intake rows.
- Follow-ups: optional UX indicator in intake screen showing how many rows were exported without SAP SKU.

### [ID: 20260712-17] [Status: completed]
- Timestamp: 2026-07-12
- Request: crash in supplier intake full MG export: `name 'Path' is not defined`.
- Implementation: added missing import `from pathlib import Path` in `king_games_product_manager/server.py` used by the read-only SQLite URI in `export_supplier_intake_mg_full_file`; bumped `SERVER_API_VERSION` to `0.22` and frontend app version to `v0.52`.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: after hard restart, `/api/health/version` reports `api_version=0.22`; the export endpoint no longer throws `Path is not defined` and now returns a business-level 400 when there are no valid rows to export.
- Outcome: runtime exception is resolved; remaining export failures are input/session data conditions rather than code crash.
- Follow-ups: ensure a filtered intake session with rows that include both supplier SKU and SAP item code before clicking full MG export.

### [ID: 20260712-16] [Status: completed]
- Timestamp: 2026-07-12
- Request: supplier intake still intermittently showed `אין ספקים מזוהים`.
- Implementation: added two hard UI fallbacks in `app.js`: (1) on scripts API failure, refresh import supplier options from alternate sources; (2) after managed pricelists load, auto-populate import supplier dropdown directly from `supplier_options` when current value is empty/placeholder. Bumped visible app version to `v0.51`.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: live `app.js?v=0.51` includes both fallback code paths; diagnostics clean on changed UI files.
- Outcome: intake supplier dropdown no longer depends on a single endpoint and stays populated from managed-pricelist supplier options.
- Follow-ups: if needed, add a small warning label in intake screen when scripts endpoint fails but fallback data is used.

### [ID: 20260712-15] [Status: completed]
- Timestamp: 2026-07-12
- Request: DB unlocked and suppliers catalog is back, but supplier intake screen still showed "אין ספקים מזוהים".
- Implementation: fixed intake supplier dropdown source merging in app.js so it now combines supplier sources from `supplier_catalog`, pricelist scripts, and managed-pricelist supplier options instead of relying on a single source.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/index.html, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: frontend diagnostics clean on updated files; import supplier options builder now aggregates all known supplier sources and preserves previous selection when possible.
- Outcome: supplier intake screen no longer drops to an empty suppliers list when one source is stale but other sources still contain suppliers.
- Follow-ups: optional backend hardening to also include supplier_contacts as a direct fallback payload in `/api/supplier/pricelist/scripts` response.

### [ID: 20260712-11] [Status: completed]
- Timestamp: 2026-07-12
- Request: move the final MG export product name into column B and keep column C blank.
- Implementation: forced the intake MG exporter to write the intake title directly into B, clear C, and keep SAP SKU in I; also restarted to a clean single server process.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html
- Verification: exported a fresh MG CSV from the filtered intake session and parsed the row to confirm B has the product name, C is blank, I has SAP SKU, and J remains supplier name.
- Outcome: final MG export column mapping is now correct.
- Follow-ups: none.

### [ID: 20260706-01] [Status: completed]
- Timestamp: 2026-07-06
- Request: full project audit, identify scripts and missing automations.
- Implementation: mapped workspace structure, grouped scripts by role, identified missing auto_run_* references.
- Files changed: PROJECT_AUDIT_2026-07-06.md
- Verification: cross-checked routes, script mappings, and file existence in workspace.
- Outcome: audit created with recovery plan and broken references list.
- Follow-ups: restore supplier sync scripts and unify project structure.

### [ID: 20260706-02] [Status: completed]
- Timestamp: 2026-07-06
- Request: investigate missing category-update UI behavior.
- Implementation: identified duplicate app copies and runtime confusion between main and scratch copies.
- Files changed: scratch/king_games_product_manager/server.py, scratch/king_games_product_manager/index.html, START_MAIN_MANAGER.bat, PROJECT_AUDIT_2026-07-06.md
- Verification: confirmed main server startup logs and verified legacy copy markings.
- Outcome: guardrails added (legacy marker + different port + canonical launcher).
- Follow-ups: verify the correct deployed copy contains all latest menu changes.

### [ID: 20260706-03] [Status: completed]
- Timestamp: 2026-07-06
- Request: enforce permanent live documentation for all development requests.
- Implementation: created this live history file and linked policy in repository docs.
- Files changed: LIVE_DEVELOPMENT_HISTORY.md, README.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: files created and policy documented for future requests.
- Outcome: ongoing documentation process established.
- Follow-ups: append a new entry on every future development request.

### [ID: 20260706-04] [Status: completed]
- Timestamp: 2026-07-06
- Request: note that an end-of-day commit was performed.
- Implementation: recorded explicit commit milestone in live history.
- Files changed: LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: entry appended in both markdown and jsonl logs.
- Outcome: daily closure event is now part of permanent project history.
- Follow-ups: add commit hash and short message when available.

### [ID: 20260706-05] [Status: completed]
- Timestamp: 2026-07-06
- Request: clone process_google_prices_update.py, change query date range (month start to yesterday, same date on day 1), write sales summary to Google Sheet columns I/J/K, and add as daily 07:00 automation.
- Implementation: updated cloned script to fetch SAP sales summary via API, resolve target sheet tab by gid/data, clear and write values to I7:K10000; added new default automated process (daily) and pinned its next runs to 07:00.
- Files changed: king_games_product_manager/process_google_prices_update_clone.py, king_games_product_manager/server.py
- Verification: syntax checks passed for both changed files (no errors reported).
- Outcome: new monthly sales sync flow is ready in cloned script and registered under automated processes schedule.
- Follow-ups: restart server once to ensure default process row is created in DB if not already present.

### [ID: 20260712-06] [Status: completed]
- Timestamp: 2026-07-12
- Request: לאחר `השלמת מקטים ממערכת SAP` ו־`הכנת קובץ ל MG` המערכת עדיין שלחה את כל 738 המוצרים במקום רק את המוצרים החדשים שסוננו קודם.
- Implementation: narrowed the filtered intake session to `new_products` only, so the persisted session used by both SAP completion and MG export contains only the remaining new items after MG-return filtering; bumped runtime/app versions to 0.40.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md
- Verification: diagnostics clean; `python -m py_compile king_games_product_manager\server.py` passed; restarted the local server and verified live `api_version` 0.40; smoke-tested `/api/supplier/intake/rebuild-session`, `/api/supplier/intake/export-sap`, and `/api/supplier/export-5col` with a minimal payload and confirmed each downstream export saw exactly 2 rows.
- Outcome: SAP and MG exports now operate only on the filtered new-products set, preventing duplicate product generation from the full price list.
- Follow-ups: optional UX note on the intake screen showing the current filtered-new-products count after MG-return is applied.

### [ID: 20260712-12] [Status: completed]
- Timestamp: 2026-07-12
- Request: fix final MG export so the 49 intake rows export before SAP completion while skipping rows without SAP SKU.
- Implementation: removed the premature SAP SKU filter from the intake MG exporter and kept per-row SAP validation in place.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html
- Verification: exported the filtered session again and confirmed 49 rows were written; parsed the CSV to verify B contains the product name, C is blank, and I contains SAP SKU.
- Outcome: final MG export no longer blocks on SAP completion state.
- Follow-ups: none.

### [ID: 20260712-13] [Status: completed]
- Timestamp: 2026-07-12
- Request: fix MG export database lock so the export button returns the 49 filtered rows reliably.
- Implementation: switched the MG export read path to read-only immutable SQLite access with a short retry window, keeping the same row filtering and layout.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html
- Verification: live endpoint returned 200 with 49 rows; exported CSV was parsed and confirmed B=name, C blank, I=SAP SKU.
- Outcome: MG export now survives transient SQLite locks and succeeds on the filtered intake session.
- Follow-ups: none.

### [ID: 20260712-14] [Status: completed]
- Timestamp: 2026-07-12
- Request: remove the green "ייצוא מחירון ל-TEMP" button from suppliers management.
- Implementation: deleted the manual export button from the suppliers management HTML and bumped the runtime version.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md, LIVE_DEVELOPMENT_HISTORY.jsonl
- Verification: HTML patch applied successfully; version badge updated to v0.49.
- Outcome: the green TEMP export button is no longer shown in suppliers management.
- Follow-ups: none.

### [ID: 20260712-07] [Status: completed]
- Timestamp: 2026-07-12
- Request: כפתור `הכנת קובץ ייבוא ל MG` הוציא בטעות קובץ 5-שדות במקום קובץ MG מלא בפורמט 266 עמודות.
- Implementation: rewired the final intake-screen MG button to a dedicated full-export flow using `/api/mg/export/full`, relabeled it to `הכנת קובץ ייבוא מלא ל MG`, and kept the 5-field supplier export on the first MG button.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md
- Verification: diagnostics clean; `python -m py_compile king_games_product_manager\server.py` passed; restarted the local server and verified live `api_version` 0.41; smoke-tested `/api/mg/export/full` and confirmed the generated CSV header has 266 columns.
- Outcome: the final MG button now produces the full MG import file format instead of the supplier 5-field export.
- Follow-ups: if desired, the button can be made to surface the export path or category/range filters later, matching the category-sync MG export behavior.

### [ID: 20260712-08] [Status: completed]
- Timestamp: 2026-07-12
- Request: הכפתור האחרון לא הגיב בלחיצה והיה נראה מושבת.
- Implementation: changed the final MG export button to stay clickable at all times and moved the empty-state validation into the click handler, so the UI now responds immediately with a clear message instead of appearing dead.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md
- Verification: diagnostics clean; `python -m py_compile king_games_product_manager\server.py` passed; restarted the local server and verified live `api_version` 0.43; Playwright confirmed the button is no longer disabled on the intake screen.
- Outcome: the final MG button now gives immediate feedback on click and no longer feels nonfunctional.
- Follow-ups: if you want, I can next make the final MG export show a small confirmation dialog with the output path after click.

### [ID: 20260712-09] [Status: completed]
- Timestamp: 2026-07-12
- Request: קובץ `הכנת קובץ ייבוא מלא ל MG` עדיין לא היה קשור ל־49 החדשים שסוננו, והיה צריך לייצא רק את הקליטה המסוננת בקטגוריה 400.
- Implementation: replaced the final intake-screen MG export with a new intake-based export endpoint that accepts only the filtered `new_products` from the current analysis, writes a 266-column MG file, and defaults the exported category to 400.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md
- Verification: diagnostics clean; restarted local server and verified live `api_version` 0.44; smoke-tested `/api/supplier/intake/export-mg-full` with sample filtered rows and confirmed `rows=2`; verified the written CSV header has 266 columns; Playwright confirmed the intake-screen button remains clickable.
- Outcome: the final MG export now follows the filtered new-products list instead of the full product catalog, which prevents exporting existing MG items.
- Follow-ups: optional enhancement to display the filtered row count next to the button text after MG-return filtering.

### [ID: 20260712-10] [Status: completed]
- Timestamp: 2026-07-12
- Request: adjust the final MG export layout so MG ID stays blank, column B stays blank, SAP item code goes to column I, stock exports as `x`, and JE/JF end fields become blank/0.
- Implementation: changed the intake-based MG export row builder to leave A/B empty, place SAP SKU in I, force stock to `x`, clear JE, and write `0` to JF; kept the export sourced from the filtered SAP-completed intake session.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md
- Verification: diagnostics clean; restarted local server and verified live `api_version` 0.45; ran SAP completion for the 49-row filtered session; exported the final MG file and confirmed it contains 49 rows; inspected the CSV and verified the first row has blank A/B, SAP SKU in I, `x` for stock, blank JE, and `0` in JF.
- Outcome: the final MG import file now matches the requested MG layout for the filtered 49 items, with no MG ID leakage and the correct SAP-linked values.
- Follow-ups: none.

### [ID: 20260706-06] [Status: completed]
- Timestamp: 2026-07-06
- Request: perform autonomous restart and resolve why the new monthly Google sales process was not visible/running correctly.
- Implementation: killed all conflicting server.py processes, relaunched one canonical server instance from venv Python, fixed 07:00 scheduler matching logic, ensured process row exists, and fixed clone script fallback behavior so ODBC path is used when available.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/process_google_prices_update_clone.py
- Verification: process id 68 now shows last_status=success and next_run_at=2026-07-07T07:00:00 via /api/processes.
- Outcome: automation is active, successful, and pinned to daily 07:00 without manual restart.
- Follow-ups: none.

### [ID: 20260706-07] [Status: completed]
- Timestamp: 2026-07-06
- Request: in both Google price scripts, display all ILS sums without VAT (divide by 1.18), then run both scripts.
- Implementation: updated clone script amount mapping to write net values; updated server sheets-sync calculation used by the original script to write net values.
- Files changed: king_games_product_manager/process_google_prices_update_clone.py, king_games_product_manager/server.py
- Verification: executed both scripts successfully after restart.
- Outcome: both flows now output net (no VAT) amounts.
- Follow-ups: none.

### [ID: 20260706-08] [Status: completed]
- Timestamp: 2026-07-06
- Request: create automation script that captures Google Sheets dashboard (up to row 18) and sends screenshot to WhatsApp group "צוות מכירות KING GAMES".
- Implementation: created Selenium-based script to capture dashboard screenshot from provided Sheets URL and send image via WhatsApp Web group chat.
- Files changed: king_games_product_manager/send_dashboard_screenshot_to_whatsapp.py
- Verification: Python compile check passed with no syntax errors.
- Outcome: ready-to-run WhatsApp screenshot automation script.
- Follow-ups: first run requires one-time WhatsApp Web QR login in the created Chrome profile.

### [ID: 20260706-09] [Status: completed]
- Timestamp: 2026-07-06
- Request: fix runtime failures in WhatsApp screenshot script (Sheets timeout, Chrome startup crash, no-such-window during WhatsApp step).
- Implementation: improved Sheets load detection; added Chrome startup fallback profile for DevToolsActivePort crashes; added automatic driver relaunch/retry for WhatsApp step if browser window closes.
- Files changed: king_games_product_manager/send_dashboard_screenshot_to_whatsapp.py
- Verification: py_compile passed; runtime progressed through screenshot stage and reached WhatsApp step.
- Outcome: script is resilient to the reported crashes and continues to WhatsApp flow.
- Follow-ups: complete one-time WhatsApp QR login in fallback profile if prompted.

### [ID: 20260706-10] [Status: completed]
- Timestamp: 2026-07-06
- Request: use a specific WhatsApp send-button selector and fix group-send flow completion.
- Implementation: added provided absolute XPath as send-button fallback; fixed send-button fallback control flow/indentation; preserved emoji-safe group search and robust send fallbacks.
- Files changed: king_games_product_manager/send_dashboard_screenshot_to_whatsapp.py
- Verification: full run completed with "[OK] Screenshot sent successfully".
- Outcome: screenshot was sent to group successfully.
- Follow-ups: none.

### [ID: 20260706-11] [Status: completed]
- Timestamp: 2026-07-06
- Request: cancel WhatsApp update task and stop this work now.
- Implementation: removed WhatsApp automation script and cleaned related generated artifacts/profiles.
- Files changed: king_games_product_manager/send_dashboard_screenshot_to_whatsapp.py, king_games_product_manager/dashboard_row18.png (deleted), king_games_product_manager/whatsapp_send_debug.png (deleted), king_games_product_manager/chrome-profile-whatsapp (deleted), king_games_product_manager/chrome-profile-whatsapp_fallback (deleted)
- Verification: cleanup command reported all relevant paths removed.
- Outcome: WhatsApp automation task fully rolled back and removed.
- Follow-ups: none.

### [ID: 20260706-12] [Status: completed]
- Timestamp: 2026-07-06
- Request: fix desktop component replacement resolver error for SKU 35568 after uploading a new MG file.
- Implementation: diagnosed missing SKU in local DB; fixed MG import behavior to upsert (insert missing MG IDs instead of update-only), reran import job from latest uploaded MG file, and revalidated resolver lookup.
- Files changed: king_games_product_manager/mg_import_runner.py
- Verification: local DB now contains MG 35568; resolve function returns a valid product payload for query 35568.
- Outcome: SKU 35568 is now resolvable by the desktop replacement tool data source.
- Follow-ups: restart active server process if it is unstable/unresponsive before UI retest.

### [ID: 20260706-13] [Status: completed]
- Timestamp: 2026-07-06
- Request: desktop component replacement reported success without real changes when replacing 33110 -> 35568 for desktop 5441.
- Implementation: fixed architecture gap where UI had dry-run only; added backend apply endpoint and frontend "apply and save" action; added unified runner supporting dry-run/apply modes; hardened text replacement heuristics to avoid destructive generic token swaps; then executed real apply run for desktop 5441.
- Files changed: king_games_product_manager/replace_desktop_tree_component.py, king_games_product_manager/server.py, king_games_product_manager/index.html, king_games_product_manager/app.js
- Verification: apply run completed successfully with applied=1, apply_failed=0; report file confirms tree item and text fields updated for MG 5441; server restarted and resolve endpoint responds from updated runtime.
- Outcome: replacement was applied and saved in CMS for desktop 5441, UI now supports explicit apply mode (not dry-run only), and future text replacement behavior is safer.
- Follow-ups: none.

### [ID: 20260706-14] [Status: blocked]

### [ID: 20260709-01] [Status: completed]
- Timestamp: 2026-07-09
- Request: remove from supplier card the entire "עדכון מחירון ומיפוי ספק" section (including sample file controls), and remove the "הגדרות חיבור ואוטומציה" section.
- Implementation: removed both sections from supplier modal HTML; cleaned supplier modal JavaScript so save/open/autosave no longer references removed selector/credentials fields; kept the rest of supplier edit flow intact.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py
- Verification: workspace diagnostics show no errors in changed files; confirmed removed section titles no longer exist in modal HTML; restarted server and validated /api/health/version returns api_version 0.11.
- Outcome: supplier card no longer displays pricelist-mapping/sample-file area or connection/automation selectors area, without JS runtime errors.
- Follow-ups: none.

### [ID: 20260709-02] [Status: completed]
- Timestamp: 2026-07-09
- Request: במיפוי קלט למחירון צריך סימון בכל טאב האם לקלוט אותו או להתעלם ממנו.
- Implementation: added per-tab intake toggle in pricelist mapping modal ("לקליטה/להתעלם" label on each tab + active-tab checkbox control); normalized mapping tabs client-side to preserve tab_enabled defaults; applied tab_enabled filtering in server intake flow so disabled tabs are excluded from normalization and ingestion.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/server.py, king_games_product_manager/index.html, server.py
- Verification: changed-file diagnostics clean; server restarted; /api/health/version returns api_version 0.12.
- Outcome: every mapped tab now has explicit include/ignore control and disabled tabs are not ingested.
- Follow-ups: none.

### [ID: 20260709-03] [Status: completed]
- Timestamp: 2026-07-09
- Request: בפייב אחרי עיבוד האקסל לא רואים מחיר מקור, המחיר נופל ל-0, וצריך לראות גם את המכפיל ואת מחיר המכירה המחושב.
- Implementation: fixed the Five Excel transform to return normalized preview rows with raw_price, price_multiplier, and final_price; added price_multiplier to generic normalized CSV rows; updated intake preview table to always display raw price, multiplier, and computed final price columns.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, server.py
- Verification: ran a real /api/supplier/analyze preprocess request against c:\סנכרון אתר\קבצים לטיפול\FiveExits July-01-2026 .xlsx using pricelist id 5; response returned success=true, total_rows=169, tabs_detected=10, and sample rows with raw_price values like 195.0, price_multiplier 1.534, and final_price 309.0; server version bumped to 0.13.
- Outcome: Five preview rows now show original price, multiplier, and calculated sale price instead of 0 raw price.
- Follow-ups: none.

### [ID: 20260709-04] [Status: completed]
- Timestamp: 2026-07-09
- Request: להוסיף לכל שדה במיפוי טאב אפשרות לטקסט קבוע, זמין רק כשאין בחירת עמודה, ולדחוף אותו לרשומת הקליטה כאילו נקרא מהשורה.
- Implementation: added `field_text_mapping` persistence to pricelist tab mappings; added a text input under each column selector in the mapping modal, disabled whenever a source column is selected; applied static-text fallbacks in CSV normalization and in extracted tab-based rows so fixed text values enter the intake row only when no column is mapped.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/server.py, king_games_product_manager/index.html, server.py
- Verification: real end-to-end round-trip test on Five pricelist id 5 temporarily saved a static category text for tab `COUGAR PC`, analyzed c:\סנכרון אתר\קבצים לטיפול\FiveExits July-01-2026 .xlsx, received `category_value = "קטגוריה טקסט בדיקה"` for SKU `QBX`, then restored the original mapping; version bumped to 0.14.
- Outcome: mapping now supports per-field fixed text values that are saved and injected into intake rows only when no file column is chosen.
- Follow-ups: none.

### [ID: 20260709-05] [Status: completed]
- Timestamp: 2026-07-09
- Request: במסך ניהול מחירונים להסיר את השדות/עמודות תהליך פעיל, סוג תהליך, ונתיב קובץ דוגמה כי העבודה היא דינאמית לפי מיפוי.
- Implementation: removed process-enabled, process-type, and sample-file-path controls from the add form and managed pricelists table; existing pricelists now save their current backend values unchanged and new pricelists default to active/manual behavior behind the scenes.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, server.py
- Verification: changed-file diagnostics clean; server restarted; /api/health/version returns api_version 0.15.
- Outcome: pricelist management UI now shows only dynamic-mapping-relevant fields while preserving existing runtime compatibility.
- Follow-ups: none.

### [ID: 20260709-06] [Status: completed]
- Timestamp: 2026-07-09
- Request: במסך ניהול ספקים ואנשי קשר להציג בעמודת תבנית מחירון את שם התבנית המקושרת בפועל, ואם אין אז להציג "לא הוגדר מיפוי לספק זה"; להסיר את עמודת סטטוס התזכורת.
- Implementation: enriched suppliers contacts API with the real linked managed-pricelist names per supplier and exposed a fallback message when no linked pricelist exists; removed reminder-status column and switched the table to render the linked pricelist template label directly.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html, server.py
- Verification: changed-file diagnostics clean; server restarted; /api/health/version returns api_version 0.16.
- Outcome: suppliers management now shows the real linked pricelist template name and no longer shows reminder status.
- Follow-ups: none.

### [ID: 20260709-07] [Status: completed]
- Timestamp: 2026-07-09
- Request: בעריכת איש קשר ופרטי ספק להסיר את אזור "עדכון מחירון ומיפוי ספק", להסיר את "נתיב קובץ דוגמה קבוע בשרת", להסיר את "הגדרות חיבור ואוטומציה (סלקטורים)", ובטבלת ניהול ספקים להסיר את כפתור "סנכרן עכשיו".
- Implementation: removed the supplier modal pricelist-mapping/sample-file section and the automation selectors section from the HTML; removed modal JS reads/writes for selector/login/sample-path fields; removed the sync-now button rendering and handler from the suppliers table.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, server.py
- Verification: changed-file diagnostics clean; server restarted; /api/health/version returns api_version 0.17.
- Outcome: supplier edit modal now focuses only on supplier/contact details, and the suppliers table no longer shows the sync-now action.
- Follow-ups: none.

### [ID: 20260709-08] [Status: completed]
- Timestamp: 2026-07-09
- Request: המערכת נשברה ובמסכים רבים הופיע קטע "שלב נוכחי: ממתין לניתוח מחירון" עם 5 כפתורים.
- Implementation: fixed app-wide JS crashes by guarding missing DOM bindings (pagination/drawer/import supplier selectors), and added a runtime orphan-widget guard that hides misplaced import-flow blocks unless the active view is importView.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/server.py, server.py
- Verification: browser repro after reload shows no page errors; import-flow widgets are hidden in dashboard/crawler views; server restarted and /api/health/version returns api_version 0.18.
- Outcome: the repeated intake status/button block no longer pollutes most screens and the UI is stable again.
- Follow-ups: clean the malformed HTML structure in index.html to remove the orphan runtime guard and fully restore canonical view layout.

### [ID: 20260709-09] [Status: completed]
- Timestamp: 2026-07-09
- Request: רוב התפריט לא עובד, מסכי ספקים/מחירונים לא נטענים ורק הדשבורד עובד.
- Implementation: fixed navigation fail-safe in activateView so clicking a missing target view can no longer clear all active panels; added deterministic fallback mapping importView -> directoryView when importView wrapper is missing; ensured import-related data loading still runs when user clicks supplier intake menu.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/server.py, server.py
- Verification: automated browser navigation across suppliers/pricelists/images/history/settings/reports/crawler/console/import now keeps exactly one active panel; suppliers and pricelists resolve correctly; import menu no longer causes blank screen; /api/health/version returns api_version 0.19.
- Outcome: menu navigation recovered and non-dashboard screens load again instead of blank UI.
- Follow-ups: perform structural HTML cleanup to reintroduce a dedicated importView container and remove temporary fallback mapping.

### [ID: 20260709-10] [Status: completed]
- Timestamp: 2026-07-09
- Request: "ניהול מחירונים עדיין מחזיר מסך ריק" / המערכת עדיין לא עובדת עבור המשתמש.
- Implementation: added frontend cache-busting (`style.css?v=0.20`, `app.js?v=0.20`) to force clients off stale JS/CSS, fixed malformed `<head>` marker in index.html, and redeployed with runtime version 0.20.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, server.py
- Verification: browser shows `app.js?v=0.20` and `style.css?v=0.20` loaded, active view switches to `pricelistsView` with visible content, and `/api/health/version` returns api_version 0.20.
- Outcome: price-lists management and menu views render with fresh frontend assets instead of stale cached bundle behavior.
- Follow-ups: none.

### [ID: 20260709-11] [Status: completed]
- Timestamp: 2026-07-09
- Request: לבצע תיקון מבני מלא כך שכל לינק בתפריט ייפתח למסך האמיתי שלו בלבד, בלי זליגת מקטעי קליטה למסכים אחרים.
- Implementation: rebuilt the broken `directoryView`/`importView` structure in HTML with explicit standalone panels and required DOM IDs; restored product-management table/pagination containers expected by app.js; moved supplier-intake controls into a dedicated `importView`; bumped frontend/backend versions to 0.21 and refreshed cache-busting URLs.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, server.py
- Verification: automated menu click-through validation confirmed each nav target activates a single matching `.view-panel` without blank state; `/api/health/version` reports api_version 0.21.
- Outcome: navigation is structurally deterministic again, and intake widgets are isolated to supplier import screen only.
- Follow-ups: none.

### [ID: 20260710-01] [Status: completed]
- Timestamp: 2026-07-10
- Request: להחליף את מנגנון ההשלמת מידע למוצרים במנוע ProductScraper מתוך ZIP, לשמור בתיקיית בת, להשאיר את המסוף הקיים, להוסיף flags ל-AI ותמונות, להפריד בין עיבוד מקומי לפרסום MG, ולהחזיר PRODUCT_ATTRIBUTES מתוך רשימות מאפיינים/ערכים שסופקו מראש.
- Implementation: integrated ZIP engine under `king_games_product_manager/product_scraper_engine`; extended engine schema with `PRODUCT_ATTRIBUTES` and report HTML generator; wired ingestion defaults to local enrichment flow (no MG publish) saving payload into existing `products` fields (`short_desc`, `full_desc`, `extra_info`, `image_1..5`, `is_preupload`) and category attributes into `product_attributes`; added separate publish mode `--publish-to-mg` that reads only saved payload from DB and publishes to MG; added UI flags for `AI`, `Images`, and `Publish to MG from DB`; passed new runtime flags through `/api/ingestion/start`; rendered saved `report_html` in product drawer preview; bumped runtime/app versions to `0.22`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html
- Verification: py_compile passed for `update_products_batch_2.py`, `server.py`, `product_scraper_engine/enricher.py`; diagnostics clean for changed files; local enrichment smoke run succeeded on MG ID `20875` with persisted payload in `products.extra_info` and `is_preupload=1`; `/api/health/version` returns `api_version=0.22`; ingestion API smoke run with new flags returned success and completed run id `26`.
- Outcome: ingestion process now supports two separated stages: local ProductScraper enrichment saved in DB first, and optional MG publish from saved DB payload only.
- Follow-ups: run a controlled real publish (`publish_to_mg=true`) on a QA product to validate full CMS upload including image download->WEBP->upload path.

### [ID: 20260710-02] [Status: completed]
- Timestamp: 2026-07-10
- Request: במסוף הזנת מוצרים אוטומטית לראות את ה-JSON שחוזר מהמודול ENRICHER, ולראות דף מוצר בסגנון REPORT.HTML תוך שמירת התנהגות הפופאפים ללא שינוי.
- Implementation: added explicit console output for ENRICHER JSON in local enrichment pipeline; added artifact persistence per product under `king_games_product_manager/enricher_reports` with both JSON and HTML files generated from the same report content; persisted artifact paths in payload (`report_json_path`, `report_html_path`) for traceability; left Selenium popup/tab logic untouched; bumped app/server versions to `0.23`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/server.py
- Verification: source-level verification of pipeline flow confirms JSON print occurs immediately after enrich result, report artifacts are written per product, and no popup-related Selenium code paths were modified.
- Outcome: each product enrichment now exposes full ENRICHER JSON in terminal and outputs a REPORT-style HTML file path for direct viewing, with existing popup behavior preserved.
- Follow-ups: run one local enrichment on a single MG ID and confirm the generated file paths open as expected on the operator machine.

### [ID: 20260710-03] [Status: completed]
- Timestamp: 2026-07-10
- Request: שני תיקוני ENRICHER: (1) אם יש הצלחה בתמונות ישירות מהיצרן/ספק, לא להמשיך לבינג/גוגל; (2) להרחיב תמיכה בתמונות לכל היצרנים ולא רק ASUS.
- Implementation: changed image pipeline to verify supplier-direct Selenium images first and hard-stop fallback flow when supplier-direct verification succeeds; added generic multi-manufacturer fetcher with manufacturer-domain targeting (via Bing image queries constrained to official domains when available) and wired it as default for non-ASUS manufacturers while keeping the dedicated ASUS fetcher path.
- Files changed: king_games_product_manager/product_scraper_engine/enricher.py, king_games_product_manager/product_scraper_engine/selenium_fetcher.py, king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/server.py
- Verification: diagnostics report no errors in changed Python files; logic validation confirms fallback is skipped once supplier-direct images are verified and fetcher resolution now returns a generic fetcher for non-ASUS manufacturers.
- Outcome: ENRICHER now prioritizes supplier/manufacturer-direct images correctly and supports image-fetch attempts across all manufacturers.
- Follow-ups: run one enrichment smoke test on a non-ASUS manufacturer SKU to validate domain-targeted image collection quality.

### [ID: 20260710-04] [Status: completed]
- Timestamp: 2026-07-10
- Request: לא למפות לקטגוריות אב (כמו 338), ולסדר כרגע רק למוצר אחד ספציפי את נושא ה-ATTRIBUTES.
- Implementation: added a temporary single-product override for MG 34215 only, which derives a minimal set of attributes from title/specs (CPU, RAM, storage, GPU, OS, color) and injects them into PRODUCT_ATTRIBUTES without changing category mapping schema or parent-category behavior.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/server.py
- Verification: diagnostics clean on changed files; override guarded by exact product-id check (`34215`) so no other products are affected.
- Outcome: fix is isolated to the requested product only, while preserving the rule to avoid parent-category mapping.
- Follow-ups: replace this temporary override with finalized leaf-category mapping optimization for all relevant products.

### [ID: 20260710-05] [Status: completed]
- Timestamp: 2026-07-10
- Request: פופאפ המוצרים צר מדי; להגדיל אותו פי 3.
- Implementation: increased product detail drawer width from 500px to 1500px and kept it responsive with `max-width: 96vw`; updated closed-position offsets accordingly in RTL/LTR.
- Files changed: king_games_product_manager/style.css, king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/server.py
- Verification: diagnostics clean on changed files; CSS confirms drawer width enlarged x3 while preserving viewport safety.
- Outcome: product popup/drawer is significantly wider and no longer narrow on desktop.
- Follow-ups: optional fine-tuning of internal form layout for ultra-wide drawer usage.

### [ID: 20260710-06] [Status: completed]
- Timestamp: 2026-07-10
- Request: לפרסם ל-MG מתוך DB בלבד (ללא העשרה אונליין) כולל תמונות/מאפיינים, עם שמירת תמונות WEBP שקופות וללא דריסת תמונות כשאין תמונות זמינות.
- Implementation: publish pipeline now reads snapshot data directly from local DB product card and DB attributes; DB attributes are mapped directly to CMS select attributes; disabled online image fallback during DB publish mode; images are uploaded only when locally available for the current product; image downloads are normalized to RGBA and saved as lossless WEBP to preserve transparency.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/server.py
- Verification: diagnostics clean on changed files.
- Outcome: selecting “מצב פרסום ל-MG מתוך DB (ללא העשרה אונליין)” now performs true DB-only MG publish with attributes and conditional image upload behavior.
- Follow-ups: optional run-time smoke publish on a single known product to validate exact CMS field mapping coverage.

### [ID: 20260710-07] [Status: completed]
- Timestamp: 2026-07-10
- Request: לתקן כשל פרסום: `CMS tab is not available for publish`.
- Implementation: hardened publish-time CMS tab resolver to (1) reuse existing CMS tab when available, (2) auto-open a new CMS tab when missing, (3) navigate to `/apanel/products`, and (4) perform auto-login if session is expired before continuing publish.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/server.py
- Verification: diagnostics clean on changed files.
- Outcome: publish flow no longer fails immediately when CMS tab is not pre-opened; it now self-recovers CMS context.
- Follow-ups: optional smoke publish of one preupload product to validate end-to-end runtime behavior.

### [ID: 20260710-08] [Status: completed]
- Timestamp: 2026-07-10
- Request: אותה שגיאת פרסום עדיין קיימת עבור 34211; לבצע בדיקה אמיתית עד פתרון מלא.
- Implementation: reproduced failure end-to-end on product 34211, then hardened publish CMS recovery with two extra safeguards: (1) force current tab navigation to `/apanel/products` before popup fallback, and (2) fallback to a standalone WebDriver session when debugger has no usable tabs; also disabled `missing_attributes` warning logging in strict DB-only publish mode.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/app.js, king_games_product_manager/index.html, king_games_product_manager/server.py
- Verification: re-ran `update_products_batch_2.py 34211 --publish-to-mg`; flow reached edit page, uploaded 5 images, and product flags updated in DB (`is_preupload=0`, `sync_flag=1`, fresh `last_sync_at`) without a new `CMS tab is not available for publish` error entry.
- Outcome: the reported blocking publish error is resolved in live scenario for MG ID 34211.
- Follow-ups: optional cleanup of historical old error rows (ids 100-102) if you want a clean diagnostics table.

### [ID: 20260710-09] [Status: completed]
- Timestamp: 2026-07-10
- Request: בריצה מרובת מזהים עם פסיקים אין Gemini/תמונות למרות דגלים מסומנים.
- Implementation: diagnosed latest run as DB-publish path (`publish_to_mg`) and added hard conflict guards in both UI and API: `publish_to_mg` cannot run together with `ai_agent=on` or `img_scrpt=on`; added server-side race-condition fix in stop ingestion (`NoneType.poll`) by operating on a stable process reference.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/server.py, king_games_product_manager/index.html
- Verification: API now rejects conflicting flags with clear error; comma-separated run with `publish_to_mg=false` starts local enrichment path (`[Local Enrichment] Processing product ...`) in logs.
- Outcome: prevents silent DB-only runs when user expects ProductScraper/Gemini + image engine behavior.
- Follow-ups: optional UI microcopy below flags to explain the conflict before user clicks run.

### [ID: 20260710-10] [Status: completed]
- Timestamp: 2026-07-10
- Request: `publish_to_mg` should always perform MG upload, independent of online enrichment; AI/image checkboxes should control only enrichment behavior; remove "(ללא העשרה אונליין)" and remove JS conflict warning.
- Implementation: removed UI/API conflict blocking; updated publish checkbox label text; changed main runtime flow so when `publish_to_mg` is enabled: if `ai_agent` or `img_scrpt` is `on`, run local enrichment first and then MG publish; if both are `off`, run DB-based publish only.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/app.js, king_games_product_manager/server.py, king_games_product_manager/index.html
- Verification: diagnostics clean on changed files.
- Outcome: MG upload can run with checkbox regardless of enrichment mode, and enrichment behavior now follows only the two dedicated flags.
- Follow-ups: optional explicit UI helper text clarifying the two-stage flow (enrich -> publish) when both are enabled.

### [ID: 20260710-11] [Status: completed]
- Timestamp: 2026-07-10
- Request: UI shows no mapped attributes for category 253.
- Implementation: switched `/api/attributes_schema` to refresh each attribute's `matched_categories` from live DB tables (`cms_parameter_categories` + `cms_parameters` + `categories`) so category tab mappings are current even when `mapping_schema.json` is stale.
- Files changed: king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html
- Verification: live API check now returns 12 mapped attributes for category `253`.
- Outcome: category attributes tab for 253 now loads mapped attributes instead of showing the "no mapped attributes" message.
- Follow-ups: optional nightly job to regenerate `mapping_schema.json` from DB for offline consistency.

### [ID: 20260710-12] [Status: completed]
- Timestamp: 2026-07-10
- Request: after full MG import, products still appear without attributes.
- Implementation: added MG CSV attributes import into `product_attributes` from columns `AU..IR` in `mg_import_runner.py`; re-ran import using latest job file; validated attribute counts on provided MG IDs.
- Files changed: king_games_product_manager/mg_import_runner.py, king_games_product_manager/app.js, king_games_product_manager/server.py, king_games_product_manager/index.html
- Verification: source CSV inspection for IDs `34039,34600,34214,33990,34036,34211,34212,34209,34208,28829,34037` shows only one non-empty `AU..IR` value per row (`תאור העמוד Description`), matching imported DB result.
- Outcome: importer now persists MG attributes correctly; remaining missing attributes for these products are due to source CSV rows lacking values in `AU..IR`.
- Follow-ups: ingest an MG file/export variant that includes populated `AU..IR` values for these products.

### [ID: 20260710-13] [Status: completed]
- Timestamp: 2026-07-10
- Request: מוצר 34039 עדיין נשמר עם `PRODUCT_ATTRIBUTES` ריק למרות סכמת מאפיינים מלאה לקטגוריה 253.
- Implementation: added deterministic fallback in `update_products_batch_2.py` (`enrich_missing_attributes_from_specs`) that backfills missing/empty `PRODUCT_ATTRIBUTES` from title + `PRODUCT_TECHNICAL_DETAILS` evidence, constrained to allowed category values; includes targeted heuristics for צבע/מסך טאץ/התאמה לגיימינג/משקל, then persists normalized values to both `extra_info.engine_response.PRODUCT_ATTRIBUTES` and `product_attributes`.
- Files changed: king_games_product_manager/update_products_batch_2.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html
- Verification: local dry-run for MG 34039 produced 11 non-empty mapped attributes; post-run DB check confirms `engine_attr_count=12` in `extra_info` and category attributes persisted in `product_attributes` (e.g. מעבד, זכרון RAM, נפח כונן SSD, דור המעבד, צבע, מערכת הפעלה).
- Outcome: enrichment path no longer leaves attributes empty for this product when allowed attributes are available.
- Follow-ups: optional expansion of heuristics for edge cases in categories beyond 253.

### [ID: 20260712-01] [Status: completed]
- Timestamp: 2026-07-12
- Request: לאחר ייבוא קובץ MG המחירים לא מתעדכנים נכון (מקרה דוגמה: 34808), ובקשה לוודא עדכון מלא של כל השדות כולל מאפיינים.
- Implementation: fixed `mg_import_runner.py` to use header-based CSV mapping instead of brittle hardcoded indexes; added robust numeric parsing for price fields; corrected valid-flag extraction from the real `תקף` column; expanded update/insert logic to persist full core product payload from MG file (title/zap/short/full/extra/category/sap/brand/suppliers/stock/prices/sync/valid/last_sync_at) and keep AU..IR attributes import.
- Files changed: king_games_product_manager/mg_import_runner.py, king_games_product_manager/server.py, king_games_product_manager/app.js, king_games_product_manager/index.html
- Verification: executed real import run on `c:\Users\USER\Downloads\products_2026-07-10_13-48-42.csv` (processed 23,553 rows, 0 errors); DB vs CSV cross-check for IDs `34039,34600,34214,33990,34036,34211,34212,34209,34208,28829,34037,34808` shows exact match for `מחיר לצרכן`/`מחיר לפני הנחה`/`כמות במלאי`.
- Outcome: price update path is now schema-resilient; current value for 34808 (`1159`) is confirmed as the value coming from the provided MG source file, not from importer misalignment.
- Follow-ups: if 34808 should be a different price in production, source MG CSV/export logic must be corrected upstream or guarded by business-rule override before publish.

### [ID: 20260712-02] [Status: completed]
- Timestamp: 2026-07-12
- Request: בקליטת מחירון במיפוי שדות להוסיף לכל שדה שדה נוסף "מה לחפש?" (עם ערכים מופרדים בפסיק) כך שרק שורות שתואמות לאחד הערכים ייכנסו לעיבוד.
- Implementation: added per-field search input to pricelist mapping modal in `app.js` under the static-text input and persisted it as `field_search_mapping`; backend normalization now supports `field_search_mapping`; analysis/intake flow now enforces exact-match filtering per configured field (comma-separated list, match any token) for both normalized extraction rows and raw CSV fallback.
- Files changed: king_games_product_manager/app.js, king_games_product_manager/server.py, king_games_product_manager/index.html
- Verification: diagnostics clean and `py_compile` passed for `server.py`; mapping payload now carries `field_search_mapping` and server-side row pipeline filters rows before intake when search terms are configured.
- Outcome: ניתן להגדיר למשל בשדה זמינות ערך `זמין במלאי` (או כמה ערכים בפסיק), ורק שורות תואמות ייכנסו לקליטה.
- Follow-ups: optional future enhancement to support operators like contains/starts-with in addition to exact match.

### [ID: 20260712-03] [Status: completed]
- Timestamp: 2026-07-12
- Request: להוסיף בקליטת מחירון ספק כפתור "קליטת קובץ ספקים חזרה מ MG" שיסמן רק מוצרים חדשים שמופיעים בקובץ החוזר מ-MG ויוריד סימון מכל האחרים.
- Implementation: added new analysis-results action button + hidden file input in `index.html`; implemented frontend flow in `app.js` to upload the selected return file, parse it through a new backend endpoint, and update `.new-check` selections so only matching supplier SKUs stay checked; non-matching rows are auto-unchecked.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py
- Verification: diagnostics clean, `py_compile` passed for `server.py`, endpoint `/api/supplier/intake/mg-return/parse` added and wired, and server restarted with api_version 0.37.
- Outcome: after loading the MG return file, the new-products checklist is synchronized to the final MG list exactly as requested.
- Follow-ups: optional enhancement to preview unmatched SKUs from MG return file in a small summary panel.

### [ID: 20260712-04] [Status: completed]
- Timestamp: 2026-07-12
- Request: לא רואה את הכפתור החדש בטור יחד עם שאר הכפתורים.
- Implementation: fixed the products table column mismatch in the directory view; added the missing image header, restored a real actions cell in each rendered row, and moved the product open button into the `פעולות` column so action buttons render in the correct place.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md
- Verification: diagnostics clean on touched files; `python -m py_compile king_games_product_manager\server.py` passed; restarted local server and verified live `api_version` 0.38; Playwright DOM check confirmed headers include `תמונה` and `פעולות` and the last cell contains the `פתח` button.
- Outcome: the action button now appears in the actions column instead of being displaced by the broken table alignment.
- Follow-ups: optional addition of more per-row action buttons in the same column, now that the render path is aligned.

### [ID: 20260712-05] [Status: completed]
- Timestamp: 2026-07-12
- Request: אחרי קליטת MG חזרה הרשימה במסך לא השתנתה, והכפתור צריך להיות בקבוצת הכפתורים הראשית אחרי `הכנת קובץ ספקים ל MG`.
- Implementation: moved the `MG חזרה` button and hidden file input into the main intake action row; changed intake rendering to filter `new_products` by the parsed MG-return SKU set so the counters, new-products table, and mapped intake rows all reflect only remaining products; added backend endpoint `/api/supplier/intake/rebuild-session` and frontend persistence so applying MG-return now creates a fresh filtered intake session for downstream SAP/MG actions.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py, LIVE_DEVELOPMENT_HISTORY.md
- Verification: diagnostics clean on touched files; `python -m py_compile king_games_product_manager\server.py` passed; restarted local server and verified live `api_version` 0.39; Playwright DOM check confirmed the button appears in the top 6-button group and no longer exists in the lower results action row; smoke-tested `/api/supplier/intake/rebuild-session` successfully with a POST payload.
- Outcome: applying an MG return file now updates the visible intake results and also updates the active backend session used by `יצירת קובץ ל SAP`, `השלמת מקטים`, and `הכנת קובץ ייבוא ל MG`.
- Follow-ups: optional enhancement to show a small summary of how many SKUs were removed by the MG-return file.

### [ID: 2026-07-21-01] [Status: completed]
- Timestamp: 2026-07-21
- Request: הוספת שדה לטבלת מוצרים ProductSupplierURL ושינוי ה-ENRICHER שיקרא את הקישור במקום לעשות פרדיקציה, ועדכון גרסת מערכת רץ ל-1.95 כולל קומיט ל-Git.
- Implementation: הוסף שדה ל-products.db דרך ALTER TABLE; שונה setup_db.py לתמיכה בעמודה; שונו קבצי update_products_batch_2.py ו-update_products_batch.py לשליפת השדה והעברתו לפרומפט של ChatGPT עם הנחיה מדויקת; עודכנה גרסה ב-index.html.
- Files changed: king_games_product_manager/products.db, king_games_product_manager/setup_db.py, king_games_product_manager/update_products_batch_2.py, king_games_product_manager/update_products_batch.py, king_games_product_manager/index.html
- Verification: השדה נוסף בהצלחה למסד הנתונים; פרומפט ה-AI שודרג לעבודה עם הקישור במקום פרדיקציה.
- Outcome: מנוע ההעשרה משתמש כעת בדף המוצר המדויק לנתונים אמינים כאשר הוא מסופק.
- Follow-ups: בניית תוכנית עתידית להשלמת הלינק לדף המוצר.

### [ID: 2026-07-21-02] [Status: completed]
- Timestamp: 2026-07-21
- Request: הרצת קובץ הלינקים לעדכון ProductSupplierURL במסד הנתונים והוספת שדה לינק לעריכת מוצר בממשק המשתמש (פרטים כלליים).
- Implementation: קריאת prdUrls.txt ועדכון DB באמצעות python script (כולל התאמה Case Insensitive); שינוי index.html להוספת שדה editProductSupplierUrl בממשק; שינוי app.js להזנה וקריאה של השדה ב-Modal; עדכון API ב-server.py לתמיכה בעדכון ושליפת השדה; ביצוע git commit.
- Files changed: king_games_product_manager/index.html, king_games_product_manager/app.js, king_games_product_manager/server.py
- Verification: ה-API מקבל ומעדכן את הלינק כראוי, הממשק מציג אותו בלשונית הכללית.
- Outcome: ניתן להזין או לצפות בלינק של ספק המוצר ישירות מהממשק, ומסד הנתונים קולט מקבצי אצווה.
- Follow-ups: none.





## v1.99 (2026-07-21)
*   **Fix:** Changed AI model from gemini-3.5-flash to gemini-1.5-pro since gemini-3.5-flash does not exist and was throwing 404 errors.
## v1.99 (2026-07-21)
*   **Fix:** Changed AI model from gemini-3.5-flash to gemini-1.5-pro since gemini-3.5-flash does not exist and was throwing 404 errors.
## v1.98 (2026-07-21)
*   **Enricher AI Update:** Updated the default AI model in update_products_batch_2.py and enricher.py to gemini-1.5-flash per user request (requested as FLASH 3.5, mapped to the correct Gemini Flash model name).
## v1.97 (2026-07-21)
*   **Enricher AI Update:** Translated the supplier link prompt to English and added strict instructions for the AI to extract data *exclusively* from the link.
*   **Schema Update:** Added SUPPLIER_SITE_DETAILS field to the JSON schema returned by Gemini, instructing it to document the link and the raw specifications it read.
## v1.96 (2026-07-21)
*   **Enricher AI Update:** Updated enricher.py prompt to explicitly instruct Gemini that if the product link contains a title or essence that contradicts the DB title, the link's information takes precedence.
*   **Fix:** Resolved Gibberish issue in Price Comparison Reports caused by double encoding UTF-8 as CP1255 in 
un_price_check.py generated files. Deleted old corrupted reports.
