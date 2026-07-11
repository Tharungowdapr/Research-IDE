"""
Application Configuration
All settings loaded from environment variables with defaults.
"""

from pydantic_settings import BaseSettings
from typing import List
import os
import json


_DEFAULT_SECRET = "change-this-in-production-use-a-long-random-string"
_DEFAULT_ENCRYPTION = "change-this-32-char-encryption-key!"


def _parse_cors(origins_val) -> List[str]:
    if isinstance(origins_val, list):
        return origins_val
    s = str(origins_val).strip()
    if s.startswith("["):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            pass
    return [o.strip().strip('"').strip("'") for o in s.split(",") if o.strip()]


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ResearchIDE"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./research_ide.db"

    # Redis (for Celery task queue)
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    SECRET_KEY: str = _DEFAULT_SECRET
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # ── LLM Provider Keys (users set these per-account, stored encrypted) ──
    # These are DEFAULTS used if user has no key set
    DEFAULT_LLM_PROVIDER: str = "ollama"  # ollama | openai | anthropic | groq | gemini | cohere

    # Ollama settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = "llama3.2"

    # Encryption key for storing user API keys
    ENCRYPTION_KEY: str = _DEFAULT_ENCRYPTION
    
    # Gemini API key
    GEMINI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True

    def model_post_init(self, __context) -> None:
        import os
        if os.environ.get("TESTING") == "1":
            return
        if self.SECRET_KEY == _DEFAULT_SECRET:
            raise ValueError(
                "SECRET_KEY is set to an insecure default. "
                "Set a strong SECRET_KEY in your .env file."
            )
        if self.ENCRYPTION_KEY == _DEFAULT_ENCRYPTION:
            raise ValueError(
                "ENCRYPTION_KEY is set to an insecure default. "
                "Set a 32-char ENCRYPTION_KEY in your .env file."
            )


settings = Settings()

# Parse ALLOWED_ORIGINS from env var if pydantic didn't handle it
_env_origins = os.environ.get("ALLOWED_ORIGINS", "")
if _env_origins and len(settings.ALLOWED_ORIGINS) <= 2:
    settings.ALLOWED_ORIGINS = _parse_cors(_env_origins)
