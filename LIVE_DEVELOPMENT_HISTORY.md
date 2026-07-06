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

## Entries

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
- Timestamp: 2026-07-06
- Request: run full replacement 33110 -> 35568 across all desktop products with mandatory double-verification logs.
- Implementation: added per-product post-apply verification (PASS/FAIL) to replacement engine; added strict run-status semantics so API/CLI no longer report false success when load/apply/verify failures exist; added desktop-only log endpoint to isolate logs from unrelated automations; added single-instance lock and category candidate pre-filter for non-desktop noise.
- Files changed: king_games_product_manager/replace_desktop_tree_component.py, king_games_product_manager/server.py, king_games_product_manager/app.js
- Verification: targeted smoke tests now return explicit failure status when CMS form cannot load; backend now reports `success=false` with structured `load_failed_products` instead of misleading success.
- Outcome: false-success bug is fixed and diagnostics are explicit, but full all-desktops apply is currently blocked by CMS auth/session failure (`CMS login appears to have failed (login form still visible)`).
- Follow-ups: complete one interactive CMS login in the automation profile, then rerun full apply (existing code now emits per-product verify logs and truthful pass/fail summary).
