"""
Planner Agent — Enhanced Execution Plan Generation
Includes: Gantt-style timeline, resource allocation, milestones, risk mitigation, budget, lit review plan
"""

import json
import re
from typing import Dict, List, Any, AsyncGenerator
from core.llm_client import LLMClient

PLAN_SYSTEM = "You are a senior ML researcher and system architect. Return ONLY valid JSON."

PLAN_PROMPT = """Create a detailed execution plan for this research idea.

Idea: {title}
Description: {description}
Approach: {approach}
Domain Context: {domain}

Return a JSON object with ALL fields:
{{
  "overview": "2-3 sentence project overview",
  "architecture": {{
    "components": ["component 1", "component 2"],
    "diagram_description": "Text description of the system architecture"
  }},
  "phases": [
    {{
      "phase": 1,
      "name": "Phase name",
      "duration": "X weeks",
      "tasks": ["task 1", "task 2"],
      "deliverables": ["deliverable 1"],
      "dependencies": ["phase 0"],  
      "resources_required": {{"gpu": "1x RTX 3090", "memory": "32GB", "storage": "50GB", "compute_hours": 100}},
      "milestones": [
        {{"name": "Milestone name", "criteria": "go/no-go criteria for this milestone", "deadline": "End of week X"}}
      ]
    }}
  ],
  "tech_stack": {{
    "languages": ["Python"],
    "frameworks": ["PyTorch", "HuggingFace"],
    "tools": ["wandb", "docker"],
    "infrastructure": ["local GPU or Colab"],
    "collaboration": ["GitHub", "Overleaf", "Slack"]
  }},
  "datasets": [
    {{"name": "Dataset name", "source": "URL or description", "why": "Why this dataset", "size": "~X GB", "licensing": "MIT / CC-BY"}}
  ],
  "evaluation_metrics": ["metric 1", "metric 2"],
  "baseline_comparison": "What to compare against",
  "risks": [
    {{"risk": "Data scarcity", "severity": "high|medium|low", "mitigation": "Use data augmentation and synthetic data", "contingency": "If data insufficient, pivot to related benchmark"}}
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

PASS2_SYSTEM = "You are a machine learning engineer. Return ONLY valid JSON."

PASS2_PROMPT = """Given this research plan and idea, generate detailed experiment configurations.

Idea: {title}
Approach: {approach}
Base Plan Overview: {overview}
Related Papers: {paper_titles}

