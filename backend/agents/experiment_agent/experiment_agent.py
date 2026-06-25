"""
Experiment Agent
Designs experiments, hyperparameter configurations, and evaluation protocols.
"""

import json
from typing import Dict
from core.llm_client import LLMClient
from agents.shared.context_builder import format_project_context, parse_json

SYSTEM = "You are an ML experiment design expert. Return ONLY valid JSON."

PROMPT = """Given this full project context, design detailed experiments.

Full Project Context:
{full_context}

Return EXACTLY this JSON structure with project-specific content:
{{
  "experiments": [
    {{
      "name": "Experiment name tied to the project approach",
      "objective": "What this experiment tests (2-3 sentences)",
      "dataset": "Specific dataset to use",
      "model_config": {{"architecture": "Model type", "learning_rate": 0.001, "batch_size": 32, "epochs": 100, "optimizer": "Adam", "loss_function": "CrossEntropyLoss", "dropout": 0.1, "num_layers": 4}},
      "data_split": {{"train": 0.7, "val": 0.15, "test": 0.15}},
      "baselines": ["Baseline 1 - specific name", "Baseline 2 - specific name"],
      "metrics": ["Accuracy", "F1", "Precision", "Recall"],
      "expected_runtime": "2-4 hours on single GPU",
      "ablation": ["Remove component A", "Remove component B"],
      "hypothesis": "What this experiment expects to find",
      "failure_analysis": "What to check if results are unexpected"
    }}
  ],
  "hyperparameter_tuning": {{
    "method": "grid_search / bayesian / random",
    "params": {{"learning_rate": [0.0001, 0.001, 0.01], "batch_size": [16, 32, 64], "dropout": [0.0, 0.1, 0.2]}},
    "trials": 20,
    "early_stopping": true,
    "budget": "Total compute budget for tuning"
  }},
  "evaluation_protocol": [
    {{"step": 1, "task": "Specific evaluation task", "metrics_tracked": ["loss", "accuracy"], "rationale": "Why this step matters"}}
  ],
  "ablation_studies": [
    {{"name": "Ablation 1", "variant": "What to remove/change", "purpose": "What this tests", "expected_insight": "What we expect to learn"}}
  ],
  "statistical_tests": ["paired t-test", "Wilcoxon signed-rank", "Cohen's d effect size"],
  "visualization_plan": ["Loss curves", "Confusion matrix", "ROC curves", "Ablation bar chart", "Feature importance plot"],
  "detailed_explanation": "3-4 paragraph explanation of the experimental design, why each experiment is needed, and how results will validate the research approach"
}}

IMPORTANT: Design experiments SPECIFICALLY for this project's approach. Baselines should be real methods from the papers/references. Metrics should match the project's domain. The detailed_explanation should connect experiments to the research hypothesis."""


async def run_experiment_generation(
    idea: Dict,
    methodology: Dict,
    llm: LLMClient,
    gaps: list = None,
    papers: list = None,
    plan: dict = None,
    objectives: list = None,
    data_plan: dict = None,
    intent: dict = None,
) -> Dict:
    full_context = format_project_context(
        idea=idea, gaps=gaps, papers=papers,
        plan=plan or methodology, objectives=objectives,
        data_plan=data_plan, intent=intent,
    )

    try:
        prompt = PROMPT.format(
            full_context=full_context or f"Idea: {idea.get('title', 'N/A')}\nMethodology: {methodology.get('overview', '')[:500]}"
        )
        raw = await llm.complete(prompt, system=SYSTEM, json_mode=True)
        result = parse_json(raw)
        if isinstance(result, dict) and "experiments" in result:
            return result
        raise ValueError(f"LLM returned invalid format: {str(raw)[:200]}")
    except Exception as e:
        raise ValueError(f"Experiment generation failed: {e}") from e
