"""Planner Agent - generates execution plan for a selected research idea."""

import json, re
from typing import Dict, Any
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


async def run_planning(idea: Dict, intent: Dict, llm: LLMClient) -> Dict:
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    prompt = PLAN_PROMPT.format(
        title=idea.get("title", "Research Idea"),
        description=idea.get("description", ""),
        approach=idea.get("approach", ""),
        domain=domain,
    )
    try:
        raw = await llm.complete(prompt, system=PLAN_SYSTEM, json_mode=True)
        return _parse_json(raw)
    except Exception as e:
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
            "_fallback": True,
        }


def _parse_json(raw: str) -> Dict:
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    s, e = clean.find("{"), clean.rfind("}") + 1
    return json.loads(clean[s:e]) if s != -1 and e > s else {}
