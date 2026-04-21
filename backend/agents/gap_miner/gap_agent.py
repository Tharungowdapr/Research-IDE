"""
Gap Mining Agent
Analyzes a set of papers to identify research gaps, limitations, and opportunities.
"""

import json
import re
from typing import List, Dict, Any
from core.llm_client import LLMClient


GAP_SYSTEM = """You are an expert research analyst specializing in identifying gaps 
in the scientific literature. Analyze papers and return ONLY valid JSON."""

GAP_PROMPT_TEMPLATE = """Analyze these research papers and identify key research gaps.

Research Context:
Domain: {domain}
Problem: {problem}

Papers Summary:
{papers_summary}

Return a JSON array of gaps (up to 6 gaps):
[
  {{
    "title": "Short gap title",
    "description": "Detailed description of the gap",
    "type": "methodological|dataset|evaluation|application|theoretical",
    "confidence": "high|medium|low",
    "supporting_papers": ["paper title 1", "paper title 2"],
    "opportunity": "How this gap could be addressed",
    "novelty_potential": 1-10
  }}
]"""


async def run_gap_analysis(
    papers: List[Dict[str, Any]],
    intent: Dict,
    llm: LLMClient,
) -> List[Dict]:
    """Analyze papers for research gaps."""
    if not papers:
        return _default_gaps()

    # Build a condensed paper summary for the prompt
    papers_summary = _summarize_papers(papers[:15])  # Limit to 15 papers

    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    problem = intent.get("problem_statement", intent.get("task", "research problem"))

    prompt = GAP_PROMPT_TEMPLATE.format(
        domain=domain,
        problem=problem,
        papers_summary=papers_summary,
    )

    try:
        raw = await llm.complete(prompt, system=GAP_SYSTEM, json_mode=True)
        gaps = _parse_json_list(raw)
        return gaps if gaps else _default_gaps()
    except Exception as e:
        print(f"Gap analysis error: {e}")
        return _extracted_gaps_from_papers(papers)


def _summarize_papers(papers: List[Dict]) -> str:
    """Create a compact summary of papers for the prompt."""
    lines = []
    for i, p in enumerate(papers, 1):
        title = p.get("title", "Unknown")
        abstract = p.get("abstract", "")[:200]
        year = p.get("year", "")
        citations = p.get("citations", "N/A")
        lines.append(f"{i}. [{year}] {title} (citations: {citations})\n   {abstract}...")
    return "\n\n".join(lines)


def _parse_json_list(raw: str) -> List[Dict]:
    """Parse a JSON array from LLM response."""
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    start = clean.find("[")
    end = clean.rfind("]") + 1
    if start != -1 and end > start:
        return json.loads(clean[start:end])
    # Try as object with a key
    obj = json.loads(clean)
    for v in obj.values():
        if isinstance(v, list):
            return v
    return []


def _extracted_gaps_from_papers(papers: List[Dict]) -> List[Dict]:
    """Simple rule-based fallback gap extraction."""
    limitation_keywords = ["however", "limitation", "future work", "not considered",
                           "lack of", "insufficient", "limited", "cannot handle"]
    gaps = []
    for paper in papers[:10]:
        abstract = paper.get("abstract", "").lower()
        for kw in limitation_keywords:
            if kw in abstract:
                idx = abstract.find(kw)
                snippet = abstract[max(0, idx-20):idx+100]
                gaps.append({
                    "title": f"Gap from: {paper.get('title', 'Unknown')[:50]}",
                    "description": snippet,
                    "type": "methodological",
                    "confidence": "low",
                    "supporting_papers": [paper.get("title", "")],
                    "opportunity": "Address the mentioned limitation",
                    "novelty_potential": 5,
                })
                break

    return gaps[:6] if gaps else _default_gaps()


def _default_gaps() -> List[Dict]:
    return [
        {
            "title": "Insufficient paper data",
            "description": "Could not retrieve enough papers for proper gap analysis. Try refining your search query.",
            "type": "methodological",
            "confidence": "low",
            "supporting_papers": [],
            "opportunity": "Manually search for papers in your domain",
            "novelty_potential": 5,
        }
    ]
