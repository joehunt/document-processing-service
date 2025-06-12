from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os
from pathlib import Path
import magic
import uuid
from datetime import datetime

from app.database import get_db, create_tables
from app.models import Artifact, Conversion, ProcessingTemplate, Extraction
from app.conversion_service import ConversionService
from app.llm_service import LLMService, LLMConfig
from app.schemas import *

app = FastAPI(title="Document Processing Service", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Initialize services
STORAGE_PATH = "/app/storage"
Path(STORAGE_PATH).mkdir(exist_ok=True)
conversion_service = ConversionService(STORAGE_PATH)

# LLM configuration from environment
llm_config = LLMConfig(
    provider=os.getenv("LLM_PROVIDER", "openai"),
    model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
    api_key=os.getenv("LLM_API_KEY", ""),
    temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
    max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4000"))
)

if llm_config.api_key:
    llm_service = LLMService(llm_config)
else:
    llm_service = None

@app.on_event("startup")
async def startup_event():
    create_tables()

@app.post("/artifacts/upload", response_model=ArtifactResponse)
async def upload_artifact(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a document and create an artifact"""
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        filename = f"{file_id}{file_extension}"
        file_path = Path(STORAGE_PATH) / "uploads" / filename
        file_path.parent.mkdir(exist_ok=True)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file info
        file_size = file_path.stat().st_size
        mime_type = magic.from_file(str(file_path), mime=True)
        
        # Create artifact record
        artifact = Artifact(
            id=file_id,
            filename=filename,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            mime_type=mime_type
        )
        
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        
        return ArtifactResponse.from_orm(artifact)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/artifacts/{artifact_id}/convert", response_model=ConversionResponse)
async def convert_artifact(
    artifact_id: str,
    request: ConversionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Convert an artifact to a different format"""
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    # Check if conversion already exists
    existing = db.query(Conversion).filter(
        Conversion.artifact_id == artifact_id,
        Conversion.format == request.format
    ).first()
    
    if existing:
        return ConversionResponse.from_orm(existing)
    
    # Perform conversion
    result = conversion_service.convert_document(artifact.file_path, request.format)
    
    # Create conversion record
    conversion = Conversion(
        artifact_id=artifact_id,
        format=request.format,
        file_path=result.get("output_path", ""),
        file_size=result.get("file_size", 0),
        success=result["success"],
        error_message=result.get("error")
    )
    
    db.add(conversion)
    db.commit()
    db.refresh(conversion)
    
    return ConversionResponse.from_orm(conversion)

@app.post("/templates", response_model=TemplateResponse)
async def create_template(
    request: TemplateRequest,
    db: Session = Depends(get_db)
):
    """Create a processing template"""
    template = ProcessingTemplate(
        name=request.name,
        description=request.description,
        system_prompt=request.system_prompt,
        user_prompt_template=request.user_prompt_template,
        json_schema=request.json_schema,
        preferred_format=request.preferred_format
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return TemplateResponse.from_orm(template)

@app.get("/templates", response_model=List[TemplateResponse])
async def list_templates(db: Session = Depends(get_db)):
    """List all processing templates"""
    templates = db.query(ProcessingTemplate).all()
    return [TemplateResponse.from_orm(t) for t in templates]

@app.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str, db: Session = Depends(get_db)):
    """Get a specific template by ID"""
    template = db.query(ProcessingTemplate).filter(ProcessingTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateResponse.from_orm(template)

@app.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    request: TemplateRequest,
    db: Session = Depends(get_db)
):
    """Update an existing template"""
    template = db.query(ProcessingTemplate).filter(ProcessingTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Update template fields
    template.name = request.name
    template.description = request.description
    template.system_prompt = request.system_prompt
    template.user_prompt_template = request.user_prompt_template
    template.json_schema = request.json_schema
    template.preferred_format = request.preferred_format
    
    db.commit()
    db.refresh(template)
    
    return TemplateResponse.from_orm(template)

@app.delete("/templates/{template_id}")
async def delete_template(template_id: str, db: Session = Depends(get_db)):
    """Delete a template"""
    template = db.query(ProcessingTemplate).filter(ProcessingTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(template)
    db.commit()
    
    return {"message": "Template deleted successfully"}

@app.post("/artifacts/{artifact_id}/extract", response_model=ExtractionResponse)
async def extract_data(
    artifact_id: str,
    request: ExtractionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Extract structured data from an artifact using a template"""
    if not llm_service:
        raise HTTPException(status_code=503, detail="LLM service not configured")
    
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    template = db.query(ProcessingTemplate).filter(ProcessingTemplate.id == request.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Get document in preferred format
    document_text = ""
    if template.preferred_format == "text":
        document_text = conversion_service.extract_text(artifact.file_path)
    else:
        # Check if conversion exists
        conversion = db.query(Conversion).filter(
            Conversion.artifact_id == artifact_id,
            Conversion.format == template.preferred_format,
            Conversion.success == True
        ).first()
        
        if conversion:
            # Use conversion service to safely extract text
            document_text = conversion_service.extract_text(conversion.file_path)
        else:
            # Convert on demand
            result = conversion_service.convert_document(artifact.file_path, template.preferred_format)
            if result["success"]:
                # Use conversion service to safely extract text
                document_text = conversion_service.extract_text(result["output_path"])
            else:
                raise HTTPException(status_code=500, detail=f"Conversion failed: {result['error']}")
    
    # Perform extraction
    print(f"DEBUG: About to extract from document with {len(document_text)} characters")
    print(f"DEBUG: Using template: {template.name}")
    result = llm_service.extract_data(
        document_text,
        template.system_prompt,
        template.user_prompt_template,
        template.json_schema
    )
    print(f"DEBUG: Extraction result success: {result.get('success')}")
    if not result.get('success'):
        print(f"DEBUG: Error: {result.get('error')}")
        print(f"DEBUG: Raw response: {result.get('raw_response', 'No raw response')[:200]}")
    
    # Create extraction record
    extraction = Extraction(
        artifact_id=artifact_id,
        template_id=request.template_id,
        success=result["success"],
        extracted_data=result.get("extracted_data"),
        error_message=result.get("error"),
        llm_model=llm_config.model,
        processing_time_seconds=int(result["processing_time_seconds"])
    )
    
    db.add(extraction)
    db.commit()
    db.refresh(extraction)
    
    return ExtractionResponse.from_orm(extraction)

@app.get("/extractions", response_model=List[ExtractionResponse])
async def list_extractions(db: Session = Depends(get_db)):
    """List all extractions"""
    extractions = db.query(Extraction).order_by(Extraction.extraction_date.desc()).all()
    return [ExtractionResponse.from_orm(e) for e in extractions]

@app.get("/artifacts/{artifact_id}", response_model=ArtifactDetailResponse)
async def get_artifact(artifact_id: str, db: Session = Depends(get_db)):
    """Get artifact with all conversions and extractions"""
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    return ArtifactDetailResponse.from_orm(artifact)

@app.get("/artifacts", response_model=List[ArtifactResponse])
async def list_artifacts(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """List all artifacts"""
    artifacts = db.query(Artifact).offset(skip).limit(limit).all()
    return [ArtifactResponse.from_orm(a) for a in artifacts]

@app.get("/")
async def read_root():
    """Serve the main web interface"""
    from fastapi.responses import FileResponse
    return FileResponse('app/static/index.html')

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)