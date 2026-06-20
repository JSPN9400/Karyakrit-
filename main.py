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
from core.command_parser import parse_command
from core.intent_engine import detect_intent
from core.task_router import route_task
from core.voice_input import listen_from_mic

def main():
    print("Welcome to Karyakrit Lite v1!")
    print("Type 'help' for commands or 'exit' to quit.")

    while True:
        try:
            user_input = input("Karyakrit> ").strip()
            if user_input.lower() == 'exit':
                print("Goodbye!")
                break
            elif user_input.lower() == 'help':
                print("Commands:")
                print("- create excel <filename>")
                print("- create presentation <filename>")
                print("- open app <app_name>")
                print("- voice <seconds>  (record and transcribe from microphone)")
                print("- exit")
                continue

            # Voice input trigger: 'voice' or 'voice <seconds>'
            if user_input.lower().startswith('voice'):
                parts = user_input.split()
                secs = 5
                if len(parts) > 1 and parts[1].isdigit():
                    secs = int(parts[1])
                try:
                    transcribed = listen_from_mic(timeout=secs)
                    print(f"You said: {transcribed}")
                    user_input = transcribed
                except Exception as e:
                    print(f"Voice input failed: {e}")
                    continue

            # Parse command
            parsed = parse_command(user_input)
            if not parsed:
                print("Invalid command. Type 'help' for options.")
                continue

            # Detect intent
            intent = detect_intent(parsed)
            if not intent:
                print("Intent not recognized.")
                continue

            # Route task
            route_task(intent, parsed)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()