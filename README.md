# Karyakrit Lite

Karyakrit Lite is a lightweight Python assistant that can:

- create Excel files
- generate PowerPoint presentations
- draft email text files
- create, list, and complete tasks
- answer broader natural-language questions
- search the web and summarize result sets
- summarize local PDF files
- remember personal profile details and projects, and answer questions about you from that saved data
- open social, messaging, and productivity apps
- search local files
- open any installed desktop app by approximate name (not just a fixed list)
- accept optional voice input
- run a Python snippet or file on request (asks for confirmation first)

It now includes both a CLI and a browser-based local GUI.

## Features

- CLI workflow for quick command-based use
- Browser-based local GUI with no extra GUI dependencies
- AI-assisted content generation with fallback mode
- Offline-friendly fallback behavior when AI providers are unavailable
- Persistent task storage in `data/tasks.json`
- Local personal profile memory in `data/profile.json`
- Output folders for generated spreadsheets, presentations, and email drafts

## Project Structure

```text
Karyakrit-/
|- core/
|- modules/
|- data/
|- output/
|- main.py
|- gui.py
|- requirements.txt
```

## Setup

1. Create a virtual environment:

```powershell
python -m venv .venv
```

2. Activate it on Windows:

```powershell
.venv\Scripts\activate
```

3. Install the main dependencies:

```powershell
pip install -r requirements.txt
```

4. Optional: install voice dependencies:

```powershell
pip install -r requirements-voice.txt
```

5. Copy `.env.example` to `.env` and add any API keys you want to use.

## Run The App

Run the CLI:

```powershell
python main.py
```

Run the GUI:

```powershell
python gui.py
```

This starts a local server and opens the interface in your browser.

Or launch the GUI from the main entrypoint:

```powershell
python main.py --gui
```

## Example Commands

```text
create excel student marks
create presentation climate change
create task finish client proposal
list tasks
complete task finish client proposal
ask how should I structure a weekly work plan
search web latest AI productivity tools
summarize pdf data/sample.pdf
remember about me I am a Python developer from Delhi
tell me about myself
what is my profession
show profile
add project Karyakrit AI desktop assistant
list projects
linkedin jobs python developer remote
open whatsapp
search file resume
open app notepad
open app spotify
list apps
python run print("hello")
voice 5
help
exit
```

`open app <name>` first checks a small list of known aliases, then searches
the apps actually installed on your system (Start Menu shortcuts on Windows,
`/Applications` on macOS, `.desktop` entries on Linux) using approximate
name matching - so you can open most installed apps, not just a fixed list.
Use `list apps` to see what was discovered.

`python run <code>` and `python file <path>` execute real Python on your
machine and will always ask for an explicit "yes" confirmation first, since
they run with your full user privileges.

## AI Configuration

You can configure providers in `.env`. All are optional - configure as many
or as few as you like; Karyakrit tries them in the order listed in
`KARYAKRIT_ONLINE_PROVIDER_ORDER` and uses the first one that's configured
and succeeds:

- `KARYAKRIT_ENABLE_AI=true`
- `GEMINI_API_KEY=...` (Google Gemini)
- `XAI_API_KEY=...` (xAI's Grok)
- `OPENAI_API_KEY=...`
- `DEEPSEEK_API_KEY=...`
- `ANTHROPIC_API_KEY=...` (Claude)
- `GROQ_API_KEY=...` (Groq's fast inference - a different company from xAI's Grok, despite the similar name; has a free tier)
- `OPENROUTER_API_KEY=...` (gateway to many hosted models behind one API key, including some free ones)
- `OLLAMA_HOST=http://localhost:11434` (free, fully local, no API key needed)
- `OLLAMA_MODEL=phi3:mini`

Model names per provider can be overridden too (see `.env.example` for the
full list, e.g. `GEMINI_MODEL`, `OPENROUTER_MODEL`).

If no keys are configured, none are reachable, or the network is unavailable,
Karyakrit falls back to deterministic local templates - the app always works,
just with simpler generated content.

## Local Models

For local use through Ollama (free, no API key, runs on your machine),
lightweight options you can try are:

- `phi3:mini`
- `llama3.2:1b`
- `qwen2.5:1.5b`

Change `OLLAMA_MODEL` in `.env` to switch local models.

## Output Locations

- Excel files: `data/`
- Presentations: `output/presentations/`
- Email drafts: `output/emails/`

## Notes

- Voice input is optional and may require `PyAudio` support on Windows.
- App launching depends on the operating system and available installed apps.
- Some intents in the router are still placeholders and currently print status messages only.
- `open whatsapp` / `open linkedin` only open the website in your browser, where you log in yourself.
  There is no automated/real account access (reading messages, connections, etc.) - WhatsApp has no
  public personal-account API, and LinkedIn's API requires partner approval. Building unofficial
  scraping-based access to either would risk violating their Terms of Service, so it isn't included.
- `python run` / `python file` execute real code with your full user privileges. Karyakrit always asks
  for explicit confirmation before running anything from these commands.
