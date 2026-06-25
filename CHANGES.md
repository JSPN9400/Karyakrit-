# Changes Log

## Session 2 — NLU power-up, more AI models, OS-wide app opening, profile Q&A

### 🚨 Security

- `.git` history still contained the originally-leaked API keys from session 1
  and a committed `.venv` folder. Removed `.git` from this delivered copy again
  — re-init git fresh once your keys are rotated (you confirmed `.env` is now
  clean, but the old commits should not be pushed anywhere).
- `.gitignore` was missing from this upload (likely dropped during other
  changes) — re-added, covering `.env`, `__pycache__/`, `.venv/`, and
  generated output/profile/task data.
- `python run` / `python file` were defined in `modules/python_assistant.py`
  but never wired into the app — meaning they were dead code, not yet a live
  risk. Wired them up **with** a mandatory confirmation step from the start:
  the assistant always shows the code/file and requires an explicit "yes"
  before executing anything, since these run with full user privileges.

### NLU fixes (this session)

- **Regex word-boundary bug**: entity patterns like `(?:on|about|for|regarding)`
  had no `\b` word boundaries, so "on" matched inside the word "presentati**on**"
  itself, corrupting topic extraction (e.g. "presentation on indian climate"
  -> topic became "on indian climate" instead of "indian climate"). Fixed by
  adding `\b` boundaries to all entity regex patterns.
- **Hinglish filler words leaking into entities**: words like `do`, `ka`, `ko`,
  `karo` (grammatical filler in Hindi/Hinglish phrasing) were ending up inside
  extracted topics/task titles (e.g. "excel bana do contacts ka" -> topic
  "do contacts ka" instead of "contacts"). Added a filler-word stripper applied
  to all phrase-type entities.
- **`manager` fuzzy-collision**: the word "manager" was being silently
  rewritten to "organize" (92% match against the "manage" synonym), breaking
  email recipient extraction entirely (e.g. "mail draft karo manager ko" lost
  the recipient). Added "manager" and similar common-recipient words (client,
  colleague, team, boss, hr, recruiter) to the protected-word list.
- **Hinglish recipient word order**: "manager ko" (Hindi: "to manager") wasn't
  recognized as a recipient pattern since only English "to"/"for" were
  supported. Added `ko` as a recognized recipient marker in both word orders.
- **Profile fact corruption (data-integrity bug)**: `remember about me <fact>`
  extracted the fact from the *normalized* (synonym-rewritten) text instead of
  the original wording, so saved facts could be silently corrupted - e.g.
  "I **like** cricket" became "I **note** cricket" (since "like" fuzzy-matches
  the Hindi "likh"/note synonym at 75%). This is the most important fix this
  session: it affected stored user data, not just command routing. Fixed by
  threading the raw, pre-normalization text through to entity extraction
  specifically for free-text fields (`profile_fact`, `project_name`), with
  multiple raw-prefix variants tried since the normalized prefix itself can
  differ from the literal raw prefix (e.g. "remember about me" normalizes to
  "remember profile me").
- **New `ask_about_me` intent**: phrases like "tell me about myself", "what is
  my profession", "mera naam kya hai" are now recognized explicitly and always
  answered from saved profile data (grounded via AI prompt when a provider is
  reachable, or directly from stored facts when none is - see below). Required
  checking against raw (pre-normalization) text too, since words like "about"/
  "myself" can get fuzzy-rewritten before the normalized text is checked.
- Added a `list apps` / `show apps` intent.

### More AI models / providers

- Fixed two **deprecated/retired model names** that were silently causing
  every real API call to fail even with valid keys: `gemini-pro` (Gemini
  retired this in favor of e.g. `gemini-2.0-flash`) and `grok-beta` (xAI
  retired this in favor of e.g. `grok-2-latest`). Both are now configurable
  via `GEMINI_MODEL` / `XAI_MODEL` env vars with updated defaults, and every
  other provider's model is similarly configurable.
