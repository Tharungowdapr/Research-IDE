"""
Code Generation Agent - generates detailed implementation code
based on the full research context (idea, plan, project structure, papers).
"""

import json
import logging
from typing import Any, AsyncIterator

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a senior software engineer implementing a research project. "
    "Generate detailed, working code files based on the project plan and architecture. "
    "Each file must have complete imports, class/function signatures with docstrings, "
    "and real logic (not just pass/placeholder). "
    "Return ONLY a valid JSON object with a 'file_structure' array."
)

def _build_prompt(
    idea: dict,
    plan: dict,
    project_structure: list,
    intent: str,
    papers_summary: str,
) -> str:
    title = str(idea.get("title", "Untitled"))
    description = str(idea.get("description", ""))
    approach = str(idea.get("approach", ""))
    domain = str(idea.get("domain", intent))

    plan_overview = plan.get("overview", "")
    plan_overview_str = str(plan_overview) if not isinstance(plan_overview, str) else plan_overview
    intent_str = str(intent) if not isinstance(intent, str) else intent
    tech_stack = plan.get("tech_stack", {})
    phases = plan.get("phases", [])
    architecture = plan.get("architecture", {})

    structure_text = "\n".join(project_structure) if project_structure else "src/main.py"

    tech_text = ""
    if isinstance(tech_stack, dict):
        for category, items in tech_stack.items():
            if isinstance(items, list):
                tech_text += f"  {category}: {', '.join(str(i) for i in items)}\n"
            else:
                tech_text += f"  {category}: {items}\n"

    phases_text = ""
    for i, phase in enumerate(phases[:3]):
        name = phase.get("phase", f"Phase {i+1}")
        tasks = phase.get("tasks", [])
        if isinstance(tasks, list):
            tasks_text = "; ".join(str(t) for t in tasks[:5])
        else:
            tasks_text = str(tasks)[:200]
        phases_text += f"  {i+1}. {name}: {tasks_text}\n"

    arch_components = ""
    if isinstance(architecture, dict):
        comps = architecture.get("components", [])
        if isinstance(comps, list):
            for c in comps[:5]:
                if isinstance(c, dict):
                    arch_components += f"    - {c.get('name', '')}: {c.get('description', '')}\n"
                else:
                    arch_components += f"    - {c}\n"

    return f"""Research Project: {title}
Domain: {domain}
Description: {description}
Approach: {approach}

Architecture:
{arch_components or '  See plan for details'}

Tech Stack:
{tech_text or '  Python'}

Implementation Phases:
{phases_text or '  See plan for details'}

Plan Overview:
{plan_overview_str[:500]}

Required Files (generate ALL of these):
{structure_text}

Research Context:
{intent_str[:500]}

Key Papers:
{papers_summary}

Generate complete, runnable code files. Each file must have:
  - Proper imports
  - Complete class/function signatures with docstrings
  - Real logic matching the research project's domain
  - Error handling where appropriate
  - Type hints (Python) or equivalent

Output format: {{"file_structure": [{{"path": "src/file.py", "content": "full file content here"}}]}}
Include ALL files from the required file list."""


async def run_code_generation(
    project_id: str,
    intent: str,
    retrieved_papers: list,
    user_id: str,
    llm_client: Any,
    idea: dict | None = None,
    plan: dict | None = None,
    project_structure: list | None = None,
) -> dict:
    try:
        papers_summary = "\n".join(
            f"- {p.get('title', 'N/A')}: {p.get('abstract', '')[:200]}"
            for p in retrieved_papers[:5]
        )

        prompt = _build_prompt(
            idea=idea or {},
            plan=plan or {},
            project_structure=project_structure or [],
            intent=intent or "",
            papers_summary=papers_summary,
        )

        response = await llm_client.complete(prompt, system=SYSTEM_PROMPT, json_mode=False)

        from agents.shared.context_builder import parse_json
        code_data = parse_json(response) or {}

        file_structure = code_data.get("file_structure", [])
        if not file_structure and project_structure:
            file_structure = [
                {"path": p, "content": f"# {p}\n# TODO: Implement\n"}
                for p in project_structure
            ]

        for f in file_structure:
            if isinstance(f.get("content"), str):
                f["content"] = f["content"]

        return {
            "project_id": project_id,
            "file_structure": file_structure,
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"Code generation error: {e}")
        raise


async def run_code_generation_stream(
    project_id: str,
    intent: str,
    retrieved_papers: list,
    user_id: str,
    llm_client: Any,
    idea: dict | None = None,
    plan: dict | None = None,
    project_structure: list | None = None,
) -> AsyncIterator[str]:
    try:
        papers_summary = "\n".join(
            f"- {p.get('title', 'N/A')}: {p.get('abstract', '')[:200]}"
            for p in retrieved_papers[:5]
        )

        prompt = _build_prompt(
            idea=idea or {},
            plan=plan or {},
            project_structure=project_structure or [],
            intent=intent or "",
            papers_summary=papers_summary,
        )

        async for chunk in llm_client.stream_complete(prompt, system=SYSTEM_PROMPT, json_mode=True):
            yield chunk
    except Exception as e:
        logger.error(f"Code generation stream error: {e}")
        raise
