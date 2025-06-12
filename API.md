# API Documentation

This document provides comprehensive API documentation for the Document Processing Service.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: Update with your production URL

## Authentication

Currently, the API does not require authentication. For production deployment, consider adding API keys or OAuth.

## API Endpoints

### Health Check

#### GET /health
Check if the service is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-03-15T10:30:00.000Z"
}
```

---

## Artifacts (Document Management)

### Upload Document

#### POST /artifacts/upload
Upload a document for processing.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with `file` field

**Supported File Types:**
- PDF (`.pdf`)
- Microsoft Word (`.doc`, `.docx`) 
- Microsoft Excel (`.xls`, `.xlsx`)
- Microsoft PowerPoint (`.ppt`, `.pptx`)
- Text files (`.txt`, `.md`, `.csv`)
- LibreOffice formats (`.odt`, `.ods`, `.odp`)

**Response:**
```json
{
  "id": "uuid-string",
  "filename": "generated-filename.pdf",
  "original_filename": "document.pdf",
  "file_size": 1234567,
  "mime_type": "application/pdf",
  "upload_date": "2024-03-15T10:30:00.000Z"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/artifacts/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### List Artifacts

#### GET /artifacts
Retrieve all uploaded artifacts.

**Query Parameters:**
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Maximum records to return (default: 100)

**Response:**
```json
[
  {
    "id": "uuid-string",
    "filename": "document.pdf",
    "original_filename": "document.pdf",
    "file_size": 1234567,
    "mime_type": "application/pdf",
    "upload_date": "2024-03-15T10:30:00.000Z"
  }
]
```

### Get Artifact Details

#### GET /artifacts/{artifact_id}
Get detailed information about a specific artifact, including conversions and extractions.

**Path Parameters:**
- `artifact_id` (string): UUID of the artifact

**Response:**
```json
{
  "id": "uuid-string",
  "filename": "document.pdf", 
  "original_filename": "document.pdf",
  "file_size": 1234567,
  "mime_type": "application/pdf",
  "upload_date": "2024-03-15T10:30:00.000Z",
  "conversions": [
    {
      "id": "conv-uuid",
      "format": "txt",
      "file_path": "/app/storage/conversions/doc_txt.txt",
      "file_size": 5432,
      "success": true,
      "conversion_date": "2024-03-15T10:31:00.000Z"
    }
  ],
  "extractions": [
    {
      "id": "ext-uuid",
      "template_id": "template-uuid",
      "success": true,
      "extracted_data": {...},
      "llm_model": "gpt-4o-mini",
      "processing_time_seconds": 3,
      "extraction_date": "2024-03-15T10:32:00.000Z"
    }
  ]
}
```

### Convert Document

#### POST /artifacts/{artifact_id}/convert
Convert an artifact to a different format.

**Path Parameters:**
- `artifact_id` (string): UUID of the artifact

**Request Body:**
```json
{
  "format": "txt"
}
```

**Supported Output Formats:**
- `txt` - Plain text
- `pdf` - PDF document
- `csv` - Comma-separated values
- `html` - HTML document

**Response:**
```json
{
  "id": "conv-uuid",
  "artifact_id": "artifact-uuid",
  "format": "txt",
  "file_path": "/app/storage/conversions/doc_txt.txt",
  "file_size": 5432,
  "success": true,
  "conversion_date": "2024-03-15T10:31:00.000Z"
}
```

---

## Templates (Processing Configuration)

### Create Template

#### POST /templates
Create a new processing template for data extraction.

**Request Body:**
```json
{
  "name": "Invoice Extractor",
  "description": "Extract key fields from invoices",
  "system_prompt": "You are an expert at extracting structured data from invoices.",
  "user_prompt_template": "Extract the following information from this invoice:\n\n{document}",
  "json_schema": {
    "type": "object",
    "properties": {
      "invoice_number": {"type": "string"},
      "date": {"type": "string"},
      "total": {"type": "number"},
      "vendor": {"type": "string"}
    },
    "required": ["invoice_number", "date", "total", "vendor"]
  },
  "preferred_format": "text"
}
```

**Field Descriptions:**
- `name`: Unique name for the template
- `description`: Human-readable description
- `system_prompt`: LLM system instructions
- `user_prompt_template`: User prompt with `{document}` placeholder
- `json_schema`: JSON schema for output validation
- `preferred_format`: Format to convert documents to before processing

**Response:**
```json
{
  "id": "template-uuid",
  "name": "Invoice Extractor",
  "description": "Extract key fields from invoices",
  "system_prompt": "You are an expert...",
  "user_prompt_template": "Extract the following...",
  "json_schema": {...},
  "preferred_format": "text",
  "created_date": "2024-03-15T10:30:00.000Z"
}
```

### List Templates

#### GET /templates
Retrieve all processing templates.

**Response:**
```json
[
  {
    "id": "template-uuid",
    "name": "Invoice Extractor",
    "description": "Extract key fields from invoices",
    "system_prompt": "You are an expert...",
    "user_prompt_template": "Extract the following...",
    "json_schema": {...},
    "preferred_format": "text",
    "created_date": "2024-03-15T10:30:00.000Z"
  }
]
```

### Get Template

#### GET /templates/{template_id}
Get details of a specific template.

**Path Parameters:**
- `template_id` (string): UUID of the template

**Response:** Same as create template response.

### Update Template

#### PUT /templates/{template_id}
Update an existing template.

**Path Parameters:**
- `template_id` (string): UUID of the template

**Request Body:** Same as create template request.

**Response:** Updated template object.

### Delete Template

#### DELETE /templates/{template_id}
Delete a template.

**Path Parameters:**
- `template_id` (string): UUID of the template

**Response:**
```json
{
  "message": "Template deleted successfully"
}
```

---

## Data Extraction

### Extract Data

#### POST /artifacts/{artifact_id}/extract
Extract structured data from an artifact using a template.

**Path Parameters:**
- `artifact_id` (string): UUID of the artifact

**Request Body:**
```json
{
  "template_id": "template-uuid"
}
```

**Response:**
```json
{
  "id": "extraction-uuid",
  "artifact_id": "artifact-uuid",
  "template_id": "template-uuid",
  "success": true,
  "extracted_data": {
    "invoice_number": "INV-2024-001",
    "date": "2024-03-15",
    "total": 1250.00,
    "vendor": "Tech Solutions Inc"
  },
  "llm_model": "gpt-4o-mini",
  "processing_time_seconds": 3,
  "extraction_date": "2024-03-15T10:32:00.000Z"
}
```

**Error Response (when extraction fails):**
```json
{
  "id": "extraction-uuid",
  "artifact_id": "artifact-uuid", 
  "template_id": "template-uuid",
  "success": false,
  "extracted_data": null,
  "error_message": "Invalid JSON response from LLM",
  "llm_model": "gpt-4o-mini",
  "processing_time_seconds": 2,
  "extraction_date": "2024-03-15T10:32:00.000Z"
}
```

### List Extractions

#### GET /extractions
Retrieve all extractions (newest first).

**Response:**
```json
[
  {
    "id": "extraction-uuid",
    "artifact_id": "artifact-uuid",
    "template_id": "template-uuid", 
    "success": true,
    "extracted_data": {...},
    "llm_model": "gpt-4o-mini",
    "processing_time_seconds": 3,
    "extraction_date": "2024-03-15T10:32:00.000Z"
  }
]
```

---

## Error Handling

### HTTP Status Codes

- `200` - Success
- `404` - Resource not found
- `422` - Validation error
- `500` - Internal server error
- `503` - Service unavailable (LLM not configured)

### Error Response Format

```json
{
  "detail": "Error description"
}
```

### Common Errors

#### 404 Not Found
```json
{
  "detail": "Artifact not found"
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 503 Service Unavailable
```json
{
  "detail": "LLM service not configured"
}
```

---

## Configuration

### Environment Variables

The API behavior is controlled by environment variables:

```bash
# LLM Configuration
LLM_PROVIDER=openai          # "openai" or "anthropic"
LLM_MODEL=gpt-4o-mini        # Model name
LLM_API_KEY=sk-...           # API key (OPENAI_API_KEY or ANTHROPIC_API_KEY)
LLM_TEMPERATURE=0.1          # Temperature (0.0-1.0)
LLM_MAX_TOKENS=4000          # Maximum tokens

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Optional Settings
STORAGE_PATH=/app/storage    # File storage location
```

### LLM Provider Setup

#### OpenAI
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-proj-...
```

#### Anthropic
```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Interactive API Documentation

Once the service is running, you can access interactive API documentation at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These interfaces allow you to test API endpoints directly from your browser.

---

## Rate Limits & Usage

### Current Limits
- No rate limiting implemented
- File upload size limited by FastAPI defaults (16MB)
- LLM API calls subject to provider limits

### Recommendations for Production
- Implement API rate limiting
- Add file size restrictions based on needs
- Monitor LLM API usage and costs
- Add request logging and analytics

---

## SDK Examples

### Python SDK Example

```python
import requests
import json

class DocumentProcessingClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def upload_document(self, file_path):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{self.base_url}/artifacts/upload", files=files)
            return response.json()
    
    def create_template(self, name, description, system_prompt, user_prompt, schema):
        data = {
            "name": name,
            "description": description,
            "system_prompt": system_prompt,
            "user_prompt_template": user_prompt,
            "json_schema": schema,
            "preferred_format": "text"
        }
        response = requests.post(f"{self.base_url}/templates", json=data)
        return response.json()
    
    def extract_data(self, artifact_id, template_id):
        data = {"template_id": template_id}
        response = requests.post(f"{self.base_url}/artifacts/{artifact_id}/extract", json=data)
        return response.json()

# Usage
client = DocumentProcessingClient()
artifact = client.upload_document("invoice.pdf")
template = client.create_template("Invoice", "Extract invoice data", ...)
result = client.extract_data(artifact["id"], template["id"])
print(result["extracted_data"])
```

### JavaScript SDK Example

```javascript
class DocumentProcessingClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async uploadDocument(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${this.baseUrl}/artifacts/upload`, {
            method: 'POST',
            body: formData
        });
        
        return await response.json();
    }
    
    async createTemplate(templateData) {
        const response = await fetch(`${this.baseUrl}/templates`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(templateData)
        });
        
        return await response.json();
    }
    
    async extractData(artifactId, templateId) {
        const response = await fetch(`${this.baseUrl}/artifacts/${artifactId}/extract`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ template_id: templateId })
        });
        
        return await response.json();
    }
}

// Usage
const client = new DocumentProcessingClient();
const artifact = await client.uploadDocument(fileInput.files[0]);
const template = await client.createTemplate({...});
const result = await client.extractData(artifact.id, template.id);
console.log(result.extracted_data);
```