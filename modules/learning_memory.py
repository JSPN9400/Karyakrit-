"""
Persistent learning memory for chat history and typo correction.
"""

import json
import os
import re
from collections import deque
from datetime import datetime
from typing import Deque, Dict, List


class LearningMemory:
    """Store conversation history and learned word corrections."""

    def __init__(self, base_dir: str = None):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.base_dir = base_dir or os.path.join(project_root, "data")
        os.makedirs(self.base_dir, exist_ok=True)
        self.chat_path = os.path.join(self.base_dir, "chat_history.json")
        self.words_path = os.path.join(self.base_dir, "learned_words.json")

    def apply_corrections(self, text: str) -> str:
        """Apply learned typo corrections token by token."""
        corrections = self._load_json(self.words_path, {})
        if not corrections:
            return text

        tokens = text.split()
        corrected: List[str] = []
        for token in tokens:
            key = re.sub(r"[^\w.-]", "", token.lower())
            replacement = corrections.get(key)
            if replacement:
                prefix = token[: len(token) - len(token.lstrip("([{\"'"))]
                suffix = token[len(token.rstrip(")]}\"',.!?")) :]
                corrected.append(f"{prefix}{replacement}{suffix}")
            else:
                corrected.append(token)
        return " ".join(corrected)

    def learn_from_normalization(self, raw_text: str, normalized_text: str):
        """Learn stable word corrections from successful normalization."""
        raw_tokens = [re.sub(r"[^\w.-]", "", token.lower()) for token in raw_text.split()]
        normalized_tokens = [re.sub(r"[^\w.-]", "", token.lower()) for token in normalized_text.split()]
        corrections = self._load_json(self.words_path, {})

        for raw, normalized in zip(raw_tokens, normalized_tokens):
            if not raw or not normalized or raw == normalized:
                continue
            if len(raw) < 3:
                continue
            corrections[raw] = normalized

        self._save_json(self.words_path, corrections)

    def manual_learn(self, wrong_word: str, correct_word: str):
        """Save a manual typo correction."""
        corrections = self._load_json(self.words_path, {})
        corrections[wrong_word.strip().lower()] = correct_word.strip().lower()
        self._save_json(self.words_path, corrections)

    def show_learned_words(self) -> str:
        """Format learned corrections for display."""
        corrections = self._load_json(self.words_path, {})
        if not corrections:
            return "No learned typo corrections yet."
        lines = ["Learned corrections:"]
        for wrong, correct in sorted(corrections.items()):
            lines.append(f"- {wrong} -> {correct}")
        return "\n".join(lines)

    def log_chat(self, user_input: str, effective_input: str, output: str):
        """Persist one interaction."""
        history = self._load_json(self.chat_path, [])
        history.append(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "user_input": user_input,
                "effective_input": effective_input,
                "assistant_output": output,
            }
        )
        history = history[-200:]
        self._save_json(self.chat_path, history)

    def recent_history_text(self, limit: int = 8) -> str:
        """Return recent interactions as text context."""
        history = self._load_json(self.chat_path, [])
        if not history:
            return "No prior chat history."

        recent: Deque[Dict] = deque(history, maxlen=limit)
        lines: List[str] = []
        for item in recent:
            lines.append(f"User: {item['user_input']}")
            lines.append(f"Assistant: {item['assistant_output']}")
        return "\n".join(lines)

    def show_recent_history(self, limit: int = 10) -> str:
        """Format recent chat history for display."""
        history = self._load_json(self.chat_path, [])
        if not history:
            return "No chat history yet."
        lines = ["Recent chat memory:"]
        for item in history[-limit:]:
            lines.append(f"- {item['timestamp']} | {item['user_input']} -> {item['assistant_output']}")
        return "\n".join(lines)

    def _load_json(self, path: str, default):
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _save_json(self, path: str, payload):
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=True)
