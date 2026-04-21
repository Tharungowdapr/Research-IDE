"""
Pipeline Routes: NLP Intent Extraction, Paper Retrieval
"""

from fastapi import APIRouter, Depends, HTTPException
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
        papers = await retrieve_papers(queries, keywords, max_results=body.max_papers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

    _save_output(db, project.id, "papers", {"papers": papers})
    project.current_stage = "gaps"
    db.commit()

    return {"project_id": project.id, "papers": papers, "count": len(papers)}


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
