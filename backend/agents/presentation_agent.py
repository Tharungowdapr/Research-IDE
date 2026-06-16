"""
Presentation Agent — Generates presentation slide content from research context.
"""

import json
import re
from typing import Dict, List, Any
from core.llm_client import LLMClient


PRESENTATION_SYSTEM = """You are an expert at creating academic presentation content.
Generate well-structured slide decks that effectively communicate research.
Return ONLY valid JSON."""

PRESENTATION_PROMPT = """Create a presentation slide deck for this research project:

Title: {title}
Domain: {domain}
Description: {description}
Approach: {approach}
Novelty: {novelty}
Key Results: {results}

Executive Summary: {executive_summary}

Generate 8-12 slides as a JSON array:
[
  {{
    "title": "Slide Title",
    "subtitle": "optional subtitle",
    "bullets": [
      "bullet point 1",
      "bullet point 2"
    ],
    "notes": "speaker notes for this slide"
  }}
]

Include slides for: Title, Problem Statement, Related Work, Methodology, 
Key Contributions, Experiments/Results, Discussion, Conclusion, Future Work, Thank You."""


async def run_presentation_generation(
    guide: Dict,
    idea: Dict,
    papers: List[Dict],
    intent: Dict,
    llm: LLMClient,
) -> Dict:
    """Generate presentation slide content."""
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    report = guide.get("project_report", {}) if guide else {}

    prompt = PRESENTATION_PROMPT.format(
        title=idea.get("title", "Research Project"),
        domain=domain,
        description=idea.get("description", ""),
        approach=idea.get("approach", ""),
        novelty=idea.get("novelty", ""),
        results=idea.get("expected_results", ""),
        executive_summary=report.get("executive_summary", ""),
    )

    try:
        raw = await llm.complete(prompt, system=PRESENTATION_SYSTEM, json_mode=True)
        result = _parse_json(raw)
        if isinstance(result, list) and len(result) > 0:
            return {"slides": result}
        if isinstance(result, dict) and "slides" in result:
            return result
        return _fallback_presentation(idea, papers, domain)
    except Exception as e:
        print(f"Presentation agent error: {e}")
        return _fallback_presentation(idea, papers, domain)


def _fallback_presentation(idea: Dict, papers: List[Dict], domain: str) -> Dict:
    title = idea.get("title", "Research Project")
    description = idea.get("description", "")
    approach = idea.get("approach", "")

    slides = [
        {"title": title, "subtitle": f"A Novel Approach in {domain}", "bullets": ["Research Project Overview"], "notes": "Welcome everyone"},
        {"title": "Problem Statement", "bullets": [description, "Current approaches have limitations requiring novel solutions"], "notes": ""},
        {"title": "Related Work", "bullets": [p.get("title", "") for p in papers[:4]], "notes": "Overview of existing literature"},
        {"title": "Proposed Approach", "bullets": [approach, "Novel methodology addressing identified gaps"], "notes": ""},
        {"title": "Methodology", "bullets": ["Systematic approach to research", "Rigorous evaluation framework", "Reproducible experiments"], "notes": ""},
        {"title": "Key Contributions", "bullets": ["Novel approach to the problem", "Comprehensive evaluation", "Open-source implementation"], "notes": ""},
        {"title": "Expected Results", "bullets": ["Improved performance over baselines", "Significant findings in the domain", "Practical implications"], "notes": ""},
        {"title": "Conclusion & Future Work", "bullets": ["Summary of contributions", "Limitations and future directions", "Call for collaboration"], "notes": ""},
    ]

    return {"slides": slides}


def _parse_json(raw: str) -> Any:
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    s = clean.find("[")
    if s == -1:
        s = clean.find("{")
    if s == -1:
        return None
    if clean[s] == "[":
        e = clean.rfind("]") + 1
    else:
        e = clean.rfind("}") + 1
    return json.loads(clean[s:e]) if e > s else None
