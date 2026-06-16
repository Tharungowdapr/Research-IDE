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
        return _fallback_guide(idea, papers, gaps, plan, intent)
    except Exception as e:
        print(f"Guide agent error: {e}")
        return _fallback_guide(idea, papers, gaps, plan, intent)


def _format_papers_for_prompt(papers: List[Dict]) -> str:
    lines = []
    for i, p in enumerate(papers, 1):
        authors = ", ".join(p.get("authors", ["Unknown"])[:3])
        title = p.get("title", "Untitled")
        year = p.get("year", "N/A")
        abstract = (p.get("abstract", "") or "")[:200]
        lines.append(f"{i}. [{year}] {authors}. \"{title}\".\n   {abstract}...")
    return "\n\n".join(lines)


def _fallback_guide(idea: Dict, papers: List[Dict], gaps: List[Dict], plan: Dict, intent: Dict) -> Dict:
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    description = idea.get("description", "the research problem")

    methodology_steps = []
    if plan:
        phases = plan.get("phases", plan.get("steps", []))
        for i, phase in enumerate(phases):
            methodology_steps.append({
                "step": phase.get("phase", phase.get("name", f"Phase {i+1}")),
                "description": phase.get("description", f"Execute {phase.get('phase', f'phase {i+1}')}"),
                "tools": phase.get("tools", []),
                "time_estimate": phase.get("duration", "TBD"),
                "difficulty": "intermediate",
            })

    if not methodology_steps:
        methodology_steps = [
            {"step": "Literature Review", "description": f"Conduct comprehensive review of {domain} literature", "tools": ["Semantic Scholar", "Google Scholar"], "time_estimate": "2-3 weeks", "difficulty": "beginner"},
            {"step": "Data Collection", "description": f"Gather and prepare datasets for {domain} research", "tools": ["Python", "Pandas"], "time_estimate": "3-4 weeks", "difficulty": "intermediate"},
            {"step": "Implementation", "description": f"Implement proposed methodology for {description}", "tools": ["PyTorch", "scikit-learn"], "time_estimate": "4-6 weeks", "difficulty": "advanced"},
            {"step": "Evaluation", "description": "Evaluate results against baselines and state-of-the-art", "tools": ["Jupyter", "Weights & Biases"], "time_estimate": "2-3 weeks", "difficulty": "intermediate"},
            {"step": "Paper Writing", "description": "Write and format the research paper", "tools": ["LaTeX", "Overleaf"], "time_estimate": "2-3 weeks", "difficulty": "beginner"},
        ]

    gap_names = [g.get("title", "") for g in (gaps or [])[:3]]

    return {
        "project_report": {
            "executive_summary": f"This research project addresses {description} in the domain of {domain}. "
                               f"The proposed approach combines established methodologies with novel contributions "
                               f"to advance the state of the art. The guide below provides a comprehensive roadmap "
                               f"for executing this research project successfully.",
            "methodology_walkthrough": methodology_steps,
            "tech_stack_recommendations": {
                "frameworks": ["PyTorch", "TensorFlow", "scikit-learn"],
                "libraries": ["transformers", "datasets", "numpy", "pandas"],
                "tools": ["Jupyter Notebook", "Weights & Biases", "Git"],
                "datasets": ["domain-specific datasets"],
                "hardware": ["GPU (minimum 8GB VRAM)", "16GB+ RAM"],
            },
            "research_methodology": {
                "approach_type": "mixed",
                "data_collection": "Automated data collection from public datasets and benchmarks",
                "evaluation_framework": "Standard metrics and cross-validation with statistical significance testing",
                "validation_strategy": "Hold-out validation with multiple train-test splits",
            },
            "related_work_deep_dive": [
                {
                    "topic": domain,
                    "key_papers": [p.get("title", "") for p in papers[:5]],
                    "how_this_differs": f"This work addresses gaps not covered in existing {domain} literature",
                }
            ],
            "project_timeline": [
                {"phase": "Literature Review", "duration": "2-3 weeks", "tasks": ["Review related work", "Identify gaps", "Refine research questions"]},
                {"phase": "Implementation", "duration": "4-6 weeks", "tasks": ["Set up environment", "Implement baseline", "Develop proposed method"]},
                {"phase": "Experimentation", "duration": "3-4 weeks", "tasks": ["Run experiments", "Collect results", "Statistical analysis"]},
                {"phase": "Paper Writing", "duration": "2-3 weeks", "tasks": ["Write draft", "Create figures", "Format and submit"]},
            ],
            "success_criteria": [
                "Outperform baseline methods on primary metrics",
                "Ablation studies validate each component's contribution",
                "Reproducible results with documented code and data",
            ],
            "potential_challenges": [
                "Limited computational resources",
                "Data availability and quality",
                "Reproducibility across different environments",
            ],
            "mitigation_strategies": [
                "Use cloud computing and pre-trained models to reduce compute needs",
                "Leverage multiple data sources and augmentation techniques",
                "Containerize environment and document all dependencies",
            ],
            "resources_needed": [
                "GPU compute (cloud or local)",
                f"Access to {domain} datasets",
                "Python development environment",
            ],
        }
    }


def _parse_json(raw: str) -> Dict:
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    s, e = clean.find("{"), clean.rfind("}") + 1
    return json.loads(clean[s:e]) if s != -1 and e > s else {}
