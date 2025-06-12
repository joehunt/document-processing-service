from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ArtifactResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    upload_date: datetime
    
    class Config:
        from_attributes = True

class ConversionRequest(BaseModel):
    format: str  # pdf, txt, csv, html

class ConversionResponse(BaseModel):
    id: str
    artifact_id: str
    format: str
    file_size: int
    conversion_date: datetime
    success: bool
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class TemplateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str
    user_prompt_template: str
    json_schema: Dict[str, Any]
    preferred_format: str = "text"

class TemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    system_prompt: str
    user_prompt_template: str
    json_schema: Dict[str, Any]
    preferred_format: str
    created_date: datetime
    
    class Config:
        from_attributes = True

class ExtractionRequest(BaseModel):
    template_id: str

class ExtractionResponse(BaseModel):
    id: str
    artifact_id: str
    template_id: str
    extraction_date: datetime
    success: bool
    extracted_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    llm_model: Optional[str] = None
    processing_time_seconds: Optional[int] = None
    
    class Config:
        from_attributes = True

class ArtifactDetailResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    upload_date: datetime
    conversions: List[ConversionResponse]
    extractions: List[ExtractionResponse]
    
    class Config:
        from_attributes = True