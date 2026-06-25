"""
Shared command execution service for CLI and GUI entrypoints.
"""

from contextlib import redirect_stdout
from io import StringIO

from core.command_parser import parse_command
from core.intent_engine import detect_intent
from core.task_router import route_task
from core.voice_input import listen_from_mic
from modules.learning_memory import LearningMemory
from modules.python_assistant import run_python_file, run_python_snippet


learning_memory = LearningMemory()

# Tracks whether the *next* command in this process should be treated as a
# confirmed "yes, run that code" response. Pending code/file is stored here
# between the request and the confirmation, since execute_command is
# stateless per call otherwise.
_pending_python_execution = {"kind": None, "payload": None}


HELP_TEXT = """Commands:
- create excel <filename or topic>
- create presentation <topic>
- create task <task name>
- list tasks
- complete task <task name>
- ask <question>
- search web <query>
- summarize pdf <path>
- remember about me <fact>
- show memory
- show learned words
- learn typo <wrong> = <correct>
- python run <code>      (asks for confirmation before executing)
- python file <path>     (asks for confirmation before executing)
- show profile
- add project <name>
- list projects
- linkedin jobs <query>
- open whatsapp / linkedin / github / youtube
- search file <name>
- open website <domain>
- open app <app_name>
- list apps
- voice <seconds>
- exit"""


def _start_python_confirmation(kind: str, payload: str) -> str:
    """Stage a pending python execution and ask the user to confirm it."""
    _pending_python_execution["kind"] = kind
    _pending_python_execution["payload"] = payload
    if kind == "snippet":
        preview = payload if len(payload) <= 200 else payload[:200] + "..."
        return (
            "This will run the following Python code on your machine with your "
            "user privileges:\n"
            f"---\n{preview}\n---\n"
            "Type 'yes' to run it, or anything else to cancel."
        )
    return (
        f"This will execute the Python file '{payload}' on your machine with your "
        "user privileges.\n"
        "Type 'yes' to run it, or anything else to cancel."
    )


def _clear_pending_python_execution():
    _pending_python_execution["kind"] = None
    _pending_python_execution["payload"] = None


def execute_command(raw_text: str) -> str:
    """
    Execute a Karyakrit command and return human-readable output.

    Args:
        raw_text: Raw user input.

    Returns:
        str: Collected output messages for the caller to display.
    """
    user_input = (raw_text or "").strip()
    if not user_input:
        return "Please enter a command."

    # If a python run/file confirmation is pending, this input is the
    # yes/no answer to it, not a new command.
    if _pending_python_execution["kind"]:
        kind = _pending_python_execution["kind"]
        payload = _pending_python_execution["payload"]
        _clear_pending_python_execution()
        if user_input.strip().lower() in {"yes", "y", "confirm"}:
            if kind == "snippet":
                result = run_python_snippet(payload)
            else:
                result = run_python_file(payload)
            learning_memory.log_chat(raw_text, raw_text, result)
            return result
        return "Cancelled. No code was executed."

    original_input = user_input
    user_input = learning_memory.apply_corrections(user_input)

    lowered = user_input.lower()
    if lowered == "help":
        return HELP_TEXT
    if lowered == "exit":
        return "Goodbye!"

    if lowered.startswith("python run "):
        code = user_input[len("python run "):]
        return _start_python_confirmation("snippet", code)
    if lowered.startswith("python file "):
        path = user_input[len("python file "):].strip()
        return _start_python_confirmation("file", path)

    if lowered.startswith("voice"):
        parts = user_input.split()
        secs = 5
        if len(parts) > 1 and parts[1].isdigit():
            secs = int(parts[1])
        try:
            transcribed = listen_from_mic(timeout=secs)
        except Exception as exc:
            return f"Voice input failed: {exc}"

        if not transcribed:
            return "I couldn't understand the voice input."
        user_input = transcribed

    parsed = parse_command(user_input)
    if not parsed:
        return "Invalid command. Type 'help' for options."

    intent = detect_intent(parsed)
    if not intent:
        return "Intent not recognized."

    captured = StringIO()
    try:
        with redirect_stdout(captured):
            route_task(intent, parsed)
    except Exception as exc:
        output = captured.getvalue().strip()
        if output:
            final_output = f"{output}\nError: {exc}"
            learning_memory.log_chat(original_input, user_input, final_output)
            return final_output
        final_output = f"Error: {exc}"
        learning_memory.log_chat(original_input, user_input, final_output)
        return final_output

    output = captured.getvalue().strip()
    if lowered.startswith("voice"):
        output = f"You said: {user_input}\n{output}".strip()
    final_output = output or "Command completed."
    learning_memory.log_chat(original_input, user_input, final_output)
    if original_input.lower() != user_input.lower():
        final_output = f"Interpreted command: {user_input}\n{final_output}"
    return final_output
