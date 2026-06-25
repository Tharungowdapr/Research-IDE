"""
Shared utilities for building rich project context and detailed prompts.
Every agent should use format_project_context() to include ALL available project data.
"""

import json
from typing import Any


def format_project_context(
    idea: dict | None = None,
    gaps: list | None = None,
    papers: list | None = None,
    plan: dict | None = None,
    objectives: list | None = None,
    intent: dict | None = None,
    experiments: dict | None = None,
    data_plan: dict | None = None,
) -> str:
    parts = []

    if intent:
        domain = intent.get("domain", [])
        if isinstance(domain, list):
            domain = ", ".join(str(d) for d in domain)
        parts.append("[RESEARCH INTENT]")
        parts.append(f"Domain: {domain}")
        parts.append(f"Problem: {intent.get('problem_statement', intent.get('description', intent.get('task', '')))}")
        parts.append("")

    if idea:
        parts.append("[SELECTED IDEA]")
        parts.append(f"Title: {idea.get('title', 'N/A')}")
        parts.append(f"Description: {idea.get('description', 'N/A')}")
        parts.append(f"Approach: {idea.get('approach', 'N/A')}")
        parts.append(f"Novelty: {idea.get('novelty', 'N/A')}")
        parts.append(f"Feasibility: {idea.get('feasibility', 'N/A')}")
        parts.append(f"Impact: {idea.get('expected_impact', 'N/A')}")
        parts.append("")

    if gaps:
        parts.append(f"[IDENTIFIED GAPS ({len(gaps)})]")
        for i, g in enumerate(gaps[:5], 1):
            parts.append(f"{i}. {g.get('title', 'N/A')}: {str(g.get('description', ''))[:200]}")
            if g.get("opportunity"):
                parts.append(f"   Opportunity: {str(g.get('opportunity', ''))[:150]}")
        parts.append("")

    if objectives:
        parts.append(f"[RESEARCH OBJECTIVES ({len(objectives)})]")
        for i, o in enumerate(objectives[:4], 1):
            parts.append(f"{i}. {o.get('objective', 'N/A')} [{o.get('type', 'N/A')}]")
            parts.append(f"   Success: {o.get('success_criteria', 'N/A')}")
        parts.append("")

    if plan:
        parts.append("[METHODOLOGY PLAN]")
        parts.append(f"Overview: {str(plan.get('overview', ''))[:400]}")
        tech = plan.get("tech_stack", {})
        if tech:
            parts.append(f"Tech Stack: {json.dumps(tech, indent=1)}")
        phases = plan.get("phases", [])
        if phases:
            parts.append("Phases:")
            for p in phases[:3]:
                name = p.get("name", p.get("phase", "Phase"))
                dur = p.get("duration", "TBD")
                tasks = p.get("tasks", [])
                if isinstance(tasks, list):
                    tasks = "; ".join(str(t) for t in tasks[:4])
                parts.append(f"  - {name} ({dur}): {tasks}")
        arch = plan.get("architecture", {})
        if isinstance(arch, dict):
            comps = arch.get("components", [])
            if isinstance(comps, list):
                parts.append(f"Architecture: {', '.join(str(c) for c in comps[:5])}")
        parts.append("")

    if papers:
        parts.append(f"[KEY PAPERS ({len(papers)})]")
        for i, p in enumerate(papers[:6], 1):
            parts.append(f"{i}. [{p.get('year', 'N/A')}] {p.get('title', 'N/A')}")
            abstract = p.get("abstract", "") or ""
            parts.append(f"   {abstract[:200]}")
        parts.append("")

    if experiments:
        exps = experiments.get("experiments", [])
        if exps:
            parts.append(f"[EXPERIMENT DESIGN ({len(exps)})]")
            for e in exps[:3]:
                parts.append(f"  - {e.get('name', 'N/A')}: {e.get('objective', 'N/A')}")
                metrics = e.get("metrics", [])
                if metrics:
                    parts.append(f"    Metrics: {', '.join(str(m) for m in metrics)}")
            parts.append("")

    if data_plan:
        datasets = data_plan.get("suggested_datasets", [])
        if datasets:
            parts.append(f"[DATASETS ({len(datasets)})]")
            for d in datasets[:3]:
                parts.append(f"  - {d.get('name', 'N/A')}: {d.get('why_suitable', d.get('description', ''))[:150]}")
            parts.append("")

    return "\n".join(parts)


def parse_json(raw: str) -> dict | list | None:
    if not raw or not raw.strip():
        return None
    import re
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    # Try direct parse
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass
    # Find outermost { }
    start = clean.find("{")
    end = clean.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(clean[start:end])
        except json.JSONDecodeError:
            pass
    # Find outermost [ ]
    start = clean.find("[")
    end = clean.rfind("]") + 1
    if start != -1 and end > start:
        try:
            return json.loads(clean[start:end])
        except json.JSONDecodeError:
            pass
    # If content looks like a JSON object without outer braces, wrap them
    stripped = clean.strip()
    if stripped.startswith('"') or stripped.startswith("'"):
        # Looks like a bare string key-value, wrap in {}
        wrapped = "{" + stripped + "}"
        try:
            return json.loads(wrapped)
        except json.JSONDecodeError:
            pass
    return None


def detailed_section(name: str, items: list[dict], fields: list[str]) -> str:
    if not items:
        return ""
    lines = [f"--- {name} ---"]
    for i, item in enumerate(items, 1):
        for f in fields:
            val = item.get(f, "")
            if val:
                lines.append(f"  {i}.{f}: {str(val)[:200]}")
        lines.append("")
    return "\n".join(lines)
