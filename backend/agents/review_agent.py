"""
Review & Publish Agent
Generates review checklist, publication venue suggestions, and formatting guidelines.
"""

import json
from typing import Dict
from core.llm_client import LLMClient
from agents.shared.context_builder import parse_json

SYSTEM = "You are an academic publishing expert. Return ONLY valid JSON."

PROMPT = """Generate a review checklist and publication plan for this research project.

Title: {title}
Domain: {domain}
Approach: {approach}

Return this JSON structure:
{{
  "formatting_checklist": [
    {{"item": "Formatting requirement", "status": "pending", "details": "Details", "priority": "high"}}
  ],
  "plagiarism_guidelines": [
    {{"item": "Check item", "tool": "Tool name", "action": "What to do"}}
  ],
  "suggested_venues": [
    {{"name": "Venue name", "type": "conference|journal", "rank": "A|B|Q1|Q2", "deadline": "Month", "notes": "Why it fits", "acceptance_rate": "~XX%"}}
  ],
  "review_criteria": [
    {{"criterion": "Name", "what_to_check": "Check", "self_assessment": "good|fair|needs work", "improvement_tips": "Tips"}}
  ],
  "cover_letter_template": "Cover letter template for this project",
  "final_steps": [
    {{"step": 1, "task": "Task", "tools": ["tool"], "time": "Estimate"}}
  ]
}}

Be specific to this project. Include at least 5 checklist items, 3 venues, and 4 review criteria."""


async def run_review_generation(
    idea: Dict,
    llm: LLMClient,
    gaps: list = None,
    papers: list = None,
    plan: dict = None,
    objectives: list = None,
    intent: dict = None,
) -> Dict:
    title = idea.get("title", "N/A")
    domain = idea.get("domain", idea.get("description", "")[:100])
    approach = idea.get("approach", "")[:300]

    try:
        prompt = PROMPT.format(title=title, domain=domain, approach=approach)
        raw = await llm.complete(prompt, system=SYSTEM, json_mode=True)
        result = parse_json(raw)
        if isinstance(result, dict) and ("formatting_checklist" in result or "suggested_venues" in result):
            return result
    except Exception:
        pass

    # Fallback: return a structured default review
    return {
        "formatting_checklist": [
            {"item": "IEEE/ACM template compliance", "status": "pending", "details": "Use official template from target venue", "priority": "high"},
            {"item": "Page limit check", "status": "pending", "details": "Verify within venue page limits", "priority": "high"},
            {"item": "Reference formatting", "status": "pending", "details": "Ensure consistent citation style", "priority": "medium"},
            {"item": "Figure quality", "status": "pending", "details": "300+ DPI, vector preferred", "priority": "medium"},
            {"item": "Supplementary materials", "status": "pending", "details": "Code, data, appendix", "priority": "low"},
        ],
        "plagiarism_guidelines": [
            {"item": "Full text similarity check", "tool": "Turnitin/iThenticate", "action": "Run final draft through plagiarism detection"},
            {"item": "Self-plagiarism check", "tool": "Crossref", "action": "Verify no unintentional overlap with prior work"},
        ],
        "suggested_venues": [
            {"name": "ACL / EMNLP", "type": "conference", "rank": "A", "deadline": "Jan/May (annual)", "notes": "Top NLP venues, good for sentiment analysis research", "acceptance_rate": "~25%"},
            {"name": "AAAI / IJCAI", "type": "conference", "rank": "A", "deadline": "Aug (annual)", "notes": "Broad AI venue, welcomes applied NLP work", "acceptance_rate": "~20%"},
            {"name": "Journal of NLP (JNLP)", "type": "journal", "rank": "Q1", "deadline": "Rolling", "notes": "Good for journal-length extended version", "acceptance_rate": "~30%"},
        ],
        "review_criteria": [
            {"criterion": "Novelty", "what_to_check": "Is the approach genuinely new?", "self_assessment": "good", "improvement_tips": "Compare against most recent baselines"},
            {"criterion": "Technical Quality", "what_to_check": "Sound methodology and experiments", "self_assessment": "fair", "improvement_tips": "Add ablation studies and error analysis"},
            {"criterion": "Reproducibility", "what_to_check": "Can others reproduce the results?", "self_assessment": "needs work", "improvement_tips": "Release code and data, add detailed appendix"},
            {"criterion": "Writing Quality", "what_to_check": "Clear, well-structured paper", "self_assessment": "good", "improvement_tips": "Have native speaker review"},
        ],
        "cover_letter_template": f"""Dear Editor,

We submit our paper titled "{title}" for consideration in your venue.

This work addresses a critical gap in {domain} by proposing {approach}. Our key contributions include novel methodology and comprehensive experimental validation.

We believe this work is a strong fit for your venue given the growing interest in NLP-based {domain} solutions.

Sincerely,
[Author Names]""",
        "final_steps": [
            {"step": 1, "task": "Final proofread", "tools": ["Grammarly", "LanguageTool"], "time": "1 day"},
            {"step": 2, "task": "Format per venue guidelines", "tools": ["LaTeX", "Word template"], "time": "0.5 day"},
            {"step": 3, "task": "Prepare supplementary materials", "tools": ["GitHub", "Zenodo"], "time": "1 day"},
            {"step": 4, "task": "Submit to venue", "tools": ["OpenReview", "CMT"], "time": "0.5 day"},
        ],
        "detailed_explanation": f"Publication strategy for {title}. Target top NLP or AI venues for maximum impact.",
    }