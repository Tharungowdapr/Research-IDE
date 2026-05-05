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


# ── Streaming retrieval ────────────────────────────────────────────────────────

import json
from fastapi.responses import StreamingResponse as _StreamingResponse
from core.database import get_fresh_db
from models.project import Project, Output


@router.get("/stream/{project_id}/retrieve")
async def stream_retrieve(
    project_id: str,
    current_user=Depends(get_current_user),
):
    """SSE streaming paper retrieval with live progress."""
    async def event_stream():
        def sse(t, **kw):
            return f"data: {json.dumps({'type': t, **kw})}\n\n"

        db = get_fresh_db()
        try:
            project = db.query(Project).filter(
                Project.id == project_id,
                Project.user_id == current_user.id,
            ).first()
            if not project:
                yield sse("error", message="Project not found")
                return

            intent_out = db.query(Output).filter(
                Output.project_id == project_id,
                Output.output_type == "intent",
            ).first()
            intent = intent_out.data if intent_out else {}
            queries = intent.get("queries", [project.input_text[:100]])
            keywords = intent.get("keywords", [])

            yield sse("progress", message="Searching arXiv...")
            import asyncio; await asyncio.sleep(0.05)
            yield sse("progress", message="Searching Semantic Scholar...")
            await asyncio.sleep(0.05)
            yield sse("progress", message="Searching OpenAlex...")
            await asyncio.sleep(0.05)
            yield sse("progress", message="Searching PapersWithCode...")

            from services.retrieval.retrieval_service import retrieve_papers
            papers = await retrieve_papers(queries, keywords, max_results=25)

            yield sse("progress", message=f"Re-ranking {len(papers)} papers by relevance...")
            await asyncio.sleep(0.05)

            # Save
            existing = db.query(Output).filter(
                Output.project_id == project_id,
                Output.output_type == "papers",
            ).first()
            if existing:
                existing.data = {"papers": papers}
            else:
                db.add(Output(project_id=project_id, output_type="papers", data={"papers": papers}))
            project.current_stage = "gaps"
            db.commit()

            yield sse("result", data={"papers": papers, "count": len(papers)})
            yield sse("done", message="Retrieval complete")
        except Exception as e:
            yield sse("error", message=str(e))
        finally:
            db.close()

    return _StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


from pydantic import BaseModel as _BaseModel

class AddPaperRequest(_BaseModel):
    project_id: str
    title: str
    abstract: str = ""
    authors: list = []
    year: str = ""
    url: str = ""


@router.post("/papers/add")
async def add_paper_manually(
    body: AddPaperRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Add a paper manually to a project."""
    from models.project import Project, Output
    import uuid
    project = db.query(Project).filter(
        Project.id == body.project_id,
        Project.user_id == current_user.id,
    ).first()
    if not project:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Project not found")

    existing = db.query(Output).filter(
        Output.project_id == body.project_id,
        Output.output_type == "papers",
    ).first()
    papers_data = existing.data if existing else {"papers": []}
    papers = list(papers_data.get("papers", []))

    new_paper = {
        "id": f"manual_{uuid.uuid4().hex[:8]}",
        "title": body.title,
        "abstract": body.abstract,
        "authors": body.authors,
        "year": body.year,
        "citations": "0",
        "source": "manual",
        "url": body.url,
        "github_url": "",
        "score": 0.5,
        "methods": [],
        "datasets": [],
        "limitations": [],
    }
    papers.append(new_paper)

    if existing:
        existing.data = {"papers": papers}
    else:
        db.add(Output(project_id=body.project_id, output_type="papers", data={"papers": papers}))
    db.commit()
    return {"message": "Paper added", "paper": new_paper, "total": len(papers)}


@router.get("/stream/{project_id}/intent")
async def stream_intent(
    project_id: str,
    current_user=Depends(get_current_user),
):
    """SSE streaming intent extraction with live progress."""
    async def event_stream():
        def sse(t, **kw):
            return f"data: {json.dumps({'type': t, **kw})}\n\n"

        db = get_fresh_db()
        try:
            from models.project import Project, Output
            project = db.query(Project).filter(
                Project.id == project_id,
                Project.user_id == current_user.id,
            ).first()
            if not project:
                yield sse("error", message="Project not found")
                return

            yield sse("progress", message="Parsing research description...")
            import asyncio; await asyncio.sleep(0.05)
            yield sse("progress", message="Extracting domain and keywords...")

            from core.llm_client import build_llm_client_for_user
            from services.intent.intent_service import extract_intent
            llm = build_llm_client_for_user(current_user)

            yield sse("progress", message="Building search queries...")
            intent = await extract_intent(project.input_text, llm)

            existing = db.query(Output).filter(
                Output.project_id == project_id,
                Output.output_type == "intent",
            ).first()
            if existing:
                existing.data = intent
            else:
                db.add(Output(project_id=project_id, output_type="intent", data=intent))
            project.current_stage = "papers"
            db.commit()

            yield sse("result", data={"intent": intent})
            yield sse("done", message="Intent extracted")
        except Exception as e:
            yield sse("error", message=str(e))
        finally:
            db.close()

    from fastapi.responses import StreamingResponse as _SR
    return _SR(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
