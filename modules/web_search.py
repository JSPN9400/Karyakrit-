"""
Simple web search and answer helpers.
"""

import html
import re
from typing import Dict, List
from urllib.parse import quote_plus

import requests

from core.llm_provider import LLMProviderManager


def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search the web using DuckDuckGo's lightweight HTML endpoint."""
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    pattern = re.compile(
        r'<a[^>]+class="result__a"[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    results: List[Dict[str, str]] = []
    for match in pattern.finditer(response.text):
        title = re.sub(r"<.*?>", "", match.group("title"))
        title = html.unescape(title).strip()
        href = html.unescape(match.group("href")).strip()
        results.append({"title": title, "url": href})
        if len(results) >= max_results:
            break
    return results


def answer_from_web(query: str) -> str:
    """Search the web and return a compact answer with links."""
    try:
        results = search_web(query)
    except Exception as exc:
        return f"Web search failed: {exc}"

    if not results:
        return f"No web results found for: {query}"

    manager = LLMProviderManager()
    context = "\n".join(f"- {item['title']} :: {item['url']}" for item in results)
    answer = manager.generate_assistant_answer(
        f"Answer this using the web results only.\nQuestion: {query}\nResults:\n{context}"
    )

    lines = [answer.answer, "Web results:"]
    for item in results:
        lines.append(f"- {item['title']} - {item['url']}")
    return "\n".join(lines)
