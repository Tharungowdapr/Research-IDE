"""
Planner Agent — 2-Pass Execution Plan Generation
Pass 1: Base plan | Pass 2: Experiment configs + file structure
"""

import json
import re
from typing import Dict, List, Any
from core.llm_client import LLMClient

PLAN_SYSTEM = "You are a senior ML researcher and system architect. Return ONLY valid JSON."

PLAN_PROMPT = """Create a detailed execution plan for this research idea.

Idea: {title}
Description: {description}
Approach: {approach}
Domain Context: {domain}

Return a JSON object:
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
      "deliverables": ["deliverable 1"]
    }}
  ],
  "tech_stack": {{
    "languages": ["Python"],
    "frameworks": ["PyTorch", "HuggingFace"],
    "tools": ["wandb", "docker"],
    "infrastructure": ["local GPU or Colab"]
  }},
  "datasets": [
    {{
      "name": "Dataset name",
      "source": "URL or description",
      "why": "Why this dataset"
    }}
  ],
  "evaluation_metrics": ["metric 1", "metric 2"],
  "baseline_comparison": "What to compare against",
  "risks": ["risk 1", "risk 2"],
  "total_estimate": "X-Y months"
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
    "src/train.py — Training loop with validation",
    "src/evaluate.py — Evaluation script computing all metrics",
    "src/dataset.py — Data loading and preprocessing",
    "src/utils.py — Helper functions",
    "config.py — Configuration dataclass",
    "main.py — Entry point with argparse",
    "requirements.txt — Dependencies",
    "Makefile — Build and run targets",
    "tests/test_model.py — Unit tests",
    "README.md — Project documentation"
  ],
  "makefile_targets": [
    {{"target": "train", "command": "python main.py --mode train", "description": "Train the model"}},
    {{"target": "eval", "command": "python main.py --mode eval", "description": "Evaluate the model"}},
    {{"target": "test", "command": "python -m pytest tests/ -v", "description": "Run tests"}}
  ],
  "baseline_implementations": [
    {{"method_name": "Baseline method", "paper_reference": "Paper title", "why_baseline": "State-of-the-art comparison"}}
  ]
}}"""


async def run_planning(idea: Dict, intent: Dict, llm: LLMClient, papers: List[Dict] = None) -> Dict:
    """2-pass planning: base plan + experiment details."""
    domain = ", ".join(intent.get("domain", ["AI/ML"]))

    # Pass 1: Base plan
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

    # Pass 2: Experiment configs
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


def _fallback_plan(idea: Dict) -> Dict:
    return {
        "overview": f"Execution plan for: {idea.get('title', 'research idea')}",
        "architecture": {"components": ["Data Pipeline", "Model", "Evaluation"], "diagram_description": "Standard ML pipeline"},
        "phases": [
            {"phase": 1, "name": "Data Collection & Preprocessing", "duration": "2 weeks", "tasks": ["Collect data", "Clean data", "Split train/val/test"], "deliverables": ["Clean dataset"]},
            {"phase": 2, "name": "Model Development", "duration": "4 weeks", "tasks": ["Implement baseline", "Train model", "Tune hyperparameters"], "deliverables": ["Trained model"]},
            {"phase": 3, "name": "Evaluation & Writing", "duration": "2 weeks", "tasks": ["Evaluate metrics", "Write paper"], "deliverables": ["Paper draft"]},
        ],
        "tech_stack": {"languages": ["Python"], "frameworks": ["PyTorch", "scikit-learn"], "tools": ["wandb"], "infrastructure": ["Google Colab or local GPU"]},
        "datasets": [],
        "evaluation_metrics": ["Accuracy", "F1", "AUC"],
        "baseline_comparison": "State-of-the-art on benchmark",
        "risks": ["Data scarcity", "Compute constraints"],
        "total_estimate": "2-3 months",
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