- Added three new providers: **Anthropic Claude**, **Groq** (fast inference,
  has a free tier - a different company from xAI's Grok despite the similar
  name, both are supported separately), and **OpenRouter** (a gateway to many
  hosted models behind one API key, including some free ones).
- Refactored the 4 previously-duplicated provider-dispatch if/elif chains
  (presentation, email, assistant-answer, summary generation) into a single
  `_call_provider()` method, since the duplication was the root cause of a
  bug where `excel_generator.py` had its own incomplete copy missing `deepseek`
  entirely. New providers now only need to be added in one place.
- Added a proper `AssistantAnswer.is_fallback` flag so callers can reliably
  detect when the deterministic (non-AI) template was used, instead of
  string-matching the answer text.

### OS-wide app opening (`modules/app_control.py`)

- Previously `open_app` only recognized a small hardcoded list of apps per OS.
  Rewrote it to actually scan the OS's normal "installed apps" locations:
  - **Windows**: Start Menu shortcut folders (`.lnk` files)
  - **macOS**: `/Applications` and `~/Applications` (`.app` bundles)
  - **Linux**: standard XDG `.desktop` directories
  Approximate/fuzzy name matching finds the closest installed app to what was
  typed (e.g. "vs code" finds "Visual Studio Code"). Results are cached for
  5 minutes to avoid rescanning on every command. Verified live against this
  environment's actual LibreOffice install.
  - Found and fixed a real hang: launching a GUI app with the launching
    process's stdout/stderr inherited could block if the app's startup
    output filled the pipe buffer (reproduced with LibreOffice). Fixed by
    fully detaching all launched processes (`stdout=DEVNULL`, `start_new_session`).
  - Added a `list apps` command to show what's discoverable.

### Profile-aware "ask about me" answering

- New `ask_about_me` intent (see NLU section above) grounds answers in saved
  profile data. When a real AI provider is reachable, the model is given the
  saved facts and instructed not to invent anything beyond them. When no
  provider actually succeeds (detected via the new `is_fallback` flag, not
  by guessing whether keys/Ollama are configured), it shows the saved profile
  data directly instead of a generic, profile-blind template.

### WhatsApp / LinkedIn - explicitly out of scope, with reasoning

Real account access (reading messages/connections via OAuth/API) was
requested but not built because:
- WhatsApp has no public personal-account API (only a separate Business API
  for business accounts, with its own approval process).
- LinkedIn's API requires partner approval and doesn't offer a general
  personal-account "read your connections/messages" flow.
- Building unauthorized scraping/automation for either risks violating their
  Terms of Service and account bans.

Current behavior (kept as-is, per explicit confirmation): `open whatsapp` /
`open linkedin` open the website in your default browser, where you log in
yourself.

---

## Session 1 — Initial bug-fix pass

### Security

- `.env` and `.env.example` contained live API keys (Gemini + OpenAI), and
  were committed to git history with a real GitHub remote attached. Keys were
  rotated by the user; placeholders only going forward.
- Added `.gitignore` covering `.env`, `__pycache__/`, `.venv/`, and generated
  output.

### Bug fixes

1. AI providers were never actually used due to an `isinstance()` validation
   bug comparing raw dicts against dataclass types - added proper dict-to-
   dataclass converters.
2. Excel generation ignored the user's request, always producing the same
   hardcoded sample data - rewritten to generate topic-relevant data via AI,
   with a generic fallback template.
3. Missing `openpyxl` dependency would crash a clean install on first Excel
   creation - added to `requirements.txt`.
4. Voice input crashed with a raw import error - now optional via
   `requirements-voice.txt` with a clear install message.
5. `open_app` was Windows-only and crashed on macOS/Linux - made cross-platform
   (later superseded by full OS-wide discovery in session 2).
6. Several NLU misroutes fixed (`notepad` vs `note` collision, `marks` vs
   `mark` collision, `calc` vs `call` collision, topic entity leaking command
   words).
