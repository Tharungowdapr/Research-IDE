"""
LLM Configuration Routes
- Save/retrieve API keys per provider
- Set preferred model
- Test connections
- List available Ollama models
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user, encrypt_api_key
from core.llm_client import (
    PROVIDER_MODELS,
    get_ollama_models,
    LLMClient,
    LLMProvider,
    build_llm_client_for_user,
)
from models.user import User

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class SaveAPIKeyRequest(BaseModel):
    provider: str
    api_key: str


class SetPreferencesRequest(BaseModel):
    provider: str
    model: str
    ollama_base_url: Optional[str] = "http://localhost:11434"


class TestConnectionRequest(BaseModel):
    provider: str
    model: Optional[str] = None
    api_key: Optional[str] = None      # If provided, test with THIS key (not stored)
    ollama_base_url: Optional[str] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/providers")
async def list_providers():
    """Return all supported providers and their available models."""
    return {
        "providers": [
            {
                "id": "openai",
                "name": "OpenAI",
                "description": "GPT-4o, GPT-4o Mini, GPT-3.5 Turbo",
                "requires_key": True,
                "get_key_url": "https://platform.openai.com/api-keys",
                "models": PROVIDER_MODELS[LLMProvider.OPENAI],
            },
            {
                "id": "anthropic",
                "name": "Anthropic (Claude)",
                "description": "Claude Opus, Sonnet, Haiku",
                "requires_key": True,
                "get_key_url": "https://console.anthropic.com/account/keys",
                "models": PROVIDER_MODELS[LLMProvider.ANTHROPIC],
            },
            {
                "id": "groq",
                "name": "Groq (Ultra-Fast)",
                "description": "Llama 3.1, Mixtral — extremely fast inference",
                "requires_key": True,
                "get_key_url": "https://console.groq.com/keys",
                "models": PROVIDER_MODELS[LLMProvider.GROQ],
            },
            {
                "id": "gemini",
                "name": "Google Gemini",
                "description": "Gemini 1.5 Pro/Flash with 1M context",
                "requires_key": True,
                "get_key_url": "https://aistudio.google.com/app/apikey",
                "models": PROVIDER_MODELS[LLMProvider.GEMINI],
            },
            {
                "id": "cohere",
                "name": "Cohere",
                "description": "Command R+ — great for RAG and search",
                "requires_key": True,
                "get_key_url": "https://dashboard.cohere.com/api-keys",
                "models": PROVIDER_MODELS[LLMProvider.COHERE],
            },
            {
                "id": "ollama",
                "name": "Ollama (Local / Free)",
                "description": "Run open-source models locally. No API key needed.",
                "requires_key": False,
                "get_key_url": "https://ollama.ai",
                "models": [],  # Loaded dynamically
            },
            {
                "id": "openrouter",
                "name": "OpenRouter (Free Tier)",
                "description": "Access many models including free options",
                "requires_key": True,
                "get_key_url": "https://openrouter.ai/keys",
                "models": PROVIDER_MODELS[LLMProvider.OPENROUTER],
            },
        ]
    }


@router.get("/ollama/models")
async def list_ollama_models(
    base_url: str = "http://localhost:11434",
    current_user: User = Depends(get_current_user),
):
    """Fetch locally installed Ollama models."""
    url = base_url or current_user.ollama_base_url or "http://localhost:11434"
    models = await get_ollama_models(url)
    return {"models": models, "base_url": url}


@router.post("/keys")
async def save_api_key(
    body: SaveAPIKeyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save (encrypted) an API key for a provider."""
    if body.provider not in [p.value for p in LLMProvider if p != LLMProvider.OLLAMA]:
        raise HTTPException(status_code=400, detail="Unknown provider")

    encrypted = encrypt_api_key(body.api_key)
    keys = current_user.llm_api_keys or {}
    keys[body.provider] = encrypted
    current_user.llm_api_keys = keys
    db.commit()

    return {"message": f"API key for {body.provider} saved successfully"}


@router.delete("/keys/{provider}")
async def delete_api_key(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a stored API key."""
    keys = current_user.llm_api_keys or {}
    keys.pop(provider, None)
    current_user.llm_api_keys = keys
    db.commit()
    return {"message": f"API key for {provider} removed"}


@router.get("/keys/status")
async def get_keys_status(current_user: User = Depends(get_current_user)):
    """Return which providers have keys configured (without revealing keys)."""
    keys = current_user.llm_api_keys or {}
    return {
        "configured_providers": list(keys.keys()),
        "preferred_provider": current_user.preferred_provider,
        "preferred_model": current_user.preferred_model,
        "ollama_base_url": current_user.ollama_base_url,
    }


@router.post("/preferences")
async def set_preferences(
    body: SetPreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Set preferred LLM provider and model."""
    current_user.preferred_provider = body.provider
    current_user.preferred_model = body.model
    if body.ollama_base_url:
        current_user.ollama_base_url = body.ollama_base_url
    db.commit()
    return {"message": "Preferences saved", "provider": body.provider, "model": body.model}


@router.post("/test")
async def test_llm_connection(
    body: TestConnectionRequest,
    current_user: User = Depends(get_current_user),
):
    """Test connectivity to a provider with the given (or stored) key."""
    from core.security import decrypt_api_key

    # Resolve API key: use provided key first, then stored key
    api_key = body.api_key
    if not api_key and body.provider != "ollama":
        stored_keys = current_user.llm_api_keys or {}
        if body.provider in stored_keys:
            api_key = decrypt_api_key(stored_keys[body.provider])

    ollama_url = body.ollama_base_url or current_user.ollama_base_url or "http://localhost:11434"

    client = LLMClient(
        provider=body.provider,
        api_key=api_key,
        model=body.model,
        base_url=ollama_url if body.provider == "ollama" else None,
    )

    result = await client.test_connection()
    return result
