"""
Plugin Management Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from core.database import get_db
from core.security import get_current_user
from models.user import User
from services.plugin_service import registry, load_plugins, create_sample_plugin

router = APIRouter()


@router.get("/")
async def list_plugins(
    current_user: User = Depends(get_current_user),
):
    """List all available plugins."""
    return {"plugins": registry.list_plugins()}


@router.post("/{name}/enable")
async def enable_plugin(
    name: str,
    current_user: User = Depends(get_current_user),
):
    """Enable a plugin."""
    if name not in registry._plugins:
        raise HTTPException(status_code=404, detail=f"Plugin {name} not found")
    
    if name not in registry._enabled:
        registry._enabled.append(name)
    
    return {"success": True, "message": f"Plugin {name} enabled"}


@router.post("/{name}/disable")
async def disable_plugin(
    name: str,
    current_user: User = Depends(get_current_user),
):
    """Disable a plugin."""
    if name in registry._enabled:
        registry._enabled.remove(name)
    
    return {"success": True, "message": f"Plugin {name} disabled"}


@router.post("/{name}/execute")
async def execute_plugin(
    name: str,
    params: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    """Execute a plugin."""
    try:
        result = registry.execute_plugin(name, **params)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load")
async def reload_plugins(
    current_user: User = Depends(get_current_user),
):
    """Reload all plugins from disk."""
    load_plugins()
    return {"success": True, "message": "Plugins reloaded"}


@router.get("/sample/create")
async def create_sample(
    current_user: User = Depends(get_current_user),
):
    """Create a sample plugin for reference."""
    create_sample_plugin()
    return {"success": True, "message": "Sample plugin created"}
