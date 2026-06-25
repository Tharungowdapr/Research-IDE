"""
Objective Generator Agent
Generates SMART research objectives from a selected idea and full project context.
"""

import json
from typing import List, Dict
from core.llm_client import LLMClient
from agents.shared.context_builder import format_project_context, parse_json

SYSTEM = "You are a research methodology expert. Return ONLY valid JSON."

PROMPT = """Generate 5 detailed SMART research objectives for this project.

Full Project Context:
{full_context}

Research Gap driving this work:
{gap_description}

Return EXACTLY this JSON array of 5 objectives:
[
  {{
    "objective": "Specific, measurable research objective (one clear sentence)",
    "type": "exploratory|developmental|evaluatory|comparative",
    "success_criteria": "How to measure success — specific metric or milestone",
    "timeline": "Estimated time to complete (e.g., X-Y weeks)",
    "methodology_hint": "Brief hint on how to achieve this (specific tools or techniques)",
    "detailed_explanation": "3-4 sentence explanation of why this objective matters, how it addresses the gap, and what the expected outcome is",
    "key_deliverables": ["deliverable 1", "deliverable 2", "deliverable 3"],
    "risks": ["risk 1", "risk 2"]
  }}
]

IMPORTANT: Each objective must be SPECIFICALLY tied to this project idea and gap — not generic. The detailed_explanation must reference the actual research problem."""


async def run_objective_generation(
    idea: Dict,
    gaps: List[Dict],
    llm: LLMClient,
    plan: Dict = None,
    papers: List[Dict] = None,
    intent: Dict = None,
) -> List[Dict]:
    gap_desc = ""
    if gaps:
        gap_desc = gaps[0].get("description", "")

    full_context = format_project_context(
        idea=idea,
        gaps=gaps,
        papers=papers,
        plan=plan,
        intent=intent,
    )

    try:
        prompt = PROMPT.format(
            full_context=full_context or "No additional context available.",
            gap_description=gap_desc or "Not specified",
        )
        raw = await llm.complete(prompt, system=SYSTEM, json_mode=True)
        result = parse_json(raw)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "objectives" in result and isinstance(result["objectives"], list):
            return result["objectives"]
        raise ValueError(f"LLM returned invalid format: {str(raw)[:200]}")
    except Exception as e:
        raise ValueError(f"Objective generation failed: {e}") from e
