"""
LLM Provider Module

Multi-provider LLM routing system for content generation tasks.
Supports Gemini, Grok (xAI), OpenAI with automatic fallback.
"""

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import requests

logger = logging.getLogger(__name__)


@dataclass
class PresentationOutline:
    """Structured presentation outline."""
    slides: List[Dict[str, Any]]  # Each slide: {"title": str, "content": List[str]}


@dataclass
class EmailDraft:
    """Structured email draft."""
    subject: str
    body: str


class LLMProviderError(Exception):
    """Custom exception for LLM provider errors."""
    pass


class LLMProviderManager:
    """Manages multiple LLM providers with automatic fallback and online/offline detection."""

    def __init__(self):
        """Initialize the provider manager."""
        self.enable_ai = os.getenv('KARYAKRIT_ENABLE_AI', 'true').lower() == 'true'
        self.online_provider_order = os.getenv('KARYAKRIT_ONLINE_PROVIDER_ORDER', 'gemini,grok,openai,fallback').split(',')
        self.offline_provider_order = os.getenv('KARYAKRIT_OFFLINE_PROVIDER_ORDER', 'ollama,fallback').split(',')

        # API keys
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.xai_api_key = os.getenv('XAI_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'llama2')

        # Provider configurations
        self.timeouts = {
            'gemini': 30,
            'grok': 30,
            'openai': 30,
            'ollama': 10
        }

        # Check internet connectivity
        self.is_online = self._check_internet_connectivity()

        # Select provider order based on connectivity
        self.provider_order = self.online_provider_order if self.is_online else self.offline_provider_order

        logger.info(f"LLM Provider Manager initialized. AI enabled: {self.enable_ai}, Online: {self.is_online}, Order: {self.provider_order}")

    def _check_internet_connectivity(self) -> bool:
        """Check if internet is available using a lightweight HTTP request."""
        try:
            # Use a reliable, lightweight endpoint
            response = requests.get('https://www.google.com', timeout=5)
            return response.status_code == 200
        except (requests.RequestException, requests.Timeout):
            logger.info("Internet connectivity check failed - operating in offline mode")
            return False

    def generate_presentation_outline(self, topic: str, slide_count: int) -> PresentationOutline:
        """
        Generate a presentation outline using available providers.

        Args:
            topic: The presentation topic.
            slide_count: Number of slides to generate.

        Returns:
            PresentationOutline: Structured outline. Falls back to a deterministic
            template if every configured provider fails or is unavailable.
        """
        if not self.enable_ai:
            logger.info("AI disabled, using fallback")
            return self._generate_fallback_presentation(topic, slide_count)

        prompt = self._build_presentation_prompt(topic, slide_count)

        for provider in self.provider_order:
            try:
                logger.info(f"Attempting presentation generation with provider: {provider}")
                if provider == 'gemini':
                    raw = self._call_gemini(prompt)
                elif provider == 'grok':
                    raw = self._call_grok(prompt)
                elif provider == 'openai':
                    raw = self._call_openai(prompt)
                elif provider == 'ollama':
                    raw = self._call_ollama(prompt)
                elif provider == 'fallback':
                    return self._generate_fallback_presentation(topic, slide_count)
                else:
                    continue

                # Convert the raw JSON dict returned by the API into a PresentationOutline
                result = self._to_presentation_outline(raw)

                if self._validate_presentation_outline(result):
                    logger.info(f"Successfully generated presentation with {provider}")
                    return result
                else:
                    logger.warning(f"Invalid response from {provider}, trying next provider")
                    continue

            except Exception as e:
                logger.warning(f"Provider {provider} failed: {e}")
                continue

        logger.warning("All AI providers failed or are unconfigured; using deterministic fallback")
        return self._generate_fallback_presentation(topic, slide_count)

    def generate_email_draft(self, email_type: str, recipient: str, tone: str, purpose: str) -> EmailDraft:
        """
        Generate an email draft using available providers.

        Args:
            email_type: Type of email (e.g., 'leave_request', 'meeting_invite').
            recipient: Recipient name or role.
            tone: Email tone (e.g., 'formal', 'casual').
            purpose: Email purpose.

        Returns:
            EmailDraft: Structured email draft. Falls back to a deterministic
            template if every configured provider fails or is unavailable.
        """
        if not self.enable_ai:
            logger.info("AI disabled, using fallback")
            return self._generate_fallback_email(email_type, recipient, tone, purpose)

        prompt = self._build_email_prompt(email_type, recipient, tone, purpose)

        for provider in self.provider_order:
            try:
                logger.info(f"Attempting email generation with provider: {provider}")
                if provider == 'gemini':
                    raw = self._call_gemini(prompt)
                elif provider == 'grok':
                    raw = self._call_grok(prompt)
                elif provider == 'openai':
                    raw = self._call_openai(prompt)
                elif provider == 'ollama':
                    raw = self._call_ollama(prompt)
                elif provider == 'fallback':
                    return self._generate_fallback_email(email_type, recipient, tone, purpose)
                else:
                    continue

                # Convert the raw JSON dict returned by the API into an EmailDraft
                result = self._to_email_draft(raw)

                if self._validate_email_draft(result):
                    logger.info(f"Successfully generated email with {provider}")
                    return result
                else:
                    logger.warning(f"Invalid response from {provider}, trying next provider")
                    continue

            except Exception as e:
                logger.warning(f"Provider {provider} failed: {e}")
                continue

        logger.warning("All AI providers failed or are unconfigured; using deterministic fallback")
        return self._generate_fallback_email(email_type, recipient, tone, purpose)

    # ------------------------------------------------------------------
    # Provider calls
    # ------------------------------------------------------------------

    def _call_gemini(self, prompt: str) -> Dict:
        """Call Gemini API. Returns a raw parsed JSON dict."""
        if not self.gemini_api_key:
            raise LLMProviderError("Gemini API key not configured")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.gemini_api_key}"
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        response = requests.post(url, headers=headers, json=data, timeout=self.timeouts['gemini'])
        response.raise_for_status()

        result = response.json()
        return self._parse_gemini_response(result)

    def _call_grok(self, prompt: str) -> Dict:
        """Call Grok (xAI) API. Returns a raw parsed JSON dict."""
        if not self.xai_api_key:
            raise LLMProviderError("xAI API key not configured")

        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            'Authorization': f'Bearer {self.xai_api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            "model": "grok-beta",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        }

        response = requests.post(url, headers=headers, json=data, timeout=self.timeouts['grok'])
        response.raise_for_status()

        result = response.json()
        return self._parse_grok_response(result)

    def _call_openai(self, prompt: str) -> Dict:
        """Call OpenAI API. Returns a raw parsed JSON dict."""
        if not self.openai_api_key:
            raise LLMProviderError("OpenAI API key not configured")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            'Authorization': f'Bearer {self.openai_api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        }

        response = requests.post(url, headers=headers, json=data, timeout=self.timeouts['openai'])
        response.raise_for_status()

        result = response.json()
        return self._parse_openai_response(result)

    def _call_ollama(self, prompt: str) -> Dict:
        """Call Ollama API. Returns a raw parsed JSON dict."""
        url = f"{self.ollama_host}/api/generate"
        data = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(url, json=data, timeout=self.timeouts['ollama'])
            response.raise_for_status()
            result = response.json()
            return self._parse_ollama_response(result)
        except requests.RequestException as e:
            raise LLMProviderError(f"Ollama request failed: {e}")

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_json_text(text: str) -> str:
        """
        Strip common LLM response wrapping (markdown code fences, leading/trailing
        prose) so json.loads has a fighting chance. LLMs frequently wrap JSON in
        ```json ... ``` even when explicitly asked for raw JSON.
        """
        text = text.strip()
        fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if fence_match:
            return fence_match.group(1).strip()
        return text

    def _parse_gemini_response(self, response: Dict) -> Dict:
        """Parse Gemini API response into a raw dict."""
        try:
            text = response['candidates'][0]['content']['parts'][0]['text']
            return json.loads(self._extract_json_text(text))
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise LLMProviderError(f"Failed to parse Gemini response: {e}")

    def _parse_grok_response(self, response: Dict) -> Dict:
        """Parse Grok API response into a raw dict."""
        try:
            text = response['choices'][0]['message']['content']
            return json.loads(self._extract_json_text(text))
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise LLMProviderError(f"Failed to parse Grok response: {e}")

    def _parse_openai_response(self, response: Dict) -> Dict:
        """Parse OpenAI API response into a raw dict."""
        try:
            text = response['choices'][0]['message']['content']
            return json.loads(self._extract_json_text(text))
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise LLMProviderError(f"Failed to parse OpenAI response: {e}")

    def _parse_ollama_response(self, response: Dict) -> Dict:
        """Parse Ollama API response into a raw dict."""
        try:
            text = response['response']
            return json.loads(self._extract_json_text(text))
        except (KeyError, json.JSONDecodeError) as e:
            raise LLMProviderError(f"Failed to parse Ollama response: {e}")

    # ------------------------------------------------------------------
    # Raw dict -> dataclass conversion
    #
    # The provider calls above all return plain dicts from json.loads().
    # These helpers turn those dicts into the typed dataclasses the rest
    # of the app expects, and are what was missing before: validation was
    # checking isinstance(raw_dict, PresentationOutline), which can never
    # be true for a plain dict, so every successful API call was being
    # discarded and the app always silently fell back to the static
    # template. These converters close that gap.
    # ------------------------------------------------------------------

    @staticmethod
    def _to_presentation_outline(raw: Any) -> Optional[PresentationOutline]:
        """Convert a raw JSON dict into a PresentationOutline, or None if malformed."""
        if isinstance(raw, PresentationOutline):
            return raw
        if not isinstance(raw, dict):
            return None
        slides = raw.get('slides')
        if not isinstance(slides, list):
            return None
        return PresentationOutline(slides=slides)

    @staticmethod
    def _to_email_draft(raw: Any) -> Optional[EmailDraft]:
        """Convert a raw JSON dict into an EmailDraft, or None if malformed."""
        if isinstance(raw, EmailDraft):
            return raw
        if not isinstance(raw, dict):
            return None
        subject = raw.get('subject')
        body = raw.get('body')
        if not subject or not body:
            return None
        return EmailDraft(subject=subject, body=body)

    # ------------------------------------------------------------------
    # Prompt building
    # ------------------------------------------------------------------

    def _build_presentation_prompt(self, topic: str, slide_count: int) -> str:
        """Build prompt for presentation outline generation."""
        return f"""
Generate a presentation outline for the topic "{topic}" with exactly {slide_count} slides.

Return ONLY a raw JSON object (no markdown formatting, no code fences, no extra text) with this structure:
{{
  "slides": [
    {{
      "title": "Slide Title",
      "content": ["Bullet point 1", "Bullet point 2", "Bullet point 3"]
    }},
    ...
  ]
}}

Ensure each slide has a title and 3-5 bullet points. Make it suitable for a professional office presentation.
"""

    def _build_email_prompt(self, email_type: str, recipient: str, tone: str, purpose: str) -> str:
        """Build prompt for email draft generation."""
        return f"""
Generate a {tone} email draft for a {email_type} to {recipient}.

Purpose: {purpose}

Return ONLY a raw JSON object (no markdown formatting, no code fences, no extra text) with this structure:
{{
  "subject": "Email Subject Line",
  "body": "Full email body text here..."
}}

Make it professional and appropriate for office communication.
"""

    # ------------------------------------------------------------------
    # Deterministic fallbacks (no network / no AI required)
    # ------------------------------------------------------------------

    def _generate_fallback_presentation(self, topic: str, slide_count: int) -> PresentationOutline:
        """Generate deterministic fallback presentation outline."""
        logger.info(f"Using fallback presentation generation for topic: {topic}")

        structure = [
            {
                "title": f"Introduction to {topic.title()}",
                "content": [
                    f"Overview of {topic}",
                    "Importance and relevance",
                    "Objectives of this presentation"
                ]
            },
            {
                "title": f"Current Situation - {topic.title()}",
                "content": [
                    "Background and context",
                    "Current trends and developments",
                    "Key statistics and data"
                ]
            },
            {
                "title": f"Key Issues and Analysis - {topic.title()}",
                "content": [
                    "Main challenges and opportunities",
                    "Analysis of current approaches",
                    "Critical factors to consider"
                ]
            },
            {
                "title": f"Recommendations - {topic.title()}",
                "content": [
                    "Proposed solutions and strategies",
                    "Implementation steps",
                    "Expected outcomes and benefits"
                ]
            },
            {
                "title": f"Conclusion and Next Steps - {topic.title()}",
                "content": [
                    "Summary of key points",
                    "Recommendations for action",
                    "Future outlook and monitoring"
                ]
            }
        ]

        # If more slides were requested than the template provides, repeat
        # generic sections rather than silently truncating expectations.
        if slide_count > len(structure):
            extra_needed = slide_count - len(structure)
            for i in range(extra_needed):
                structure.append({
                    "title": f"Additional Discussion {i + 1} - {topic.title()}",
                    "content": [
                        "Supporting details and context",
                        "Further analysis",
                        "Open questions for discussion"
                    ]
                })

        slides = structure[:slide_count] if slide_count > 0 else structure
        return PresentationOutline(slides=slides)

    def _generate_fallback_email(self, email_type: str, recipient: str, tone: str, purpose: str) -> EmailDraft:
        """Generate deterministic fallback email draft."""
        logger.info(f"Using fallback email generation for {email_type} to {recipient}")

        subject = f"Regarding {purpose.title()}" if purpose else f"Regarding {email_type.title()}"
        body = f"""
Dear {recipient},

I am writing to {purpose or email_type}.

Please let me know if you need any additional information.

Best regards,
[Your Name]
"""

        return EmailDraft(subject=subject, body=body.strip())

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_presentation_outline(self, outline: Any) -> bool:
        """Validate presentation outline structure."""
        if not isinstance(outline, PresentationOutline):
            return False

        if not outline.slides or len(outline.slides) == 0:
            return False

        for slide in outline.slides:
            if not isinstance(slide, dict):
                return False
            if 'title' not in slide or 'content' not in slide:
                return False
            if not slide['title'] or not isinstance(slide['content'], list):
                return False
            if len(slide['content']) == 0:
                return False

        return True

    def _validate_email_draft(self, draft: Any) -> bool:
        """Validate email draft structure."""
        if not isinstance(draft, EmailDraft):
            return False

        if not draft.subject or not draft.body:
            return False

        return True
