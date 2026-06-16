"""
Agent Routes: Gap Analysis, Idea Generation, Planning, Code, Report, Downloads, Streaming
"""

import io
import json as json_lib
import re
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
from agents.code_agent.code_agent import run_code_generation, run_code_generation_stream
from agents.writer.writer_agent import run_report_generation
from agents.literature_review_agent import generate_literature_review as _generate_literature_review, generate_annotated_bibliography as _generate_annotated_bibliography
from agents.guide_agent import run_guide_generation
from agents.presentation_agent import run_presentation_generation
from agents.chat_agent import run_chat, run_chat_stream
from services.citation_service import build_citation_graph

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
    llm = build_llm_client_for_user(current_user, max_tokens=8192)

    try:
        gaps = await run_gap_analysis(papers_data.get("papers", []), intent, llm, db=db)
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

    llm = build_llm_client_for_user(current_user, max_tokens=8192)

    try:
        papers_list = papers_data.get("papers", [])
        plan = await run_planning(selected.get("idea", {}), intent, llm, papers=papers_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning failed: {str(e)}")

    _save_output(db, project.id, "plan", plan)
    project.current_stage = "code"
    db.commit()

    return {"project_id": project.id, "plan": plan}

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

    llm = build_llm_client_for_user(current_user, max_tokens=8192)
    papers_list = papers_data.get("papers", [])

    async def event_generator():
        try:
            full_content = ""
            try:
                async for chunk in run_planning_stream(selected.get("idea", {}), intent, llm, papers=papers_list):
                    full_content += chunk
                    yield f"data: {json_lib.dumps({'chunk': chunk})}\n\n"
            except Exception as stream_err:
                logging.warning(f"Streaming failed, falling back to non-streaming: {stream_err}")
                # Fallback: use non-streaming planning
                try:
                    from agents.planner.planner_agent import run_planning
                    plan = await run_planning(selected.get("idea", {}), intent, llm, papers=papers_list)
                    full_content = json_lib.dumps(plan)
                    yield f"data: {json_lib.dumps({'chunk': json_lib.dumps(plan)})}\n\n"
                except Exception as fallback_err:
                    yield f"data: {json_lib.dumps({'error': f'Planning failed: {str(fallback_err)}'})}\n\n"
                    yield "data: [DONE]\n\n"
                    return
            
            # When done, try to parse the full content to save to DB
            if full_content:
                try:
                    content_to_parse = full_content.strip()
                    match = re.search(r'\{.*\}', content_to_parse, re.DOTALL)
                    if match:
                        content_to_parse = match.group(0)
                        
                    parsed_plan = json_lib.loads(content_to_parse)
                    _save_output(db, project.id, "plan", parsed_plan)
                    project.current_stage = "code"
                    db.commit()
                except Exception as e:
                    logging.error(f"Failed to parse streamed plan: {e}")
                
            yield "data: [DONE]\n\n"
        except Exception as e:
            logging.error(f"Planning streaming error: {e}")
            yield f"data: {json_lib.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/generate-code")
