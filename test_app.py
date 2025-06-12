from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List
import uvicorn
import uuid
from datetime import datetime

app = FastAPI(title="Document Processing Service - Test", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# In-memory storage for testing
artifacts_db = []
templates_db = []

# Pydantic models
class TemplateRequest(BaseModel):
    name: str
    description: str
    system_prompt: str
    user_prompt_template: str
    json_schema: Dict[str, Any]
    preferred_format: str

class ExtractionRequest(BaseModel):
    template_id: str

@app.get("/")
async def read_root():
    """Serve the main web interface"""
    return FileResponse('app/static/index.html')

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/artifacts/upload")
async def upload_artifact(file: UploadFile = File(...)):
    """Test upload endpoint"""
    artifact_id = str(uuid.uuid4())
    artifact = {
        "id": artifact_id,
        "filename": f"{artifact_id}_{file.filename}",
        "original_filename": file.filename,
        "file_size": 0,  # Would be actual size in real implementation
        "mime_type": file.content_type or "application/octet-stream",
        "created_at": datetime.utcnow().isoformat()
    }
    artifacts_db.append(artifact)
    return artifact

@app.get("/artifacts")
async def list_artifacts():
    """List all artifacts"""
    return artifacts_db

@app.post("/templates")
async def create_template(template: TemplateRequest):
    """Create a processing template"""
    template_id = str(uuid.uuid4())
    template_data = {
        "id": template_id,
        "name": template.name,
        "description": template.description,
        "system_prompt": template.system_prompt,
        "user_prompt_template": template.user_prompt_template,
        "json_schema": template.json_schema,
        "preferred_format": template.preferred_format,
        "created_at": datetime.utcnow().isoformat()
    }
    templates_db.append(template_data)
    return template_data

@app.get("/templates")
async def list_templates():
    """List all templates"""
    return templates_db

@app.post("/artifacts/{artifact_id}/extract")
async def extract_data(artifact_id: str, request: ExtractionRequest):
    """Mock extraction endpoint - returns fake data since we don't have LLM setup"""
    artifact = next((a for a in artifacts_db if a["id"] == artifact_id), None)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    template = next((t for t in templates_db if t["id"] == request.template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Mock extraction result
    mock_extracted_data = {
        "invoice_number": "INV-2024-001",
        "date": "January 15, 2024",
        "total": 9720.00,
        "vendor": "Tech Solutions Inc."
    }
    
    return {
        "id": str(uuid.uuid4()),
        "artifact_id": artifact_id,
        "template_id": request.template_id,
        "success": True,
        "extracted_data": mock_extracted_data,
        "llm_model": "mock-model",
        "processing_time_seconds": 2,
        "created_at": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)