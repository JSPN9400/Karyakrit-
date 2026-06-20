"""
Browser-based local GUI for Karyakrit.
"""

import json
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from core.assistant_service import HELP_TEXT, execute_command


HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Karyakrit Assistant</title>
  <style>
    :root {
      --bg: #08111f;
      --panel: #101a2b;
      --panel-2: #0d1523;
      --text: #eff6ff;
      --muted: #a5b4cc;
      --accent: #f97316;
      --accent-2: #22c55e;
      --border: #243042;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(249, 115, 22, 0.22), transparent 30%),
        radial-gradient(circle at top right, rgba(34, 197, 94, 0.16), transparent 26%),
        linear-gradient(160deg, #08111f, #111c31 55%, #08111f);
      min-height: 100vh;
    }
    .wrap {
      max-width: 1080px;
      margin: 0 auto;
      padding: 32px 20px 40px;
    }
    .hero {
      display: grid;
      grid-template-columns: 1.4fr 1fr;
      gap: 20px;
      align-items: stretch;
    }
    .card {
      background: rgba(16, 26, 43, 0.92);
      border: 1px solid var(--border);
      border-radius: 22px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.28);
    }
    .hero-copy {
      padding: 28px;
    }
    h1 {
      margin: 0;
      font-size: clamp(2rem, 4vw, 3.6rem);
      line-height: 0.95;
      letter-spacing: -0.04em;
    }
    .sub {
      margin-top: 14px;
      color: var(--muted);
      font-size: 1rem;
      line-height: 1.6;
      max-width: 54ch;
    }
    .badge-row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 18px;
    }
    .badge {
      border: 1px solid rgba(255,255,255,0.08);
      background: rgba(255,255,255,0.03);
      color: #dbeafe;
      padding: 8px 12px;
      border-radius: 999px;
      font-size: 0.92rem;
    }
    .quick {
      padding: 24px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }
    .quick h2, .panel h2 {
      margin: 0 0 14px;
      font-size: 1.05rem;
      color: #fdba74;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .quick-grid {
      display: grid;
      gap: 10px;
    }
    button, .run-btn {
      border: 0;
      border-radius: 14px;
      padding: 12px 16px;
      cursor: pointer;
      background: linear-gradient(135deg, var(--accent), #fb7185);
      color: white;
      font-weight: 700;
      transition: transform 120ms ease, opacity 120ms ease;
    }
    button:hover, .run-btn:hover {
      transform: translateY(-1px);
      opacity: 0.96;
    }
    .panel {
      margin-top: 20px;
      padding: 24px;
    }
    .command-row {
      display: grid;
      grid-template-columns: 1fr auto auto;
      gap: 12px;
      margin-bottom: 16px;
    }
    input {
      width: 100%;
      padding: 14px 16px;
      border-radius: 14px;
      border: 1px solid var(--border);
      background: var(--panel-2);
      color: var(--text);
      font-size: 1rem;
    }
    .voice-btn {
      background: linear-gradient(135deg, var(--accent-2), #14b8a6);
    }
    .console {
      background: #020617;
      border: 1px solid #182235;
      border-radius: 18px;
      padding: 18px;
      min-height: 360px;
      white-space: pre-wrap;
      font-family: Consolas, monospace;
      line-height: 1.55;
      overflow: auto;
    }
    .help {
      margin-top: 14px;
      color: var(--muted);
      font-size: 0.95rem;
      white-space: pre-wrap;
    }
    @media (max-width: 820px) {
      .hero { grid-template-columns: 1fr; }
      .command-row { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="card hero-copy">
        <h1>Karyakrit<br>Assistant</h1>
        <p class="sub">Run the same commands from a cleaner local GUI. Create spreadsheets, presentations, draft emails, launch apps, and test voice input without leaving the browser.</p>
        <div class="badge-row">
          <div class="badge">CLI + GUI</div>
          <div class="badge">Localhost only</div>
          <div class="badge">No extra GUI packages</div>
        </div>
      </div>
      <div class="card quick">
        <h2>Quick Actions</h2>
        <div class="quick-grid">
          <button onclick="runCommand('help')">Help</button>
          <button onclick="runCommand('create excel student marks')">Create Excel</button>
          <button onclick="runCommand('create presentation climate change')">Create Presentation</button>
          <button onclick="runCommand('open app notepad')">Open Notepad</button>
        </div>
      </div>
    </section>

    <section class="card panel">
      <h2>Command Console</h2>
      <div class="command-row">
        <input id="commandInput" placeholder="Type a command like: create excel sales report">
        <button class="run-btn" onclick="submitInput()">Run Command</button>
        <button class="voice-btn" onclick="runCommand('voice 5')">Voice</button>
      </div>
      <div id="console" class="console">Karyakrit GUI is ready.
Type a command below or use a quick action.</div>
      <div class="help">%HELP_TEXT%</div>
    </section>
  </div>

  <script>
    const input = document.getElementById('commandInput');
    const consoleBox = document.getElementById('console');

    input.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        submitInput();
      }
    });

    function appendLine(text) {
      consoleBox.textContent += "\\n\\n" + text;
      consoleBox.scrollTop = consoleBox.scrollHeight;
    }

    function submitInput() {
      const value = input.value.trim();
      if (!value) {
        appendLine('Please enter a command.');
        return;
      }
      input.value = '';
      runCommand(value);
    }

    async function runCommand(command) {
      appendLine('> ' + command);
      try {
        const response = await fetch('/api/command', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command })
        });
        const data = await response.json();
        appendLine(data.output || 'Command completed.');
      } catch (error) {
        appendLine('Error: ' + error.message);
      }
    }
  </script>
</body>
</html>
"""


def _render_html() -> bytes:
    return HTML_PAGE.replace("%HELP_TEXT%", HELP_TEXT).encode("utf-8")


class KaryakritHandler(BaseHTTPRequestHandler):
    """HTTP handler for the local GUI."""

    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        content = _render_html()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        if self.path != "/api/command":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)

        try:
            payload = json.loads(raw_body.decode("utf-8"))
            command = str(payload.get("command", ""))
            output = execute_command(command)
            body = json.dumps({"output": output}).encode("utf-8")
            self.send_response(HTTPStatus.OK)
        except Exception as exc:
            body = json.dumps({"output": f"Error: {exc}"}).encode("utf-8")
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)

        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):
        return


def _open_browser(url: str):
    webbrowser.open(url, new=1)


def run_gui(host: str = "127.0.0.1", port: int = 8765):
    """Run the local browser GUI."""
    server = ThreadingHTTPServer((host, port), KaryakritHandler)
    url = f"http://{host}:{port}"
    print(f"Karyakrit GUI running at {url}")
    print("Press Ctrl+C to stop the server.")

    opener = threading.Timer(0.8, _open_browser, args=(url,))
    opener.daemon = True
    opener.start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down GUI server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    run_gui()
