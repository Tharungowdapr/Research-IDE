"""
Zotero Integration Routes
"""

import fastapi
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from core.security import get_current_user, encrypt_api_key, decrypt_api_key
from models.user import User
from services.zotero_service import get_user_libraries, search_zotero_library, export_to_zotero

router = APIRouter()


class ZoteroConfig(BaseModel):
    zotero_key: str
    user_id: str
    collection_id: Optional[str] = None


@router.post("/config")
async def save_zotero_config(
    config: ZoteroConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save Zotero API credentials for user (encrypted)."""
    current_user.zotero_key_encrypted = encrypt_api_key(config.zotero_key)
    current_user.zotero_user_id = config.user_id
    db.commit()
    return {"success": True, "message": "Zotero config saved securely"}


@router.get("/libraries")
async def list_libraries(
    current_user: User = Depends(get_current_user),
):
    """List user's Zotero libraries using stored credentials."""
    if not current_user.zotero_key_encrypted or not current_user.zotero_user_id:
        raise HTTPException(status_code=400, detail="Zotero not configured. Save config first.")
    zotero_key = decrypt_api_key(current_user.zotero_key_encrypted)
    libraries = await get_user_libraries(zotero_key, current_user.zotero_user_id)
    return {"libraries": libraries}


@router.get("/search")
async def search_library(
    query: str = Query(..., description="Search query"),
    limit: int = Query(20, description="Max results"),
    current_user: User = Depends(get_current_user),
):
    """Search papers in Zotero library using stored credentials."""
    if not current_user.zotero_key_encrypted or not current_user.zotero_user_id:
        raise HTTPException(status_code=400, detail="Zotero not configured. Save config first.")
    zotero_key = decrypt_api_key(current_user.zotero_key_encrypted)
    papers = await search_zotero_library(zotero_key, current_user.zotero_user_id, query, limit)
    return {"papers": papers}


@router.post("/export/{project_id}")
async def export_project_papers(
    project_id: str,
    collection_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export project papers to Zotero using stored credentials."""
    from models.project import Project, Output

    if not current_user.zotero_key_encrypted or not current_user.zotero_user_id:
        raise HTTPException(status_code=400, detail="Zotero not configured. Save config first.")

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    papers_data = db.query(Output).filter(
        Output.project_id == project_id,
        Output.output_type == "papers"
    ).first()

    if not papers_data or not papers_data.data.get("papers"):
        raise HTTPException(status_code=400, detail="No papers found in project")

    zotero_key = decrypt_api_key(current_user.zotero_key_encrypted)
    result = await export_to_zotero(
        zotero_key,
        current_user.zotero_user_id,
        papers_data.data["papers"],
        collection_id
    )

    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Export failed"))
