"""
Shared utilities used across all agents and services.
Central place for JSON parsing, text normalization, and error handling.
"""

import json
import re
import ast
import asyncio
import hashlib
from typing import Any, Union


# ── Robust LLM JSON Parser ────────────────────────────────────────────────────

def parse_llm_json(raw: str) -> Union[dict, list]:
    """
    Parse JSON from LLM output robustly, handling all common failure modes:
    - Markdown fences (```json ... ```)
    - Python-style booleans (True/False/None)
    - Trailing commas
    - Leading/trailing garbage text
    - Truncated JSON (best-effort recovery)
    """
    if not raw or not raw.strip():
        raise ValueError("Empty LLM response")

    text = raw.strip()

    # Step 1: Strip markdown fences
    text = re.sub(r"^```(?:json)?\s*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n?```\s*$", "", text, flags=re.MULTILINE)
    text = text.strip()

    # Step 2: Find outermost JSON structure
    obj_start = text.find("{")
    arr_start = text.find("[")

    if obj_start == -1 and arr_start == -1:
        raise ValueError(f"No JSON structure found in: {text[:200]}")

    if obj_start != -1 and (arr_start == -1 or obj_start < arr_start):
        start, end_char = obj_start, "}"
    else:
        start, end_char = arr_start, "]"

    end = text.rfind(end_char)
    if end == -1 or end <= start:
        # Try to close truncated JSON
        text = text[start:] + end_char
        end = len(text) - 1
    else:
        text = text[start:end + 1]

    # Step 3: Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Step 4: Fix Python-style values
    fixed = (
        text
        .replace(": True", ": true")
        .replace(": False", ": false")
        .replace(": None", ": null")
        .replace(",]", "]")
        .replace(",}", "}")
    )
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Step 5: Remove trailing commas before ] or }
    fixed2 = re.sub(r",\s*([}\]])", r"\1", fixed)
    try:
        return json.loads(fixed2)
    except json.JSONDecodeError:
        pass

    # Step 6: Try ast.literal_eval as last resort (handles Python dicts)
    try:
        result = ast.literal_eval(text)
        if isinstance(result, (dict, list)):
            return result
    except (ValueError, SyntaxError):
        pass

    raise ValueError(f"Could not parse JSON from LLM response: {text[:300]}")


def safe_parse_llm_json(raw: str, default: Any = None) -> Any:
    """Parse JSON, returning default if parsing fails."""
    try:
        return parse_llm_json(raw)
    except (ValueError, Exception):
        return default


# ── Text Utilities ────────────────────────────────────────────────────────────

def normalize_title(title: str) -> str:
    """Normalize paper title for deduplication comparison."""
    return re.sub(r"[^a-z0-9]", "", title.lower())[:60]


def truncate_text(text: str, max_chars: int = 300) -> str:
    """Truncate text at word boundary."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    return (truncated[:last_space] if last_space > max_chars * 0.8 else truncated) + "..."


def keyword_overlap_score(query_terms: list[str], title: str, abstract: str) -> float:
    """
    Compute relevance score as keyword overlap ratio.
    query_terms: list of lowercased words from intent keywords + queries
    """
    if not query_terms:
        return 0.5
    paper_text = (title + " " + abstract).lower()
    matches = sum(1 for term in query_terms if term in paper_text)
    return min(matches / max(len(query_terms), 1), 1.0)


def recency_score(year_str: str) -> float:
    """Score paper recency. Newest = 1.0."""
    import datetime
    current_year = datetime.datetime.now().year
    try:
        year = int(str(year_str)[:4])
        diff = current_year - year
        if diff <= 1:
            return 1.0
        elif diff <= 2:
            return 0.8
        elif diff <= 3:
            return 0.6
        elif diff <= 5:
            return 0.4
        else:
            return 0.2
    except (ValueError, TypeError):
        return 0.3


def citation_weight(citations_str: str) -> float:
    """Normalize citation count. Caps at 500."""
    try:
        count = int(str(citations_str).replace(",", "").split(".")[0])
        return min(count / 500.0, 1.0)
    except (ValueError, TypeError):
        return 0.0


def compute_paper_score(paper: dict, query_terms: list[str]) -> float:
    """Compute composite relevance score for ranking."""
    relevance = keyword_overlap_score(
        query_terms,
        paper.get("title", ""),
        paper.get("abstract", ""),
    )
    recency = recency_score(paper.get("year", ""))
    citations = citation_weight(paper.get("citations", "0"))
    return relevance * 0.5 + recency * 0.3 + citations * 0.2


# ── Async Rate Limiter ────────────────────────────────────────────────────────

class RateLimiter:
    """Simple async semaphore-based rate limiter for external API calls."""

    def __init__(self, max_concurrent: int = 3, delay_seconds: float = 0.3):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._delay = delay_seconds

    async def __aenter__(self):
        await self._semaphore.acquire()
        await asyncio.sleep(self._delay)
        return self

    async def __aexit__(self, *args):
        self._semaphore.release()


# Global rate limiter instance for all external API calls
api_rate_limiter = RateLimiter(max_concurrent=3, delay_seconds=0.3)


# ── ETag Utilities ────────────────────────────────────────────────────────────

def compute_etag(data: Any) -> str:
    """Compute ETag hash for caching download responses."""
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.md5(serialized.encode()).hexdigest()
