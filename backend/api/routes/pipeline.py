"""
Pipeline Routes: NLP Intent Extraction, Paper Retrieval, Auto-Pipeline
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List

from core.database import get_db
from core.security import get_current_user
from core.llm_client import build_llm_client_for_user
from models.user import User
from models.project import Project, Output
from services.intent.intent_service import extract_intent
from services.retrieval.retrieval_service import retrieve_papers
from agents.gap_miner.gap_agent import run_gap_analysis
from agents.idea_generator.idea_agent import run_idea_generation
from agents.planner.planner_agent import run_planning
from agents.research_guide.research_guide_agent import run_research_guide_generation
from agents.writer.writer_agent import run_report_generation

router = APIRouter()


class IntentRequest(BaseModel):
    project_id: str
    text: Optional[str] = None  # If None, uses project.input_text


class RetrievalRequest(BaseModel):
    project_id: str
    max_papers: int = 20


@router.post("/intent")
async def run_intent_extraction(
    body: IntentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Extract structured intent from the user's research query."""
    project = _get_project(body.project_id, current_user.id, db)
    text = body.text or project.input_text

    llm = build_llm_client_for_user(current_user)

    try:
        intent = await extract_intent(text, llm)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intent extraction failed: {str(e)}")

    # Persist output
    _save_output(db, project.id, "intent", intent)
    project.current_stage = "papers"
    db.commit()

    return {"project_id": project.id, "intent": intent}


@router.post("/retrieve")
async def run_paper_retrieval(
    body: RetrievalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve relevant papers using the extracted intent queries."""
    project = _get_project(body.project_id, current_user.id, db)

    # Load intent output
    intent_output = _get_output(db, project.id, "intent")
    if not intent_output:
        raise HTTPException(status_code=400, detail="Run intent extraction first")

    queries = intent_output.get("queries", [])
    keywords = intent_output.get("keywords", [])

    try:
        papers = await retrieve_papers(queries, keywords, max_results=body.max_papers, db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

    _save_output(db, project.id, "papers", {"papers": papers})
    project.current_stage = "gaps"
    db.commit()

    return {"project_id": project.id, "papers": papers, "count": len(papers)}


# ── Auto-Pipeline Orchestrator ────────────────────────────────────────────────

class RunFullRequest(BaseModel):
    project_id: str


@router.post("/run-full")
async def run_full_pipeline(
    body: RunFullRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute all pipeline steps in sequence with streaming progress."""
    project = _get_project(body.project_id, current_user.id, db)
    llm = build_llm_client_for_user(current_user)
    text = project.input_text

    async def event_generator():
        try:
            # Step 1: Intent
            yield "data: " + json.dumps({"stage": "intent", "status": "running", "message": "Extracting research intent..."}) + "\n\n"
            intent = await extract_intent(text, llm)
            _save_output(db, project.id, "intent", intent)
            project.current_stage = "papers"
            db.commit()
            yield "data: " + json.dumps({"stage": "intent", "status": "done", "message": "Intent extracted"}) + "\n\n"

            # Step 2: Paper Retrieval
            yield "data: " + json.dumps({"stage": "papers", "status": "running", "message": "Retrieving papers from arXiv, Semantic Scholar, OpenAlex, PapersWithCode..."}) + "\n\n"
            queries = intent.get("queries", [])
            keywords = intent.get("keywords", [])
            papers = await retrieve_papers(queries, keywords, max_results=25, db=db)
            _save_output(db, project.id, "papers", {"papers": papers})
            project.current_stage = "gaps"
            db.commit()
            yield "data: " + json.dumps({"stage": "papers", "status": "done", "message": f"Retrieved {len(papers)} papers"}) + "\n\n"

            # Step 3: Gap Analysis
            yield "data: " + json.dumps({"stage": "gaps", "status": "running", "message": "Analyzing research gaps..."}) + "\n\n"
            gaps = await run_gap_analysis(papers, intent, llm)
            _save_output(db, project.id, "gaps", {"gaps": gaps})
            project.current_stage = "ideas"
            db.commit()
            yield "data: " + json.dumps({"stage": "gaps", "status": "done", "message": f"Identified {len(gaps)} gaps"}) + "\n\n"

            # Step 4: Idea Generation
            yield "data: " + json.dumps({"stage": "ideas", "status": "running", "message": "Generating research ideas..."}) + "\n\n"
            ideas = await run_idea_generation(gaps, papers, intent, llm)
            _save_output(db, project.id, "ideas", {"ideas": ideas})
            yield "data: " + json.dumps({"stage": "ideas", "status": "done", "message": f"Generated {len(ideas)} ideas"}) + "\n\n"

            # Auto-select best idea
            selected_idea = ideas[0] if ideas else None
            if selected_idea:
                _save_output(db, project.id, "selected_idea", {"idea": selected_idea})
                project.current_stage = "planner"
                db.commit()
                yield "data: " + json.dumps({"stage": "select_idea", "status": "done", "message": f"Selected best idea: {selected_idea.get('title', '')[:60]}"}) + "\n\n"
            else:
                yield "data: " + json.dumps({"stage": "select_idea", "status": "error", "message": "No ideas generated"}) + "\n\n"
                yield "data: [DONE]\n\n"
                return

            # Step 5: Execution Plan
            yield "data: " + json.dumps({"stage": "planner", "status": "running", "message": "Generating execution plan..."}) + "\n\n"
            plan = await run_planning(selected_idea, intent, llm, papers=papers)
            _save_output(db, project.id, "plan", plan)
            project.current_stage = "guide"
            db.commit()
            yield "data: " + json.dumps({"stage": "planner", "status": "done", "message": "Plan generated"}) + "\n\n"

            # Step 6: Research Guide (replaces old code gen)
            yield "data: " + json.dumps({"stage": "guide", "status": "running", "message": "Generating research guide..."}) + "\n\n"
            guide = await run_research_guide_generation(selected_idea, papers, gaps, plan, intent, llm)
            _save_output(db, project.id, "guide", guide)
            project.current_stage = "report"
            db.commit()
            yield "data: " + json.dumps({"stage": "guide", "status": "done", "message": "Research guide generated"}) + "\n\n"

            # Step 7: Report
            yield "data: " + json.dumps({"stage": "report", "status": "running", "message": "Generating research paper..."}) + "\n\n"
            report = await run_report_generation(selected_idea, papers, gaps, plan, intent, llm)
            _save_output(db, project.id, "report", report)
            project.status = "done"
            db.commit()
            yield "data: " + json.dumps({"stage": "report", "status": "done", "message": "Research paper generated"}) + "\n\n"

            yield "data: " + json.dumps({"stage": "complete", "status": "done", "message": "All steps completed!"}) + "\n\n"
        except Exception as e:
            logging.error(f"Auto-pipeline error: {e}")
            yield "data: " + json.dumps({"stage": "error", "status": "error", "message": str(e)}) + "\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_project(project_id: str, user_id: str, db: Session) -> Project:
    p = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


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


def _get_output(db: Session, project_id: str, output_type: str) -> Optional[dict]:
    o = db.query(Output).filter(
        Output.project_id == project_id,
        Output.output_type == output_type
    ).first()
    return o.data if o else None
