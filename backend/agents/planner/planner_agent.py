"""
Planner Agent — Methodology & Architecture Plan
Focuses on: project structure, tech stack, architecture overview, phases, risks, budget
"""

import json
import re
from typing import Dict, List, AsyncGenerator
from core.llm_client import LLMClient

PLAN_SYSTEM = "You are a senior ML researcher and system architect. Return ONLY valid JSON."

PLAN_PROMPT = """Create a methodology and architecture plan for this research idea.

Idea: {title}
Description: {description}
Approach: {approach}
Domain Context: {domain}

Return a JSON object with ALL these fields:
{{
  "overview": "2-3 sentence project overview describing what this project builds and why",

  "architecture": {{
    "components": ["component 1", "component 2"],
    "diagram_description": "Text description of the system architecture and how components interact"
  }},

  "project_structure": [
    "src/ — Source code",
    "src/model.py — Model architecture definition",
    "src/train.py — Training loop",
    "src/data.py — Data loading and preprocessing",
    "src/eval.py — Evaluation and metrics",
    "configs/ — Configuration files",
    "notebooks/ — Exploration notebooks",
    "tests/ — Unit tests",
    "requirements.txt — Dependencies",
    "README.md — Setup and usage"
  ],

  "phases": [
    {{
      "phase": 1,
      "name": "Phase name",
      "duration": "X weeks",
      "tasks": ["task 1", "task 2"],
      "deliverables": ["deliverable 1"],
      "dependencies": [],
      "resources_required": {{"gpu": "1x RTX 3090", "memory": "32GB", "storage": "50GB", "compute_hours": 100}},
      "milestones": [
        {{"name": "Milestone name", "criteria": "go/no-go criteria", "deadline": "End of week X"}}
      ]
    }}
  ],

  "tech_stack": {{
    "languages": ["Python"],
    "frameworks": ["PyTorch", "HuggingFace"],
    "tools": ["wandb", "docker"],
    "infrastructure": ["local GPU or Colab"],
    "collaboration": ["GitHub", "Overleaf"]
  }},

  "datasets": [
    {{"name": "Dataset name", "source": "URL or description", "why": "Why this dataset", "size": "~X GB", "licensing": "MIT / CC-BY"}}
  ],

  "evaluation_metrics": ["metric 1", "metric 2"],
  "baseline_comparison": "What to compare against",

  "risks": [
    {{"risk": "Risk description", "severity": "high|medium|low", "mitigation": "How to mitigate", "contingency": "Fallback plan"}}
  ],

  "total_estimate": "X-Y months",

  "budget_estimation": {{
    "compute_costs": "$XXX - $XXX for cloud GPU",
    "api_costs": "$XX - $XX for LLM APIs",
    "dataset_licensing": "Free / $XXX for proprietary data",
    "total_estimated": "$XXX - $XXX"
  }},

  "literature_review_plan": [
    {{"priority": 1, "topic": "Core methodology", "key_papers": ["Paper A (2024)", "Paper B (2023)"], "why_first": "Foundational reading before implementation"}}
  ]
}}"""


async def run_planning(idea: Dict, intent: Dict, llm: LLMClient, papers: List[Dict] = None) -> Dict:
    """Generate methodology and architecture plan."""
    domain = ", ".join(intent.get("domain", ["AI/ML"]))

    prompt = PLAN_PROMPT.format(
        title=idea.get("title", "Research Idea"),
        description=idea.get("description", ""),
        approach=idea.get("approach", ""),
        domain=domain,
    )
    try:
        raw = await llm.complete(prompt, system=PLAN_SYSTEM, json_mode=True)
        plan = _parse_json(raw)
        if not plan:
            raise ValueError("Plan generation failed: LLM returned empty or unparseable response")
    except Exception as e:
        raise ValueError(f"Plan generation failed: {e}") from e

    return plan


