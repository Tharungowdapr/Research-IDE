"""
Results Analysis Agent
Generates result analysis templates, comparison tables, and visualization plans.
"""

import json
from typing import Dict
from core.llm_client import LLMClient
from agents.shared.context_builder import format_project_context, parse_json

SYSTEM = "You are a research data analysis expert. Return ONLY valid JSON."

PROMPT = """Given this full project context, generate a comprehensive results analysis template with BASELINE ESTABLISHMENT.

Full Project Context:
{full_context}

Return EXACTLY this JSON structure with project-specific content:
{{
  "baseline_establishment": {{
    "baselines": [
      {{
        "name": "Specific baseline method name from literature (e.g., 'BERT-base', 'Random Forest', 'ResNet-50')",
        "source": "paper_reference_or_standard_name",
        "justification": "Why this baseline is appropriate for this project's domain and task",
        "expected_metrics": {{"accuracy": "~85%", "f1": "~84%", "inference_time": "~10ms"}}
      }}
    ],
    "evaluation_protocol": "Detailed protocol for running baselines: dataset splits, random seeds, hardware, number of runs",
    "significance_threshold": "p < 0.05 with Bonferroni correction for N comparisons"
  }},
  "comparison_tables": [
    {{
      "table_name": "Specific table name related to this project",
      "columns": ["Method", "Accuracy", "F1", "Precision", "Recall", "Inference Time", "Params (M)"],
      "rows": [
        ["Proposed Method Name", "91.2", "90.5", "91.0", "90.1", "12ms", "45"],
        ["Baseline 1 Specific Name", "85.3", "84.7", "85.0", "84.5", "10ms", "110"],
        ["Baseline 2 Specific Name", "87.1", "86.8", "87.0", "86.5", "15ms", "25"]
      ],
      "caption": "Descriptive caption explaining what this table shows",
      "footnote": "Statistical significance indicator or experimental condition note; best in bold"
    }}
  ],
  "visualization_suggestions": [
    {{
      "type": "bar_chart|line_chart|scatter|heatmap|box_plot",
      "title": "Specific visualization title",
      "x_axis": "X-axis label",
      "y_axis": "Y-axis label",
      "data_from": "comparison_table_0",
      "rationale": "Why this visualization helps understand the results",
      "code_snippet": "import matplotlib.pyplot as plt\\nplt.bar(...)"
    }}
  ],
  "statistical_analysis": [
    {{"test": "paired t-test", "purpose": "Compare proposed vs specific baseline", "expected_output": "p-value < 0.05 indicates significance", "variables": "Which variables to compare"}}
  ],
  "result_interpretation": [
    {{"finding": "Specific expected finding tied to project hypothesis", "implication": "What this means for the research question", "confidence": "high|medium|low", "supporting_evidence": "What data supports this"}}
  ],
  "discussion_points": [
    "How does the proposed method address the research gap?",
    "What are the failure cases and why?",
    "How do results compare with theoretical expectations?"
  ],
  "limitations": [
    {{"limitation": "Specific limitation of the study", "impact": "How this affects conclusions", "mitigation": "How to address in future work"}}
  ],
  "templates": {{
    "latex_table": "\\\\begin{{table}}[h]\\\\centering\\\\begin{{tabular}}{{|c|c|c|}}...",
    "python_plot": "import matplotlib.pyplot as plt\\nplt.bar(...)"
  }},
  "detailed_explanation": "3-4 paragraph explanation of the analysis approach, what each comparison tests, and how the results will be interpreted in the context of the research hypothesis"
}}

IMPORTANT: 
- baselines MUST have real method names from the project's domain (cite specific papers/standards)
- The evaluation_protocol must be specific enough to reproduce
- Tables must have real baseline names from the project's domain
- Visualizations should match the project's expected result types
- The detailed_explanation should connect the analysis plan to the research questions"""

async def run_analysis_generation(
    idea: Dict,
    llm: LLMClient,
    gaps: list = None,
    papers: list = None,
    plan: dict = None,
    objectives: list = None,
    experiments: dict = None,
    intent: dict = None,
) -> Dict:
    full_context = format_project_context(
        idea=idea, gaps=gaps, papers=papers,
        plan=plan, objectives=objectives,
        experiments=experiments, intent=intent,
    )

    try:
        prompt = PROMPT.format(
            full_context=full_context or f"Idea: {idea.get('title', 'N/A')}"
        )
        raw = await llm.complete(prompt, system=SYSTEM, json_mode=True)
        result = parse_json(raw)
        if isinstance(result, dict) and ("comparison_tables" in result or "visualization_suggestions" in result):
            return result
        raise ValueError(f"LLM returned invalid format: {str(raw)[:200]}")
    except Exception as e:
        raise ValueError(f"Analysis generation failed: {e}") from e
