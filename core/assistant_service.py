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


learning_memory = LearningMemory()


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
- python run <code>
- python file <path>
- show profile
- add project <name>
- list projects
- linkedin jobs <query>
- open whatsapp / linkedin / github / youtube
- search file <name>
- open website <domain>
- open app <app_name>
- voice <seconds>
- exit"""


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

    original_input = user_input
    user_input = learning_memory.apply_corrections(user_input)

    lowered = user_input.lower()
    if lowered == "help":
        return HELP_TEXT
    if lowered == "exit":
        return "Goodbye!"

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
