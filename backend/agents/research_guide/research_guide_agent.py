"""
Research Guide Agent — Generates detailed project report, methodology, and tool recommendations.
Replaces the old code generation agent (Step 6).
"""

import json
import re
from typing import Dict, List, Any
from core.llm_client import LLMClient


GUIDE_SYSTEM = """You are a senior research methodology expert. Generate a comprehensive research guide.
Return ONLY valid JSON."""

GUIDE_PROMPT = """Generate a detailed research guide for this project.

Title: {title}
Domain: {domain}
Idea: {description}
Approach: {approach}
Novelty: {novelty}
Plan Overview: {overview}
Datasets: {datasets}
Evaluation Metrics: {metrics}
Risks: {risks}
Tech Stack: {tech_stack}

Related Papers:
{related_papers}

Return EXACTLY this JSON structure:
{{
  "project_report": {{
    "title": "Project Title",
    "executive_summary": "2-3 paragraph summary of the project, its goals, and expected outcomes",
    "methodology_walkthrough": [
      {{
        "step": "Step 1: ...",
        "description": "Detailed description of this step",
        "tools": ["tool1", "tool2"],
        "expected_output": "What this step produces",
        "time_estimate": "X-Y days/weeks"
      }}
    ],
    "tech_stack_recommendations": {{
      "programming_languages": ["Python"],
      "frameworks_libraries": ["PyTorch", "HuggingFace"],
      "experiment_tracking": ["wandb", "mlflow"],
      "data_tools": ["pandas", "numpy"],
      "visualization": ["matplotlib", "seaborn"],
      "compute_resources": ["local GPU", "Google Colab Pro", "AWS p3.2xlarge"],
      "estimated_costs": "Free to $XXX depending on compute"
    }},
    "research_methodology": {{
      "approach": "quantitative|qualitative|mixed",
      "data_collection": "How data will be collected or sourced",
      "experiment_design": "How experiments are structured",
      "statistical_analysis": "What statistical methods to use",
      "validation_strategy": "Cross-validation, held-out test set, human evaluation"
    }},
    "related_work_deep_dive": [
      {{
        "topic": "Topic area",
        "key_papers": ["Paper 1: Key finding", "Paper 2: Key finding"],
        "how_this_differs": "How your work differs from or advances this area"
      }}
    ],
    "project_timeline": [
      {{
        "phase": "Phase name",
        "duration": "X weeks",
        "tasks": ["task 1", "task 2"],
        "milestones": ["milestone 1"]
      }}
    ],
    "success_criteria": ["criterion 1", "criterion 2"],
    "potential_challenges": ["challenge 1", "challenge 2"],
    "mitigation_strategies": ["strategy 1", "strategy 2"]
  }}
}}"""


async def run_research_guide_generation(
    idea: Dict,
    papers: List[Dict],
    gaps: List[Dict],
    plan: Dict,
    intent: Dict,
    llm: LLMClient,
) -> Dict:
    """Generate a comprehensive research guide."""
    domain_list = intent.get("domain", ["AI/ML"])
    domain = ", ".join(str(d) if not isinstance(d, dict) else d.get("name", str(d)) for d in domain_list)
    related = _format_papers_for_prompt(papers[:8])
    datasets = [d.get("name", "") for d in plan.get("datasets", [])]
    metrics = plan.get("evaluation_metrics", [])
    risks_list = plan.get("risks", [])
    risks = [r.get("risk", str(r)) if isinstance(r, dict) else str(r) for r in risks_list]
    tech = plan.get("tech_stack", {})

    prompt = GUIDE_PROMPT.format(
        title=idea.get("title", "Research Project"),
        domain=domain,
        description=idea.get("description", ""),
        approach=idea.get("approach", ""),
        novelty=idea.get("novelty", ""),
        overview=plan.get("overview", ""),
        datasets=", ".join(str(d) for d in datasets if d) or "standard benchmarks",
        metrics=", ".join(str(m) for m in metrics if m) or "accuracy, F1",
        risks="; ".join(str(r) for r in risks if r) if risks else "None identified",
        tech_stack=json.dumps(tech, indent=1) if tech else "Standard ML stack",
        related_papers=related,
    )

    try:
        raw = await llm.complete(prompt, system=GUIDE_SYSTEM, json_mode=True)
        result = _parse_json(raw)
        if "project_report" in result:
            return result
        raise ValueError("LLM response missing 'project_report' key")
    except Exception as e:
        print(f"Research guide error: {e}")
        raise ValueError(f"Guide generation failed: {e}") from e


def _format_papers_for_prompt(papers: List[Dict]) -> str:
    lines = []
    for i, p in enumerate(papers, 1):
        authors = ", ".join(p.get("authors", ["Unknown"])[:3])
        text = p.get("full_text") or p.get("abstract", "")
        snippet = text[:150].replace("\n", " ")
        lines.append(f"[{i}] {authors}. \"{p.get('title', '')}\" — {snippet}...")
    return "\n".join(lines)


def _parse_json(raw: str) -> Dict:
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    s, e = clean.find("{"), clean.rfind("}") + 1
    return json.loads(clean[s:e]) if s != -1 and e > s else {}
