"""
Project and Output SQLAlchemy models
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    input_text = Column(Text, nullable=False)
    status = Column(String, default="created")  # created | processing | ideas | planning | done
    current_stage = Column(String, default="input")  # input | papers | gaps | ideas | planner | code | report
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    outputs = relationship("Output", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project id={self.id} title={self.title}>"


class Output(Base):
    __tablename__ = "outputs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    output_type = Column(String, nullable=False)  # intent | papers | gaps | ideas | plan | code | report
    data = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    project = relationship("Project", back_populates="outputs")

    def __repr__(self):
        return f"<Output id={self.id} type={self.output_type}>"


class PaperCache(Base):
    __tablename__ = "paper_cache"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    external_id = Column(String, unique=True, index=True)  # DOI, arXiv ID, etc.
    title = Column(Text, nullable=False)
    abstract = Column(Text)
    authors = Column(JSON, default=list)
    year = Column(String)
    citations = Column(String, default="0")
    source = Column(String)  # arxiv | semantic_scholar | openalex
    url = Column(Text)
    methods = Column(JSON, default=list)
    datasets = Column(JSON, default=list)
    limitations = Column(JSON, default=list)
    embedding = Column(JSON)  # stored as list of floats
    cached_at = Column(DateTime, default=datetime.utcnow)
