"""
Export Routes — Full project ZIP export and section PDF exports.
"""

import io
import json
import zipfile
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.project import Project, Output


router = APIRouter()


def _get_output(db: Session, project_id: str, output_type: str):
    o = db.query(Output).filter(Output.project_id == project_id, Output.output_type == output_type).first()
    return o.data if o else None


def _papers_to_md(papers_data: dict) -> str:
    lines = ["# Retrieved Papers\n"]
    papers = papers_data.get("papers", []) if papers_data else []
    for i, p in enumerate(papers, 1):
        lines.append(f"## {i}. {p.get('title', 'Untitled')}")
        lines.append(f"**Authors:** {', '.join(p.get('authors', []))}")
        lines.append(f"**Year:** {p.get('year', 'N/A')} | **Citations:** {p.get('citations', 0)} | **Source:** {p.get('source', 'unknown')}")
        if p.get("url"):
            lines.append(f"**URL:** {p['url']}")
        if p.get("abstract"):
            lines.append(f"\n{p['abstract']}")
        lines.append("")
    return "\n".join(lines)


def _gaps_to_md(gaps_data: dict) -> str:
    lines = ["# Gap Analysis Report\n"]
    gaps = gaps_data.get("gaps", []) if gaps_data else []
    for i, g in enumerate(gaps, 1):
        lines.append(f"## Gap {i}: {g.get('title', 'Untitled')}")
        lines.append(f"**Type:** {g.get('type', 'N/A')} | **Confidence:** {g.get('confidence', 'N/A')} | **Score:** {g.get('final_score', 'N/A')}")
        lines.append(f"\n### Description\n{g.get('description', '')}")
        if g.get("explanation"):
            lines.append(f"\n### Why This Gap Exists\n{g['explanation']}")
        refs = g.get("direct_references", g.get("supporting_papers", []))
        if refs:
            lines.append("\n### Source Papers")
            for ref in refs:
                lines.append(f"- {ref}")
        if g.get("opportunity"):
            lines.append(f"\n### Research Opportunity\n{g['opportunity']}")
        lines.append(f"\n**Addressability:** {g.get('addressability', 'N/A')}/10 | **Impact:** {g.get('impact', 'N/A')}/10 | **Novelty Potential:** {g.get('novelty_potential', 'N/A')}/10")
        lines.append("")
    return "\n".join(lines)


def _ideas_to_md(ideas_data: dict) -> str:
    lines = ["# Research Ideas & Evaluation\n"]
    ideas = ideas_data.get("ideas", []) if ideas_data else []
    for i, idea in enumerate(ideas, 1):
        lines.append(f"## Idea {i}: {idea.get('title', 'Untitled')}")
        lines.append(f"**Complexity:** {idea.get('complexity', 'N/A')} | **Feasibility:** {idea.get('feasibility', 'N/A')} | **Innovation Level:** {idea.get('innovation_level', 'N/A')}/10")
        lines.append(f"**Estimated Time:** {idea.get('estimated_time', 'N/A')}")
        if idea.get("problem_statement"):
            lines.append(f"\n### Problem Statement\n{idea['problem_statement']}")
        if idea.get("proposed_solution"):
            lines.append(f"\n### Proposed Solution\n{idea['proposed_solution']}")
        if idea.get("why_it_addresses_gap"):
            lines.append(f"\n### Why It Addresses the Gap\n{idea['why_it_addresses_gap']}")
        if idea.get("potential_challenges"):
            lines.append(f"\n### Potential Challenges\n{idea['potential_challenges']}")
        methods = idea.get("suggested_methods", [])
        if methods:
            lines.append("\n### Suggested Methods")
            for m in methods:
                lines.append(f"- {m}")
        datasets = idea.get("suggested_datasets", [])
        if datasets:
            lines.append("\n### Suggested Datasets")
            for d in datasets:
                lines.append(f"- {d}")
        lines.append(f"\n**Novelty Score:** {idea.get('novelty_score', 'N/A')}/10 | **Feasibility Score:** {idea.get('feasibility_score', 'N/A')}/10")
        if idea.get("critique_summary"):
            lines.append(f"\n> **Peer Review:** {idea['critique_summary']}")
        lines.append("")
    return "\n".join(lines)


