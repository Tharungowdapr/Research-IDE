"""
Data Pipeline Agent
Suggests datasets, preprocessing steps, data sources, and data pipeline tools.
"""

import json
from typing import Dict
from core.llm_client import LLMClient
from agents.shared.context_builder import format_project_context, parse_json

SYSTEM = "You are a data engineering expert. Return ONLY valid JSON."

PROMPT = """Given this full project context, suggest a comprehensive data pipeline plan.

Full Project Context:
{full_context}

Return EXACTLY this JSON structure with project-specific content:
{{
  "suggested_datasets": [
    {{
      "name": "Dataset name specific to this domain",
      "source": "Kaggle/UCI/HuggingFace/etc with URL if possible",
      "description": "What this dataset contains (2-3 sentences)",
      "size": "~X GB or X examples",
      "format": "CSV/JSON/Parquet/image/text",
      "licensing": "MIT/CC-BY/etc",
      "why_suitable": "2-3 sentence explanation of why this dataset fits this specific research",
      "preprocessing_needed": "Specific cleaning steps required",
      "expected_metrics": ["metric this dataset enables"]
    }}
  ],
  "data_collection": [
    {{"step": 1, "task": "Specific task", "tools": ["tool1", "tool2"], "expected_output": "What this step produces", "time_estimate": "X days"}}
  ],
  "preprocessing": [
    {{"step": 1, "task": "Specific preprocessing step", "technique": "Exact technique name", "tools": ["pandas", "nltk"], "output": "What this produces", "rationale": "Why this step is needed"}}
  ],
  "augmentation": [
    {{"technique": "Augmentation technique", "description": "How it helps this specific project", "tools": ["tool"]}}
  ],
  "data_pipeline_tools": ["pandas", "numpy", "scikit-learn"],
  "data_validation": ["Specific validation check 1", "Specific validation check 2"],
  "ethical_considerations": [
    {{"concern": "Specific ethical concern", "mitigation": "How to address it"}}
  ],
  "storage_recommendation": "Specific storage recommendation with rationale",
  "detailed_explanation": "3-4 paragraph explanation of the data strategy, why each dataset was chosen, and how preprocessing enables the research goals"
}}

IMPORTANT: Be specific to this project. Include real dataset names from the project's domain. Reference the project idea and approach when justifying dataset choices."""




async def run_data_plan_generation(
    idea: Dict,
    methodology: Dict,
    llm: LLMClient,
    gaps: list = None,
    papers: list = None,
    plan: dict = None,
    objectives: list = None,
    intent: dict = None,
) -> Dict:
    full_context = format_project_context(
        idea=idea, gaps=gaps, papers=papers,
        plan=plan or methodology, objectives=objectives, intent=intent,
    )

    try:
        prompt = PROMPT.format(
            full_context=full_context or f"Idea: {idea.get('title', 'N/A')}\nMethodology: {methodology.get('overview', '')[:500]}"
        )
        raw = await llm.complete(prompt, system=SYSTEM, json_mode=True)
        result = parse_json(raw)
        if isinstance(result, dict) and ("suggested_datasets" in result or "preprocessing" in result):
            return result
        return {
            "suggested_datasets": [],
            "data_collection": [],
            "preprocessing": [],
            "augmentation": [],
            "data_pipeline_tools": [],
            "data_validation": [],
            "ethical_considerations": [],
            "storage_recommendation": "Standard local storage recommended",
            "detailed_explanation": "The LLM response did not match the expected format. Please retry this step.",
            "_warning": "Fallback data plan generated due to LLM format mismatch",
        }
    except Exception as e:
        raise ValueError(f"Data generation failed: {e}") from e
