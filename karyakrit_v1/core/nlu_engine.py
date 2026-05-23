"""
NLU Engine Module

Lightweight hybrid NLU system for understanding imperfect user commands.
Uses rule-based normalization, synonym mapping, fuzzy matching, and entity extraction.
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)


@dataclass
class NLUResult:
    """Structured result from NLU processing."""
    normalized_text: str
    detected_intent: str
    confidence: float
    extracted_entities: Dict[str, str]
    fallback_message: Optional[str] = None


class NLUEngine:
    """Lightweight NLU engine for office assistant commands."""

    def __init__(self):
        """Initialize the NLU engine with synonyms and patterns."""
        # Synonym mappings for common variations
        self.synonyms = {
            'presentation': ['presentation', 'presetion', 'ppt', 'slides', 'slide', 'powerpoint'],
            'excel': ['excel', 'xlsx', 'sheet', 'spreadsheet', 'calc'],
            'email': ['email', 'mail', 'gmail', 'outlook', 'message'],
            'task': ['task', 'todo', 'kaam', 'work', 'assignment'],
            'note': ['note', 'notes', 'likh', 'likho', 'banao'],
            'open': ['open', 'kholo', 'start', 'launch', 'run'],
            'create': ['create', 'make', 'bana', 'banao', 'generate'],
            'draft': ['draft', 'likh', 'write', 'compose'],
            'list': ['list', 'show', 'display', 'dekhao'],
            'complete': ['complete', 'finish', 'done', 'mark'],
            'search': ['search', 'find', 'dhundo'],
            'organize': ['organize', 'arrange', 'sort', 'manage'],
            'app': ['app', 'application', 'software', 'program'],
            'website': ['website', 'site', 'web', 'page'],
            'file': ['file', 'files', 'document', 'docs'],
            'folder': ['folder', 'directory', 'dir']
        }

        # Intent keywords for fuzzy matching
        self.intent_keywords = {
            'create_presentation': ['presentation', 'ppt', 'slides'],
            'create_excel': ['excel', 'sheet', 'spreadsheet'],
            'draft_email': ['email', 'mail', 'draft'],
            'create_note': ['note', 'notes', 'write'],
            'create_task': ['task', 'todo', 'kaam'],
            'list_tasks': ['list', 'show', 'tasks', 'todos'],
            'complete_task': ['complete', 'finish', 'done', 'task'],
            'open_app': ['open', 'app', 'launch', 'start'],
            'open_website': ['open', 'website', 'site', 'web'],
            'file_search': ['search', 'find', 'file', 'files'],
            'file_organize': ['organize', 'arrange', 'folder', 'files']
        }

        # Entity extraction patterns
        self.entity_patterns = {
            'slide_count': re.compile(r'(\d+)\s*(?:slide|slides)', re.IGNORECASE),
            'topic': re.compile(r'(?:on|about|for|regarding)\s+(.+)', re.IGNORECASE),
            'recipient': re.compile(r'(?:to|for)\s+(\w+)', re.IGNORECASE),
            'subject': re.compile(r'(?:subject|regarding|about)\s+(.+)', re.IGNORECASE),
            'app_name': re.compile(r'(?:open|start|launch)\s+(.+)', re.IGNORECASE),
            'file_name': re.compile(r'(?:file|folder)\s+(.+)', re.IGNORECASE),
            'task_title': re.compile(r'(?:task|todo)\s+(.+)', re.IGNORECASE)
        }

        logger.info("NLU Engine initialized")

    def process_command(self, raw_text: str) -> NLUResult:
        """
        Process a raw command and return structured NLU result.

        Args:
            raw_text: The user's raw input text.

        Returns:
            NLUResult: Structured understanding of the command.
        """
        logger.info(f"Processing command: {raw_text}")

        # Normalize text
        normalized = self._normalize_text(raw_text)

        # Detect intent
        intent, confidence = self._detect_intent(normalized)

        # Extract entities
        entities = self._extract_entities(normalized)

        # Generate fallback message if confidence is low
        fallback = None
        if confidence < 0.6:
            fallback = f"I'm not entirely sure what you mean by '{raw_text}'. I'll try to {intent.replace('_', ' ')} based on my best guess."

        result = NLUResult(
            normalized_text=normalized,
            detected_intent=intent,
            confidence=confidence,
            extracted_entities=entities,
            fallback_message=fallback
        )

        logger.info(f"NLU Result: intent={intent}, confidence={confidence:.2f}, entities={entities}")
        return result

    def _normalize_text(self, text: str) -> str:
        """Normalize text by applying synonyms and cleaning."""
        words = text.lower().split()
        normalized_words = []

        for word in words:
            # Find best synonym match
            best_match = word
            best_score = 0

            for canonical, variants in self.synonyms.items():
                for variant in variants:
                    score = fuzz.ratio(word, variant)
                    if score > best_score and score > 70:  # Threshold for synonym matching
                        best_match = canonical
                        best_score = score

            normalized_words.append(best_match)

        return ' '.join(normalized_words)

    def _detect_intent(self, normalized_text: str) -> Tuple[str, float]:
        """Detect intent using fuzzy matching against keywords."""
        words = normalized_text.split()
        best_intent = 'unknown'
        best_score = 0.0

        for intent, keywords in self.intent_keywords.items():
            for word in words:
                # Fuzzy match word against keywords
                match_result = process.extractOne(word, keywords, scorer=fuzz.ratio)
                if match_result:
                    score = match_result[1] / 100.0  # Convert to 0-1 scale
                    if score > best_score:
                        best_score = score
                        best_intent = intent

        # Boost score if multiple keywords match
        matched_keywords = sum(1 for keyword in sum(self.intent_keywords.values(), [])
                              if keyword in normalized_text)
        if matched_keywords > 1:
            best_score = min(1.0, best_score + 0.2)

        return best_intent, best_score

    def _extract_entities(self, normalized_text: str) -> Dict[str, str]:
        """Extract entities using regex patterns."""
        entities = {}

        for entity_type, pattern in self.entity_patterns.items():
            match = pattern.search(normalized_text)
            if match:
                entities[entity_type] = match.group(1).strip()

        # Special handling for topic if not found
        if 'topic' not in entities:
            # Try to extract topic from remaining text
            words = normalized_text.split()
            # Remove common command words
            command_words = ['create', 'make', 'open', 'draft', 'list', 'complete', 'search', 'organize']
            topic_words = [w for w in words if w not in command_words and not w.isdigit()]
            if topic_words:
                entities['topic'] = ' '.join(topic_words)

        return entities