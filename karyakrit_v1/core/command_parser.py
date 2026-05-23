"""
Command Parser Module

Processes raw text input into structured commands.
"""

def parse_command(raw_text):
    """
    Parse raw text into command and arguments.

    Args:
        raw_text (str): The user's input text.

    Returns:
        dict: Parsed command with 'command' and 'args' keys, or None if invalid.
    """
    parts = raw_text.split()
    if not parts:
        return None

    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []

    return {
        'command': command,
        'args': args
    }