def _plan_to_md(plan_data: dict) -> str:
    if not plan_data:
        return "# Execution Plan\n\nNo plan generated yet."
    lines = ["# Execution Plan\n"]
    if plan_data.get("overview"):
        lines.append(f"## Overview\n{plan_data['overview']}\n")
    phases = plan_data.get("phases", [])
    for phase in phases:
        lines.append(f"## Phase {phase.get('phase', '?')}: {phase.get('name', phase.get('title', ''))}")
        lines.append(f"**Duration:** {phase.get('duration', 'N/A')}")
        tasks = phase.get("tasks", phase.get("steps", []))
        if tasks:
            for t in tasks:
                if isinstance(t, str):
                    lines.append(f"- {t}")
                elif isinstance(t, dict):
                    lines.append(f"- **{t.get('title', '')}:** {t.get('description', '')}")
        lines.append("")
    if plan_data.get("tech_stack"):
        lines.append("## Tech Stack")
        for key, vals in plan_data["tech_stack"].items():
            v = ", ".join(vals) if isinstance(vals, list) else str(vals)
            lines.append(f"- **{key}:** {v}")
        lines.append("")
    return "\n".join(lines)


def _report_to_md(report_data: dict) -> str:
    if not report_data:
        return "# Research Paper\n\nNo report generated yet."
    lines = [f"# {report_data.get('title', 'Research Paper')}\n"]
    if report_data.get("authors"):
        lines.append(f"*{', '.join(report_data['authors'])}*\n")
    if report_data.get("abstract"):
        lines.append(f"## Abstract\n{report_data['abstract']}\n")
    if report_data.get("keywords"):
        lines.append(f"**Keywords:** {', '.join(report_data['keywords'])}\n")
    for section in report_data.get("sections", []):
        lines.append(f"## {section.get('heading', '')}\n{section.get('content', '')}\n")
    if report_data.get("references"):
        lines.append("## References")
        for ref in report_data["references"]:
            lines.append(f"[{ref.get('id', '')}] {ref.get('authors', '')} ({ref.get('year', '')}). \"{ref.get('title', '')}.\" {ref.get('venue', '')}.")
    return "\n".join(lines)


def _generate_readme(project: Project, outputs: dict) -> str:
    lines = [
        f"# {project.title}",
        "",
        f"**Created:** {project.created_at}",
        f"**Status:** {project.status}",
        "",
        "## Project Contents",
        "",
        "| File | Description |",
        "|------|-------------|",
        "| `papers/papers_summary.md` | Retrieved research papers with abstracts |",
        "| `analysis/gap_analysis.md` | Deep gap analysis with paper references |",
        "| `analysis/ideas.md` | Generated research ideas with evaluations |",
        "| `plan/execution_plan.md` | Phased execution and build plan |",
        "| `report/research_paper.md` | Generated IEEE-format research paper |",
        "",
        "## Statistics",
        "",
    ]
    papers = outputs.get("papers", {})
    gaps = outputs.get("gaps", {})
    ideas = outputs.get("ideas", {})
    lines.append(f"- **Papers retrieved:** {len(papers.get('papers', []))}")
    lines.append(f"- **Gaps identified:** {len(gaps.get('gaps', []))}")
    lines.append(f"- **Ideas generated:** {len(ideas.get('ideas', []))}")
    return "\n".join(lines)


@router.get("/{project_id}/export/full")
async def export_full_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export the entire project as a ZIP file."""
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Gather all outputs
    output_types = ["papers", "gaps", "ideas", "plan", "guide", "presentation", "report", "intent"]
    outputs = {}
    for ot in output_types:
        data = _get_output(db, project_id, ot)
        if data:
            outputs[ot] = data

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.md", _generate_readme(project, outputs))
        if outputs.get("papers"):
            zf.writestr("papers/papers_summary.md", _papers_to_md(outputs["papers"]))
        if outputs.get("gaps"):
            zf.writestr("analysis/gap_analysis.md", _gaps_to_md(outputs["gaps"]))
        if outputs.get("ideas"):
            zf.writestr("analysis/ideas.md", _ideas_to_md(outputs["ideas"]))
        if outputs.get("plan"):
            zf.writestr("plan/execution_plan.md", _plan_to_md(outputs["plan"]))
        if outputs.get("guide"):
            zf.writestr("guide/research_guide.md", json.dumps(outputs["guide"], indent=2))
        if outputs.get("presentation"):
            zf.writestr("guide/presentation_slides.md", json.dumps(outputs["presentation"], indent=2))
        if outputs.get("report"):
            zf.writestr("report/research_paper.md", _report_to_md(outputs["report"]))
        # Raw JSON data
        zf.writestr("data/all_outputs.json", json.dumps(outputs, indent=2, default=str))

    buf.seek(0)
    filename = f"{project.title.replace(' ', '_')[:40]}_export.zip"

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
