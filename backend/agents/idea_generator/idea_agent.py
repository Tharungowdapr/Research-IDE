"""
Idea Generation Agent
Generates ranked, novel research ideas based on gaps and context.
"""

import json
import re
from typing import List, Dict, Any
from core.llm_client import LLMClient


IDEA_SYSTEM = """You are a creative research idea generator. 
Generate specific, actionable, and novel research ideas. Return ONLY valid JSON."""

IDEA_PROMPT_TEMPLATE = """Generate innovative research ideas based on these gaps.

Research Domain: {domain}
Problem: {problem}
Constraints: {constraints}

Identified Research Gaps:
{gaps_summary}

Key Papers Context:
{papers_summary}

Generate 4 ranked research ideas as a JSON array:
[
  {{
    "title": "Concise idea title",
    "description": "2-3 sentence description of the research idea",
    "novelty": "Why this is novel — what hasn't been done",
    "approach": "High-level technical approach (2-3 sentences)",
    "addresses_gaps": ["gap title 1", "gap title 2"],
    "related_papers": ["paper 1", "paper 2"],
    "suggested_datasets": ["dataset 1", "dataset 2"],
    "suggested_methods": ["method 1", "method 2"],
    "feasibility": "high|medium|low",
    "expected_impact": "high|medium|low",
    "novelty_score": 7.5,
    "feasibility_score": 6.0,
    "time_estimate": "2-3 months",
    "difficulty": "beginner|intermediate|advanced"
  }}
]"""


async def run_idea_generation(
    gaps: List[Dict],
    papers: List[Dict],
    intent: Dict,
    llm: LLMClient,
) -> List[Dict]:
    """Generate research ideas from gaps and paper context."""
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    problem = intent.get("problem_statement", "")
    constraints = _format_constraints(intent.get("constraints", {}))
    gaps_summary = _summarize_gaps(gaps)
    papers_summary = _summarize_papers_brief(papers[:8])

    prompt = IDEA_PROMPT_TEMPLATE.format(
        domain=domain,
        problem=problem,
        constraints=constraints,
        gaps_summary=gaps_summary,
        papers_summary=papers_summary,
    )

    try:
        raw = await llm.complete(prompt, system=IDEA_SYSTEM, json_mode=True)
        ideas = _parse_json_list(raw)
        if ideas:
            ideas = _rank_ideas(ideas)
            return ideas
        return _fallback_ideas(gaps, intent)
    except Exception as e:
        print(f"Idea generation error: {e}")
        return _fallback_ideas(gaps, intent)


def _format_constraints(constraints: Dict) -> str:
    parts = []
    if constraints.get("compute"):
        parts.append(f"Compute: {constraints['compute']}")
    if constraints.get("region"):
        parts.append(f"Region: {constraints['region']}")
    if constraints.get("real_time"):
        parts.append("Real-time required")
    return ", ".join(parts) or "No specific constraints"


def _summarize_gaps(gaps: List[Dict]) -> str:
    return "\n".join(
        f"- {g.get('title', 'Unknown')}: {g.get('description', '')[:150]}"
        for g in gaps[:6]
    )


def _summarize_papers_brief(papers: List[Dict]) -> str:
    return "\n".join(
        f"- [{p.get('year','')}] {p.get('title','')}: {p.get('abstract','')[:100]}..."
        for p in papers
    )


def _rank_ideas(ideas: List[Dict]) -> List[Dict]:
    """Sort ideas by combined novelty + feasibility score."""
    def score(idea):
        n = float(idea.get("novelty_score", 5))
        f = float(idea.get("feasibility_score", 5))
        return n * 0.6 + f * 0.4
    return sorted(ideas, key=score, reverse=True)


def _parse_json_list(raw: str) -> List[Dict]:
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    start = clean.find("[")
    end = clean.rfind("]") + 1
    if start != -1 and end > start:
        return json.loads(clean[start:end])
    obj = json.loads(clean)
    for v in obj.values():
        if isinstance(v, list):
            return v
    return []


def _fallback_ideas(gaps: List[Dict], intent: Dict) -> List[Dict]:
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    return [
        {
            "title": f"Novel approach addressing {g.get('title', 'research gap')}",
            "description": f"Develop a new approach that addresses: {g.get('description', '')[:200]}",
            "novelty": "Addresses an identified gap in the literature",
            "approach": "Literature-driven methodology development",
            "addresses_gaps": [g.get("title", "")],
            "related_papers": g.get("supporting_papers", []),
            "suggested_datasets": [],
            "suggested_methods": [],
            "feasibility": "medium",
            "expected_impact": "medium",
            "novelty_score": 6.0,
            "feasibility_score": 5.0,
            "time_estimate": "3-6 months",
            "difficulty": "intermediate",
        }
        for g in gaps[:3]
    ]
