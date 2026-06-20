"""
Intent Engine Module

Detects user intent using the NLU engine for robust understanding.
"""

from core.nlu_engine import NLUEngine

# Initialize NLU engine
nlu_engine = NLUEngine()

def detect_intent(parsed_command):
    """
    Detect intent from parsed command using NLU.

    Args:
        parsed_command (dict): Parsed command with 'command' and 'args'.

    Returns:
        str: Detected intent, or None if not recognized.
    """
    # Reconstruct full command text
    full_command = parsed_command['command'] + ' ' + ' '.join(parsed_command['args'])

    # Process with NLU
    nlu_result = nlu_engine.process_command(full_command)

    # Return the detected intent
    return nlu_result.detected_intent