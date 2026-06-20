# Karyakrit Lite

Karyakrit Lite is a lightweight Python assistant that can:

- create Excel files
- generate PowerPoint presentations
- draft email text files
- create, list, and complete tasks
- answer broader natural-language questions
- search the web and summarize result sets
- summarize local PDF files
- remember personal profile details and projects
- open social, messaging, and productivity apps
- search local files
- open common desktop apps
- accept optional voice input

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
show profile
add project Karyakrit AI desktop assistant
list projects
linkedin jobs python developer remote
open whatsapp
search file resume
open app notepad
voice 5
help
exit
```

## AI Configuration

You can configure providers in `.env`:

- `KARYAKRIT_ENABLE_AI=true`
- `GEMINI_API_KEY=...`
- `XAI_API_KEY=...`
- `OPENAI_API_KEY=...`
- `DEEPSEEK_API_KEY=...`
- `OLLAMA_HOST=http://localhost:11434`
- `OLLAMA_MODEL=phi3:mini`

If keys are missing or the network is unavailable, Karyakrit falls back to deterministic local templates.

## Local Models

For local use through Ollama, lightweight options you can try are:

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
