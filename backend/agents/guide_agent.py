"""
Guide Agent — Generates comprehensive research guides with methodology,
tech stack recommendations, timelines, and success criteria.
"""

import json
import re
from typing import Dict, List, Any
from core.llm_client import LLMClient


GUIDE_SYSTEM = """You are an expert research methodology advisor. Generate a comprehensive 
research guide with actionable methodology steps, tool recommendations, and timelines.
Return ONLY valid JSON."""

GUIDE_PROMPT = """Generate a detailed research execution guide for this project:

Title: {title}
Domain: {domain}
Research Description: {description}
Proposed Approach: {approach}
Novelty: {novelty}
Methodology: {methodology}
Key Papers:
{papers_summary}
Plan Overview: {plan_overview}
Gaps Addressed: {gaps}

Return this EXACT JSON structure:
{{
  "project_report": {{
    "executive_summary": "2-3 paragraph executive summary of the project",
    "methodology_walkthrough": [
      {{
        "step": "Step name",
        "description": "Detailed description of the step with rationale",
        "tools": ["tool1", "tool2"],
        "time_estimate": "estimated time",
        "difficulty": "beginner/intermediate/advanced"
      }}
    ],
    "tech_stack_recommendations": {{
      "frameworks": ["framework1", "framework2"],
      "libraries": ["library1", "library2"],
      "tools": ["tool1", "tool2"],
      "datasets": ["dataset1", "dataset2"],
      "hardware": ["hardware requirement"]
    }},
    "research_methodology": {{
      "approach_type": "qualitative/quantitative/mixed",
      "data_collection": "method description",
      "evaluation_framework": "evaluation approach",
      "validation_strategy": "validation approach"
    }},
    "related_work_deep_dive": [
      {{
        "topic": "Research topic area",
        "key_papers": ["paper title 1", "paper title 2"],
        "how_this_differs": "How your approach differs"
      }}
    ],
    "project_timeline": [
      {{
        "phase": "Phase name",
        "duration": "2 weeks",
        "tasks": ["task1", "task2"]
      }}
    ],
    "success_criteria": ["criterion1", "criterion2"],
    "potential_challenges": ["challenge1", "challenge2"],
    "mitigation_strategies": ["strategy1", "strategy2"],
    "resources_needed": ["resource1", "resource2"]
  }}
}}"""


async def run_guide_generation(
    idea: Dict,
    papers: List[Dict],
    gaps: List[Dict],
    plan: Dict,
    intent: Dict,
    llm: LLMClient,
) -> Dict:
    """Generate a comprehensive research guide."""
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    papers_summary = _format_papers_for_prompt(papers[:10])
    gap_titles = [g.get("title", "") for g in gaps[:3]]

    prompt = GUIDE_PROMPT.format(
        title=idea.get("title", "Research Project"),
        domain=domain,
        description=idea.get("description", ""),
        approach=idea.get("approach", ""),
        novelty=idea.get("novelty", ""),
        methodology=idea.get("methodology", ""),
        papers_summary=papers_summary,
        plan_overview=plan.get("overview", plan.get("introduction", "")),
        gaps=", ".join(gap_titles) or "identified research gaps",
    )

    try:
        raw = await llm.complete(prompt, system=GUIDE_SYSTEM, json_mode=True)
        result = _parse_json(raw)
        if result and "project_report" in result:
            return result
        raise ValueError("Guide generation failed: LLM output missing 'project_report'")
    except Exception as e:
        raise ValueError(f"Guide generation failed: {e}") from e


def _format_papers_for_prompt(papers: List[Dict]) -> str:
    lines = []
    for i, p in enumerate(papers, 1):
        authors = ", ".join(p.get("authors", ["Unknown"])[:3])
        title = p.get("title", "Untitled")
        year = p.get("year", "N/A")
        abstract = (p.get("abstract", "") or "")[:200]
        lines.append(f"{i}. [{year}] {authors}. \"{title}\".\n   {abstract}...")
    return "\n\n".join(lines)



def _parse_json(raw: str) -> Dict:
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    s, e = clean.find("{"), clean.rfind("}") + 1
    return json.loads(clean[s:e]) if s != -1 and e > s else {}
