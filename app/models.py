"""
Database Models

This module defines the SQLAlchemy ORM models for the document processing service.
Models represent the core entities: artifacts (uploaded documents), processing
templates, conversions, and extractions.

Author: Generated with Claude Code
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Artifact(Base):
    """
    Represents an uploaded document/file.
    
    Artifacts are the core entities that get processed. They store metadata
    about uploaded files and have relationships to conversions and extractions.
    """
    __tablename__ = "artifacts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversions = relationship("Conversion", back_populates="artifact", cascade="all, delete-orphan")
    extractions = relationship("Extraction", back_populates="artifact", cascade="all, delete-orphan")

class Conversion(Base):
    __tablename__ = "conversions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    artifact_id = Column(String, ForeignKey("artifacts.id"), nullable=False)
    format = Column(String, nullable=False)  # pdf, text, csv, markdown
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    conversion_date = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Relationships
    artifact = relationship("Artifact", back_populates="conversions")

class ProcessingTemplate(Base):
    __tablename__ = "processing_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    system_prompt = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=False)
    json_schema = Column(JSON, nullable=False)
    preferred_format = Column(String, default="text")  # pdf, text, csv, markdown
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    extractions = relationship("Extraction", back_populates="template")

class Extraction(Base):
    __tablename__ = "extractions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    artifact_id = Column(String, ForeignKey("artifacts.id"), nullable=False)
    template_id = Column(String, ForeignKey("processing_templates.id"), nullable=False)
    extraction_date = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
    extracted_data = Column(JSON)
    error_message = Column(Text)
    llm_model = Column(String)
    processing_time_seconds = Column(Integer)
    
    # Relationships
    artifact = relationship("Artifact", back_populates="extractions")
    template = relationship("ProcessingTemplate", back_populates="extractions")