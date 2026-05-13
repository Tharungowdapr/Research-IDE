"""
Agent Routes: Gap Analysis, Idea Generation, Planning, Research Guide, Presentation, Report, Downloads, Streaming
"""

import io
import re
import json as json_lib
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from core.security import get_current_user
from core.llm_client import build_llm_client_for_user
from models.user import User
from models.project import Project, Output
from agents.gap_miner.gap_agent import run_gap_analysis
from agents.idea_generator.idea_agent import run_idea_generation
from agents.planner.planner_agent import run_planning, run_planning_stream
from agents.research_guide.research_guide_agent import run_research_guide_generation
from agents.presentation.presentation_agent import generate_slide_content, export_pptx
from agents.writer.writer_agent import run_report_generation
from agents.chat.rag_agent import chat_with_papers, chat_stream

router = APIRouter()


class AgentRequest(BaseModel):
    project_id: str


class SelectIdeaRequest(BaseModel):
    project_id: str
    idea_index: int


@router.post("/analyze-gaps")
async def analyze_gaps(
    body: AgentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run gap analysis on retrieved papers."""
    project, papers_data, intent = _load_project_context(body.project_id, current_user.id, db)
    llm = build_llm_client_for_user(current_user)

    try:
        gaps = await run_gap_analysis(papers_data.get("papers", []), intent, llm)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gap analysis failed: {str(e)}")

    _save_output(db, project.id, "gaps", {"gaps": gaps})
    project.current_stage = "ideas"
    db.commit()

    return {"project_id": project.id, "gaps": gaps}


@router.post("/generate-ideas")
async def generate_ideas(
    body: AgentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate ranked research ideas based on gap analysis."""
    project, papers_data, intent = _load_project_context(body.project_id, current_user.id, db)
    gaps_output = _get_output(db, project.id, "gaps")
    if not gaps_output:
        raise HTTPException(status_code=400, detail="Run gap analysis first")

    llm = build_llm_client_for_user(current_user)

    try:
        ideas = await run_idea_generation(
            gaps_output.get("gaps", []),
            papers_data.get("papers", []),
            intent,
            llm,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Idea generation failed: {str(e)}")

    _save_output(db, project.id, "ideas", {"ideas": ideas})
    project.current_stage = "ideas"
    db.commit()

    return {"project_id": project.id, "ideas": ideas}


@router.post("/select-idea")
async def select_idea(
    body: SelectIdeaRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Select a specific idea to proceed with."""
    project = _get_project(body.project_id, current_user.id, db)
    ideas_output = _get_output(db, project.id, "ideas")
    if not ideas_output:
        raise HTTPException(status_code=400, detail="No ideas found")

    ideas = ideas_output.get("ideas", [])
    if body.idea_index >= len(ideas):
        raise HTTPException(status_code=400, detail="Invalid idea index")

    selected = ideas[body.idea_index]
    _save_output(db, project.id, "selected_idea", {"idea": selected})
    project.current_stage = "planner"
    db.commit()

    return {"project_id": project.id, "selected_idea": selected}


@router.post("/plan")
async def create_plan(
    body: AgentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate execution plan for the selected idea."""
    project, papers_data, intent = _load_project_context(body.project_id, current_user.id, db)
    selected = _get_output(db, project.id, "selected_idea")
    if not selected:
        raise HTTPException(status_code=400, detail="Select an idea first")

    llm = build_llm_client_for_user(current_user)

    try:
        papers_list = papers_data.get("papers", [])
        plan = await run_planning(selected.get("idea", {}), intent, llm, papers=papers_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning failed: {str(e)}")

    _save_output(db, project.id, "plan", plan)
    project.current_stage = "guide"
    db.commit()

    return {"project_id": project.id, "plan": plan}

@router.post

@router.post("/plan/stream")
async def create_plan_stream(
    body: AgentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate execution plan using SSE."""
    project, papers_data, intent = _load_project_context(body.project_id, current_user.id, db)
    selected = _get_output(db, project.id, "selected_idea")
    if not selected:
        raise HTTPException(status_code=400, detail="Select an idea first")

    llm = build_llm_client_for_user(current_user)
    papers_list = papers_data.get("papers", [])

    async def event_generator():
        try:
            full_content = ""
            async for chunk in run_planning_stream(selected.get("idea", {}), intent, llm, papers=papers_list):
                full_content += chunk
                yield f"data: {json_lib.dumps({'chunk': chunk})}\n\n"
            
            try:
                content_to_parse = full_content.strip()
                match = re.search(r'\{.*\}', content_to_parse, re.DOTALL)
                if match:
                    content_to_parse = match.group(0)
                    
                parsed_plan = json_lib.loads(content_to_parse)
                _save_output(db, project.id, "plan", parsed_plan)
                project.current_stage = "guide"
                db.commit()
            except Exception as e:
                logging.error(f"Failed to parse streamed plan: {e}")
                
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json_lib.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ── Research Guide & Presentation (replaces old Code Generation) ──────────────

@router.post("/generate-guide")
async def generate_guide(
    body: AgentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate research guide for the selected idea and plan."""
    project, papers_data, intent = _load_project_context(body.project_id, current_user.id, db)
    selected = _get_output(db, project.id, "selected_idea")
    plan = _get_output(db, project.id, "plan")
    gaps = _get_output(db, project.id, "gaps")
    if not selected or not plan:
        raise HTTPException(status_code=400, detail="Complete planning step first")

    llm = build_llm_client_for_user(current_user)

    try:
        guide = await run_research_guide_generation(
            selected.get("idea", {}),
            papers_data.get("papers", []),
            gaps.get("gaps", []) if gaps else [],
            plan,
            intent,
            llm,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research guide generation failed: {str(e)}")

    _save_output(db, project.id, "guide", guide)
    project.current_stage = "report"
    db.commit()

    return {"project_id": project.id, "guide": guide}


@router.post("/generate-presentation")
async def generate_presentation(
    body: AgentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate slide content for the project."""
    project, papers_data, intent = _load_project_context(body.project_id, current_user.id, db)
    selected = _get_output(db, project.id, "selected_idea")
    plan = _get_output(db, project.id, "plan")
    if not selected:
        raise HTTPException(status_code=400, detail="Select an idea first")

    llm = build_llm_client_for_user(current_user)

    try:
        slides = await generate_slide_content(
            selected.get("idea", {}),
            papers_data.get("papers", []),
            plan or {},
            intent,
            llm,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Presentation generation failed: {str(e)}")

    _save_output(db, project.id, "presentation", slides)

    return {"project_id": project.id, "slides": slides.get("slides", [])}


@router.get("/{project_id}/download/pptx")
async def download_pptx(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download presentation as PPTX."""
    _get_project(project_id, current_user.id, db)
    slides_data = _get_output(db, project_id, "presentation")
    if not slides_data:
        raise HTTPException(status_code=400, detail="Generate the presentation first")

    pptx_bytes = export_pptx(slides_data)

    return StreamingResponse(
        io.BytesIO(pptx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": "attachment; filename=research_presentation.pptx"},
    )


@router.post("/generate-report")
async def generate_report(
    body: AgentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a research paper/report."""
    project, papers_data, intent = _load_project_context(body.project_id, current_user.id, db)
    selected = _get_output(db, project.id, "selected_idea")
    plan = _get_output(db, project.id, "plan")
    gaps = _get_output(db, project.id, "gaps")
    if not selected:
        raise HTTPException(status_code=400, detail="Select an idea first")

    llm = build_llm_client_for_user(current_user)

    try:
        report = await run_report_generation(
            selected.get("idea", {}),
            papers_data.get("papers", []),
            gaps.get("gaps", []) if gaps else [],
            plan or {},
            intent,
            llm,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

    _save_output(db, project.id, "report", report)
    project.status = "done"
    db.commit()

    return {"project_id": project.id, "report": report}


# ── Chat / RAG ────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    project_id: str
    question: str
    conversation_history: Optional[list] = None


@router.post("/chat")
async def chat_about_project(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Answer a question about the project using RAG over retrieved papers."""
    project, papers_data, intent = _load_project_context(body.project_id, current_user.id, db)
    llm = build_llm_client_for_user(current_user)

    try:
        answer = await chat_with_papers(
            body.question,
            papers_data.get("papers", []),
            intent,
            llm,
            conversation_history=body.conversation_history,
        )
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.post("/chat/stream")
async def chat_stream_endpoint(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Stream a chat response about the project."""
    project, papers_data, intent = _load_project_context(body.project_id, current_user.id, db)
    llm = build_llm_client_for_user(current_user)

    async def event_generator():
        try:
            async for chunk in chat_stream(
                body.question,
                papers_data.get("papers", []),
                intent,
                llm,
                conversation_history=body.conversation_history,
            ):
                yield f"data: {json_lib.dumps({'chunk': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json_lib.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_project(project_id: str, user_id: str, db: Session) -> Project:
    p = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


def _load_project_context(project_id: str, user_id: str, db: Session):
    project = _get_project(project_id, user_id, db)
    papers_data = _get_output(db, project_id, "papers") or {"papers": []}
    intent = _get_output(db, project_id, "intent") or {}
    return project, papers_data, intent


def _save_output(db: Session, project_id: str, output_type: str, data: dict):
    existing = db.query(Output).filter(
        Output.project_id == project_id,
        Output.output_type == output_type
    ).first()
    if existing:
        existing.data = data
    else:
        db.add(Output(project_id=project_id, output_type=output_type, data=data))
    db.commit()


def _get_output(db: Session, project_id: str, output_type: str):
    o = db.query(Output).filter(
        Output.project_id == project_id,
        Output.output_type == output_type
    ).first()
    return o.data if o else None


# ── Download Endpoints ────────────────────────────────────────────────────────

@router.get("/{project_id}/download/docx")
async def download_docx(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate and download IEEE-format DOCX."""
    _get_project(project_id, current_user.id, db)
    report = _get_output(db, project_id, "report")
    if not report:
        raise HTTPException(status_code=400, detail="Generate the report first")

    from services.export_service import generate_docx
    docx_bytes = generate_docx(report)

    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=research_paper.docx"},
    )


@router.get("/{project_id}/download/pdf")
async def download_pdf(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate and download IEEE-format PDF."""
    _get_project(project_id, current_user.id, db)
    report = _get_output(db, project_id, "report")
    if not report:
        raise HTTPException(status_code=400, detail="Generate the report first")

    from services.export_service import generate_pdf_html

    html_content = generate_pdf_html(report)

    # Try WeasyPrint first, fallback to HTML download
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_content).write_pdf()
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=research_paper.pdf"},
        )
    except ImportError:
        # WeasyPrint not installed — return HTML as PDF-like download
        html_bytes = html_content.encode("utf-8")
        return StreamingResponse(
            io.BytesIO(html_bytes),
            media_type="text/html",
            headers={"Content-Disposition": "attachment; filename=research_paper.html"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
