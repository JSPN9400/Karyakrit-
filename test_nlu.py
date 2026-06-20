#!/usr/bin/env python3
"""
Test script for NLU Engine
"""

from core.nlu_engine import NLUEngine

def test_nlu():
    nlu = NLUEngine()

    test_commands = [
        "make presetion on inidan climet",
        "ek ppt bana do on environment",
        "mail draft karo manager ko",
        "excel bana do contacts ka",
        "leave request mail likho",
        "task bana do kal client call",
        "chrome kholo",
        "downloads folder organize karo",
        "create presentation on climate change",
        "open gmail",
        "find my resume file"
    ]

    for cmd in test_commands:
        result = nlu.process_command(cmd)
        print(f"Command: {cmd}")
        print(f"  Intent: {result.detected_intent} (confidence: {result.confidence:.2f})")
        print(f"  Entities: {result.extracted_entities}")
        if result.fallback_message:
            print(f"  Fallback: {result.fallback_message}")
        print()

if __name__ == "__main__":
    test_nlu()