"""
Review & Publish Agent
Generates review checklist, publication venue suggestions, and formatting guidelines.
"""

import json
from typing import Dict
from core.llm_client import LLMClient
from agents.shared.context_builder import format_project_context, parse_json

SYSTEM = "You are an academic publishing expert. Return ONLY valid JSON."

PROMPT = """Generate a detailed review checklist and publication plan for this research project.

Full Project Context:
{full_context}

Return EXACTLY this JSON structure with comprehensive, project-specific content:
{{
  "formatting_checklist": [
    {{"item": "Specific formatting requirement", "status": "pending", "details": "How to comply, with specific template references", "priority": "high|medium|low"}}
  ],
  "plagiarism_guidelines": [
    {{"item": "Specific plagiarism check item", "tool": "Recommended tool name", "action": "What to do"}}
  ],
  "suggested_venues": [
    {{"name": "Venue full name", "type": "conference|journal|workshop", "rank": "A*|A|B|C|Q1|Q2", "deadline": "Month or Rolling", "notes": "Why this venue fits this specific project", "acceptance_rate": "~XX%", "review_time": "X-Y months", "why_good_fit": "Specific explanation linking project to venue scope"}}
  ],
  "review_criteria": [
    {{"criterion": "Criterion name", "what_to_check": "What reviewers will look for", "self_assessment": "good|fair|needs work", "improvement_tips": "How to strengthen this aspect"}}
  ],
  "cover_letter_template": "Full cover letter template with placeholders for specific project details",
  "final_steps": [
    {{"step": 1, "task": "Specific task", "tools": ["tool1", "tool2"], "time": "time estimate", "details": "How to execute this step"}}
  ],
  "detailed_explanation": "2-3 paragraph summary of the publication strategy, target audience, and key selling points of this paper"
}}

IMPORTANT: Be SPECIFIC to this project — reference the actual idea title, approach, and domain in venue suggestions and checklist items. The cover letter template must mention the actual research contribution."""

async def run_review_generation(
    idea: Dict,
    llm: LLMClient,
    gaps: list = None,
    papers: list = None,
    plan: dict = None,
    objectives: list = None,
    intent: dict = None,
) -> Dict:
    full_context = format_project_context(
        idea=idea, gaps=gaps, papers=papers,
        plan=plan, objectives=objectives, intent=intent,
    )

    try:
        prompt = PROMPT.format(
            full_context=full_context or f"Research: {idea.get('title', 'N/A')}"
        )
        raw = await llm.complete(prompt, system=SYSTEM, json_mode=True)
        result = parse_json(raw)
        if isinstance(result, dict) and ("formatting_checklist" in result or "suggested_venues" in result):
            return result
        raise ValueError(f"LLM returned invalid format: {str(raw)[:200]}")
    except Exception as e:
        raise ValueError(f"Review generation failed: {e}") from e
