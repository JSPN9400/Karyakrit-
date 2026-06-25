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

        # Entity extraction patterns. \b word boundaries are required here —
        # without them, e.g. (?:on|...) matches the literal substring "on"
        # inside the word "presentatiON", capturing everything after it
        # (including the real standalone "on") into the topic group.
        self.entity_patterns = {
            'slide_count': re.compile(r'(\d+)\s*(?:slide|slides)', re.IGNORECASE),
            'topic': re.compile(r'\b(?:on|about|for|regarding)\b\s+(.+)', re.IGNORECASE),
            'recipient': re.compile(r'\b(?:to|for|ko)\b\s+(\w+)|(\w+)\s+\bko\b', re.IGNORECASE),
            'subject': re.compile(r'\b(?:subject|regarding|about)\b\s+(.+)', re.IGNORECASE),
            'app_name': re.compile(r'\b(?:open|start|launch)\b\s+(.+)', re.IGNORECASE),
            'file_name': re.compile(r'\b(?:file|folder)\b\s+(.+)', re.IGNORECASE),
            'task_title': re.compile(r'\b(?:task|todo)\b\s+(.+)', re.IGNORECASE)
        }

        # Hinglish/English filler words that carry no topic meaning on their own
        # (e.g. "excel bana do contacts ka" -> "do" and "ka" are grammatical
        # filler, not part of the topic "contacts"). Stripped from extracted
        # topic/task_title entities after the main command word is removed.
        self._FILLER_WORDS = {
            'do', 'ka', 'ki', 'ke', 'ko', 'hai', 'he', 'karo', 'kar', 'jaldi',
            'please', 'plz', 'pls', 'ek', 'a', 'an', 'the',
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

        # Detect intent. raw_text is also passed through so certain exact-match
        # rules (e.g. "tell me about myself") can be checked against the
        # literal phrasing, since normalization can fuzzy-rewrite words like
        # "about"/"myself" into an unrelated synonym category before the
        # phrase-matching rules ever see them.
        intent, confidence = self._detect_intent(normalized, raw_text)

        # Extract entities. raw_text is passed alongside so free-text data
        # fields (profile facts, project names) can be taken from the
        # original wording instead of the normalized text, which can
        # corrupt arbitrary user content (e.g. "I like cricket" -> "I note
        # cricket", because "like" fuzzy-matches the "likh"/note synonym).
        entities = self._extract_entities(normalized, raw_text)

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
        'manager', 'managers', 'client', 'clients', 'colleague', 'colleagues',
        'team', 'boss', 'hr', 'recruiter',
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

    def _detect_intent(self, normalized_text: str, raw_text: str = "") -> Tuple[str, float]:
        """Detect intent using fuzzy matching against keywords."""
        exact_intent = self._detect_exact_intent(normalized_text, raw_text)
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

    def _detect_exact_intent(self, normalized_text: str, raw_text: str = "") -> Optional[str]:
        """Use exact phrase rules before fuzzy matching."""
        text = normalized_text.strip()
        raw = (raw_text or "").strip().lower()

        if text.startswith('ask '):
            return 'ask_assistant'
        if text.startswith(('help me ', 'explain ', 'question ')):
            return 'ask_assistant'
        if text.startswith(('search web ', 'search website ', 'search internet ', 'google ', 'web search ')):
            return 'web_search'
        if text.startswith(('summarize pdf ', 'summarise pdf ', 'pdf summary ')):
            return 'summarize_pdf'
        # Personal questions about the user - checked against the RAW phrase
        # before normalization. Words like "about"/"myself" can get
        # fuzzy-rewritten into an unrelated synonym category (e.g. "about
        # myself" -> "profile profile"), which would otherwise hide this rule
        # behind remember_profile's broader "remember "/"about " matching, so
        # this check must run on raw_text and before remember_profile.
        about_me_starts = (
            'what is my ', "what's my ", 'whats my ', 'who is my ',
            'where do i ', 'where is my ', 'tell me about myself',
            'tell me about me', 'mera ', 'meri ', 'mere ',
        )
        if raw.startswith(about_me_starts) or ('kya hai' in raw and any(w in raw for w in ('mera', 'meri', 'mere'))):
            return 'ask_about_me'
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
        if text in {'list app', 'list apps', 'show app', 'show apps', 'installed app', 'installed apps'}:
            return 'list_apps'
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

    def _clean_phrase(self, phrase: str) -> str:
        """Strip leading/trailing filler words from an extracted entity phrase."""
        words = phrase.split()
        # Strip filler words from both ends (not the middle - "ka" inside a
        # real topic like "raja ka kissa" should stay if meaningful, but for
        # simple command grammar this mainly trims trailing "ka"/"ko"/"do").
        while words and words[0].lower() in self._FILLER_WORDS:
            words.pop(0)
        while words and words[-1].lower() in self._FILLER_WORDS:
            words.pop()
        return ' '.join(words).strip()

    def _extract_entities(self, normalized_text: str, raw_text: str = "") -> Dict[str, str]:
        """Extract entities using regex patterns."""
        entities = {}

        text = normalized_text.strip()
        raw_stripped = (raw_text or normalized_text).strip()

        def _raw_after_any_prefix(raw_prefixes, normalized_prefix: str) -> str:
            """
            Slice the raw (unnormalized) text after whichever known prefix
            variant it actually starts with. Needed because normalization can
            rewrite the prefix itself (e.g. "remember about me" normalizes to
            "remember profile me" since "about" -> "profile"), so the raw
            text won't literally start with the normalized prefix string.
            Falls back to slicing the normalized text if no raw variant matches.
            """
            lowered = raw_stripped.lower()
            for prefix in raw_prefixes:
                if lowered.startswith(prefix):
                    return raw_stripped[len(prefix):].strip()
            return text[len(normalized_prefix):].strip()

        def _raw_after_prefix(prefix_lower: str) -> str:
            """Slice the raw (unnormalized) text after a case-insensitive prefix match."""
            return _raw_after_any_prefix([prefix_lower], prefix_lower)


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
        # profile_fact is free-text data the user wants stored verbatim, so it's
        # pulled from raw_text (unnormalized) to avoid corrupting their wording.
        # Multiple raw prefix variants are tried because normalization can
        # rewrite the prefix words themselves (e.g. "about" -> "profile").
        elif text.startswith('remember about me '):
            entities['profile_fact'] = _raw_after_any_prefix(
                ['remember about me ', 'yaad rakho about me ', 'yaad rakho mere baare mein '],
                'remember about me '
            )
        elif text.startswith('remember profile me '):
            entities['profile_fact'] = _raw_after_any_prefix(
                ['remember about me ', 'remember profile me '], 'remember profile me '
            )
        elif text.startswith('remember my '):
            entities['profile_fact'] = _raw_after_any_prefix(
                ['remember my ', 'yaad rakho mera ', 'yaad rakho meri '], 'remember my '
            )
        elif text.startswith('remember '):
            entities['profile_fact'] = _raw_after_any_prefix(
                ['remember ', 'yaad rakho '], 'remember '
            )
        elif text.startswith('set profile '):
            entities['profile_fact'] = _raw_after_any_prefix(['set profile '], 'set profile ')
        elif text.startswith(('add project ', 'new project ')):
            prefix = 'add project ' if text.startswith('add project ') else 'new project '
            entities['project_name'] = _raw_after_any_prefix(
                ['add project ', 'new project '], prefix
            )
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
                if entity_type == 'recipient':
                    # recipient pattern has two alternative capture groups:
                    # "to/for/ko <word>" or "<word> ko" (Hinglish word order)
                    value = match.group(1) or match.group(2)
                    if value:
                        entities[entity_type] = value.strip()
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
            preposition_words = {'to', 'on', 'about', 'for', 'regarding', 'ko'}
            skip_words = command_words | category_words | preposition_words
            topic_words = [w for w in words if w not in skip_words and not w.isdigit()]
            # Don't repeat a name already captured as the recipient.
            if 'recipient' in entities:
                topic_words = [w for w in topic_words if w.lower() != entities['recipient'].lower()]
            if topic_words:
                entities['topic'] = ' '.join(topic_words)

        # Strip leading/trailing Hinglish filler words (do/ka/ko/karo/...) and
        # any leftover command verbs from phrase-type entities, so e.g.
        # "excel bana do contacts ka" -> topic "contacts" instead of
        # "do contacts ka", and "task bana do kal client call" -> task_title
        # "kal client call" instead of "create do kal client call".
        leftover_command_words = {'create', 'make', 'bana', 'banao', 'generate'}
        for key in ('topic', 'task_title', 'project_name'):
            if key in entities and entities[key]:
                words = [w for w in entities[key].split() if w not in leftover_command_words]
                entities[key] = self._clean_phrase(' '.join(words))
                if not entities[key]:
                    del entities[key]

        return entities