Return a JSON object:
{{
  "experiment_configs": [
    {{
      "name": "Experiment name",
      "hyperparameters": {{"learning_rate": 0.001, "batch_size": 32, "epochs": 100}},
      "dataset": "Dataset to use",
      "expected_runtime": "2-4 hours on single GPU"
    }}
  ],
  "file_structure": [
    "src/model.py — PyTorch model implementing the core architecture",
    "src/train.py — Training loop with validation"
  ],
  "makefile_targets": [
    {{"target": "train", "command": "python main.py --mode train", "description": "Train the model"}}
  ],
  "baseline_implementations": [
    {{"method_name": "Baseline method", "paper_reference": "Paper title", "why_baseline": "State-of-the-art comparison"}}
  ]
}}"""


async def run_planning(idea: Dict, intent: Dict, llm: LLMClient, papers: List[Dict] = None) -> Dict:
    """2-pass planning: enhanced base plan + experiment details."""
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
            plan = _fallback_plan(idea)
    except Exception as e:
        print(f"Planner pass 1 error: {e}")
        plan = _fallback_plan(idea)

    paper_titles = ""
    if papers:
        paper_titles = ", ".join(p.get("title", "")[:60] for p in papers[:5])

    try:
        prompt2 = PASS2_PROMPT.format(
            title=idea.get("title", ""),
            approach=idea.get("approach", ""),
            overview=plan.get("overview", ""),
            paper_titles=paper_titles or "various recent works",
        )
        raw2 = await llm.complete(prompt2, system=PASS2_SYSTEM, json_mode=True)
        pass2 = _parse_json(raw2)
        if pass2:
            plan["experiment_configs"] = pass2.get("experiment_configs", [])
            plan["file_structure"] = pass2.get("file_structure", [])
            plan["makefile_targets"] = pass2.get("makefile_targets", [])
            plan["baseline_implementations"] = pass2.get("baseline_implementations", [])
    except Exception as e:
        print(f"Planner pass 2 error: {e}")
        plan.setdefault("experiment_configs", [])
        plan.setdefault("file_structure", _default_file_structure())
        plan.setdefault("makefile_targets", [])
        plan.setdefault("baseline_implementations", [])

    return plan


async def run_planning_stream(idea: Dict, intent: Dict, llm: LLMClient, papers: List[Dict] = None) -> AsyncGenerator[str, None]:
    """Stream enhanced execution plan."""
    domain = ", ".join(intent.get("domain", ["AI/ML"]))

    COMBINED_PROMPT = """Create a detailed execution plan and experiment configurations.
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
  "phases": [
    {{
      "phase": 1,
      "name": "Phase name",
      "duration": "X weeks",
      "tasks": ["task 1", "task 2"],
      "deliverables": ["deliverable 1"],
      "dependencies": ["phase 0"],
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
  ],
  "experiment_configs": [
    {{"name": "Experiment name", "hyperparameters": {{"lr": 0.001, "batch_size": 32}}, "dataset": "Dataset name", "expected_runtime": "2-4 hours on single GPU"}}
  ],
  "file_structure": ["src/model.py", "src/train.py"],
  "makefile_targets": [
    {{"target": "train", "command": "python main.py", "description": "Train model"}}
  ],
  "baseline_implementations": [
    {{"method_name": "Baseline", "paper_reference": "Paper", "why_baseline": "SOTA"}}
  ]
}}
"""
    paper_titles = ", ".join(p.get("title", "")[:60] for p in (papers or [])[:5])

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
        import logging
        logging.error(f"Planning streaming error: {e}")
        yield json.dumps(_fallback_plan(idea))


def _fallback_plan(idea: Dict) -> Dict:
    return {
        "overview": f"Execution plan for: {idea.get('title', 'research idea')}",
        "architecture": {"components": ["Data Pipeline", "Model", "Evaluation"], "diagram_description": "Standard ML pipeline"},
        "phases": [
            {"phase": 1, "name": "Data Collection & Preprocessing", "duration": "2 weeks",
             "tasks": ["Collect data", "Clean data", "Split train/val/test"],
             "deliverables": ["Clean dataset"],
             "dependencies": [],
             "resources_required": {"gpu": "None", "memory": "16GB", "storage": "20GB", "compute_hours": 20},
             "milestones": [{"name": "Data ready", "criteria": "All data cleaned and split", "deadline": "End of week 2"}]},
            {"phase": 2, "name": "Model Development", "duration": "4 weeks",
             "tasks": ["Implement baseline", "Train model", "Tune hyperparameters"],
             "deliverables": ["Trained model"],
             "dependencies": ["Phase 1"],
             "resources_required": {"gpu": "1x RTX 3090", "memory": "32GB", "storage": "50GB", "compute_hours": 200},
             "milestones": [{"name": "Baseline complete", "criteria": "Baseline accuracy >= expected minimum", "deadline": "End of week 4"}]},
            {"phase": 3, "name": "Evaluation & Writing", "duration": "2 weeks",
             "tasks": ["Evaluate metrics", "Write paper"],
             "deliverables": ["Paper draft"],
             "dependencies": ["Phase 2"],
             "resources_required": {"gpu": "None", "memory": "16GB", "storage": "10GB", "compute_hours": 10},
             "milestones": [{"name": "Paper submitted", "criteria": "All sections complete, ready for review", "deadline": "End of week 8"}]},
        ],
        "tech_stack": {"languages": ["Python"], "frameworks": ["PyTorch", "scikit-learn"],
                       "tools": ["wandb"], "infrastructure": ["Google Colab or local GPU"],
                       "collaboration": ["GitHub", "Overleaf"]},
        "datasets": [],
        "evaluation_metrics": ["Accuracy", "F1", "AUC"],
        "baseline_comparison": "State-of-the-art on benchmark",
        "risks": [
            {"risk": "Data scarcity", "severity": "high", "mitigation": "Use data augmentation and transfer learning",
             "contingency": "Pivot to few-shot or zero-shot approach"},
            {"risk": "Compute constraints", "severity": "medium", "mitigation": "Start with smaller models for faster iteration",
             "contingency": "Use cloud credits or Colab Pro"},
        ],
        "total_estimate": "2-3 months",
        "budget_estimation": {
            "compute_costs": "$100 - $300 for cloud GPU",
            "api_costs": "$0 - $50 for LLM APIs",
            "dataset_licensing": "Free (public benchmarks)",
            "total_estimated": "$100 - $350",
        },
        "literature_review_plan": [
            {"priority": 1, "topic": "Core methodology papers",
             "key_papers": [f"{p.get('title', 'Related work')}" for p in [{}] if p],
             "why_first": "Foundational understanding of the problem space"},
        ],
        "experiment_configs": [],
        "file_structure": _default_file_structure(),
        "makefile_targets": [],
        "baseline_implementations": [],
        "_fallback": True,
    }


def _default_file_structure() -> List[str]:
    return [
        "main.py — Entry point with argparse",
        "config.py — Configuration dataclass",
        "model.py — Model architecture",
        "dataset.py — Data loading",
        "train.py — Training loop",
        "evaluate.py — Evaluation",
        "utils.py — Helpers",
        "requirements.txt — Dependencies",
        "Makefile — Build targets",
        "tests/test_model.py — Unit tests",
        "README.md — Documentation",
    ]


def _parse_json(raw: str) -> Dict:
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    s, e = clean.find("{"), clean.rfind("}") + 1
    return json.loads(clean[s:e]) if s != -1 and e > s else {}
