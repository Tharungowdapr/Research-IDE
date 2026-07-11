"""
Project and Output SQLAlchemy models
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship
from core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    input_text = Column(Text, nullable=False)
    status = Column(String, default="created")  # created | processing | ideas | planning | done
    current_stage = Column(String, default="input")  # analysis | papers | gaps | ideas | objectives | planner | data | code | experiments | results | guide | report | publish
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    outputs = relationship("Output", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project id={self.id} title={self.title}>"


class Output(Base):
    __tablename__ = "outputs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    output_type = Column(String, nullable=False)  # intent | papers | gaps | ideas | plan | code | report | analysis | objectives | data_plan | experiments | analysis_template | guide | review
    data = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    project = relationship("Project", back_populates="outputs")

    def __repr__(self):
        return f"<Output id={self.id} type={self.output_type}>"


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    energy_wh = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<UsageLog user={self.user_id} provider={self.provider} tokens={self.total_tokens}>"


class PaperCache(Base):
    __tablename__ = "paper_cache"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    external_id = Column(String, unique=True, index=True)  # DOI, arXiv ID, etc.
    title = Column(Text, nullable=False)
    abstract = Column(Text)
    full_text = Column(Text)
    authors = Column(JSON, default=list)
    year = Column(String)
    citations = Column(String, default="0")
    source = Column(String)  # arxiv | semantic_scholar | openalex
    url = Column(Text)
    methods = Column(JSON, default=list)
    datasets = Column(JSON, default=list)
    limitations = Column(JSON, default=list)
    embedding = Column(JSON)  # stored as list of floats
    cached_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PipelineLog(Base):
    __tablename__ = "pipeline_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    stage = Column(String, nullable=False)
    status = Column(String, nullable=False)  # running | done | error
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime)
    output_size_bytes = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
