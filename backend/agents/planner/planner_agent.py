"""Planner Agent v2.1 — 2-pass with immediate Pass 1 save"""

import json
from typing import Dict, Any, List, Optional, Callable
from core.llm_client import LLMClient
from core.utils import safe_parse_llm_json, truncate_text

PLAN_SYSTEM = "You are a senior researcher and project manager. Return ONLY valid JSON."
ENRICH_SYSTEM = "You are an expert experiment design consultant. Return ONLY valid JSON."

PLAN_PROMPT = """Create a detailed execution plan for this research idea.

Idea: {title}
Description: {description}
Approach: {approach}
Domain: {domain}
Constraints: {constraints}

Return JSON:
{{
  "overview": "2-3 sentence project overview",
  "architecture": {{"components": [], "diagram_description": ""}},
  "phases": [{{"phase": 1, "name": "", "duration": "", "tasks": [], "deliverables": []}}],
  "tech_stack": {{"languages_or_methods": [], "frameworks_or_equipment": [], "tools": [], "infrastructure": []}},
  "resources": [{{"name": "", "source": "", "why": ""}}],
  "evaluation_metrics": [],
  "baseline_comparison": "",
  "risks": [],
  "total_estimate": ""
}}"""

ENRICH_PROMPT = """Add experiment configuration details to this research plan.

Plan overview: {overview}
Idea title: {title}
Related methods: {methods}

Return JSON with ONLY these keys:
{{
  "experiment_configs": [{{"name": "", "variables": {{}}, "material_or_dataset": "", "expected_runtime": ""}}],
  "structure": ["path/file.py or notebook or document — description"],
  "key_steps_or_targets": [{{"target": "", "action": "", "description": ""}}],
  "baseline_implementations": [{{"method_name": "", "paper_reference": "", "why_baseline": ""}}]
}}"""


async def run_planning(
    idea: Dict,
    intent: Dict,
    llm: LLMClient,
    on_pass1_complete: Optional[Callable[[Dict], None]] = None,
) -> Dict:
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    constraints = _fmt_constraints(intent.get("constraints", {}))

    # ── Pass 1: Base plan ─────────────────────────────────────────────────────
    try:
        raw = await llm.complete(
            PLAN_PROMPT.format(
                title=idea.get("title", ""),
                description=idea.get("description", ""),
                approach=idea.get("approach", ""),
                domain=domain,
                constraints=constraints,
            ),
            system=PLAN_SYSTEM, json_mode=True
        )
        plan = safe_parse_llm_json(raw, default={})
        if not isinstance(plan, dict) or not plan:
            plan = _fallback_plan(idea)
    except Exception:
        plan = _fallback_plan(idea)

    # Save Pass 1 immediately so frontend gets partial result fast
    if on_pass1_complete:
        on_pass1_complete(dict(plan))

    # ── Pass 2: Enrich (non-blocking — failures don't kill the plan) ──────────
    plan["file_structure"] = _default_file_structure()
    try:
        methods = ", ".join(idea.get("suggested_methods", [])[:3]) or "deep learning"
        enrich_raw = await llm.complete(
            ENRICH_PROMPT.format(
                overview=plan.get("overview", ""),
                title=idea.get("title", ""),
                methods=methods,
            ),
            system=ENRICH_SYSTEM, json_mode=True
        )
        enrichment = safe_parse_llm_json(enrich_raw, default={})
        if isinstance(enrichment, dict):
            for k in ("experiment_configs", "file_structure", "makefile_targets", "baseline_implementations"):
                if k in enrichment:
                    plan[k] = enrichment[k]
    except Exception as e:
        print(f"[Planner Pass 2 failed — using defaults]: {e}")

    # Ensure file_structure always exists with 12 expected files
    if not plan.get("file_structure"):
        plan["file_structure"] = _default_file_structure()

    return plan


def _default_file_structure() -> List[str]:
    return [
        "README.md — project-specific usage guide and overview",
        "data_or_materials/ — directory for raw data or material logs",
        "methods_and_protocols/ — directory for step-by-step experiment instructions",
        "analysis/ — directory for statistical analysis or code",
        "results/ — directory for charts, figures, and outcomes",
        "config_or_params.yaml — all variables and settings",
        "experiment_log.txt — daily lab notebook or execution trace",
        "requirements.txt or equipment_list.txt — pinned dependencies or tools needed",
    ]


def _fmt_constraints(c: Dict) -> str:
    parts = []
    if c.get("compute"): parts.append(f"compute: {c['compute']}")
    if c.get("region"): parts.append(f"region: {c['region']}")
    if c.get("real_time"): parts.append("real-time required")
    return ", ".join(parts) or "none specified"


def _fallback_plan(idea: Dict) -> Dict:
    return {
        "overview": f"Execution plan for: {idea.get('title', 'research idea')}",
        "architecture": {"components": ["Preparation", "Execution", "Evaluation"],
                         "diagram_description": "Standard research pipeline"},
        "phases": [
            {"phase": 1, "name": "Preparation & Setup", "duration": "2 weeks",
             "tasks": ["Gather materials/data", "Setup environment/equipment"], "deliverables": ["Ready state"]},
            {"phase": 2, "name": "Execution & Experimentation", "duration": "4 weeks",
             "tasks": ["Run baseline", "Test hypothesis"], "deliverables": ["Raw results"]},
            {"phase": 3, "name": "Evaluation & Writing", "duration": "2 weeks",
             "tasks": ["Analyze outcomes", "Write paper"], "deliverables": ["Paper draft"]},
        ],
        "tech_stack": {"languages_or_methods": ["Standard domain methods"], "frameworks_or_equipment": ["Standard tools"],
                       "tools": ["Analysis software"], "infrastructure": ["Lab space or Compute"]},
        "resources": [],
        "evaluation_metrics": ["Statistical significance", "Accuracy/Yield"],
        "baseline_comparison": "State-of-the-art literature baseline",
        "risks": ["Resource constraints", "Time constraints"],
        "total_estimate": "2-3 months",
    }
