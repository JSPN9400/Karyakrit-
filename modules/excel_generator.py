"""
Excel Generator Module

Creates Excel files using pandas. Content is shaped around the user's
requested topic: an LLM provider is asked for realistic column headers
and sample rows for that topic, falling back to a generic editable
template if AI is unavailable.
"""

import logging
import os
import re
from typing import Optional

import pandas as pd

from core.llm_provider import LLMProviderManager

logger = logging.getLogger(__name__)


def _build_excel_prompt(topic: str, row_count: int) -> str:
    return f"""
Generate sample tabular data for an Excel spreadsheet about "{topic}".

Return ONLY a raw JSON object (no markdown formatting, no code fences, no extra text) with this structure:
{{
  "columns": ["Column A", "Column B", "Column C"],
  "rows": [
    ["value", "value", "value"],
    ...
  ]
}}

Provide {row_count} rows of realistic, plausible sample data appropriate to the topic.
Keep column count between 3 and 6. Every row must have the same number of values as there are columns.
"""


def _generate_topic_data(topic: str, row_count: int = 8) -> Optional[pd.DataFrame]:
    """
    Ask the configured LLM provider for columns/rows relevant to `topic`.
    Returns None if AI is unavailable or the response can't be used, so
    the caller can fall back to a generic template.
    """
    try:
        manager = LLMProviderManager()
        if not manager.enable_ai:
            return None

        prompt = _build_excel_prompt(topic, row_count)

        for provider in manager.provider_order:
            if provider == 'fallback':
                continue
            try:
                raw = manager._call_provider(provider, prompt)
                if raw is None:
                    continue
            except Exception as e:
                logger.warning(f"Excel data provider {provider} failed: {e}")
                continue

            columns = raw.get('columns') if isinstance(raw, dict) else None
            rows = raw.get('rows') if isinstance(raw, dict) else None

            if not isinstance(columns, list) or not columns:
                continue
            if not isinstance(rows, list) or not rows:
                continue

            # Normalize row lengths to match column count; skip malformed rows.
            clean_rows = [r for r in rows if isinstance(r, list) and len(r) == len(columns)]
            if not clean_rows:
                continue

            return pd.DataFrame(clean_rows, columns=columns)

        return None
    except Exception as e:
        logger.warning(f"Topic-based Excel generation unavailable: {e}")
        return None


def _generic_template(topic: str, row_count: int = 8) -> pd.DataFrame:
    """A clearly-labeled, editable starter template when AI data isn't available."""
    columns = ["Item", "Description", "Value", "Notes"]
    rows = [
        [f"{topic.title()} item {i + 1}", "Describe here", "", ""]
        for i in range(row_count)
    ]
    return pd.DataFrame(rows, columns=columns)


def create_excel(filename: str, topic: Optional[str] = None, row_count: int = 8) -> str:
    """
    Create an Excel file shaped around `topic`.

    Args:
        filename: Name of the Excel file to create (relative to the data/ folder).
        topic: What the spreadsheet should be about. If omitted, derived from
            the filename. AI providers (if configured) are used to generate
            realistic sample columns/rows for this topic; otherwise a generic
            editable template is used.
        row_count: Number of sample rows to generate.

    Returns:
        str: The path to the created file.
    """
    if topic is None:
        # Derive a topic from the filename, e.g. "student_marks.xlsx" -> "student marks"
        base = re.sub(r'\.xlsx$', '', filename, flags=re.IGNORECASE)
        topic = base.replace('_', ' ').replace('-', ' ').strip() or 'data'

    df = _generate_topic_data(topic, row_count)
    if df is None:
        logger.info(f"Using generic template for topic: {topic}")
        df = _generic_template(topic, row_count)

    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)

    filepath = os.path.join('data', filename)
    df.to_excel(filepath, index=False)
    print(f"Excel file created: {filepath}")
    return filepath
