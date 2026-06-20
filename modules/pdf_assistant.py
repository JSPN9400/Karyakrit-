"""
PDF reading and summarization tools.
"""

import os
import re
from typing import List

from core.llm_provider import LLMProviderManager


def _extract_pdf_text(pdf_path: str, max_chars: int = 16000) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError("PDF support requires pypdf. Run: pip install -r requirements.txt")

    reader = PdfReader(pdf_path)
    parts: List[str] = []
    total = 0

    for page in reader.pages:
        text = page.extract_text() or ""
        cleaned = re.sub(r"\s+", " ", text).strip()
        if not cleaned:
            continue
        parts.append(cleaned)
        total += len(cleaned)
        if total >= max_chars:
            break

    return "\n".join(parts)[:max_chars]


def summarize_pdf(pdf_path: str) -> str:
    """Summarize a local PDF file."""
    if not os.path.exists(pdf_path):
        return f"PDF not found: {pdf_path}"

    try:
        text = _extract_pdf_text(pdf_path)
    except Exception as exc:
        return f"Could not read PDF: {exc}"

    if not text:
        return "No readable text found in the PDF."

    manager = LLMProviderManager()
    return manager.generate_summary(
        text,
        instruction="Summarize this PDF in plain English with the main topic, key points, and action items.",
    )
