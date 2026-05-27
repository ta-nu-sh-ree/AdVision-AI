**Purpose**
- **Goal**: Help AI coding agents become productive quickly in this repo (AdScore web app).

**Big Picture**
- **Type**: Small Flask web app that analyzes uploaded ad images with OCR and LLMs.
- **Data flow**: User uploads image via `/free-trial` -> saved to `uploads/` -> OCR (`easyocr`) -> image encoded -> Groq LLM calls (multiple analysis steps) -> results rendered back into `templates/free-trial.html`.
- **Why structure**: All request handling and AI orchestration live in `app.py` to keep the pipeline linear and simple (upload → guardrail → scores → detailed analysis → platform analysis).

**Key files & routes**
- **app entry**: [app.py](app.py) (main logic, sector config, routes).
- **Requirements**: [requirements.txt](requirements.txt) (install with `pip install -r requirements.txt`).
- **Templates**: [templates/free-trial.html](templates/free-trial.html) and [templates/index.html](templates/index.html) (UI patterns: upload form, result tabs, modular “advice” cards).
- **Static assets**: `static/` (css, images, JS helpers).
- **Uploads**: `uploads/` (persisted uploaded images, cleaned on GET to `/free-trial`).
- **Public endpoints**: `/` (homepage), `/free-trial` (GET/POST upload + analysis), `/api/sectors` (returns available sectors), `/uploads/<filename>` (serve saved images).

**Project-specific conventions & patterns**
- **Single-file backend**: `app.py` contains most logic (helpers, AI calls, routes). Prefer small, focused edits in this file rather than scattering logic.
- **Sector-driven analysis**: `SECTOR_CONFIG` in `app.py` drives domain-specific prompts. Add new sectors by updating this object (keys: `real_estate`, `jewellery`, `automobile`, `ecommerce`, `healthcare`).
- **Guardrail-first approach**: `check_image_category()` is a lenient filter to avoid off-topic images — keep guardrail logic when changing AI prompts.
- **Three-step AI flow**: `get_main_scores()` → `get_detailed_analysis()` → `get_platform_analysis()`. Maintain that ordering and data passed (criteria list, extracted text).
- **Retries & fallbacks**: LLM calls include retries and fallback parsing; preserve retry loops when modifying LLM interaction.

**Dev / run / debug workflow**
- **Local quick run**: Create a virtualenv, install deps, set env, then run `python app.py` (the file runs Flask via `app.run(debug=True)`).

```bash
python -m venv venv
venv\Scripts\activate    # Windows
pip install -r requirements.txt
# create .env with GROQ_API_KEY and any other keys
python app.py
```

- **Env / secrets**: `GROQ_API_KEY` must be set in environment or in a `.env` file (loaded via `python-dotenv`). Do NOT commit keys.
- **Files & limits**: uploads are written to `uploads/` and limited to 16MB (`MAX_CONTENT_LENGTH` in `app.py`).

**Testing & troubleshooting tips**
- **OCR availability**: `easyocr.Reader` is initialized on startup; if it fails the app continues but OCR will be unavailable. Check console logs for "EasyOCR loaded" messages.
- **LLM errors**: Groq client calls may throw; `app.py` prints stack traces and has fallbacks. When debugging, reproduce with a small, clear image to reduce LLM token usage.
- **Common fixes**: If model calls timeout, inspect network, API key, or intermediate base64 encoding via `encode_image_to_base64()`.

**Safe modification notes for agents**
- Preserve retry/fallback structure around `groq_client` calls. Changes to prompts must keep output-parsing regexes in `get_main_scores()` and `get_detailed_analysis()` consistent with expected formats.
- When adding features that change response shape, update both the parser code and the UI templates (see `templates/free-trial.html` tabs and advice-card blocks).

**Examples from codebase**
- Add a sector by copying the shape in `SECTOR_CONFIG` inside [app.py](app.py).
- The upload handling and validation live in `free_trial()` in [app.py](app.py); reuse `allowed_file()` and `check_file_size()` helpers for new upload endpoints.

**Where to look next**
- Start edits in [app.py](app.py) and preview UI changes via [templates/free-trial.html](templates/free-trial.html). For front-end tweaks, modify files under `static/`.

If any section above is unclear or you want extra examples (prompt text edits, a unit-test scaffold, or a deployment systemd + nginx recipe), tell me which part to expand.
