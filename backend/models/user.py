"""
User SQLAlchemy model
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON
from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    skill_level = Column(String, default="intermediate")  # beginner | intermediate | advanced
    interests = Column(JSON, default=list)  # list of domain strings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Encrypted LLM API keys stored as JSON
    # Format: {"openai": "encrypted...", "anthropic": "encrypted...", etc.}
    llm_api_keys = Column(JSON, default=dict)

    # LLM preferences
    preferred_provider = Column(String, default="ollama")
    preferred_model = Column(String, default="llama3.2")
    ollama_base_url = Column(String, default="http://localhost:11434")

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"
