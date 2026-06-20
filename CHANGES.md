# Changes — Bug Fix Pass

## 🚨 Security (do this regardless of the code fixes)

- `.env` and `.env.example` contained **live API keys** (Gemini + OpenAI), and they
  were committed to git history with a real GitHub remote attached
  (`JSPN9400/Karyakrit-`). **Rotate/revoke both keys immediately** in the
  Google AI Studio and OpenAI dashboards — treat them as already compromised.
  Regenerating new keys is faster and safer than trying to scrub git history.
- `.env` and `.env.example` have been replaced with placeholder-only versions.
- The `.git` folder was removed from this delivered copy (since it contained
  the leaked keys in history). Re-init git fresh after rotating your keys.
- Added `.gitignore` covering `.env`, `__pycache__/`, `.venv/`, and generated
  output, so secrets and build artifacts can't be committed again.

## Bug fixes

1. **AI providers were never actually used** (`core/llm_provider.py`)
   `_validate_presentation_outline` / `_validate_email_draft` checked
   `isinstance(result, PresentationOutline)` / `isinstance(result, EmailDraft)`,
   but the API call methods returned raw `dict`s from `json.loads()`, never
   actual dataclass instances. Validation always failed, so every real API
   response was silently discarded and the app always fell back to the static
   template — even with valid API keys configured. Added `_to_presentation_outline`
   and `_to_email_draft` converters that turn the raw dict into the proper
   dataclass before validation.

2. **Excel generation ignored the user's request** (`modules/excel_generator.py`)
   `create_excel()` always wrote the same hardcoded Alice/Bob/Charlie table
   regardless of what was asked. Rewrote it to derive a topic (from the
   request or filename), ask the configured LLM provider for realistic
   columns/rows for that topic, and fall back to a clearly-labeled generic
   editable template if AI is unavailable/unconfigured.

3. **Missing `openpyxl` dependency** (`requirements.txt`)
   `pandas.to_excel()` needs the `openpyxl` engine; it wasn't listed, so a
   clean install would crash the first time Excel creation ran. Added it,
   plus version floors for all dependencies.

4. **Voice input crashed with a raw import error** (`core/voice_input.py`)
   `speech_recognition`/`pyaudio` were imported but not declared anywhere.
   Voice is now treated as optional: see `requirements-voice.txt`
   (`pip install -r requirements-voice.txt`), and the error message now
   tells you exactly what to run instead of a bare traceback.

5. **`open_app` was Windows-only with no guard** (`modules/app_control.py`)
   `os.startfile()` doesn't exist on macOS/Linux and would throw an
   `AttributeError`. Rewrote with per-OS app command tables (Windows/macOS/Linux)
   and clean error messages when an app isn't supported or isn't found.

6. **NLU misrouted some commands** (`core/nlu_engine.py`)
   - `"open notepad"` / `"open app notepad"` were being silently rewritten to
     `"open note"` because `notepad` fuzzy-matched the `note` synonym at 73%
     similarity, routing to `create_note` instead of `open_app`. Added a
     protected-word list (app names, `marks`/`grades`/`scores`) that's exempt
     from fuzzy synonym collapsing.
   - Removed the ambiguous `'calc'` entry from the `excel` synonym list — it
     collided with the unrelated English word `call` (75% similarity),
     misrouting commands like `"task ... client call"` into `create_excel`.
   - `_extract_entities`'s topic fallback only stripped command verbs
     (`create`, `make`, ...), so `"create excel student marks"` produced the
     topic `"excel student marks"` instead of `"student marks"`. It now also
     strips synonym-category nouns (`excel`, `presentation`, `email`, etc.).

## Verification performed

- Fresh virtualenv install of `requirements.txt` — no missing packages.
- Ran `test_nlu.py` — same intents/entities as the original test expectations,
  plus new cases for `open_app` and `marks`-collision scenarios.
- Ran a full CLI session creating an Excel file, a presentation, an email
  draft, and exercising `open_app` — all completed without crashing.
- Opened and verified the generated `.xlsx` (via pandas) and `.pptx`
  (via python-pptx) files were structurally valid.

## Known limitations (not addressed — out of scope for this pass)

- `create_note`, `create_task`, `list_tasks`, `complete_task`,
  `open_website`, `file_search`, `file_organize` are still placeholder
  stubs that print a message and do nothing.
- The NLU's regex-based entity extraction (e.g. recipient/subject parsing
  for emails) is fairly naive and can produce odd results on complex
  sentences (e.g. "leave request mail likho" → recipient inferred oddly).
  This wasn't part of the reported bug list, so it was left as-is beyond
  the specific `marks`/`calc` collisions that blocked the requested fixes.
