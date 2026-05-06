"""
Project Routes: Create, List, Get, Delete
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.project import Project, Output

router = APIRouter()


class CreateProjectRequest(BaseModel):
    title: str
    input_text: str


class UpdateStageRequest(BaseModel):
    stage: str


@router.post("/")
async def create_project(
    body: CreateProjectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = Project(
        user_id=current_user.id,
        title=body.title,
        input_text=body.input_text,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return _project_response(project)


@router.get("/")
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    projects = (
        db.query(Project)
        .filter(Project.user_id == current_user.id)
        .order_by(Project.updated_at.desc())
        .all()
    )
    return [_project_response(p) for p in projects]


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _get_project_or_404(project_id, current_user.id, db)
    outputs = db.query(Output).filter(Output.project_id == project_id).all()
    resp = _project_response(project)
    resp["outputs"] = {o.output_type: o.data for o in outputs}
    return resp


@router.patch("/{project_id}/stage")
async def update_stage(
    project_id: str,
    body: UpdateStageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _get_project_or_404(project_id, current_user.id, db)
    project.current_stage = body.stage
    db.commit()
    return {"message": "Stage updated", "stage": body.stage}


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _get_project_or_404(project_id, current_user.id, db)
    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_project_or_404(project_id: str, user_id: str, db: Session) -> Project:
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == user_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _project_response(project: Project) -> dict:
    return {
        "id": project.id,
        "title": project.title,
        "input_text": project.input_text,
        "status": project.status,
        "current_stage": project.current_stage,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }
