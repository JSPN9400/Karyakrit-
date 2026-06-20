#!/usr/bin/env python3
r"""
Karyakrit Lite v1 - Lightweight AI Assistant

Instructions:
1. Create virtual environment: python -m venv .venv
2. Activate: .venv\Scripts\activate (Windows)
3. Install dependencies: pip install -r requirements.txt
4. Run: python main.py

This is a simple CLI-based AI assistant that can create Excel files, presentations, and control apps.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import sys

from core.assistant_service import HELP_TEXT, execute_command


def launch_gui():
    """Start the desktop GUI entrypoint."""
    from gui import run_gui

    run_gui()

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        launch_gui()
        return

    print("Welcome to Karyakrit Lite v1!")
    print("Type 'help' for commands, 'exit' to quit, or run 'python main.py --gui'.")

    while True:
        try:
            user_input = input("Karyakrit> ").strip()
            output = execute_command(user_input)
            print(output)
            if user_input.lower() == 'exit':
                break

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