async def run_planning_stream(idea: Dict, intent: Dict, llm: LLMClient, papers: List[Dict] = None) -> AsyncGenerator[str, None]:
    """Stream methodology and architecture plan."""
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    paper_titles = ", ".join(p.get("title", "")[:60] for p in (papers or [])[:5])

    COMBINED_PROMPT = """Create a methodology and architecture plan for this research idea.

Idea: {title}
Approach: {approach}
Domain Context: {domain}
Related Papers: {paper_titles}

Return ONE JSON object EXACTLY matching this structure:
{{
  "overview": "2-3 sentence project overview",
  "architecture": {{
    "components": ["component 1", "component 2"],
    "diagram_description": "Text description of the system architecture"
  }},
  "project_structure": [
    "src/ — Source code",
    "src/model.py — Model architecture",
    "src/train.py — Training loop",
    "src/data.py — Data loading",
    "configs/ — Config files",
    "tests/ — Unit tests",
    "requirements.txt — Dependencies",
    "README.md — Setup guide"
  ],
  "phases": [
    {{
      "phase": 1,
      "name": "Phase name",
      "duration": "X weeks",
      "tasks": ["task 1", "task 2"],
      "deliverables": ["deliverable 1"],
      "dependencies": [],
      "resources_required": {{"gpu": "1x RTX 3090", "memory": "32GB", "storage": "50GB", "compute_hours": 100}},
      "milestones": [
        {{"name": "Milestone name", "criteria": "go/no-go criteria", "deadline": "End of week X"}}
      ]
    }}
  ],
  "tech_stack": {{
    "languages": ["Python"],
    "frameworks": ["PyTorch", "HuggingFace"],
    "tools": ["wandb", "docker"],
    "infrastructure": ["local GPU or Colab"],
    "collaboration": ["GitHub", "Overleaf"]
  }},
  "datasets": [
    {{"name": "Dataset name", "source": "URL", "why": "Why this dataset", "size": "~X GB", "licensing": "MIT"}}
  ],
  "evaluation_metrics": ["metric 1", "metric 2"],
  "baseline_comparison": "What to compare against",
  "risks": [
    {{"risk": "Risk description", "severity": "high|medium|low", "mitigation": "How to mitigate", "contingency": "Fallback plan"}}
  ],
  "total_estimate": "X-Y months",
  "budget_estimation": {{
    "compute_costs": "$XXX cloud GPU",
    "api_costs": "$XX APIs",
    "dataset_licensing": "Free / $XXX",
    "total_estimated": "$XXX - $XXX"
  }},
  "literature_review_plan": [
    {{"priority": 1, "topic": "Core methodology", "key_papers": ["Paper A"], "why_first": "Why to read this first"}}
  ]
}}
"""

    prompt = COMBINED_PROMPT.format(
        title=idea.get("title", "Research Idea"),
        approach=idea.get("approach", ""),
        domain=domain,
        paper_titles=paper_titles or "various recent works"
    )

    try:
        async for chunk in llm.stream_complete(prompt, system=PLAN_SYSTEM, json_mode=True):
            yield chunk
    except Exception as e:
        raise ValueError(f"Plan generation failed: {e}") from e


def _parse_json(raw: str) -> Dict:
    if not raw or not raw.strip():
        return {}
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    s, e = clean.find("{"), clean.rfind("}") + 1
    if s != -1 and e > s:
        try:
            return json.loads(clean[s:e])
        except json.JSONDecodeError:
            pass
    try:
        cleaned = clean.strip().rstrip(",").rstrip(".").strip()
        s = cleaned.find("{")
        if s != -1:
            partial = cleaned[s:]
            depth = 0
            for i, ch in enumerate(partial):
                if ch == "{": depth += 1
                elif ch == "}": depth -= 1
                if depth == 0 and i > 0:
                    return json.loads(partial[:i+1])
    except (json.JSONDecodeError, Exception):
        pass
    return {}