async def generate_code(
    body: AgentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate starter code for the selected idea and plan."""
    project, papers_data, intent = _load_project_context(body.project_id, current_user.id, db)
    selected = _get_output(db, project.id, "selected_idea")
    plan = _get_output(db, project.id, "plan")
    if not selected or not plan:
        raise HTTPException(status_code=400, detail="Complete planning step first")

    llm = build_llm_client_for_user(current_user)

    file_hints = plan.get("file_structure", [])
    papers_list = papers_data.get("papers", [])

    try:
        code = await run_code_generation(selected.get("idea", {}), plan, llm, file_hints=file_hints, papers=papers_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code generation failed: {str(e)}")

    _save_output(db, project.id, "code", code)
    project.current_stage = "report"
    db.commit()

    return {"project_id": project.id, "code": code}

@router.post("/generate-code/stream")
async def generate_code_stream(
    body: AgentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate starter code using SSE."""
    project, papers_data, intent = _load_project_context(body.project_id, current_user.id, db)
    selected = _get_output(db, project.id, "selected_idea")
    plan = _get_output(db, project.id, "plan")
    if not selected or not plan:
        raise HTTPException(status_code=400, detail="Complete planning step first")

    llm = build_llm_client_for_user(current_user)
    file_hints = plan.get("file_structure", [])
    papers_list = papers_data.get("papers", [])

    async def event_generator():
        try:
            full_content = ""
            try:
                async for chunk in run_code_generation_stream(selected.get("idea", {}), plan, llm, file_hints=file_hints, papers=papers_list):
                    full_content += chunk
                    yield f"data: {json_lib.dumps({'chunk': chunk})}\n\n"
            except Exception as stream_err:
                logging.warning(f"Code streaming failed, falling back to non-streaming: {stream_err}")
                # Fallback: use non-streaming code generation
                try:
                    code = await run_code_generation(selected.get("idea", {}), plan, llm, file_hints=file_hints, papers=papers_list)
                    full_content = json_lib.dumps(code)
                    yield f"data: {json_lib.dumps({'chunk': json_lib.dumps(code)})}\n\n"
                except Exception as fallback_err:
                    yield f"data: {json_lib.dumps({'error': f'Code generation failed: {str(fallback_err)}'})}\n\n"
                    yield "data: [DONE]\n\n"
                    return
                
            # When done, try to parse
            if full_content:
                try:
                    content_to_parse = full_content.strip()
                    match = re.search(r'\{.*\}', content_to_parse, re.DOTALL)
                    if match:
                        content_to_parse = match.group(0)
                        
                    parsed_code = json_lib.loads(content_to_parse)
                    _save_output(db, project.id, "code", parsed_code)
                    project.current_stage = "report"
                    db.commit()
                except Exception as parse_err:
                    logging.error(f"Failed to parse streamed code: {parse_err}")

            yield "data: [DONE]\n\n"
        except Exception as e:
            logging.error(f"Code streaming error: {e}")
            yield f"data: {json_lib.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


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


# ── Literature Review ────────────────────────────────────────────

@router.post("/{project_id}/literature-review")
async def literature_review_route(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate automated literature review for project papers."""
    project = _get_project(project_id, current_user.id, db)
    papers_data = _get_output(db, project_id, "papers")
    intent = _get_output(db, project_id, "intent")
    
    if not papers_data or not papers_data.get("papers"):
        raise HTTPException(status_code=400, detail="No papers found for this project")
    
    try:
        llm = build_llm_client_for_user(current_user)
        review = await _generate_literature_review(
            papers_data.get("papers", []),
            intent or {},
            llm
        )
        return review
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Literature review generation failed: {str(e)}")


@router.post("/{project_id}/annotated-bibliography")
async def annotated_bibliography_route(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate annotated bibliography for project papers."""
    project = _get_project(project_id, current_user.id, db)
    papers_data = _get_output(db, project_id, "papers")
    
    if not papers_data or not papers_data.get("papers"):
        raise HTTPException(status_code=400, detail="No papers found for this project")
    
    try:
        llm = build_llm_client_for_user(current_user)
        annotations = await _generate_annotated_bibliography(
            papers_data.get("papers", []),
            llm
        )
        return {"annotations": annotations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bibliography generation failed: {str(e)}")


# ── Citation Graph ────────────────────────────────────────────

@router.get("/{project_id}/citation-graph")
async def get_citation_graph(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Build and return citation graph for the project's papers."""
    project = _get_project(project_id, current_user.id, db)
    papers_data = _get_output(db, project_id, "papers")
    
    if not papers_data or not papers_data.get("papers"):
        raise HTTPException(status_code=400, detail="No papers found for this project")
    
    try:
        graph = await build_citation_graph(papers_data.get("papers", []))
        return graph
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Citation graph generation failed: {str(e)}")


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


# ── Guide Generation ──────────────────────────────────────────────────────────

class GuideRequest(BaseModel):
    project_id: str


@router.post("/generate-guide")
async def generate_guide(
    body: GuideRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a comprehensive research guide."""
    project, papers_data, intent = _load_project_context(body.project_id, current_user.id, db)
    selected = _get_output(db, project.id, "selected_idea")
    gaps = _get_output(db, project.id, "gaps") or {"gaps": []}
    plan = _get_output(db, project.id, "plan") or {}
    if not selected:
        raise HTTPException(status_code=400, detail="Select an idea first")

    llm = build_llm_client_for_user(current_user)
    idea = selected.get("idea", {})

    try:
        guide = await run_guide_generation(
            idea,
            papers_data.get("papers", []),
            gaps.get("gaps", []),
            plan,
            intent,
            llm,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Guide generation failed: {str(e)}")

    _save_output(db, project.id, "guide", guide)
    project.current_stage = "guide"
    db.commit()

    return {"project_id": project.id, "guide": guide}


# ── Presentation Generation ───────────────────────────────────────────────────

class PresentationRequest(BaseModel):
    project_id: str


@router.post("/generate-presentation")
async def generate_presentation(
    body: PresentationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate presentation slides from research context."""
    project, papers_data, intent = _load_project_context(body.project_id, current_user.id, db)
    selected = _get_output(db, project.id, "selected_idea")
    guide = _get_output(db, project.id, "guide") or {}
    if not selected:
        raise HTTPException(status_code=400, detail="Select an idea first")

    llm = build_llm_client_for_user(current_user)
    idea = selected.get("idea", {})

    try:
        presentation = await run_presentation_generation(
            guide,
            idea,
            papers_data.get("papers", []),
            intent,
            llm,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Presentation generation failed: {str(e)}")

    _save_output(db, project.id, "presentation", presentation)
    return {"project_id": project.id, "slides": presentation.get("slides", [])}


# ── Chat (Non-Streaming) ──────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    project_id: str
    question: str
    conversation_history: list = []


@router.post("/chat")
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Non-streaming chat with research assistant."""
    project = _get_project(body.project_id, current_user.id, db)

    project_context = {
        "intent": _get_output(db, project.id, "intent") or {},
        "papers": _get_output(db, project.id, "papers") or {},
        "gaps": _get_output(db, project.id, "gaps") or {},
        "ideas": _get_output(db, project.id, "ideas") or {},
        "selected_idea": _get_output(db, project.id, "selected_idea") or {},
        "plan": _get_output(db, project.id, "plan") or {},
        "report": _get_output(db, project.id, "report") or {},
    }

    llm = build_llm_client_for_user(current_user)

    try:
        response = await run_chat(
            body.question,
            body.conversation_history,
            project_context,
            llm,
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


# ── Chat (Streaming SSE) ──────────────────────────────────────────────────────

@router.post("/chat/stream")
async def chat_stream(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Streaming chat with research assistant using SSE."""
    project = _get_project(body.project_id, current_user.id, db)

    project_context = {
        "intent": _get_output(db, project.id, "intent") or {},
        "papers": _get_output(db, project.id, "papers") or {},
        "gaps": _get_output(db, project.id, "gaps") or {},
        "ideas": _get_output(db, project.id, "ideas") or {},
        "selected_idea": _get_output(db, project.id, "selected_idea") or {},
        "plan": _get_output(db, project.id, "plan") or {},
        "report": _get_output(db, project.id, "report") or {},
    }

    llm = build_llm_client_for_user(current_user)

    async def event_generator():
        try:
            async for chunk in run_chat_stream(
                body.question,
                body.conversation_history,
                project_context,
                llm,
            ):
                yield f"data: {json_lib.dumps({'chunk': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logging.error(f"Chat streaming error: {e}")
            yield f"data: {json_lib.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── PPTX Download ─────────────────────────────────────────────────────────────

@router.get("/{project_id}/download/pptx")
async def download_pptx(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate and download presentation as PPTX."""
    _get_project(project_id, current_user.id, db)
    presentation = _get_output(db, project_id, "presentation")
    if not presentation:
        raise HTTPException(status_code=400, detail="Generate the presentation first")

    from services.export_service import generate_pptx
    pptx_bytes = generate_pptx(presentation)

    return StreamingResponse(
        io.BytesIO(pptx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": "attachment; filename=presentation.pptx"},
    )
