"""
Helpers Module

Utility functions.
"""

def log_message(message):
    """
    Simple logging function.

    Args:
        message (str): Message to log.
    """
    print(f"[LOG] {message}")

def validate_filename(filename):
    """
    Basic filename validation.

    Args:
        filename (str): Filename to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not filename or '/' in filename or '\\' in filename:
        return False
    return True