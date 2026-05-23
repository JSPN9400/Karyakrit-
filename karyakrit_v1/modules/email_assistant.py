"""
Email Assistant Module

Handles email drafting using LLM providers.
"""

import logging
import os
from core.llm_provider import LLMProviderManager, EmailDraft

logger = logging.getLogger(__name__)


class EmailAssistant:
    """Email drafting assistant using LLM providers."""

    def __init__(self):
        """Initialize the email assistant."""
        self.provider_manager = LLMProviderManager()
        logger.info("EmailAssistant initialized")

    def draft_email(self, email_type: str, recipient: str, tone: str = "formal", purpose: str = "") -> EmailDraft:
        """
        Draft an email using available LLM providers.

        Args:
            email_type: Type of email (e.g., 'leave_request', 'meeting_invite').
            recipient: Recipient name or role.
            tone: Email tone ('formal', 'casual', etc.).
            purpose: Email purpose description.

        Returns:
            EmailDraft: The drafted email.
        """
        logger.info(f"Drafting {email_type} email to {recipient} with {tone} tone")

        try:
            draft = self.provider_manager.generate_email_draft(email_type, recipient, tone, purpose)
            logger.info("Email drafted successfully")
            return draft
        except Exception as e:
            logger.error(f"Failed to draft email: {e}")
            # Return a basic fallback
            return EmailDraft(
                subject=f"Regarding {purpose or email_type}",
                body=f"Dear {recipient},\n\nI am writing regarding {purpose or email_type}.\n\nBest regards,\n[Your Name]"
            )

    def save_draft(self, draft: EmailDraft, filename: str = None) -> str:
        """
        Save the email draft to a file.

        Args:
            draft: The email draft to save.
            filename: Optional filename.

        Returns:
            str: Path to the saved file.
        """
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        output_dir = os.path.join(project_root, 'output', 'emails')
        os.makedirs(output_dir, exist_ok=True)

        if not filename:
            import time
            timestamp = int(time.time())
            filename = f"email_draft_{timestamp}.txt"

        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Subject: {draft.subject}\n\n")
            f.write(draft.body)

        logger.info(f"Email draft saved to: {filepath}")
        return filepath