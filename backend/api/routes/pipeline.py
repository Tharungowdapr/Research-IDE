"""
Pipeline Routes: NLP Intent Extraction, Paper Retrieval, Auto-Pipeline
"""

import json
import logging
import asyncio
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
from services.nlp_analysis.analyzer import analyze_text
from agents.gap_miner.gap_agent import run_gap_analysis
from agents.idea_generator.idea_agent import run_idea_generation
from agents.objective_generator.objective_agent import run_objective_generation
from agents.planner.planner_agent import run_planning
from agents.data_agent.data_agent import run_data_plan_generation
from agents.code_agent.code_agent import run_code_generation
from agents.experiment_agent.experiment_agent import run_experiment_generation
from agents.analysis_agent.analysis_agent import run_analysis_generation
from agents.research_guide.research_guide_agent import run_research_guide_generation
from agents.writer.writer_agent import run_report_generation
from agents.review_agent import run_review_generation

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


@router.post("/analyze")
async def run_nlp_analysis(
    body: IntentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deep NLP analysis of user input text."""
    project = _get_project(body.project_id, current_user.id, db)
    text = body.text or project.input_text

    llm = build_llm_client_for_user(current_user, max_tokens=1024)
    analysis = await analyze_text(text, llm)

    _save_output(db, project.id, "analysis", analysis)
    project.current_stage = "papers"
    db.commit()

    return {"project_id": project.id, "analysis": analysis}


@router.post("/retrieve")
async def run_paper_retrieval(
    body: RetrievalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve relevant papers using queries from intent or NLP analysis."""
    project = _get_project(body.project_id, current_user.id, db)

    intent_output = _get_output(db, project.id, "intent")
    analysis_output = _get_output(db, project.id, "analysis")

    queries = []
    keywords = []

    if intent_output:
        queries = intent_output.get("queries", [])
        keywords = intent_output.get("keywords", [])
    elif analysis_output:
        queries = analysis_output.get("search_queries", [])
        keyphrases = analysis_output.get("keyphrases", [])
        keywords = [kp["phrase"] for kp in keyphrases[:10]]
    else:
        raise HTTPException(status_code=400, detail="Run NLP analysis or intent extraction first")

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
    """Execute all 13 pipeline steps in sequence with streaming progress."""
    project = _get_project(body.project_id, current_user.id, db)
    llm = build_llm_client_for_user(current_user)
    text = project.input_text

    async def event_generator():
        failed_stages = []

        try:
            # ── 1: NLP Analysis ─────────────────────────────────────────────
            yield "data: " + json.dumps({"stage": "analysis", "status": "running", "message": "Running deep NLP analysis..."}) + "\n\n"
            try:
                analysis = await analyze_text(text, llm)
                _save_output(db, project.id, "analysis", analysis)
                project.current_stage = "papers"
                db.commit()
                yield "data: " + json.dumps({"stage": "analysis", "status": "done", "message": "NLP analysis complete"}) + "\n\n"
            except Exception as e:
                logging.error(f"NLP analysis failed: {e}")
                yield "data: " + json.dumps({"stage": "analysis", "status": "error", "message": f"NLP analysis failed: {str(e)[:200]}"}) + "\n\n"
                analysis = {}

            # ── 2: Intent + Papers ──────────────────────────────────────────
            await asyncio.sleep(10)
            yield "data: " + json.dumps({"stage": "papers", "status": "running", "message": "Extracting search intent & retrieving papers..."}) + "\n\n"
            intent = {}
            papers = []
            try:
                intent = await extract_intent(text, llm)
                _save_output(db, project.id, "intent", intent)
                queries = intent.get("queries", []) or (analysis.get("search_queries", []) if isinstance(analysis, dict) else [])
                keywords = intent.get("keywords", [])
                if not keywords and isinstance(analysis, dict) and analysis.get("keyphrases"):
                    keywords = [kp["phrase"] for kp in analysis["keyphrases"][:10]]
                papers = await retrieve_papers(queries, keywords, max_results=25, db=db)
                _save_output(db, project.id, "papers", {"papers": papers})
                project.current_stage = "gaps"
                db.commit()
                yield "data: " + json.dumps({"stage": "papers", "status": "done", "message": f"Retrieved {len(papers)} papers"}) + "\n\n"
            except Exception as e:
                logging.error(f"Paper retrieval failed: {e}")
                yield "data: " + json.dumps({"stage": "papers", "status": "error", "message": f"Paper retrieval failed: {str(e)[:200]}"}) + "\n\n"

            # ── 3: Research Gap ─────────────────────────────────────────────
            await asyncio.sleep(10)
            yield "data: " + json.dumps({"stage": "gaps", "status": "running", "message": "Analyzing research gaps..."}) + "\n\n"
            gaps = []
            try:
                gaps = await run_gap_analysis(papers, intent, llm, db=db)
                _save_output(db, project.id, "gaps", {"gaps": gaps})
                project.current_stage = "ideas"
                db.commit()
                yield "data: " + json.dumps({"stage": "gaps", "status": "done", "message": f"Identified {len(gaps)} gaps"}) + "\n\n"
            except Exception as e:
                logging.error(f"Gap analysis failed: {e}")
                yield "data: " + json.dumps({"stage": "gaps", "status": "error", "message": f"Gap analysis failed: {str(e)[:200]}"}) + "\n\n"

            # ── 4: Research Ideas ────────────────────────────────────────────
            await asyncio.sleep(10)
            yield "data: " + json.dumps({"stage": "ideas", "status": "running", "message": "Generating research ideas from gaps..."}) + "\n\n"
            ideas = []
            selected_idea = None
            try:
                ideas = await run_idea_generation(gaps, papers, intent, llm)
                _save_output(db, project.id, "ideas", {"ideas": ideas})
                selected_idea = ideas[0] if ideas else None
                if not selected_idea:
                    yield "data: " + json.dumps({"stage": "ideas", "status": "error", "message": "No ideas generated from gaps"}) + "\n\n"
                else:
                    _save_output(db, project.id, "selected_idea", {"idea": selected_idea})
                    project.current_stage = "objectives"
                    db.commit()
                    yield "data: " + json.dumps({"stage": "ideas", "status": "done", "message": f"Generated {len(ideas)} research ideas"}) + "\n\n"
            except Exception as e:
                logging.error(f"Idea generation failed: {e}")
                yield "data: " + json.dumps({"stage": "ideas", "status": "error", "message": f"Idea generation failed: {str(e)[:200]}"}) + "\n\n"

            if not selected_idea:
                yield "data: " + json.dumps({"stage": "error", "status": "error", "message": "Cannot continue pipeline: no idea was selected. Fix earlier errors and retry."}) + "\n\n"
                yield "data: [DONE]\n\n"
                return

            # ── 5+6: Objectives + Planning (sequential to avoid rate limits) ──
            await asyncio.sleep(10)
            yield "data: " + json.dumps({"stage": "objectives", "status": "running", "message": "Generating SMART objectives..."}) + "\n\n"
            objectives = []
            plan = {}
            try:
                objectives = await run_objective_generation(selected_idea, gaps, llm)
                _save_output(db, project.id, "objectives", {"objectives": objectives})
                yield "data: " + json.dumps({"stage": "objectives", "status": "done", "message": f"Generated {len(objectives)} SMART objectives"}) + "\n\n"
            except Exception as e:
                logging.error(f"Objectives generation failed: {e}")
                yield "data: " + json.dumps({"stage": "objectives", "status": "error", "message": f"Objectives failed: {str(e)[:200]}"}) + "\n\n"

            await asyncio.sleep(1)  # Rate limit buffer

            yield "data: " + json.dumps({"stage": "planner", "status": "running", "message": "Generating methodology plan..."}) + "\n\n"
            try:
                plan = await run_planning(selected_idea, intent, llm, papers=papers)
                _save_output(db, project.id, "plan", plan)
                project.current_stage = "data"
                db.commit()
                yield "data: " + json.dumps({"stage": "planner", "status": "done", "message": "Methodology plan generated"}) + "\n\n"
            except Exception as e:
                logging.error(f"Planning failed: {e}")
                yield "data: " + json.dumps({"stage": "planner", "status": "error", "message": f"Planning failed: {str(e)[:200]}"}) + "\n\n"

            await asyncio.sleep(8)  # Rate limit buffer before parallel-heavy block

            # ── 7+8+9: Data + Code + Experiments (sequential to avoid rate limits) ──
            yield "data: " + json.dumps({"stage": "data", "status": "running", "message": "Generating data plan, code, and experiments..."}) + "\n\n"
            try:
                data_plan = await run_data_plan_generation(
                    selected_idea, plan, llm,
                    gaps=gaps, papers=papers, objectives=objectives, intent=intent,
                )
                _save_output(db, project.id, "data_plan", data_plan)
                await asyncio.sleep(8)

                code_output = await run_code_generation(project.id, intent, papers, current_user.id, llm, idea=selected_idea, plan=plan)
                _save_output(db, project.id, "code", code_output)
                await asyncio.sleep(8)

                experiments = await run_experiment_generation(selected_idea, plan, llm)
                _save_output(db, project.id, "experiments", experiments)
                project.current_stage = "results"
                db.commit()
                yield "data: " + json.dumps({"stage": "data", "status": "done", "message": "Data plan, code, and experiments generated"}) + "\n\n"
            except Exception as e:
                logging.error(f"Data/Code/Experiments failed: {e}")
                yield "data: " + json.dumps({"stage": "data", "status": "error", "message": f"Data/Code/Experiments failed: {str(e)[:200]}"}) + "\n\n"

            # ── 10: Results Analysis ─────────────────────────────────────────
            await asyncio.sleep(8)
            yield "data: " + json.dumps({"stage": "results", "status": "running", "message": "Planning results analysis..."}) + "\n\n"
            try:
                analysis_plan = await run_analysis_generation(selected_idea, llm)
                _save_output(db, project.id, "analysis_template", analysis_plan)
                project.current_stage = "guide"
                db.commit()
                yield "data: " + json.dumps({"stage": "results", "status": "done", "message": "Results analysis planned"}) + "\n\n"
            except Exception as e:
                logging.error(f"Results analysis failed: {e}")
                yield "data: " + json.dumps({"stage": "results", "status": "error", "message": f"Results analysis failed: {str(e)[:200]}"}) + "\n\n"

            # ── 11: Research Guide ──────────────────────────────────────────
            await asyncio.sleep(8)
            yield "data: " + json.dumps({"stage": "guide", "status": "running", "message": "Generating research guide..."}) + "\n\n"
            try:
                guide = await run_research_guide_generation(selected_idea, papers, gaps, plan, intent, llm)
                _save_output(db, project.id, "guide", guide)
                project.current_stage = "report"
                db.commit()
                yield "data: " + json.dumps({"stage": "guide", "status": "done", "message": "Research guide generated"}) + "\n\n"
            except Exception as e:
                logging.error(f"Research guide failed: {e}")
                yield "data: " + json.dumps({"stage": "guide", "status": "error", "message": f"Research guide failed: {str(e)[:200]}"}) + "\n\n"

            # ── 12: Paper Writing ───────────────────────────────────────────
            await asyncio.sleep(8)
            yield "data: " + json.dumps({"stage": "report", "status": "running", "message": "Writing research paper..."}) + "\n\n"
            try:
                report = await run_report_generation(selected_idea, papers, gaps, plan, intent, llm)
                _save_output(db, project.id, "report", report)
                project.current_stage = "publish"
                db.commit()
                yield "data: " + json.dumps({"stage": "report", "status": "done", "message": "Research paper written"}) + "\n\n"
            except Exception as e:
                logging.error(f"Paper writing failed: {e}")
                yield "data: " + json.dumps({"stage": "report", "status": "error", "message": f"Paper writing failed: {str(e)[:200]}"}) + "\n\n"

            # ── 13: Review & Publish ────────────────────────────────────────
            await asyncio.sleep(8)
            yield "data: " + json.dumps({"stage": "publish", "status": "running", "message": "Generating review & publish checklist..."}) + "\n\n"
            try:
                review = await run_review_generation(selected_idea, llm)
                _save_output(db, project.id, "review", review)
                project.status = "done"
                db.commit()
                yield "data: " + json.dumps({"stage": "publish", "status": "done", "message": "Review & publish ready"}) + "\n\n"
            except Exception as e:
                logging.error(f"Review generation failed: {e}")
                yield "data: " + json.dumps({"stage": "publish", "status": "error", "message": f"Review generation failed: {str(e)[:200]}"}) + "\n\n"

            if failed_stages:
                yield "data: " + json.dumps({"stage": "complete", "status": "done", "message": f"Pipeline finished with {len(failed_stages)} failed stages: {', '.join(failed_stages)}"}) + "\n\n"
            else:
                yield "data: " + json.dumps({"stage": "complete", "status": "done", "message": "All 13 steps completed!"}) + "\n\n"

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
