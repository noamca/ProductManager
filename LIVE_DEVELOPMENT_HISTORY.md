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
