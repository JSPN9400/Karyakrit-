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
            'excel': ['excel', 'xlsx', 'sheet', 'spreadsheet'],
            'email': ['email', 'mail', 'gmail', 'outlook', 'message'],
            'task': ['task', 'todo', 'kaam', 'assignment'],
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
            'folder': ['folder', 'directory', 'dir'],
            'ask': ['ask', 'answer', 'explain', 'question', 'query', 'smart', 'assistant', 'help'],
            'pdf': ['pdf', 'document', 'report'],
            'profile': ['profile', 'about', 'bio', 'myself'],
            'project': ['project', 'projects'],
            'websearch': ['internet', 'google', 'websearch', 'searchweb', 'online']
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
            'file_organize': ['organize', 'arrange', 'folder', 'files'],
            'ask_assistant': ['ask', 'answer', 'explain', 'question', 'assistant', 'help'],
            'web_search': ['search', 'internet', 'web', 'google', 'online'],
            'summarize_pdf': ['summarize', 'summary', 'pdf', 'document'],
            'remember_profile': ['remember', 'profile', 'about', 'me'],
            'show_profile': ['show', 'profile', 'about'],
            'add_project': ['add', 'project', 'new'],
            'list_projects': ['list', 'projects'],
            'open_social': ['whatsapp', 'linkedin', 'github', 'instagram', 'youtube'],
            'linkedin_jobs': ['linkedin', 'jobs', 'job']
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

    # Known application/website names that must never be fuzzy-collapsed into an
    # unrelated synonym (e.g. "notepad" was scoring 72% against "note" and being
    # silently rewritten to "note", which broke `open app notepad` routing).
    _PROTECTED_WORDS = {
        'notepad', 'calc', 'calculator', 'chrome', 'firefox', 'edge', 'safari',
        'paint', 'explorer', 'finder', 'terminal', 'cmd', 'powershell',
        'gmail', 'outlook', 'word', 'excel', 'powerpoint', 'vscode', 'code',
        'marks', 'grades', 'scores', 'whatsapp', 'linkedin', 'github',
        'instagram', 'youtube', 'google', 'pdf', 'assistant',
    }

    def _normalize_text(self, text: str) -> str:
        """Normalize text by applying synonyms and cleaning."""
        words = text.lower().split()
        normalized_words = []

        for word in words:
            if word in self._PROTECTED_WORDS:
                normalized_words.append(word)
                continue

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
        exact_intent = self._detect_exact_intent(normalized_text)
        if exact_intent:
            return exact_intent, 0.98

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

        if best_score < 0.55 and len(words) >= 4:
            return 'ask_assistant', 0.65

        return best_intent, best_score

    def _detect_exact_intent(self, normalized_text: str) -> Optional[str]:
        """Use exact phrase rules before fuzzy matching."""
        text = normalized_text.strip()

        if text.startswith('ask '):
            return 'ask_assistant'
        if text.startswith(('help me ', 'explain ', 'question ')):
            return 'ask_assistant'
        if text.startswith(('search web ', 'search website ', 'search internet ', 'google ', 'web search ')):
            return 'web_search'
        if text.startswith(('summarize pdf ', 'summarise pdf ', 'pdf summary ')):
            return 'summarize_pdf'
        if text.startswith(('remember about me ', 'remember profile me ', 'remember my ', 'remember ', 'set profile ', 'my profile is ')):
            return 'remember_profile'
        if text in {'show profile', 'list profile', 'who am i', 'my profile'}:
            return 'show_profile'
        if text.startswith(('add project ', 'new project ')):
            return 'add_project'
        if text in {'list projects', 'list project', 'show projects'}:
            return 'list_projects'
        if text.startswith(('linkedin jobs ', 'search linkedin jobs ')):
            return 'linkedin_jobs'
        if text in {'open whatsapp', 'open linkedin', 'open github', 'open instagram', 'open youtube'}:
            return 'open_social'
        if text.startswith(('list tasks', 'list task')) or text in {'tasks', 'task list'}:
            return 'list_tasks'
        if text.startswith(('complete task ', 'finish task ', 'done task ', 'mark task ')):
            return 'complete_task'
        if text.startswith(('create task ', 'make task ', 'task ', 'todo ')):
            return 'create_task'
        if text.startswith(('search file ', 'find file ', 'find files ', 'search files ')):
            return 'file_search'
        if text.startswith(('open website ', 'open site ', 'open web ')):
            return 'open_website'
        return None

    def _extract_entities(self, normalized_text: str) -> Dict[str, str]:
        """Extract entities using regex patterns."""
        entities = {}

        text = normalized_text.strip()
        if text.startswith(('create task ', 'make task ', 'task ', 'todo ')):
            entities['task_title'] = re.sub(r'^(create task|make task|task|todo)\s+', '', text).strip()
        elif text.startswith(('complete task ', 'finish task ', 'done task ', 'mark task ')):
            entities['task_title'] = re.sub(r'^(complete task|finish task|done task|mark task)\s+', '', text).strip()
        elif text.startswith('ask '):
            entities['topic'] = text[4:].strip()
        elif text.startswith(('search file ', 'find file ', 'find files ', 'search files ')):
            entities['topic'] = re.sub(r'^(search file|find file|find files|search files)\s+', '', text).strip()
        elif text.startswith(('search web ', 'search website ', 'search internet ', 'google ', 'web search ')):
            entities['topic'] = re.sub(r'^(search web|search website|search internet|google|web search)\s+', '', text).strip()
        elif text.startswith(('summarize pdf ', 'summarise pdf ', 'pdf summary ')):
            entities['file_name'] = re.sub(r'^(summarize pdf|summarise pdf|pdf summary)\s+', '', text).strip()
        elif text.startswith('remember about me '):
            entities['profile_fact'] = text[len('remember about me '):].strip()
        elif text.startswith('remember profile me '):
            entities['profile_fact'] = text[len('remember profile me '):].strip()
        elif text.startswith('remember my '):
            entities['profile_fact'] = text[len('remember my '):].strip()
        elif text.startswith('remember '):
            entities['profile_fact'] = text[len('remember '):].strip()
        elif text.startswith('set profile '):
            entities['profile_fact'] = text[len('set profile '):].strip()
        elif text.startswith(('add project ', 'new project ')):
            entities['project_name'] = re.sub(r'^(add project|new project)\s+', '', text).strip()
        elif text.startswith(('linkedin jobs ', 'search linkedin jobs ')):
            entities['topic'] = re.sub(r'^(linkedin jobs|search linkedin jobs)\s+', '', text).strip()
        elif text.startswith('open app '):
            entities['app_name'] = text[len('open app '):].strip()
        elif text.startswith('open '):
            entities['app_name'] = text[len('open '):].strip()

        for entity_type, pattern in self.entity_patterns.items():
            match = pattern.search(normalized_text)
            if match and entity_type not in entities:
                if entity_type == 'task_title' and text.startswith('ask '):
                    continue
                if entity_type == 'task_title' and text.startswith(('remember ', 'show profile')):
                    continue
                entities[entity_type] = match.group(1).strip()

        # Special handling for topic if not found
        if 'topic' not in entities:
            # Try to extract topic from remaining text
            words = normalized_text.split()
            # Remove command words and category nouns (excel, presentation, email, etc.)
            # so e.g. "create excel student marks" yields topic "student marks", not
            # "excel student marks".
            command_words = {'create', 'make', 'open', 'draft', 'list', 'complete', 'search', 'organize'}
            category_words = set(self.synonyms.keys())
            skip_words = command_words | category_words
            topic_words = [w for w in words if w not in skip_words and not w.isdigit()]
            if topic_words:
                entities['topic'] = ' '.join(topic_words)

        return entities
