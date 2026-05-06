"""
Intent Extraction Service
Parses a free-form research query into structured fields:
- domain, task, constraints, keywords, queries
"""

import json
import re
from typing import Optional
from core.llm_client import LLMClient


INTENT_SYSTEM = """You are a research intent extraction assistant.
Given a user's research description, extract structured information.
Return ONLY valid JSON with no markdown, no commentary, no code blocks."""

INTENT_PROMPT_TEMPLATE = """Extract research intent from this input:

"{text}"

Return this exact JSON structure:
{{
  "domain": ["primary domain", "secondary domain if any"],
  "task": "specific ML/NLP/AI task being addressed",
  "problem_statement": "one sentence problem summary",
  "constraints": {{
    "compute": "low|medium|high|unspecified",
    "data_availability": "scarce|moderate|abundant|unspecified",
    "real_time": true|false,
    "region": "specific region if mentioned or null",
    "other": []
  }},
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "queries": [
    "specific search query 1",
    "specific search query 2",
    "specific search query 3"
  ],
  "target_audience": "who would benefit from this research",
  "expected_contribution": "what new contribution is expected"
}}"""


async def extract_intent(text: str, llm: LLMClient) -> dict:
    """
    Extract structured research intent from a user's free-form text.
    Falls back to a basic extraction if LLM fails.
    """
    prompt = INTENT_PROMPT_TEMPLATE.format(text=text.strip())

    try:
        raw = await llm.complete(prompt, system=INTENT_SYSTEM, json_mode=True)
        result = _parse_json_response(raw)
        result["raw_input"] = text
        return result
    except Exception as e:
        # Fallback: basic keyword extraction without LLM
        return _fallback_intent(text, error=str(e))


def _parse_json_response(raw: str) -> dict:
    """Parse JSON from LLM response, handling common formatting issues."""
    # Strip markdown code fences if present
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()

    # Find JSON object boundaries
    start = clean.find("{")
    end = clean.rfind("}") + 1
    if start != -1 and end > start:
        clean = clean[start:end]

    return json.loads(clean)


def _fallback_intent(text: str, error: str = "") -> dict:
    """Basic fallback when LLM is unavailable."""
    # Better regex to include short terms like NLP, AI, ML, CV
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
    stopwords = {"this", "that", "with", "from", "have", "will", "been", "they",
                 "research", "using", "based", "study", "paper", "model", "data",
                 "want", "about", "your", "mine", "some", "more", "very", "also"}
    
    # Priority for short research terms
    research_terms = {"nlp", "ai", "ml", "cv", "llm", "cnn", "rnn", "gnn", "rl"}
    
    found_keywords = []
    for w in words:
        if w in research_terms or (len(w) >= 3 and w not in stopwords):
            if w not in found_keywords:
                found_keywords.append(w)
    
    keywords = found_keywords[:8]
    if not keywords and text.strip():
        keywords = [text.strip().split()[0][:20]]
    
    # Create better search queries from keywords
    queries = []
    if len(keywords) >= 2:
        queries.append(f"{keywords[0]} {keywords[1]}")
    if len(keywords) >= 3:
        queries.append(f"{keywords[0]} {keywords[2]}")
    queries.append(text[:100])

    return {
        "domain": ["general AI/ML"],
        "task": "research",
        "problem_statement": text[:200],
        "constraints": {
            "compute": "unspecified",
            "data_availability": "unspecified",
            "real_time": False,
            "region": None,
            "other": [],
        },
        "keywords": keywords,
        "queries": queries[:3],
        "target_audience": "researchers",
        "expected_contribution": "novel approach",
        "raw_input": text,
        "_fallback": True,
        "_error": error,
    }
