"""
Presentation Agent — Generates presentation slide content from research context.
"""

import json
from typing import Dict, List, Any
from core.llm_client import LLMClient
from agents.shared.context_builder import format_project_context, parse_json


PRESENTATION_SYSTEM = """You are an expert at creating academic presentation content.
Generate well-structured slide decks that effectively communicate research.
Each slide should have 3-5 substantive bullet points.
Return ONLY valid JSON."""

PRESENTATION_PROMPT = """Create a professional slide deck for this research project.

Full Project Context:
{full_context}

Generate 10-14 slides as a JSON array. Each slide:
[
  {{
    "title": "Specific, descriptive slide title",
    "subtitle": "optional subtitle",
    "bullets": [
      "bullet point 1 — specific and detailed",
      "bullet point 2 — references actual data/approach",
      "bullet point 3 — connects to project contribution"
    ],
    "notes": "2-3 sentence speaker notes explaining what to say"
  }}
]

Required slide topics (in order):
1. Title Slide (project title, authors, affiliation)
2. Problem Statement (specific research problem, motivation)
3. Background & Related Work (key prior work, identified gaps)
4. Research Gap (what's missing, why it matters)
5. Proposed Approach (high-level methodology)
6. Technical Details (key innovations, architecture)
7. Experimental Setup (datasets, metrics, baselines)
8. Expected Results (what we anticipate finding)
9. Contributions (specific, numbered contributions)
10. Conclusion & Future Work
11. Thank You / Q&A

IMPORTANT: Every slide must contain project-specific content. No generic slides. Reference actual approach name, datasets, and methods from the context."""


async def run_presentation_generation(
    guide: Dict,
    idea: Dict,
    papers: List[Dict],
    intent: Dict,
    llm: LLMClient,
    gaps: list = None,
    plan: dict = None,
) -> Dict:
    full_context = format_project_context(
        idea=idea, gaps=gaps, papers=papers,
        plan=plan, intent=intent,
    )
    report = guide.get("project_report", {}) if guide else {}

    prompt = PRESENTATION_PROMPT.format(
        full_context=full_context or f"Idea: {idea.get('title', 'N/A')}"
    )

    try:
        raw = await llm.complete(prompt, system=PRESENTATION_SYSTEM, json_mode=True)
        result = parse_json(raw)
        if isinstance(result, list) and len(result) >= 3:
            return {"slides": result}
        if isinstance(result, dict) and "slides" in result:
            return result
        raise ValueError("Presentation generation returned invalid format")
    except Exception as e:
        raise ValueError(f"Presentation generation failed: {e}") from e
